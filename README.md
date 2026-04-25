# 🍽️ Restaurant Management System - BDD Framework

¡Bienvenido al Sistema de Gestión de Restaurante! Este proyecto es una solución integral diseñada para optimizar la operación de un restaurante, cubriendo desde la toma de pedidos hasta la inteligencia de negocio para administradores.

## 🚀 Tecnologías Utilizadas

*   **Backend**: Python con **FastAPI** (Rápido, moderno y asíncrono).
*   **Base de Datos**: **SQLAlchemy** con **PostgreSQL** (Motor robusto y relacional).
*   **Driver**: `psycopg2` para la conexión con el servidor de base de datos.
*   **Frontend**: HTML5, CSS3 (Vanilla) y JavaScript (Vanilla) con estética **Glassmorphism**.
*   **Seguridad**: Autenticación **JWT** (JSON Web Tokens) y cifrado de contraseñas (SHA-256).
*   **Base de Datos**: PostgreSQL corriendo en el puerto **5433** (configurado en `app/database.py`).

---

## 🛠️ Configuración y Ejecución

### 1. Requisitos Previos
*   Python 3.10 o superior instalado.
*   Pip (gestor de paquetes de Python).

### 2. Instalación de Dependencias
Abre una terminal en la raíz del proyecto y ejecuta:
```bash
pip install -r requirements.txt
```

### 3. Inicialización de la Base de Datos
Para poblar la base de datos con platos colombianos, roles y usuarios de prueba, ejecuta:
```bash
python populate_db.py
```

### 4. Ejecución del Servidor
Inicia el backend con Uvicorn:
```bash
uvicorn app.main:app --reload
```
*El sistema está configurado para correr en el puerto **8000** por defecto.*

### 5. Acceso a la Aplicación
Abre el archivo `frontend/index.html` en tu navegador.

**Credenciales de Administrador por defecto:**
*   **Usuario**: `Admin`
*   **Contraseña**: `admin123`

---

## 👥 Roles y Permisos

1.  **Administrador**: Acceso a reportes de ventas, gestión de empleados y directorio completo de clientes.
2.  **Maitre**: Gestión y edición de mesas (capacidad y estado).
3.  **Mesero**: Toma de pedidos, creación rápida de clientes y validación de cupo.
4.  **Cocinero**: Panel de cocina para visualizar órdenes pendientes y marcarlas como listas.

---

## 📋 Resumen de la Implementación (Paso a Paso)

Este sistema fue construido siguiendo una metodología incremental:

1.  **Fundamentos y Base de Datos**: Diseño del esquema relacional incluyendo Usuarios, Roles, Mesas, Platos, Pedidos y Órdenes.
2.  **Seguridad y Autenticación**: Implementación de seguridad basada en roles mediante `RoleChecker` en FastAPI y generación de tokens JWT.
3.  **Gestión de Inventario (Platos)**: Clasificación del menú en Entradas, Platos Fuertes, Postres y Bebidas, utilizando platos típicos colombianos.
4.  **Lógica de Negocio de Pedidos**: 
    *   Implementación de **Validación de Cupo** (evita pedidos si superan la capacidad de la mesa).
    *   Sistema de **Creación Rápida de Clientes** desde la pantalla de pedidos.
5.  **Módulo de Cocina**: Creación de un panel en tiempo real para los cocineros con cálculo de tiempo de espera.
6.  **Inteligencia de Negocio (BI)**:
    *   Reportes de ventas por periodo (Día/Semana/Mes).
    *   Top 5 de platos más vendidos.
    *   Directorio de clientes con historial de consumo e inversión total acumulada.
7.  **Optimización de Interfaz**: Refinamiento estético con Glassmorphism y navegación fluida tipo SPA (Single Page Application).

---
*Desarrollado con enfoque en escalabilidad y experiencia de usuario.*