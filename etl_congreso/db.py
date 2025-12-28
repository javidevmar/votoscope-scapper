from __future__ import annotations

import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()


def get_database_url() -> str:
    """
    Devuelve la cadena de conexión de Postgres desde variables de entorno,
    adaptada para SQLAlchemy (postgresql+psycopg://).
    """
    candidates = [
        "DATABASE_URL",
        "SUPABASE_DB_URL",
        "POSTGRES_URL",
        "PG_CONNECTION_STRING",
    ]
    url = None
    for env_var in candidates:
        value = os.getenv(env_var)
        if value:
            url = value
            break
    
    if not url:
        raise RuntimeError(
            "No se encontró cadena de conexión de base de datos. "
            "Define DATABASE_URL o SUPABASE_DB_URL."
        )

    # Adaptar para SQLAlchemy si es necesario
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
         # Aseguramos usar el driver moderno si no se especifica otro
         if "+psycopg2" not in url:
             url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


# Singleton del engine para no crearlo múltiples veces
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url())
    return _engine


def get_session() -> Generator[Session, None, None]:
    """
    Generador de sesiones para usar con context managers o dependencias.
    """
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Helper para uso directo sin generador si se prefiere
def create_session() -> Session:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()