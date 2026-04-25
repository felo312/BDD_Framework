import os
import sys

# Forzar a que el cliente de Postgres hable UTF-8
os.environ["PGCLIENTENCODING"] = "utf-8"

# Si estás en Windows, esto ayuda a la consola
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import datetime
from . import models, schemas, database, security

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="API Restaurante - FastAPI")

# Configurar CORS para el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar por los dominios reales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# /**
#  * @brief Registra un nuevo usuario en la base de datos (con hash de contraseña).
#  * @param user: Objeto UsuarioCreate
#  * @param db: Sesión DB
#  * @return Usuario creado (sin devolver contraseña)
#  * @pre Los datos deben ser válidos.
#  * @post Usuario guardado en BD.
#  */
@app.post("/usuarios/", response_model=schemas.Usuario)
def create_user(user: schemas.UsuarioCreate, db: Session = Depends(database.get_db)):
    hashed_password = security.get_password_hash(user.clave)
    db_user = models.Usuario(nombre=user.nombre, clave=hashed_password, rol_id=user.rol_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Endpoint de login para obtener token JWT.
#  * @param form_data: Credenciales (username, password)
#  * @param db: Sesión DB
#  * @return Token JWT
#  * @pre Credenciales correctas.
#  * @post Devuelve access_token.
#  */
@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.nombre == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.clave):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.nombre}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Crea una nueva mesa en el sistema.
#  * @param mesa: datos de la mesa (cantidad de sillas)
#  * @param db: Sesión de la base de datos
#  * @return Objeto Mesa creado
#  * @pre El usuario debe tener rol de Administrador (no validado aquí por simplicidad)
#  * @post La mesa se registra en la DB
#  */
@app.post("/mesas/", response_model=schemas.Mesa)
def create_mesa(mesa: schemas.MesaCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador", "Maitre"]))):
    db_mesa = models.Mesa(**mesa.dict())
    db.add(db_mesa)
    db.commit()
    db.refresh(db_mesa)
    return db_mesa
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Valida el cupo y crea una reservación.
#  * @param reserva: datos de la reservación
#  * @param db: Sesión de DB
#  * @return Objeto reservación o excepción si no hay cupo
#  * @pre Debe existir la mesa
#  * @post Se bloquea la mesa para ese horario si es aprobada
#  */
@app.post("/reservaciones/", response_model=schemas.Reservacion)
def create_reservacion(reserva: schemas.ReservacionCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Maitre", "Administrador"]))):
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == reserva.mesa_id).first()
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    if reserva.cantidad > db_mesa.sillas:
        raise HTTPException(status_code=400, detail="La mesa no tiene la capacidad suficiente para la cantidad de personas")
    
    db_reserva = models.Reservacion(**reserva.dict(), estado="reservada")
    db.add(db_reserva)
    db.commit()
    db.refresh(db_reserva)
    return db_reserva
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Registra un pedido con sus órdenes (caso de uso dinámico).
#  * @param pedido: Lista de platos y cantidad
#  * @param db: Sesión
#  * @return Pedido registrado
#  * @pre Platos y mesa deben ser válidos
#  * @post Pedido e items insertados
#  */
@app.post("/pedidos/", response_model=schemas.Pedido)
def create_pedido(pedido: schemas.PedidoCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Mesero"]))):
    # Crear pedido
    db_pedido = models.Pedido(cliente_id=pedido.cliente_id, mesero_id=pedido.mesero_id)
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    
    # Crear órdenes
    for orden in pedido.ordenes:
        db_orden = models.Orden(
            plato_id=orden.plato_id, 
            pedido_id=db_pedido.id, 
            estado="solicitado", 
            cantidad=orden.cantidad
        )
        db.add(db_orden)
    
    db.commit()
    return db_pedido
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Genera estadísticas y reportes de pedidos.
#  * @param db: Sesión
#  * @return Lista de todos los pedidos
#  * @pre Usuario es Admin
#  * @post Devuelve datos de inteligencia de negocio
#  */
@app.get("/reportes/pedidos")
def reportes_pedidos(db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    total_pedidos = db.query(models.Pedido).count()
    return {"total_pedidos": total_pedidos}
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Historial de clientes (Funcionalidad adicional).
#  * @param cliente_id: ID del cliente
#  * @param db: Sesión
#  * @return Historial de consumos del cliente
#  * @pre Ninguna
#  * @post Ninguna
#  */
@app.get("/clientes/{cliente_id}/historial")
def historial_cliente(cliente_id: int, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador", "Maitre"]))):
    pedidos = db.query(models.Pedido).filter(models.Pedido.cliente_id == cliente_id).all()
    return pedidos
# --------------------------------------------------------------------
