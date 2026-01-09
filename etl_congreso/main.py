from etl_congreso.domain.models import ElectionConfig
from etl_congreso.config.elections import get_election_config

import argparse
import logging
from pathlib import Path
import json
import os
from dotenv import load_dotenv

from .etl.geo import collect_geography_data
from .etl.load import load_gold
from .etl.extract import (
    parse_ambitos_superiores,
    parse_candidatos,
    parse_candidaturas,
    parse_mesas,
    parse_mesas_candidaturas,
    parse_resultados_ambito_candidatura,
)
from .etl.transform import build_gold_hemiciclo_rows, build_silver_bundle
from .config import settings

def run_etl(election_config: ElectionConfig) -> str:
    """
    Ejecuta la ETL completa para una elección concreta.
    Devuelve el ID de la elección en la base de datos.
    """
    logging.info("Iniciando ETL para %s", election_config.identifier)

    logging.info("Leyendo ficheros InfoElectoral...")
    candidaturas = parse_candidaturas(election_config.files.candidaturas)
    candidatos = parse_candidatos(election_config.files.candidatos)
    ambitos = parse_ambitos_superiores(election_config.files.ambitos_superiores)
    resultados = parse_resultados_ambito_candidatura(election_config.files.resultados_ambito_candidatura)
    mesas_raw = parse_mesas(election_config.files.datos_mesas)
    votos_mesa_raw = parse_mesas_candidaturas(election_config.files.datos_mesas_candidaturas)
    logging.info(
        "Leído: candidaturas=%d, candidatos=%d, ambitos=%d, resultados=%d, mesas=%d, votos_mesa=%d",
        len(candidaturas),
        len(candidatos),
        len(ambitos),
        len(resultados),
        len(mesas_raw),
        len(votos_mesa_raw),
    )

    raw_root = Path(__file__).resolve().parent.parent / "RAW"
    logging.info("Construyendo geografía desde diccionarios oficiales...")
    geography = collect_geography_data(
        diccionario_path=raw_root / "diccionario25.xlsx",
        codislas_path=raw_root / "25codislas.xlsx",
        ambitos=ambitos,
        municipios_path_backup=election_config.files.datos_municipios,
    )
    try:
        with (Path(__file__).resolve().parent / "resources" / "partido_colores.json").open("r", encoding="utf-8") as fh:
            color_lookup = {k.upper(): v for k, v in json.load(fh).items()}
    except FileNotFoundError:
        color_lookup = {}
        
    ###
    # TODO: 
    ###
    # - Create function which semantically links a party name with root party

    silver_bundle = build_silver_bundle(
        descripcion=election_config.descripcion,
        tipo_eleccion=election_config.tipo_eleccion,
        fecha=election_config.fecha,
        aa=election_config.aa,
        mm=election_config.mm,
        vuelta=election_config.vuelta,
        candidaturas=candidaturas,
        candidatos=candidatos,
        ambitos=ambitos,
        resultados=resultados,
    )
    logging.info("Transformación silver completada (bundle listo).")
    gold_rows = build_gold_hemiciclo_rows(
        ambitos=silver_bundle.ambitos,
        resultados=silver_bundle.resultados,
        candidaturas=silver_bundle.candidaturas,
    )
    from .etl.transform import build_mesas, build_votos_mesa

    mesas = build_mesas(mesas_raw)
    votos_mesa = build_votos_mesa(votos_mesa_raw)
    logging.info(
        "Preparado gold: hemiciclo=%d filas, mesas=%d, votos_mesa=%d",
        len(gold_rows),
        len(mesas),
        len(votos_mesa),
    )

    election_id = load_gold(silver_bundle, gold_rows, geography, mesas, votos_mesa, color_lookup)
    logging.info("ETL completada. election_id=%s", election_id)
    return election_id


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Loads congressional election data from different sources into Postgres."
    )
    parser.add_argument("--type", 
                        required=True,
                        choices=['congreso'],
                        help="Specifies an election type")
    parser.add_argument("--date",
                        help="For loading specific election data, date format: YYYY_MM")
    args = parser.parse_args()
    logging.basicConfig(level=settings.LOGGING_LEVEL, format=settings.LOGGING_FORMAT)
    election_configs= get_election_config(args.type, args.date)
    
    for election_config in election_configs:
        run_etl(election_config)


if __name__ == "__main__":
    main()
