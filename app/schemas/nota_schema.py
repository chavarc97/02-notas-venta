from pydantic import BaseModel
from typing import List


# --- ContenidoNota Schemas ---
class ContenidoNotaBase(BaseModel):
    producto_id: int
    cantidad: int
    precio_unitario: float


class ContenidoNotaCreate(ContenidoNotaBase):
    # El importe se debe calcular en el backend y no pedirlo al usuario por seguridad
    pass


class ContenidoNotaResponse(ContenidoNotaBase):
    id: int
    nota_id: int
    importe: float

    class Config:
        from_attributes = True


# --- Nota Schemas ---
class NotaBase(BaseModel):
    folio: str
    cliente_id: int
    direccion_facturacion_id: int
    direccion_envio_id: int


class NotaCreate(NotaBase):
    contenidos: List[ContenidoNotaCreate]


class NotaResponse(NotaBase):
    id: int
    total_de_la_nota: float
    contenidos: List[ContenidoNotaResponse] = []

    class Config:
        from_attributes = True
