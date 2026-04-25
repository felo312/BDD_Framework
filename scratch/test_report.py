from app import database, models
from sqlalchemy import func, text
import json

db = database.SessionLocal()
trunc_param = 'day'

ventas = db.query(
    func.date_trunc(trunc_param, models.Pedido.fecha).label("fecha_t"),
    func.sum(models.Pedido.total).label("total")
).group_by(text("fecha_t")).order_by(text("fecha_t")).all()

print(f"Ventas result: {ventas}")
db.close()
