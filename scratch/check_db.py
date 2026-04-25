from app import database, models
db = database.SessionLocal()
pedidos = db.query(models.Pedido).all()
print(f"Total pedidos: {len(pedidos)}")
for p in pedidos[:5]:
    print(f"ID: {p.id}, Fecha: {p.fecha}, Total: {p.total}")
db.close()
