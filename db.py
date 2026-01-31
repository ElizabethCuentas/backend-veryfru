import os
from typing import Any, List, Optional
import asyncpg
import re

# URL por defecto (se puede sobrescribir con la variable de entorno DATABASE_URL)
DEFAULT_DATABASE_URL = (
    "postgresql://neondb_owner:npg_Pc72IBEAMVHJ@ep-jolly-rice-ah65ictq-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

pool: Optional[asyncpg.pool.Pool] = None


async def init_db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool


async def close_db():
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def fetchrow(query: str, *args: Any) -> Optional[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def fetch(query: str, *args: Any) -> List[asyncpg.Record]:
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def execute(query: str, *args: Any) -> str:
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetchval(query: str, *args: Any) -> Any:
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)


def _is_valid_identifier(name: str) -> bool:
    return re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name) is not None


async def insert_one(table: str, payload: dict) -> Optional[asyncpg.Record]:
    if not payload:
        raise ValueError("payload vacío")
    if not _is_valid_identifier(table):
        raise ValueError("nombre de tabla inválido")
    cols = []
    for k in payload.keys():
        if not _is_valid_identifier(k):
            raise ValueError(f"nombre de columna inválido: {k}")
        cols.append(k)
    columns_sql = ", ".join(cols)
    placeholders = ", ".join(f"${i}" for i in range(1, len(cols) + 1))
    values = list(payload.values())
    query = f"INSERT INTO {table} ({columns_sql}) VALUES ({placeholders}) RETURNING *"
    return await fetchrow(query, *values)
