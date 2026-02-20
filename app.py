from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Optional, Union
from pydantic import BaseModel, Field, validator
import db
import os

app = FastAPI(title="Veryfruity Backend API", version="1.0.0")

# Habilitar CORS para permitir preflight desde el frontend (ajusta `allow_origins` en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        validate_by_name = True

    @validator("id_producto", "precio", "cantidad", "total", pre=True)
    def _coerce_to_str(cls, v):
        if v is None:
            return v
        return str(v)

class LoginRequest(BaseModel):
    username: str
    password: str


@app.on_event("startup")
async def on_startup():
    await db.init_db()


@app.on_event("shutdown")
async def on_shutdown():
    await db.close_db()

@app.get("/", status_code=200)
async def root():
    return {"status": "ok"}

@app.get("/health", status_code=200)
async def health():
    return {"status": "ok"}

@app.get("/productos")
async def get_productos():
    rows = await db.fetch("SELECT * FROM productos")
    return [dict(r) for r in rows]

@app.get("/pedidos")
async def get_pedidos():
    rows = await db.fetch("SELECT id_pedidos, total FROM pedidos")
    return [dict(r) for r in rows]

@app.get("/pedido_detalle/{id_pedido}", status_code=200)
async def get_pedido_detalle(id_pedido: int):
    try:
        if id_pedido is None:
            raise HTTPException(status_code=400, detail="El campo id_pedido es requerido")

        rows = await db.fetch(
            "SELECT producto, precio, cantidad, unidad, observaciones FROM pedido_items WHERE id_pedido = $1", id_pedido
        )
        return [dict(r) for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

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

        for el in items_raw:
            p = ProductoCreate.parse_obj(el)
            data = p.dict(by_alias=False, exclude_none=True)
            row = await db.insert_one("productos", data)
            if row is None:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo insertar uno de los productos"
                )

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
        if isinstance(payload, dict) and "items" in payload:
            items_raw = payload["items"]
            total_payload = payload.get("total")
        elif isinstance(payload, list):
            items_raw = payload
            total_payload = None
        else:
            raise HTTPException(
                status_code=400,
                detail="Payload inválido: espere un array o {items: [...]}"
            )

        if total_payload is None:
            raise HTTPException(status_code=400, detail="El campo total es requerido")

        pedido_row = await db.insert_one("pedidos", {"total": str(total_payload)})
        if pedido_row is None:
            raise HTTPException(status_code=500, detail="No se pudo crear el pedido")
        pedido_id = pedido_row["id_pedidos"]

        for el in items_raw:
            p = PedidoCreate.parse_obj(el)
            data = p.dict(by_alias=False, exclude_none=True)
            data["id_pedido"] = pedido_id
            row = await db.insert_one("pedido_items", data)
            if row is None:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo insertar uno de los items"
                )

        return {"id_pedido": pedido_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login", status_code=200)
async def login(payload: LoginRequest):
    try:
        user = await db.fetchrow(
            'SELECT username FROM users WHERE username = $1 AND password = $2',
            payload.username,
            payload.password,
        )
        if user is None:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        return {"authenticated": True, "username": user["username"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
