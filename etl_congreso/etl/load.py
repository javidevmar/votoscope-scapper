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
    # Importamos Gold si en el futuro decidimos gestionarlo desde aquí, 
    # pero por ahora usaremos SQL crudo para Gold o asumiremos que la tabla existe 
    # y la atacamos via SQL o definimos un modelo 'mirror' sin gestionarlo con Alembic.
    # Como definimos que el Front es dueño de Gold, usaremos SQL crudo para insertar en Gold
    # para no acoplar los modelos ORM de Silver a Gold.
)

logger = logging.getLogger(__name__)


def _get_or_create_election(session: Session, row: SilverElectionRow) -> str:
    year = row.fecha.year
    month = row.fecha.month
    
    # 1. Buscar coincidencia exacta
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

    # 2. Crear nueva elección
    new_election = Eleccion(
        ano=year,
        mes=month,
        tipo="Generales",
        auto_id=None,
        prov_id=None,
        muni_id=None
    )
    session.add(new_election)
    session.flush() # Para obtener el ID generado
    
    logger.info("Election created (Generales %s-%02d): %s", year, month, new_election.id)
    return str(new_election.id)


def _upsert_partidos(
    session: Session, candidaturas: Iterable[SilverCandidaturaRow], color_lookup: Dict[str, str]
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Devuelve (codigo_candidatura -> partido_id, codigo_candidatura -> siglas).
    """
    mapping: Dict[str, str] = {}
    siglas_map: Dict[str, str] = {}
    
    # Cache local de siglas -> partido_id para evitar queries repetidas en bucle
    # Primero cargamos todos los partidos existentes para tener la cache caliente
    existing_partidos = session.execute(select(Partido.siglas, Partido.id)).all()
    siglas_cache = {row.siglas: str(row.id) for row in existing_partidos if row.siglas}

    created = 0
    updated = 0
    
    for candidatura in candidaturas:
        siglas = candidatura.siglas
        partido_id = siglas_cache.get(siglas)
        color = color_lookup.get(siglas.upper())

        if partido_id:
            # Si existe, actualizamos color si hace falta mediante UPDATE directo
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
            # Insertar nuevo
            # Usamos pg_insert para manejar concurrencia si hubiera (on conflict do nothing)
            # aunque aquí confiamos en nuestra cache local.
            stmt = pg_insert(Partido).values(
                nombre=candidatura.nombre_largo or siglas,
                siglas=siglas,
                color=color
            ).returning(Partido.id)
            
            # En caso de race condition donde otro proceso lo insertó justo ahora
            stmt = stmt.on_conflict_do_nothing(index_elements=['id']) # ID es UUID, esto no pasará por ID.
            # Realmente el conflicto sería por SIGLAS si tuviéramos constraint unique en siglas (que no tenemos en el modelo estricto, pero asumimos lógica de negocio)
            # Como no hay unique constraint en siglas en el DDL, hacemos insert normal.
            # Mejor: Buscamos de nuevo por si acaso, o insertamos.
            
            # Nota: El modelo Silver actual NO tiene unique en siglas, pero la lógica de negocio asume unicidad.
            # Vamos a insertar.
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
        
    logger.info("Partidos: nuevos=%d, actualizados/revisados=%d", created, updated)
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
    # Gold es un esquema especial gestionado por el Front. 
    # Usaremos SQL crudo para no tener que definir modelos ORM para Gold aquí
    # y evitar conflictos con Alembic.
    
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
            
    logger.info("Registros gold hemiciclo: nuevos=%d, actualizados=%d", inserted, updated)


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
    
    logger.info("Geografía actualizada.")


def _upsert_mesas(session: Session, mesas: Iterable[Tuple[str, str, str, str, str]]) -> Dict[Tuple[str, str, str, str, str], str]:
    mapping: Dict[Tuple[str, str, str, str, str], str] = {}
    
    # Pre-cargar mesas existentes para esta provincia/municipio podría ser optimización,
    # pero como son muchas, mejor upsert bajo demanda o batch.
    # Dado que SQLAlchemy core es rápido, haremos batches si es necesario.
    # Para simplificar mantengo el loop, pero optimizable.
    
    # Estrategia: 
    # 1. Intentar buscar ID.
    # 2. Si no existe, insertar.
    
    # Mejor: Hacer un SELECT masivo de los IDs que necesitamos?
    # Como el input es iterable, procesamos uno a uno o en bloques.
    
    cnt_inserted = 0
    cnt_existing = 0
    
    for prov, muni, distrito, seccion, mesa_cod in mesas:
        # Clave natural compuesta
        key = (prov, muni, distrito, seccion, mesa_cod)
        
        # Primero intentamos insert on conflict do nothing y retornar ID
        # Nota: Returning ID en on_conflict_do_nothing a veces no devuelve nada en Postgres si hay conflicto.
        # Por eso el patrón suele ser: CTE o Select previo.
        
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
                # Si fallara por race condition (otro proceso insertó), hacemos rollback parcial savepoint
                # y leemos. (Complejidad extra, asumimos single worker por ahora).
                session.rollback()
                existing_id = session.execute(stmt_select).scalar_one()
                mapping[key] = str(existing_id)
                cnt_existing += 1
                
    logger.info("Mesas: nuevas=%d, existentes=%d", cnt_inserted, cnt_existing)
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

    # Ejecutar upsert masivo
    # Chunking si fuera muy grande (ej > 10000)
    chunk_size = 5000
    for i in range(0, len(batch_values), chunk_size):
        chunk = batch_values[i:i + chunk_size]
        stmt = pg_insert(Voto).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=['mesa_id', 'eleccion_id', 'candidatura'],
            set_={'votos': stmt.excluded.votos}
        )
        session.execute(stmt)
        
    logger.info("Votos procesados: %d registros", len(batch_values))


def load_gold(
    bundle: SilverBundle,
    gold_rows: Iterable[GoldHemicicloRow],
    geography: GeographyData,
    mesas: Iterable[Tuple[str, str, str, str, str]],
    votos_mesa: Iterable[Tuple[str, str, str, str, str, str, int]],
    color_lookup: Dict[str, str],
) -> str:
    """
    Orquestador de carga usando SQLAlchemy Session.
    """
    session = create_session()
    try:
        # 1. Elección
        election_id = _get_or_create_election(session, bundle.election)
        
        # 2. Geografía
        _upsert_geography(session, geography)
        
        # 3. Partidos
        candidatura_to_partido, siglas_map = _upsert_partidos(session, bundle.candidaturas, color_lookup)
        
        # 4. Enlace Partido-Elección
        for cod, partido_id in candidatura_to_partido.items():
            siglas = siglas_map.get(cod, "")
            _link_partido_eleccion(session, election_id, partido_id, siglas)
            
        # 5. Mesas
        # Necesitamos convertir el iterable de mesas a lista si vamos a iterar varias veces o si es generator
        # Asumimos que mesas es lista o re-iterable. Si es generador de un solo uso, cuidado.
        # En transformers_congreso suele ser generador. Lo consumimos a lista si no lo es.
        mesas_list = list(mesas) if not isinstance(mesas, list) else mesas
        mesa_ids = _upsert_mesas(session, mesas_list)
        
        # 6. Votos
        _upsert_votos(session, election_id, mesa_ids, candidatura_to_partido, votos_mesa)
        
        # 7. Gold (Hemiciclo)
        _upsert_gold(session, election_id, gold_rows, candidatura_to_partido)
        
        session.commit()
        logger.info("Carga completada exitosamente. Election ID: %s", election_id)
        return election_id
        
    except Exception as e:
        session.rollback()
        logger.error("Error durante la carga, rollback ejecutado: %s", e)
        raise e
    finally:
        session.close()