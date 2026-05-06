from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum


class TipoDireccionEnum(str, Enum):
    FACTURACION = "FACTURACIÓN"
    ENVIO = "ENVÍO"


# --- Domicilio Schemas ---
class DomicilioBase(BaseModel):
    domicilio: str
    colonia: str
    municipio: str
    estado: str
    tipo_de_direccion: TipoDireccionEnum


class DomicilioCreate(DomicilioBase):
    pass


class DomicilioUpdate(BaseModel):
    domicilio: Optional[str] = None
    colonia: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    tipo_de_direccion: Optional[TipoDireccionEnum] = None


class DomicilioResponse(DomicilioBase):
    id: int
    cliente_id: int

    class Config:
        from_attributes = True


# --- Client Schemas ---
class ClientBase(BaseModel):
    razon_social: str
    nombre_comercial: str
    rfc: str
    email: EmailStr
    telefono: str


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    rfc: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    domicilios: List[DomicilioResponse] = []

    class Config:
        from_attributes = True
