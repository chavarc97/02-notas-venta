import io
import os
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.nota import Nota, ContenidoNota
from app.schemas.nota_schema import NotaCreate, NotaResponse

from app.services.pdf_generator import PDFGenerator
from app.services.s3_service import S3Service

router = APIRouter(prefix="/notas", tags=["notas"])

s3_service = S3Service()

CATALOGO_SERVICE_URL = os.environ.get("CATALOGO_SERVICE_URL", "http://localhost:8001")
NOTIFICACIONES_SERVICE_URL = os.environ.get("NOTIFICACIONES_SERVICE_URL", "http://localhost:8002")

@router.post("/", response_model=NotaResponse)
def create_nota(nota: NotaCreate, request: Request, db: Session = Depends(get_db)):
    # 1. Validate Existence of Client via HTTP
    client_resp = requests.get(f"{CATALOGO_SERVICE_URL}/clientes/{nota.cliente_id}")
    if client_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en el microservicio de catálogo")
    client_data = client_resp.json()

    # 2. Prevent Folio Collisions
    if db.query(Nota).filter(Nota.folio == nota.folio).first():
        raise HTTPException(status_code=400, detail="El folio ya existe")

    # 3. Create Note core record
    db_nota = Nota(
        folio=nota.folio,
        cliente_id=nota.cliente_id,
        direccion_facturacion_id=nota.direccion_facturacion_id,
        direccion_envio_id=nota.direccion_envio_id,
        total_de_la_nota=0.0,
    )
    db.add(db_nota)
    db.flush()

    total = 0.0
    report_contents = []

    # 4. Fill in Contents and calculate totals
    for item in nota.contenidos:
        prod_resp = requests.get(f"{CATALOGO_SERVICE_URL}/productos/{item.producto_id}")
        if prod_resp.status_code != 200:
            db.rollback()
            raise HTTPException(
                status_code=404, detail=f"Producto {item.producto_id} no encontrado en catálogo"
            )
        prod_data = prod_resp.json()

        importe = item.cantidad * item.precio_unitario
        total += importe

        db_contenido = ContenidoNota(
            nota_id=db_nota.id,
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            importe=importe,
        )
        db.add(db_contenido)

        report_contents.append(
            {
                "cantidad": item.cantidad,
                "nombre": prod_data["nombre"],
                "precio_unitario": item.precio_unitario,
                "importe": importe,
            }
        )

    db_nota.total_de_la_nota = total
    db.commit()
    db.refresh(db_nota)

    # 5. Generate PDF
    pdf_data = {
        "client": {
            "razon_social": client_data.get("razon_social"),
            "nombre_comercial": client_data.get("nombre_comercial"),
            "rfc": client_data.get("rfc"),
            "email": client_data.get("email"),
            "telefono": client_data.get("telefono"),
        },
        "nota": {"folio": db_nota.folio},
        "contenidos": report_contents,
    }

    pdf_bytes = PDFGenerator.generate_nota_pdf(pdf_data)

    # 6. Upload PDF to S3 with Initial Metadata
    s3_key = f"{client_data['rfc']}/{db_nota.folio}.pdf"
    success, error = s3_service.upload_pdf(pdf_bytes, s3_key)
    if not success:
        print(f"Error uploading to S3: {error}")

    return db_nota


@router.get("/{folio}", response_model=NotaResponse)
def get_nota_json(folio: str, db: Session = Depends(get_db)):
    """Lectura de una nota de venta (Mostrar un JSON, los metadatos no deben de afectarse)"""
    db_nota = db.query(Nota).filter(Nota.folio == folio).first()
    if not db_nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return db_nota


@router.get("/{folio}/download")
def download_nota_pdf(folio: str, db: Session = Depends(get_db)):
    """Descarga de una nota de venta (Descargar PDF, los metadatos deben de afectarse)"""
    db_nota = db.query(Nota).filter(Nota.folio == folio).first()
    if not db_nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada en BD")

    client_resp = requests.get(f"{CATALOGO_SERVICE_URL}/clientes/{db_nota.cliente_id}")
    if client_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en catálogo")
    client_data = client_resp.json()

    s3_key = f"{client_data['rfc']}/{db_nota.folio}.pdf"

    file_bytes, _ = s3_service.get_pdf(s3_key)

    if not file_bytes:
        raise HTTPException(status_code=404, detail="PDF no encontrado en S3")

    # Update Metadata (nota-descargada: true)
    s3_service.set_nota_descargada(s3_key)

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={db_nota.folio}.pdf"},
    )


@router.post("/{folio}/send")
def send_nota_email(folio: str, request: Request, db: Session = Depends(get_db)):
    """Endpoint para envio de notas de venta"""
    db_nota = db.query(Nota).filter(Nota.folio == folio).first()
    if not db_nota:
        raise HTTPException(status_code=404, detail="Nota no encontrada")

    client_resp = requests.get(f"{CATALOGO_SERVICE_URL}/clientes/{db_nota.cliente_id}")
    if client_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en catálogo")
    client_data = client_resp.json()

    s3_key = f"{client_data['rfc']}/{db_nota.folio}.pdf"

    public_base = os.environ.get("PUBLIC_BASE_URL", str(request.base_url).rstrip("/"))
    download_link = f"{public_base}/notas/{folio}/download"

    # Comunicación HTTP con Notificaciones
    notify_resp = requests.post(
        f"{NOTIFICACIONES_SERVICE_URL}/notificaciones/send",
        json={"folio": db_nota.folio, "download_link": download_link}
    )

    if notify_resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error al enviar correo (desde microservicio): {notify_resp.text}")

    # Update S3 metadata (veces-enviado + 1, hora-envio)
    s3_service.increment_enviado(s3_key)

    return notify_resp.json()
