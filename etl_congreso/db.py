from __future__ import annotations

import os
from typing import Optional


def get_database_url() -> str:
    """
    Devuelve la cadena de conexión de Postgres desde variables de entorno.
    """
    candidates = [
        "DATABASE_URL",
        "SUPABASE_DB_URL",
        "POSTGRES_URL",
        "PG_CONNECTION_STRING",
    ]
    for env_var in candidates:
        value = os.getenv(env_var)
        if value:
            return value
    raise RuntimeError(
        "No se encontró cadena de conexión de base de datos. "
        "Define DATABASE_URL o SUPABASE_DB_URL."
    )


def get_connection():
    """
    Abre una conexión psycopg usando la URL disponible en entorno.
    """
    try:
        import psycopg
    except ImportError as exc:
        raise ImportError("psycopg no está instalado en el entorno actual") from exc

    return psycopg.connect(get_database_url())

