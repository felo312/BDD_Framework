from app import main, schemas, database
import traceback

db = database.SessionLocal()
u = schemas.UsuarioCreate(nombre='Admin2', rol_id=1, clave='123')

try:
    user = main.create_user(u, db)
    print('OK:', user)
except Exception as e:
    print('ERROR:')
    traceback.print_exc()
