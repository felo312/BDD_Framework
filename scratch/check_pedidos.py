from app.database import SessionLocal
from app.models import Usuario, Rol, Actuacion, Pedido

db = SessionLocal()
try:
    print("--- PEDIDOS EN BD ---")
    pedidos = db.query(Pedido).all()
    if not pedidos:
        print("No hay pedidos registrados.")
    for p in pedidos:
        print(f"ID: {p.id}, Cliente ID: {p.cliente_id}, Total: {p.total}, Fecha: {p.fecha}")

finally:
    db.close()
