from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base


class Nota(Base):
    __tablename__ = "notas"

    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String, unique=True, index=True)
    cliente_id = Column(Integer)
    direccion_facturacion_id = Column(Integer)
    direccion_envio_id = Column(Integer)
    total_de_la_nota = Column(Float, default=0.0)

    contenidos = relationship(
        "ContenidoNota", back_populates="nota", cascade="all, delete-orphan"
    )


class ContenidoNota(Base):
    __tablename__ = "contenido_notas"

    id = Column(Integer, primary_key=True, index=True)
    nota_id = Column(Integer, ForeignKey("notas.id"))
    producto_id = Column(Integer)
    cantidad = Column(Integer)
    precio_unitario = Column(Float)
    importe = Column(Float)

    nota = relationship("Nota", back_populates="contenidos")
