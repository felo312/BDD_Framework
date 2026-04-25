import os
import sys

# Forzar a que el cliente de Postgres hable UTF-8
os.environ["PGCLIENTENCODING"] = "utf-8"

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List
import datetime
from . import models, schemas, database, security

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="API Restaurante - FastAPI")

# Configurar CORS para el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# GESTIÓN DE EMPLEADOS / USUARIOS (CRUD)
# ==========================================
@app.post("/usuarios/", response_model=schemas.Usuario)
def create_user(user: schemas.UsuarioCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    db_rol = db.query(models.Rol).filter(models.Rol.id == user.rol_id).first()
    if not db_rol:
        raise HTTPException(status_code=400, detail=f"El rol_id {user.rol_id} no existe en la BD.")

    hashed_password = security.get_password_hash(user.clave)
    db_user = models.Usuario(nombre=user.nombre, clave=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    db_actuacion = models.Actuacion(rol_id=user.rol_id, usuario_id=db_user.id)
    db.add(db_actuacion)
    db.commit()
    
    db_user.rol_id = user.rol_id
    return db_user

@app.get("/empleados/")
def get_empleados(db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    # Devuelve todos los empleados con sus roles y especialidades
    usuarios = db.query(models.Usuario).all()
    resultado = []
    for u in usuarios:
        roles = [r.nombre for r in u.roles]
        especialidades = []
        if "Cocinero" in roles:
            esps = db.query(models.Especialidad).filter(models.Especialidad.cocinero_id == u.id).all()
            especialidades = [{"plato_id": e.plato_id} for e in esps]
            
        resultado.append({
            "id": u.id,
            "nombre": u.nombre,
            "roles": roles,
            "especialidades": especialidades
        })
    return resultado

@app.delete("/empleados/{empleado_id}")
def delete_empleado(empleado_id: int, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    emp = db.query(models.Usuario).filter(models.Usuario.id == empleado_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    
    # Eliminar relaciones
    db.query(models.Actuacion).filter(models.Actuacion.usuario_id == empleado_id).delete()
    db.query(models.Especialidad).filter(models.Especialidad.cocinero_id == empleado_id).delete()
    
    db.delete(emp)
    db.commit()
    return {"status": "ok", "message": "Empleado eliminado"}

@app.put("/empleados/{empleado_id}")
def update_empleado(empleado_id: int, user: schemas.UsuarioCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    emp = db.query(models.Usuario).filter(models.Usuario.id == empleado_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
        
    emp.nombre = user.nombre
    if user.clave:
        emp.clave = security.get_password_hash(user.clave)
    db.commit()
    
    db.query(models.Actuacion).filter(models.Actuacion.usuario_id == empleado_id).delete()
    db.add(models.Actuacion(rol_id=user.rol_id, usuario_id=empleado_id))
    db.commit()
    return {"status": "ok", "message": "Empleado actualizado"}

# ==========================================
# SEGURIDAD Y LOGIN
# ==========================================
@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.nombre == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrecto")

    clave_db = user.clave
    is_valid = False
    needs_upgrade = False
    
    if isinstance(clave_db, str) and len(clave_db) == 64:
        is_valid = security.verify_password(form_data.password, clave_db)
    else:
        try:
            if isinstance(clave_db, bytes) or isinstance(clave_db, memoryview):
                clave_texto = bytes(clave_db).decode('utf-8')
            elif isinstance(clave_db, str) and clave_db.startswith('\\x'):
                clave_texto = bytes.fromhex(clave_db[2:]).decode('utf-8')
            else:
                clave_texto = str(clave_db)
            if clave_texto == form_data.password:
                is_valid = True
                needs_upgrade = True
        except Exception:
            pass

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrecto")
        
    if needs_upgrade:
        user.clave = security.get_password_hash(form_data.password)
        db.commit()

    access_token_expires = datetime.timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    roles = [r.nombre for r in user.roles]
    access_token = security.create_access_token(
        data={"sub": user.nombre, "roles": roles}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# GESTIÓN DE MESAS
# ==========================================
@app.post("/mesas/", response_model=schemas.Mesa)
def create_mesa(mesa: schemas.MesaCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Maitre"]))):
    db_mesa = models.Mesa(**mesa.dict())
    db.add(db_mesa)
    db.commit()
    db.refresh(db_mesa)
    return db_mesa

@app.get("/mesas/")
def get_mesas(db: Session = Depends(database.get_db)):
    return db.query(models.Mesa).order_by(models.Mesa.id).all()

@app.delete("/mesas/{mesa_id}")
def delete_mesa(mesa_id: int, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Maitre"]))):
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    db.delete(db_mesa)
    db.commit()
    return {"status": "ok", "message": "Mesa eliminada"}

@app.get("/platos/")
def get_platos(db: Session = Depends(database.get_db)):
    return db.query(models.Plato).order_by(models.Plato.id).all()

@app.patch("/mesas/{mesa_id}/estado")
def update_mesa_estado(mesa_id: int, estado: str, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Maitre", "Mesero"]))):
    # Estados permitidos: Disponible, Reservada, Ocupada
    if estado not in ["Disponible", "Reservada", "Ocupada"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
    
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
        
    db_mesa.estado = estado
    db.commit()
    return {"status": "ok", "mesa_id": mesa_id, "nuevo_estado": estado}

@app.put("/mesas/{mesa_id}", response_model=schemas.Mesa)
def update_mesa(mesa_id: int, mesa_data: schemas.MesaCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Maitre"]))):
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == mesa_id).first()
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    
    db_mesa.sillas = mesa_data.sillas
    db_mesa.estado = mesa_data.estado
    db.commit()
    db.refresh(db_mesa)
    return db_mesa

# ==========================================
# VALIDACIÓN DE CUPO Y RESERVAS
# ==========================================
@app.post("/reservaciones/", response_model=schemas.Reservacion)
def create_reservacion(reserva: schemas.ReservacionCreate, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Maitre", "Administrador"]))):
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == reserva.mesa_id).first()
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
        
    # Validación de Cupo
    if reserva.cantidad > db_mesa.sillas:
        raise HTTPException(
            status_code=400, 
            detail=f"Excede capacidad. Mesa {reserva.mesa_id} solo tiene {db_mesa.sillas} sillas. Sugerimos buscar mesa de mayor capacidad."
        )
    
    db_reserva = models.Reservacion(**reserva.dict(), estado="reservada")
    db_mesa.estado = "Reservada" # Actualizamos estado físico de la mesa
    db.add(db_reserva)
    db.commit()
    db.refresh(db_reserva)
    return db_reserva

# ==========================================
# REGISTRO DE PEDIDOS (ASÍNCRONO)
# ==========================================
def notificar_cocina(pedido_id: int, mesa_id: int, items_count: int):
    # Simula una notificación websocket/push a cocina
    print(f"[COCINA] Nuevo pedido #{pedido_id} para la Mesa {mesa_id}. Platos solicitados: {items_count}")

@app.post("/pedidos/")
async def create_pedido(pedido: schemas.PedidoCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Mesero"]))):
    db_mesa = db.query(models.Mesa).filter(models.Mesa.id == pedido.mesa_id).first()
    if not db_mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
        
    # Validación de Cupo
    if pedido.personas > db_mesa.sillas:
        raise HTTPException(
            status_code=400, 
            detail=f"Excede capacidad. Mesa {pedido.mesa_id} solo tiene {db_mesa.sillas} sillas. Busque una mesa más grande."
        )

    # Cambiamos estado de la mesa a Ocupada
    db_mesa.estado = "Ocupada"
    
    # Calcular total del pedido
    total_pedido = 0.0
    for orden in pedido.ordenes:
        plato = db.query(models.Plato).filter(models.Plato.id == orden.plato_id).first()
        if plato:
            total_pedido += float(plato.precio) * orden.cantidad

    db_pedido = models.Pedido(
        cliente_id=pedido.cliente_id, 
        mesero_id=pedido.mesero_id, 
        mesa_id=pedido.mesa_id,
        total=total_pedido
    )
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    
    for orden in pedido.ordenes:
        db_orden = models.Orden(
            plato_id=orden.plato_id, 
            pedido_id=db_pedido.id, 
            estado="solicitado", 
            cantidad=orden.cantidad
        )
        db.add(db_orden)
    
    db.commit()
    
    # Procesamiento Asíncrono de Notificación a Cocina
    background_tasks.add_task(notificar_cocina, db_pedido.id, db_pedido.mesa_id, len(pedido.ordenes))
    
    return {
        "status": "ok", 
        "pedido_id": db_pedido.id, 
        "total": total_pedido,
        "mensaje": "Pedido registrado y cocina notificada asíncronamente."
    }

# ==========================================
# REPORTES Y ESTADÍSTICAS (BI)
# ==========================================
@app.get("/reportes/dashboard")
def reportes_dashboard(db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    # Total de ingresos históricos
    ingresos = db.query(func.sum(models.Pedido.total)).scalar() or 0.0
    
    # Frecuencia de consumo (Pedidos por día)
    pedidos_fecha = db.query(
        func.date(models.Pedido.fecha).label("dia"),
        func.count(models.Pedido.id).label("cantidad")
    ).group_by(func.date(models.Pedido.fecha)).all()
    
    historico = [{"fecha": str(row.dia), "pedidos": row.cantidad} for row in pedidos_fecha]
    
    return {
        "ingresos_totales": ingresos,
        "frecuencia_consumo": historico,
        "total_historico_pedidos": sum([r.cantidad for r in pedidos_fecha])
    }

@app.get("/reportes/pedidos/detallados")
def get_all_pedidos_detallados(db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    pedidos = db.query(models.Pedido).order_by(models.Pedido.fecha.desc()).all()
    resultado = []
    for p in pedidos:
        ordenes = db.query(models.Orden).filter(models.Orden.pedido_id == p.id).all()
        items = []
        for o in ordenes:
            plato = db.query(models.Plato).filter(models.Plato.id == o.plato_id).first()
            items.append({
                "plato": plato.nombre if plato else "Desconocido",
                "cantidad": o.cantidad,
                "subtotal": float(plato.precio * o.cantidad) if plato else 0.0
            })
        resultado.append({
            "id": p.id,
            "fecha": p.fecha,
            "mesa_id": p.mesa_id,
            "total": float(p.total),
            "items": items
        })
    return resultado

@app.get("/reportes/ventas")
def reportes_ventas(periodo: str = "dia", db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    trunc_param = 'day'
    if periodo == 'semana': trunc_param = 'week'
    elif periodo == 'mes': trunc_param = 'month'
    
    ventas = db.query(
        func.date_trunc(trunc_param, models.Pedido.fecha).label("fecha_t"),
        func.sum(models.Pedido.total).label("total")
    ).group_by(text("fecha_t")).order_by(text("fecha_t")).all()
    
    return [{"fecha": str(v.fecha_t), "total": float(v.total)} for v in ventas]

@app.get("/reportes/reservaciones")
def reportes_reservaciones(periodo: str = "dia", db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    trunc_param = 'day'
    if periodo == 'semana': trunc_param = 'week'
    elif periodo == 'mes': trunc_param = 'month'
    
    reservas = db.query(
        func.date_trunc(trunc_param, models.Reservacion.inicio).label("fecha_t"),
        func.count(models.Reservacion.id).label("cantidad")
    ).group_by(text("fecha_t")).order_by(text("fecha_t")).all()
    
    return [{"fecha": str(r.fecha_t), "cantidad": r.cantidad} for r in reservas]

@app.get("/reportes/top-platos")
def reportes_top_platos(db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador"]))):
    top = db.query(
        models.Plato.nombre,
        func.sum(models.Orden.cantidad).label("total_pedido")
    ).join(models.Orden, models.Orden.plato_id == models.Plato.id)\
     .group_by(models.Plato.nombre)\
     .order_by(text("total_pedido DESC"))\
     .limit(5).all()
     
    return [{"plato": t.nombre, "cantidad": int(t.total_pedido)} for t in top]

# ==========================================
# HISTORIAL DE CLIENTES
# ==========================================
@app.get("/clientes/{cliente_id}/historial")
def historial_cliente(cliente_id: int, db: Session = Depends(database.get_db), current_user: models.Usuario = Depends(security.RoleChecker(["Administrador", "Maitre", "Mesero"]))):
    pedidos = db.query(models.Pedido).filter(models.Pedido.cliente_id == cliente_id).order_by(models.Pedido.fecha.desc()).all()
    
    resultados = []
    for p in pedidos:
        ordenes = db.query(models.Orden).filter(models.Orden.pedido_id == p.id).all()
        resultados.append({
            "pedido_id": p.id,
            "fecha": p.fecha,
            "mesa_id": p.mesa_id,
            "total": p.total,
            "items_consumidos": [{"plato_id": o.plato_id, "cantidad": o.cantidad} for o in ordenes]
        })
        
    return {
        "cliente_id": cliente_id,
        "total_visitas": len(pedidos),
        "historial": resultados
    }
