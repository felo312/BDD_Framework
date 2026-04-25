from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

class UsuarioBase(BaseModel):
    nombre: str
    rol_id: int

class UsuarioCreate(UsuarioBase):
    clave: str

class Usuario(UsuarioBase):
    id: int
    fecha_clave: datetime
    class Config:
        from_attributes = True

class MesaBase(BaseModel):
    sillas: int
    estado: str = "Disponible"

class MesaCreate(MesaBase):
    pass

class Mesa(MesaBase):
    id: int
    class Config:
        from_attributes = True

class ReservacionBase(BaseModel):
    cliente_id: int
    cantidad: int
    mesa_id: int
    inicio: datetime
    duracion: timedelta

class ReservacionCreate(ReservacionBase):
    pass

class Reservacion(ReservacionBase):
    id: int
    estado: str
    class Config:
        from_attributes = True

class PlatoBase(BaseModel):
    nombre: str
    descripcion: str
    tipo_id: int
    precio: float

class Plato(PlatoBase):
    id: int
    tiempo: timedelta
    class Config:
        from_attributes = True

class OrdenBase(BaseModel):
    plato_id: int
    cantidad: int

class PedidoCreate(BaseModel):
    cliente_id: int
    mesero_id: int
    mesa_id: int
    personas: int
    ordenes: List[OrdenBase]

class Pedido(BaseModel):
    id: int
    cliente_id: int
    mesero_id: int
    mesa_id: int
    total: float
    class Config:
        from_attributes = True
