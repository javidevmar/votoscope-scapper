from __future__ import annotations

import logging
from typing import Dict, Iterable

from .db import get_connection
from .models import (
    GeographyData,
    GoldHemicicloRow,
    SilverBundle,
    SilverCandidaturaRow,
    SilverElectionRow,
)

logger = logging.getLogger(__name__)


def _get_or_create_election(cur, row: SilverElectionRow) -> str:
    cur.execute(
        """
        SELECT id FROM eleccion
        WHERE ano = %s AND tipo = %s AND auto_id IS NULL AND prov_id IS NULL AND muni_id IS NULL
        LIMIT 1;
        """,
        (row.fecha.year, "Generales"),
    )
    found = cur.fetchone()
    if found:
        return found[0]

    cur.execute(
        """
        INSERT INTO eleccion(ano, tipo, auto_id, prov_id, muni_id)
        VALUES (%s, %s, NULL, NULL, NULL)
        RETURNING id;
        """,
        (row.fecha.year, "Generales"),
    )
    election_id = cur.fetchone()[0]
    logger.info("Election created (Generales %s): %s", row.fecha.year, election_id)
    return election_id


def _upsert_partidos(
    cur, candidaturas: Iterable[SilverCandidaturaRow], color_lookup: Dict[str, str]
) -> tuple[Dict[str, str], Dict[str, str]]:
    """
    Devuelve (codigo_candidatura -> partido_id, codigo_candidatura -> siglas).
    Inserta partidos por siglas si no existen.
    """
    mapping: Dict[str, str] = {}
    siglas_map: Dict[str, str] = {}
    siglas_cache: Dict[str, str] = {}
    for candidatura in candidaturas:
        siglas = candidatura.siglas
        if siglas in siglas_cache:
            partido_id = siglas_cache[siglas]
        else:
            cur.execute("SELECT id FROM partido WHERE siglas = %s LIMIT 1;", (siglas,))
            row = cur.fetchone()
            if row:
                partido_id = row[0]
                color = color_lookup.get(siglas.upper())
                if color:
                    cur.execute(
                        "UPDATE partido SET color = %s WHERE id = %s AND (color IS NULL OR color = '')",
                        (color, partido_id),
                    )
            else:
                color = color_lookup.get(siglas.upper())
                cur.execute(
                    """
                    INSERT INTO partido(nombre, siglas, color)
                    VALUES (%s, %s, NULL)
                    RETURNING id;
                    """,
                    (candidatura.nombre_largo or siglas, siglas),
                )
                partido_id = cur.fetchone()[0]
                if color:
                    cur.execute("UPDATE partido SET color = %s WHERE id = %s", (color, partido_id))
            siglas_cache[siglas] = partido_id
        mapping[candidatura.codigo] = partido_id
        siglas_map[candidatura.codigo] = siglas
    logger.info("Partidos reconciliados/creados: %d", len(siglas_cache))
    return mapping, siglas_map


def _link_partido_eleccion(cur, election_id: str, partido_id: str, siglas: str) -> None:
    cur.execute(
        """
        INSERT INTO partido_eleccion(partido_id, eleccion_id, siglas_eleccion)
        VALUES (%s, %s, %s)
        ON CONFLICT (partido_id, eleccion_id) DO NOTHING;
        """,
        (partido_id, election_id, siglas),
    )


def _upsert_gold(
    cur,
    election_id: str,
    gold_rows: Iterable[GoldHemicicloRow],
    candidatura_to_partido: Dict[str, str],
) -> None:
    total = 0
    for row in gold_rows:
        partido_id = candidatura_to_partido.get(row.cod_candidatura)
        if not partido_id:
            continue
        cur.execute(
            """
            INSERT INTO gold_congreso_hemiciclo (
                eleccion_id, partido_id, codigo_candidatura_infoelectoral,
                nivel_ambito, cod_provincia, nombre_ambito,
                siglas_candidatura, color_hex, escanos, votos, porcentaje_voto
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULLIF(%s, ''), %s, %s, %s)
            ON CONFLICT (eleccion_id, nivel_ambito, cod_provincia, partido_id)
            DO UPDATE SET
                nombre_ambito = EXCLUDED.nombre_ambito,
                siglas_candidatura = EXCLUDED.siglas_candidatura,
                color_hex = EXCLUDED.color_hex,
                escanos = EXCLUDED.escanos,
                votos = EXCLUDED.votos,
                porcentaje_voto = EXCLUDED.porcentaje_voto,
                codigo_candidatura_infoelectoral = EXCLUDED.codigo_candidatura_infoelectoral;
            """,
            (
                election_id,
                partido_id,
                row.cod_candidatura,
                row.nivel_ambito,
                row.cod_provincia,
                row.nombre_ambito,
                row.siglas_candidatura,
                None,
                row.escanos,
                row.votos,
                row.porcentaje_voto,
            ),
        )
        total += 1
    logger.info("Registros gold hemiciclo upserted: %d", total)


def _upsert_provinces(cur, provinces: Iterable) -> None:
    total = 0
    for prov in provinces:
        cur.execute(
            """
            INSERT INTO provincia(ine_code, auto_code, nombre)
            VALUES (%s, %s, %s)
            ON CONFLICT (ine_code) DO UPDATE SET auto_code = EXCLUDED.auto_code, nombre = EXCLUDED.nombre;
            """,
            (prov.ine_code, prov.auto_code, prov.name),
        )
        total += 1
    logger.info("Provincias upserted: %d", total)


def _upsert_municipios(cur, municipios: Iterable) -> None:
    total = 0
    for muni in municipios:
        cur.execute(
            """
            INSERT INTO municipio(prov_code, muni_code, nombre)
            VALUES (%s, %s, %s)
            ON CONFLICT (prov_code, muni_code) DO UPDATE SET nombre = EXCLUDED.nombre;
            """,
            (muni.prov_code, muni.muni_code, muni.name),
        )
        total += 1
    logger.info("Municipios upserted: %d", total)


def _upsert_mesas(cur, mesas: Iterable[tuple[str, str, str, str, str]]) -> Dict[tuple[str, str, str, str, str], str]:
    mapping: Dict[tuple[str, str, str, str, str], str] = {}
    for prov, muni, distrito, seccion, mesa in mesas:
        cur.execute(
            """
            INSERT INTO mesa(cod_prov, cod_muni, cod_distrito, cod_seccion, cod_mesa)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cod_prov, cod_muni, cod_distrito, cod_seccion, cod_mesa) DO NOTHING
            RETURNING id;
            """,
            (prov, muni, distrito, seccion, mesa),
        )
        row = cur.fetchone()
        if row:
            mesa_id = row[0]
        else:
            cur.execute(
                """
                SELECT id FROM mesa WHERE cod_prov = %s AND cod_muni = %s AND cod_distrito = %s AND cod_seccion = %s AND cod_mesa = %s
                """,
                (prov, muni, distrito, seccion, mesa),
            )
            result = cur.fetchone()
            if not result:
                continue
            mesa_id = result[0]
        mapping[(prov, muni, distrito, seccion, mesa)] = mesa_id
    logger.info("Mesas upserted/resolved: %d", len(mapping))
    return mapping


def _upsert_votos(
    cur,
    election_id: str,
    mesa_ids: Dict[tuple[str, str, str, str, str], str],
    candidatura_to_partido: Dict[str, str],
    votos: Iterable[tuple[str, str, str, str, str, str, int]],
) -> None:
    total = 0
    for prov, muni, distrito, seccion, mesa, cod_candidatura, votos_val in votos:
        mesa_id = mesa_ids.get((prov, muni, distrito, seccion, mesa))
        partido_id = candidatura_to_partido.get(cod_candidatura)
        if not mesa_id or not partido_id:
            continue
        cur.execute(
            """
            INSERT INTO voto(mesa_id, eleccion_id, candidatura, votos)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (mesa_id, eleccion_id, candidatura)
            DO UPDATE SET votos = EXCLUDED.votos;
            """,
            (mesa_id, election_id, partido_id, votos_val),
        )
        total += 1
    logger.info("Votos por mesa upserted: %d", total)


def _upsert_geography(cur, geography: GeographyData) -> None:
    for code, name in geography.autonomias.items():
        cur.execute(
            """
            INSERT INTO autonomia(ine_code, nombre)
            VALUES (%s, %s)
            ON CONFLICT (ine_code) DO UPDATE SET nombre = EXCLUDED.nombre;
            """,
            (code, name),
        )
    _upsert_provinces(cur, geography.provinces)
    _upsert_municipios(cur, geography.municipios)


def load_gold(
    bundle: SilverBundle,
    gold_rows: Iterable[GoldHemicicloRow],
    geography: GeographyData,
    mesas: Iterable[tuple[str, str, str, str, str]],
    votos_mesa: Iterable[tuple[str, str, str, str, str, str, int]],
) -> str:
    """
    Inserta o actualiza los datos en tablas existentes (eleccion, partido, partido_eleccion), mesas/votos y la tabla gold_congreso_hemiciclo.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                election_id = _get_or_create_election(cur, bundle.election)
                _upsert_geography(cur, geography)
                candidatura_to_partido, siglas_map = _upsert_partidos(cur, bundle.candidaturas)
                for cod, partido_id in candidatura_to_partido.items():
                    siglas = siglas_map.get(cod, "")
                    _link_partido_eleccion(cur, election_id, partido_id, siglas)
                mesa_ids = _upsert_mesas(cur, mesas)
                _upsert_votos(cur, election_id, mesa_ids, candidatura_to_partido, votos_mesa)
                _upsert_gold(cur, election_id, gold_rows, candidatura_to_partido)
        return election_id
    finally:
        conn.close()
