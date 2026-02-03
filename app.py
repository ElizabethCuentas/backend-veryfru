from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
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
class PedidoCreate(BaseModel):
    producto: str = Field(alias="name")
    id_producto: Union[str, int] = Field(alias="id")
    precio: Union[str, int] = Field(alias="price")
    observaciones: str = Field(alias="observation")
    cantidad: Union[str, int] = Field(alias="quantity")
    unidad: str = Field(alias="unit")
    total: Optional[Union[str, int]] = Field(default=None, alias="total")

    class Config:
        allow_population_by_field_name = True

    @field_validator("id_producto", "precio", "cantidad", "total", mode="before")
    @classmethod
    def _coerce_to_str(cls, v):
        if v is None:
            return v
        return str(v)


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
            data = p.dict(by_alias=False, exclude_none=True)
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

@app.post("/crear_pedido", status_code=200)
async def crear_pedido(payload: Any = Body(...)):
    try:
        print(payload)
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
            p = PedidoCreate.parse_obj(el)
            data = p.dict(by_alias=False, exclude_none=True)
            row = await db.insert_one("pedidos", data)
            if row is None:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo insertar uno de los pedidos"
                )
            inserted.append(dict(row))

        return inserted

    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
