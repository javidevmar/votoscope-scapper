from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from .orm import Eleccion

logger = logging.getLogger(__name__)

def get_election_by_type_and_date(session: Session, tipo: str, year: int, month: int) -> Optional[Eleccion]:
    """
    Retrieves an existing election by type and date (year/month).
    """
    stmt = select(Eleccion).where(
        and_(
            Eleccion.ano == year,
            Eleccion.mes == month,
            Eleccion.tipo == tipo,
            Eleccion.auto_id.is_(None),  # Assume national level generals
            Eleccion.prov_id.is_(None),
            Eleccion.muni_id.is_(None)
        )
    )
    return session.execute(stmt).scalar_one_or_none()

def election_exists(session: Session, tipo: str, year: int, month: int) -> bool:
    """
    Returns True if an election with these parameters already exists.
    """
    return get_election_by_type_and_date(session, tipo, year, month) is not None
