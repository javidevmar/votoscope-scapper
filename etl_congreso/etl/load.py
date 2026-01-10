from __future__ import annotations

import logging
from typing import Dict, Iterable, Optional, Tuple, List

from sqlalchemy import select, and_, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..config.db import create_session
from ..domain.models import (
    GeographyData,
    GoldHemicicloRow,
    SilverBundle,
    SilverCandidaturaRow,
    SilverElectionRow,
)
from ..domain.orm import (
    Eleccion,
    Partido,
    PartidoEleccion,
    Mesa,
    Voto,
    Autonomia,
    Provincia,
    Municipio,
    # Import Gold if in the future we decide to manage it from here,
    # but for now we use raw SQL for Gold or assume the table exists
    # and access it via SQL or define a 'mirror' model without managing it with Alembic.
    # Since we defined that Front owns Gold, we use raw SQL to insert into Gold
    # to avoid coupling Silver ORM models to Gold.
)

logger = logging.getLogger(__name__)


def _get_or_create_election(session: Session, row: SilverElectionRow) -> str:
    year = row.fecha.year
    month = row.fecha.month
    
    # 1. Look for exact match
    stmt = select(Eleccion).where(
        and_(
            Eleccion.ano == year,
            Eleccion.mes == month,
            Eleccion.tipo == "Generales",
            Eleccion.auto_id.is_(None),
            Eleccion.prov_id.is_(None),
            Eleccion.muni_id.is_(None)
        )
    )
    election = session.execute(stmt).scalar_one_or_none()
    
    if election:
        logger.info("Election encontrada (Generales %s-%02d): %s", year, month, election.id)
        return str(election.id)

    # 2. Create new election
    new_election = Eleccion(
        ano=year,
        mes=month,
        tipo="Generales",
        auto_id=None,
        prov_id=None,
        muni_id=None
    )
    session.add(new_election)
    session.flush() # To obtain generated ID
    
    logger.info("Election created (Generales %s-%02d): %s", year, month, new_election.id)
    return str(new_election.id)


def _upsert_partidos(
    session: Session, candidaturas: Iterable[SilverCandidaturaRow], color_lookup: Dict[str, str]
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Returns (candidacy_code -> party_id, candidacy_code -> acronyms).
    """
    mapping: Dict[str, str] = {}
    siglas_map: Dict[str, str] = {}
    
    # Local cache of acronyms -> party_id to avoid repeated loops queries
    # First load all existing parties to warm up the cache
    existing_partidos = session.execute(select(Partido.siglas, Partido.id)).all()
    siglas_cache = {row.siglas: str(row.id) for row in existing_partidos if row.siglas}

    created = 0
    updated = 0
    
    for candidatura in candidaturas:
        siglas = candidatura.siglas
        partido_id = siglas_cache.get(siglas)
        color = color_lookup.get(siglas.upper())

        if partido_id:
            # If exists, update color if needed via direct UPDATE
            if color:
                from sqlalchemy import update
                stmt = (
                    update(Partido).
                    where(
                        and_(
                            Partido.id == partido_id,
                            (Partido.color.is_(None) | (Partido.color == ''))
                        )
                    ).
                    values(color=color)
                )
                session.execute(stmt)
                updated += 1
        else:
            # Insert new
            # Use pg_insert to handle concurrency if any (on conflict do nothing)
            # although here we trust our local cache.
            stmt = pg_insert(Partido).values(
                nombre=candidatura.nombre_largo or siglas,
                siglas=siglas,
                color=color
            ).returning(Partido.id)
            
            # In case of race condition where another process inserted right now
            stmt = stmt.on_conflict_do_nothing(index_elements=['id']) # ID is UUID, this won't happen by ID.
            # Actually the conflict would be by ACRONYM if we had unique constraint on acronym (which we don't in strict model, but assume business logic)
            # As there is no unique constraint on acronyms in DDL, we do normal insert.
            # Better: Search again just in case, or insert.
            
            # Note: Current Silver model does NOT have unique on acronyms, but business logic assumes uniqueness.
            # We will insert.
            new_partido = Partido(
                nombre=candidatura.nombre_largo or siglas,
                siglas=siglas,
                color=color
            )
            session.add(new_partido)
            session.flush()
            partido_id = str(new_partido.id)
            siglas_cache[siglas] = partido_id
            created += 1

        mapping[candidatura.codigo] = partido_id
        siglas_map[candidatura.codigo] = siglas
        
    logger.info("Parties: new=%d, updated/reviewed=%d", created, updated)
    return mapping, siglas_map


def _link_partido_eleccion(session: Session, election_id: str, partido_id: str, siglas: str) -> None:
    stmt = pg_insert(PartidoEleccion).values(
        partido_id=partido_id,
        eleccion_id=election_id,
        siglas_eleccion=siglas
    ).on_conflict_do_nothing(
        index_elements=['partido_id', 'eleccion_id'] # PK
    )
    session.execute(stmt)


def _upsert_gold(
    session: Session,
    election_id: str,
    gold_rows: Iterable[GoldHemicicloRow],
    candidatura_to_partido: Dict[str, str],
) -> None:
    # Gold is a special schema owned by Front. 
    # We use raw SQL to avoid defining ORM models for Gold here
    # and avoid conflicts with Alembic.
    
    inserted = 0
    updated = 0
    
    for row in gold_rows:
        partido_id = candidatura_to_partido.get(row.cod_candidatura)
        if not partido_id:
            continue
            
        sql = """
            INSERT INTO gold.congreso_hemiciclo (
                eleccion_id, partido_id,
                nivel_ambito, cod_provincia, nombre_ambito,
                escanos, votos, porcentaje_voto
            )
            VALUES (:eleccion_id, :partido_id, :nivel_ambito, :cod_provincia, :nombre_ambito, :escanos, :votos, :porcentaje_voto)
            ON CONFLICT (eleccion_id, nivel_ambito, cod_provincia, partido_id)
            DO UPDATE SET
                nombre_ambito = EXCLUDED.nombre_ambito,
                escanos = EXCLUDED.escanos,
                votos = EXCLUDED.votos,
                porcentaje_voto = EXCLUDED.porcentaje_voto
            RETURNING (xmax = 0) AS inserted;
        """
        params = {
            "eleccion_id": election_id,
            "partido_id": partido_id,
            "nivel_ambito": row.nivel_ambito,
            "cod_provincia": row.cod_provincia,
            "nombre_ambito": row.nombre_ambito,
            "escanos": row.escanos,
            "votos": row.votos,
            "porcentaje_voto": row.porcentaje_voto,
        }
        
        result = session.execute(text(sql), params)
        row_result = result.fetchone()
        if row_result and row_result[0]:
            inserted += 1
        else:
            updated += 1
            
    logger.info("Gold hemiciclo records: new=%d, updated=%d", inserted, updated)


def _upsert_geography(session: Session, geography: GeographyData) -> None:
    # Autonomias
    for code, name in geography.autonomias.items():
        stmt = pg_insert(Autonomia).values(
            ine_code=code, 
            nombre=name
        ).on_conflict_do_update(
            index_elements=['ine_code'],
            set_={'nombre': name}
        )
        session.execute(stmt)

    # Provincias
    for prov in geography.provinces:
        stmt = pg_insert(Provincia).values(
            ine_code=prov.ine_code,
            auto_code=prov.auto_code,
            nombre=prov.name
        ).on_conflict_do_update(
            index_elements=['ine_code'],
            set_={'auto_code': prov.auto_code, 'nombre': prov.name}
        )
        session.execute(stmt)

    # Municipios
    for muni in geography.municipios:
        stmt = pg_insert(Municipio).values(
            prov_code=muni.prov_code,
            muni_code=muni.muni_code,
            nombre=muni.name
        ).on_conflict_do_update(
            index_elements=['prov_code', 'muni_code'],
            set_={'nombre': muni.name}
        )
        session.execute(stmt)
    
    logger.info("Geography updated.")


def _upsert_mesas(session: Session, mesas: Iterable[Tuple[str, str, str, str, str]]) -> Dict[Tuple[str, str, str, str, str], str]:
    mapping: Dict[Tuple[str, str, str, str, str], str] = {}
    
    # Pre-load existing tables for this province/municipality could be optimization,
    # but since they are many, better upsert on demand or batch.
    # Since SQLAlchemy core is fast, we will do batches if necessary.
    # To simplify I keep the loop, but optimizable.
    
    # Strategy: 
    # 1. Try to search ID.
    # 2. If not exists, insert.
    
    # Better: Do a massive SELECT of IDs we need?
    # Since input is iterable, process one by one or in blocks.
    
    cnt_inserted = 0
    cnt_existing = 0
    
    for prov, muni, distrito, seccion, mesa_cod in mesas:
        # Composite natural key
        key = (prov, muni, distrito, seccion, mesa_cod)
        
        # First try insert on conflict do nothing and return ID
        # Note: Returning ID in on_conflict_do_nothing sometimes returns nothing in Postgres if conflict.
        # That's why the pattern is usually: CTE or previous Select.
        
        stmt_select = select(Mesa.id).where(and_(
            Mesa.cod_prov == prov,
            Mesa.cod_muni == muni,
            Mesa.cod_distrito == distrito,
            Mesa.cod_seccion == seccion,
            Mesa.cod_mesa == mesa_cod
        ))
        existing_id = session.execute(stmt_select).scalar_one_or_none()
        
        if existing_id:
            mapping[key] = str(existing_id)
            cnt_existing += 1
        else:
            new_mesa = Mesa(
                cod_prov=prov,
                cod_muni=muni,
                cod_distrito=distrito,
                cod_seccion=seccion,
                cod_mesa=mesa_cod
            )
            session.add(new_mesa)
            # Flush para tener ID
            try:
                session.flush()
                mapping[key] = str(new_mesa.id)
                cnt_inserted += 1
            except Exception:
                # If failed due to race condition (another process inserted), partial rollback savepoint
                # and read. (Extra complexity, assuming single worker for now).
                session.rollback()
                existing_id = session.execute(stmt_select).scalar_one()
                mapping[key] = str(existing_id)
                cnt_existing += 1
                
    logger.info("Mesas: new=%d, existing=%d", cnt_inserted, cnt_existing)
    return mapping


def _upsert_votos(
    session: Session,
    election_id: str,
    mesa_ids: Dict[Tuple[str, str, str, str, str], str],
    candidatura_to_partido: Dict[str, str],
    votos: Iterable[Tuple[str, str, str, str, str, str, int]],
) -> None:
    
    # Batch insert values
    batch_values = []
    
    for prov, muni, distrito, seccion, mesa, cod_candidatura, votos_val in votos:
        mesa_id = mesa_ids.get((prov, muni, distrito, seccion, mesa))
        partido_id = candidatura_to_partido.get(cod_candidatura)
        
        if mesa_id and partido_id:
            batch_values.append({
                "mesa_id": mesa_id,
                "eleccion_id": election_id,
                "candidatura": partido_id,
                "votos": votos_val
            })
            
    if not batch_values:
        return

    # Execute massive upsert
    # Chunking if very large (e.g. > 10000)
    chunk_size = 5000
    for i in range(0, len(batch_values), chunk_size):
        chunk = batch_values[i:i + chunk_size]
        stmt = pg_insert(Voto).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=['mesa_id', 'eleccion_id', 'candidatura'],
            set_={'votos': stmt.excluded.votos}
        )
        session.execute(stmt)
        
    logger.info("Votes processed: %d records", len(batch_values))


def load_gold(
    session: Session,
    bundle: SilverBundle,
    gold_rows: Iterable[GoldHemicicloRow],
    geography: GeographyData,
    mesas: Iterable[Tuple[str, str, str, str, str]],
    votos_mesa: Iterable[Tuple[str, str, str, str, str, str, int]],
    color_lookup: Dict[str, str],
) -> str:
    """
    Load orchestrator using an existing SQLAlchemy Session.
    """
        
    # 1. Election
    election_id = _get_or_create_election(session, bundle.election)
        
    # 2. Geography
    _upsert_geography(session, geography)
        
    # 3. Parties
    candidatura_to_partido, siglas_map = _upsert_partidos(session, bundle.candidaturas, color_lookup)
        
    # 4. Party-Election Link
    for cod, partido_id in candidatura_to_partido.items():
        siglas = siglas_map.get(cod, "")
        _link_partido_eleccion(session, election_id, partido_id, siglas)
            
    # 5. Mesas
    # We need to convert mesas iterable to list if iterating multiple times or if generator
    # Assume mesas is list or re-iterable. If single-use generator, careful.
    # In transformers_congreso usually generator. Consume to list if not.
    mesas_list = list(mesas) if not isinstance(mesas, list) else mesas
    mesa_ids = _upsert_mesas(session, mesas_list)
        
    # 6. Votes
    _upsert_votos(session, election_id, mesa_ids, candidatura_to_partido, votos_mesa)
        
    # 7. Gold (Hemiciclo)
    _upsert_gold(session, election_id, gold_rows, candidatura_to_partido)
        
    session.commit()
    logger.info("Load successfully completed. Election ID: %s", election_id)
    return election_id