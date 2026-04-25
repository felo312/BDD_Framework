from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Numeric, Interval
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Rol(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)

class Actuacion(Base):
    __tablename__ = "actuaciones"
    id = Column(Integer, primary_key=True, index=True)
    rol_id = Column(Integer, ForeignKey("roles.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)
    clave = Column(String)
    fecha_clave = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relación muchos a muchos a través de actuaciones
    roles = relationship("Rol", secondary="actuaciones", backref="usuarios")

class Mesa(Base):
    __tablename__ = "mesas"
    id = Column(Integer, primary_key=True, index=True)
    sillas = Column(Integer)
    estado = Column(String, default="Disponible") # Disponible, Reservada, Ocupada

class Reservacion(Base):
    __tablename__ = "reservaciones"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"))
    cantidad = Column(Integer)
    estado = Column(String)
    mesa_id = Column(Integer, ForeignKey("mesas.id"))
    inicio = Column(DateTime)
    duracion = Column(Interval)

class TipoPlato(Base):
    __tablename__ = "tipos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String)

class Plato(Base):
    __tablename__ = "platos"
    id = Column(Integer, primary_key=True, index=True)
    tipo_id = Column(Integer, ForeignKey("tipos.id"))
    nombre = Column(String)
    descripcion = Column(String)
    tiempo = Column(Interval)
    precio = Column(Numeric)

class Especialidad(Base):
    __tablename__ = "especialidades"
    id = Column(Integer, primary_key=True, index=True)
    cocinero_id = Column(Integer, ForeignKey("usuarios.id"))
    plato_id = Column(Integer, ForeignKey("platos.id"))

class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"))
    mesero_id = Column(Integer, ForeignKey("usuarios.id"))
    mesa_id = Column(Integer, ForeignKey("mesas.id"))
    fecha = Column(DateTime, default=datetime.datetime.utcnow)
    total = Column(Numeric, default=0.0)

class Orden(Base):
    __tablename__ = "ordenes"
    id = Column(Integer, primary_key=True, index=True)
    plato_id = Column(Integer, ForeignKey("platos.id"))
    pedido_id = Column(Integer, ForeignKey("pedidos.id"))
    estado = Column(String)
    cantidad = Column(Integer)
    solicitado = Column(DateTime, default=datetime.datetime.utcnow)

class Preparacion(Base):
    __tablename__ = "preparaciones"
    id = Column(Integer, primary_key=True, index=True)
    cocinero_id = Column(Integer, ForeignKey("usuarios.id"))
    orden_id = Column(Integer, ForeignKey("ordenes.id"))
