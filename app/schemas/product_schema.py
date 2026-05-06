from pydantic import BaseModel
from typing import Optional


class ProductBase(BaseModel):
    nombre: str
    unidad_de_medida: str
    precio_base: float


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    unidad_de_medida: Optional[str] = None
    precio_base: Optional[float] = None


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True
