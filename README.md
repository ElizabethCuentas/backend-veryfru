# Proyecto FastAPI simple

Este es un proyecto mínimo de FastAPI sin modelos (almacenamiento en memoria).

Comandos rápidos:

```powershell
pip install -r requirements.txt
uvicorn app:app --reload
```

Endpoints disponibles:

- `GET /` - Mensaje de bienvenida
- `GET /items/{item_id}` - Obtener item
- `POST /items/{item_id}` - Crear item (body JSON libre)
- `PUT /items/{item_id}` - Actualizar item (body JSON libre)
- `DELETE /items/{item_id}` - Eliminar item
