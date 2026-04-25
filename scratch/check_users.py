from app import database, models
db = database.SessionLocal()
users = db.query(models.Usuario).all()
for u in users:
    roles = [r.nombre for r in u.roles]
    print(f"User: {u.nombre}, Roles: {roles}")
db.close()
