from app import database, models

db = database.SessionLocal()
usuarios = db.query(models.Usuario).all()

for u in usuarios:
    # Obtener contraseña
    clave = u.clave
    if isinstance(clave, bytes):
        clave = clave.decode('utf-8')
    elif isinstance(clave, str) and clave.startswith('\\x'):
        clave = bytes.fromhex(clave[2:]).decode('utf-8')
        
    roles = [r.nombre for r in u.roles]
    print(f"[{' | '.join(roles)}] Usuario: '{u.nombre}' => Contraseña: '{clave}'")
