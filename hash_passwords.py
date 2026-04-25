import os
import sys
os.environ["PGCLIENTENCODING"] = "utf-8"

from app import database, models, security

def run_migration():
    db = database.SessionLocal()
    usuarios = db.query(models.Usuario).all()
    updated = 0
    for u in usuarios:
        # Convertir a string si viene como bytes (por ser BYTEA en postgres)
        clave_str = u.clave
        if isinstance(clave_str, bytes) or isinstance(clave_str, memoryview):
            clave_str = bytes(clave_str).decode('utf-8')
        elif isinstance(clave_str, str) and clave_str.startswith('\\x'):
            # A veces psycopg2 o la consola lo lee como string hexadecimal
            try:
                clave_str = bytes.fromhex(clave_str[2:]).decode('utf-8')
            except:
                pass
                
        # Si la longitud no es 64 (longitud de un SHA-256 en hex), lo hasheamos
        if len(str(clave_str)) != 64:
            u.clave = security.get_password_hash(str(clave_str))
            updated += 1
            
    db.commit()
    db.close()
    print(f"Migración completada: {updated} contraseñas convertidas a SHA-256.")

if __name__ == "__main__":
    run_migration()
