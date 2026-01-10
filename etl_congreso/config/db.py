from __future__ import annotations

import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()


def get_database_url() -> str:
    """
    Returns Postgres connection string from env vars,
    adapted for SQLAlchemy (postgresql+psycopg://).
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
            "Database connection string not found. "
            "Define DATABASE_URL or SUPABASE_DB_URL."
        )

    # Adapt for SQLAlchemy if necessary
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
         # Ensure modern driver usage if none specified
         if "+psycopg2" not in url:
             url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


# Engine singleton to avoid creating multiple instances
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(get_database_url())
    return _engine


def get_session() -> Generator[Session, None, None]:
    """
    Session generator for use with context managers or dependencies.
    """
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Helper for direct use without generator if preferred
def create_session() -> Session:
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()