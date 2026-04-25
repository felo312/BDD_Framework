from app import database, models, security
from datetime import datetime, timedelta
import random

def populate():
    db = database.SessionLocal()

    # 1. Crear Tipos
    tipos_nombres = ["Entrada", "Plato Fuerte", "Postre", "Bebida"]
    for nombre in tipos_nombres:
        if not db.query(models.TipoPlato).filter_by(nombre=nombre).first():
            db.add(models.TipoPlato(nombre=nombre))
    db.commit()
    
    tipos_map = {t.nombre: t.id for t in db.query(models.TipoPlato).all()}

    # 2. Crear Platos Colombianos
    platos_data = [
        # Entradas
        {"nombre": "Patacones con Hogao", "descripcion": "Plátano verde frito con salsa de tomate y cebolla", "tiempo": timedelta(minutes=12), "precio": 12000, "tipo_id": tipos_map["Entrada"]},
        {"nombre": "Chicharrón con Arepa", "descripcion": "Cerdo crocante con arepa de maíz", "tiempo": timedelta(minutes=15), "precio": 18000, "tipo_id": tipos_map["Entrada"]},
        {"nombre": "Empanadas de Pipián", "descripcion": "Empanadas típicas del Cauca", "tiempo": timedelta(minutes=10), "precio": 10000, "tipo_id": tipos_map["Entrada"]},
        
        # Platos Fuertes
        {"nombre": "Bandeja Paisa", "descripcion": "Frijoles, arroz, carne, huevo, chicharrón, aguacate y arepa", "tiempo": timedelta(minutes=30), "precio": 45000, "tipo_id": tipos_map["Plato Fuerte"]},
        {"nombre": "Ajiaco Santafereño", "descripcion": "Sopa de pollo con tres tipos de papas y guascas", "tiempo": timedelta(minutes=25), "precio": 38000, "tipo_id": tipos_map["Plato Fuerte"]},
        {"nombre": "Lechona Tolimense", "descripcion": "Cerdo relleno de arroz y arveja", "tiempo": timedelta(minutes=20), "precio": 35000, "tipo_id": tipos_map["Plato Fuerte"]},
        
        # Postres
        {"nombre": "Brevas con Arequipe", "descripcion": "Higos en almíbar con dulce de leche", "tiempo": timedelta(minutes=5), "precio": 12000, "tipo_id": tipos_map["Postre"]},
        {"nombre": "Postre de Natas", "descripcion": "Postre tradicional a base de leche y huevos", "tiempo": timedelta(minutes=5), "precio": 14000, "tipo_id": tipos_map["Postre"]},
        
        # Bebidas
        {"nombre": "Limonada de Coco", "descripcion": "Refrescante limonada con crema de coco", "tiempo": timedelta(minutes=8), "precio": 15000, "tipo_id": tipos_map["Bebida"]},
        {"nombre": "Refajo", "descripcion": "Mezcla de cerveza y gaseosa Colombiana", "tiempo": timedelta(minutes=3), "precio": 10000, "tipo_id": tipos_map["Bebida"]},
        {"nombre": "Jugo de Lulo", "descripcion": "Jugo natural de fruta exótica", "tiempo": timedelta(minutes=5), "precio": 9000, "tipo_id": tipos_map["Bebida"]}
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
