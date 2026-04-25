from app import database, models
db = database.SessionLocal()
roles = db.query(models.Rol).all()
for r in roles:
    print(f"Role ID: {r.id}, Name: {r.nombre}")
db.close()
