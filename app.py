from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import db

app = FastAPI(title="Proyecto FastAPI simple")

# Habilitar CORS para permitir preflight desde el frontend (ajusta `allow_origins` en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento en memoria sencillo (sin models)
items: Dict[int, Dict[str, Any]] = {}


class ProductoCreate(BaseModel):
    nombre: str 
    precio: str
    unidad: str

    class Config:
        allow_population_by_field_name = True


@app.on_event("startup")
async def on_startup():
    await db.init_db()


@app.on_event("shutdown")
async def on_shutdown():
    await db.close_db()


@app.get("/")
async def root():
    return {"message": "API FastAPI simple"}


@app.get("/productos")
async def get_productos():
    rows = await db.fetch("SELECT nombre, precio, unidad FROM productos")
    return [dict(r) for r in rows]


@app.post("/cargue_producto", status_code=200)
async def cargue_producto(payload: Any = Body(...)):
    print("Payload recibido:", payload)
    try:
        if isinstance(payload, dict) and "items" in payload:
            items_raw = payload["items"]
        elif isinstance(payload, list):
            items_raw = payload
        else:
            raise HTTPException(
                status_code=400,
                detail="Payload inválido: espere un array o {items: [...]}"
            )

        inserted = []
        for el in items_raw:
            p = ProductoCreate.parse_obj(el)
            data = p.dict(by_alias=True)
            row = await db.insert_one("productos", data)
            if row is None:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo insertar uno de los productos"
                )
            inserted.append(dict(row))

        return inserted

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return {"item_id": item_id, "item": item}


@app.post("/items/{item_id}")
async def create_item(item_id: int, payload: dict):
    if item_id in items:
        raise HTTPException(status_code=400, detail="Item ya existe")
    items[item_id] = payload
    return {"item_id": item_id, "item": payload}


@app.put("/items/{item_id}")
async def update_item(item_id: int, payload: dict):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    items[item_id] = payload
    return {"item_id": item_id, "item": payload}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    del items[item_id]
    return {"detail": "Eliminado"}
