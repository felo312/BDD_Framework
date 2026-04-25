import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models, schemas, database

# Configuración JWT (En producción debe estar en variables de entorno)
SECRET_KEY = "super_secret_key_para_el_proyecto_restaurante"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ------------------------------------------------------------------
# /**
#  * @brief Genera el hash SHA-256 de una contraseña.
#  * @param password: La contraseña en texto plano.
#  * @return String con el hash hexadecimal.
#  * @pre La contraseña no debe estar vacía.
#  * @post Retorna el hash estandarizado (SHA-256).
#  */
def get_password_hash(password: str) -> str:
    # Cumpliendo con PUR (Punto Único de Retorno)
    hash_result = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hash_result
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Verifica si una contraseña coincide con su hash.
#  * @param plain_password: La contraseña a verificar.
#  * @param hashed_password: El hash almacenado en base de datos.
#  * @return Booleano indicando si coinciden.
#  * @pre Ambos parámetros deben ser strings válidos.
#  * @post Ninguna.
#  */
def verify_password(plain_password: str, hashed_password: str) -> bool:
    is_valid = get_password_hash(plain_password) == hashed_password
    return is_valid
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Crea un token JWT para el manejo de sesión.
#  * @param data: Diccionario con la información a encriptar (ej. sub/nombre de usuario).
#  * @param expires_delta: Tiempo de expiración opcional.
#  * @return String con el token codificado.
#  * @pre Datos de entrada deben ser un diccionario válido.
#  * @post Se genera un JWT firmado.
#  */
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Obtiene el usuario actual basado en el token JWT.
#  * @param token: Token JWT obtenido del header de autorización.
#  * @param db: Sesión de la base de datos.
#  * @return Objeto Usuario autenticado.
#  * @pre El token debe ser válido y no haber expirado.
#  * @post Si es inválido, lanza HTTPException 401.
#  */
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.Usuario).filter(models.Usuario.nombre == username).first()
    if user is None:
        raise credentials_exception
    
    return user
# --------------------------------------------------------------------

# ------------------------------------------------------------------
# /**
#  * @brief Clase para control de acceso por roles (RBAC).
#  * @param allowed_roles: Lista de nombres de roles permitidos.
#  * @return Función de dependencia que valida el rol del usuario.
#  * @pre El usuario debe estar autenticado.
#  * @post Si el usuario no tiene el rol, lanza HTTPException 403.
#  */
class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: models.Usuario = Depends(get_current_user)):
        if user.rol.nombre not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operación no permitida. Requiere uno de los siguientes roles: {', '.join(self.allowed_roles)}"
            )
        return user
# --------------------------------------------------------------------
