from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import available_elections, get_election_config
from .geography_sources import collect_geography_data
from .loaders_postgres import load_gold
from .parsers_infoelectoral import (
    parse_ambitos_superiores,
    parse_candidatos,
    parse_candidaturas,
    parse_mesas,
    parse_mesas_candidaturas,
    parse_resultados_ambito_candidatura,
)
from .transformers_congreso import build_gold_hemiciclo_rows, build_silver_bundle


def run_etl(election_identifier: str) -> str:
    """
    Ejecuta la ETL completa para una elección concreta.
    Devuelve el ID de la elección en la base de datos.
    """
    config = get_election_config(election_identifier)
    logging.info("Iniciando ETL para %s", election_identifier)

    candidaturas = parse_candidaturas(config.files.candidaturas)
    candidatos = parse_candidatos(config.files.candidatos)
    ambitos = parse_ambitos_superiores(config.files.ambitos_superiores)
    resultados = parse_resultados_ambito_candidatura(config.files.resultados_ambito_candidatura)
    mesas_raw = parse_mesas(config.files.datos_mesas)
    votos_mesa_raw = parse_mesas_candidaturas(config.files.datos_mesas_candidaturas)

    raw_root = Path(__file__).resolve().parent.parent / "RAW"
    geography = collect_geography_data(
        diccionario_path=raw_root / "diccionario25.xlsx",
        codislas_path=raw_root / "25codislas.xlsx",
        ambitos=ambitos,
    )

    silver_bundle = build_silver_bundle(
        descripcion=config.descripcion,
        tipo_eleccion=config.tipo_eleccion,
        fecha=config.fecha,
        aa=config.aa,
        mm=config.mm,
        vuelta=config.vuelta,
        candidaturas=candidaturas,
        candidatos=candidatos,
        ambitos=ambitos,
        resultados=resultados,
    )
    gold_rows = build_gold_hemiciclo_rows(
        ambitos=silver_bundle.ambitos,
        resultados=silver_bundle.resultados,
        candidaturas=silver_bundle.candidaturas,
    )
    from .transformers_congreso import build_mesas, build_votos_mesa

    mesas = build_mesas(mesas_raw)
    votos_mesa = build_votos_mesa(votos_mesa_raw)

    election_id = load_gold(silver_bundle, gold_rows, geography, mesas, votos_mesa)
    logging.info("ETL completada. election_id=%s", election_id)
    return election_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Carga en Postgres los datos de elecciones al Congreso (InfoElectoral)."
    )
    parser.add_argument(
        "--election",
        required=True,
        choices=available_elections(),
        help="Identificador interno de elección, por ejemplo congreso_2019_11",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    run_etl(args.election)


if __name__ == "__main__":
    main()
