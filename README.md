# Proyecto FastAPI simple

Backend de FastAPI conectado a PostgreSQL (asyncpg) para productos y pedidos.

## Desarrollo local

Comandos rapidos:

```powershell
pip install -r requirements.txt
$env:PYTHON_ENV="development"
$env:PORT="8000"
$env:DATABASE_URL="postgresql://usuario:password@host:5432/dbname"
uvicorn app:app --reload
```

## Endpoints disponibles

- `GET /` - Health basico
- `GET /health` - Health basico
- `GET /productos` - Lista de productos
- `POST /cargue_producto` - Crear productos (array o `{items: [...]}`)
- `DELETE /eliminar_productos` - Eliminar todos los productos
- `GET /pedidos` - Lista de pedidos
- `GET /pedido_detalle/{id_pedido}` - Detalle de pedido
- `POST /crear_pedido` - Crear pedido (requiere `total`)

## Deploy en Render

Este repo incluye `render.yaml` para desplegar como servicio web y `runtime.txt` para fijar Python 3.11 (necesario para `asyncpg`).

Pasos:

1. En Render, crea un servicio desde este repo.
2. Render leera `render.yaml` y usara:
   - `buildCommand`: `pip install -r requirements.txt`
   - `startCommand`: `uvicorn app:app --host 0.0.0.0 --port $PORT`
3. Configura las variables de entorno en el dashboard:
   - `DATABASE_URL` (obligatoria)
   - `CORS_ORIGINS` (opcional, por defecto `*`)

## Variables locales

Este proyecto carga automaticamente variables desde `.env` usando `python-dotenv`.
