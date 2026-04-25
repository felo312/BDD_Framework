from app.database import SessionLocal
from app.models import Usuario, Rol, Actuacion

db = SessionLocal()
try:
    # 1. Ver Roles
    print("--- ROLES EN BD ---")
    roles = db.query(Rol).all()
    for r in roles:
        print(f"ID: {r.id}, Nombre: {r.nombre}")

    # 2. Buscar Rol Cliente
    rol_cliente = db.query(Rol).filter(Rol.nombre == "Cliente").first()
    
    # 3. Ver todos los usuarios (para ver si se crearon sin rol)
    print("\n--- TODOS LOS USUARIOS ---")
    users = db.query(Usuario).all()
    for u in users:
        # Ver qué roles tiene cada uno
        u_roles = [db.query(Rol).get(a.rol_id).nombre for a in db.query(Actuacion).filter(Actuacion.usuario_id == u.id).all()]
        print(f"ID: {u.id}, Nombre: {u.nombre}, Roles: {u_roles}")

finally:
    db.close()
