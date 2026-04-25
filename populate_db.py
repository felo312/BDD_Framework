from app import database, models, security
from datetime import datetime, timedelta
import random

def populate():
    db = database.SessionLocal()

    # 1. Crear Tipos
    tipos = [
        models.TipoPlato(nombre="Entrada"),
        models.TipoPlato(nombre="Plato Fuerte"),
        models.TipoPlato(nombre="Postre")
    ]
    for t in tipos:
        if not db.query(models.TipoPlato).filter_by(nombre=t.nombre).first():
            db.add(t)
    db.commit()
    
    tipos_db = db.query(models.TipoPlato).all()

    # 2. Crear Platos
    platos_data = [
        {"nombre": "Empanadas", "descripcion": "Empanadas de carne", "tiempo": timedelta(minutes=10), "precio": 5.0, "tipo_id": tipos_db[0].id},
        {"nombre": "Churrasco", "descripcion": "Carne asada con papas", "tiempo": timedelta(minutes=25), "precio": 15.0, "tipo_id": tipos_db[1].id},
        {"nombre": "Tiramisú", "descripcion": "Postre de café", "tiempo": timedelta(minutes=5), "precio": 6.0, "tipo_id": tipos_db[2].id}
    ]
    for p in platos_data:
        if not db.query(models.Plato).filter_by(nombre=p["nombre"]).first():
            db.add(models.Plato(**p))
    db.commit()

    # 3. Crear Mesas
    mesas_data = [
        {"sillas": 2, "estado": "Disponible"},
        {"sillas": 4, "estado": "Disponible"},
        {"sillas": 6, "estado": "Ocupada"},
        {"sillas": 8, "estado": "Reservada"}
    ]
    if db.query(models.Mesa).count() < 4:
        for m in mesas_data:
            db.add(models.Mesa(**m))
        db.commit()

    # 4. Crear Empleado Cocinero y asignarle especialidad si existe
    cocinero = db.query(models.Usuario).filter(models.Usuario.nombre == "Cocinero Test").first()
    if not cocinero:
        cocinero = models.Usuario(nombre="Cocinero Test", clave=security.get_password_hash("clave123"))
        db.add(cocinero)
        db.commit()
        db.refresh(cocinero)
        db.add(models.Actuacion(rol_id=4, usuario_id=cocinero.id)) # 4 es Cocinero
        
        # Especialidad
        plato = db.query(models.Plato).first()
        db.add(models.Especialidad(cocinero_id=cocinero.id, plato_id=plato.id))
        db.commit()

    # 5. Crear Datos Históricos de Pedidos
    admin_user = db.query(models.Usuario).filter(models.Usuario.nombre == "Admin").first()
    if admin_user and db.query(models.Pedido).count() == 0:
        mesa = db.query(models.Mesa).first()
        for i in range(5): # 5 pedidos históricos
            pedido = models.Pedido(
                cliente_id=admin_user.id, 
                mesero_id=admin_user.id,
                mesa_id=mesa.id,
                total=random.choice([15.0, 20.0, 25.0, 30.0]),
                fecha=datetime.utcnow() - timedelta(days=i) # Fechas diferentes
            )
            db.add(pedido)
            db.commit()
            db.refresh(pedido)
            
            # Orden para el pedido
            plato = db.query(models.Plato).first()
            db.add(models.Orden(pedido_id=pedido.id, plato_id=plato.id, estado="entregado", cantidad=2))
        db.commit()

    print("Datos de prueba insertados con éxito.")

if __name__ == "__main__":
    populate()
