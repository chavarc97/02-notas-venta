import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from typing import Dict, Any


class PDFGenerator:
    @staticmethod
    def generate_nota_pdf(nota_data: Dict[str, Any]) -> bytes:
        """
        Generates a PDF buffer containing the Sales Note details.
        nota_data should contain:
        - client: {razon_social, nombre_comercial, rfc, email, telefono}
        - nota: {folio}
        - contenidos: list of {cantidad, nombre, precio_unitario, importe}
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Helper variables
        y_position = height - 50

        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y_position, "Nota de Venta")
        y_position -= 30

        # Note Info
        c.setFont("Helvetica", 12)
        c.drawString(50, y_position, f"Folio: {nota_data['nota']['folio']}")
        y_position -= 30

        # Client Info
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "Información del Cliente:")
        y_position -= 20
        c.setFont("Helvetica", 12)

        client = nota_data["client"]
        c.drawString(50, y_position, f"Razón Social: {client['razon_social']}")
        y_position -= 15
        c.drawString(50, y_position, f"Nombre Comercial: {client['nombre_comercial']}")
        y_position -= 15
        c.drawString(50, y_position, f"RFC: {client['rfc']}")
        y_position -= 15
        c.drawString(50, y_position, f"Email: {client['email']}")
        y_position -= 15
        c.drawString(50, y_position, f"Teléfono: {client['telefono']}")
        y_position -= 30

        # Table Header
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Cant.")
        c.drawString(100, y_position, "Producto")
        c.drawString(350, y_position, "Precio Unit.")
        c.drawString(450, y_position, "Importe")
        y_position -= 20

        # Items Table
        c.setFont("Helvetica", 12)
        total = 0.0
        for item in nota_data["contenidos"]:
            c.drawString(50, y_position, str(item["cantidad"]))

            # Simple word wrap for product name if needed
            prod_name = item["nombre"]
            if len(prod_name) > 30:
                prod_name = prod_name[:27] + "..."
            c.drawString(100, y_position, prod_name)

            c.drawString(350, y_position, f"${item['precio_unitario']:.2f}")
            c.drawString(450, y_position, f"${item['importe']:.2f}")

            total += item["importe"]
            y_position -= 15

            # Basic pagination handling if items are too many
            if y_position < 50:
                c.showPage()
                y_position = height - 50
                c.setFont("Helvetica", 12)

        # Total
        y_position -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, y_position, "Total:")
        c.drawString(450, y_position, f"${total:.2f}")

        # Finish up
        c.save()
        buffer.seek(0)
        return buffer.read()
