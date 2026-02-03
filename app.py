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

@app.get("/productos")
async def get_productos():
    rows = await db.fetch("SELECT * FROM productos")
    return [dict(r) for r in rows]


@app.post("/cargue_producto", status_code=200)
async def cargue_producto(payload: Any = Body(...)):
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

@app.delete("/eliminar_productos", status_code=200)
async def delete_item():
    await db.delete("productos")
    return {"detail": "Productos eliminados"}