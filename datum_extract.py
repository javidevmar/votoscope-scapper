#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import pandas as pd

# Encoding and directories
ENCODING = "cp1252"
DEFAULT_DATUM_DIR = Path("DATUM_RAW") / "Congreso"


class FieldKind(StrEnum):
    STR = "str"
    INT = "int"

    @property
    def is_numeric(self) -> bool:
        return self is FieldKind.INT


@dataclass(frozen=True, slots=True)
class Field:
    name: str
    start: int
    end: int
    kind: FieldKind = FieldKind.STR

    @property
    def colspec(self) -> tuple[int, int]:
        return self.start - 1, self.end

    @property
    def requires_numeric(self) -> bool:
        return self.kind.is_numeric


FIELD_LAYOUTS = {
    "01": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("fichero_01", 10, 10, FieldKind.INT),
        Field("fichero_02", 11, 11, FieldKind.INT),
        Field("fichero_03", 12, 12, FieldKind.INT),
        Field("fichero_04", 13, 13, FieldKind.INT),
        Field("fichero_05", 14, 14, FieldKind.INT),
        Field("fichero_06", 15, 15, FieldKind.INT),
        Field("fichero_07", 16, 16, FieldKind.INT),
        Field("fichero_08", 17, 17, FieldKind.INT),
        Field("fichero_09", 18, 18, FieldKind.INT),
        Field("fichero_10", 19, 19, FieldKind.INT),
        Field("fichero_1104", 20, 20, FieldKind.INT),
        Field("fichero_1204", 21, 21, FieldKind.INT),
        Field("fichero_0510", 22, 22, FieldKind.INT),
        Field("fichero_0610", 23, 23, FieldKind.INT),
        Field("fichero_0710", 24, 24, FieldKind.INT),
        Field("fichero_0810", 25, 25, FieldKind.INT),
    ],
    "02": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("tipo_ambito", 10, 10),
        Field("cod_ambito", 11, 12),
        Field("fecha_dia", 13, 14, FieldKind.INT),
        Field("fecha_mes", 15, 16, FieldKind.INT),
        Field("fecha_anio", 17, 20, FieldKind.INT),
        Field("hora_apertura", 21, 25),
        Field("hora_cierre", 26, 30),
        Field("hora_avance_1", 31, 35),
        Field("hora_avance_2", 36, 40),
    ],
    "03": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("cod_candidatura", 9, 14),
        Field("siglas", 15, 64),
        Field("denominacion", 65, 214),
        Field("cabecera_provincial", 215, 220),
        Field("cabecera_autonomica", 221, 226),
        Field("cabecera_nacional", 227, 232),
    ],
    "04": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("cod_provincia", 10, 11),
        Field("cod_distrito_electoral", 12, 12),
        Field("cod_municipio_o_senador", 13, 15),
        Field("cod_candidatura", 16, 21),
        Field("orden_candidato", 22, 24, FieldKind.INT),
        Field("tipo_candidato", 25, 25),
        Field("nombre", 26, 50),
        Field("primer_apellido", 51, 75),
        Field("segundo_apellido", 76, 100),
        Field("sexo", 101, 101),
        Field("nacimiento_dia", 102, 103, FieldKind.INT),
        Field("nacimiento_mes", 104, 105, FieldKind.INT),
        Field("nacimiento_anio", 106, 109, FieldKind.INT),
        Field("dni", 110, 119),
        Field("elegido", 120, 120),
    ],
    "05": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("cod_autonomia", 10, 11),
        Field("cod_provincia", 12, 13),
        Field("cod_municipio", 14, 16),
        Field("num_distrito", 17, 18),
        Field("nombre_municipio", 19, 118),
        Field("cod_distrito_electoral", 119, 119),
        Field("cod_partido_judicial", 120, 122),
        Field("cod_diputacion", 123, 125),
        Field("cod_comarca", 126, 128),
        Field("poblacion_derecho", 129, 136, FieldKind.INT),
        Field("num_mesas", 137, 141, FieldKind.INT),
        Field("censo_ine", 142, 149, FieldKind.INT),
        Field("censo_escrutinio", 150, 157, FieldKind.INT),
        Field("censo_cere_escrutinio", 158, 165, FieldKind.INT),
        Field("total_votantes_cere", 166, 173, FieldKind.INT),
        Field("votantes_avance_1", 174, 181, FieldKind.INT),
        Field("votantes_avance_2", 182, 189, FieldKind.INT),
        Field("votos_blanco", 190, 197, FieldKind.INT),
        Field("votos_nulos", 198, 205, FieldKind.INT),
        Field("votos_candidaturas", 206, 213, FieldKind.INT),
        Field("num_escanos", 214, 216, FieldKind.INT),
        Field("votos_afirmativos", 217, 224, FieldKind.INT),
        Field("votos_negativos", 225, 232, FieldKind.INT),
        Field("oficial", 233, 233),
    ],
    "06": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("cod_provincia", 10, 11),
        Field("cod_municipio", 12, 14),
        Field("num_distrito", 15, 16),
        Field("cod_candidatura", 17, 22),
        Field("votos", 23, 30, FieldKind.INT),
        Field("candidatos", 31, 33, FieldKind.INT),
    ],
    "07": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("cod_autonomia", 10, 11),
        Field("cod_provincia", 12, 13),
        Field("cod_distrito_electoral", 14, 14),
        Field("nombre_ambito", 15, 64),
        Field("poblacion_derecho", 65, 72, FieldKind.INT),
        Field("num_mesas", 73, 77, FieldKind.INT),
        Field("censo_ine", 78, 85, FieldKind.INT),
        Field("censo_escrutinio", 86, 93, FieldKind.INT),
        Field("censo_cere_escrutinio", 94, 101, FieldKind.INT),
        Field("total_votantes_cere", 102, 109, FieldKind.INT),
        Field("votantes_avance_1", 110, 117, FieldKind.INT),
        Field("votantes_avance_2", 118, 125, FieldKind.INT),
        Field("votos_blanco", 126, 133, FieldKind.INT),
        Field("votos_nulos", 134, 141, FieldKind.INT),
        Field("votos_candidaturas", 142, 149, FieldKind.INT),
        Field("num_escanos", 150, 155, FieldKind.INT),
        Field("votos_afirmativos", 156, 163, FieldKind.INT),
        Field("votos_negativos", 164, 171, FieldKind.INT),
        Field("oficial", 172, 172),
    ],
    "08": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("cod_autonomia", 10, 11),
        Field("cod_provincia", 12, 13),
        Field("cod_distrito_electoral", 14, 14),
        Field("cod_candidatura", 15, 20),
        Field("votos", 21, 28, FieldKind.INT),
        Field("candidatos", 29, 33, FieldKind.INT),
    ],
    "09": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("cod_autonomia", 10, 11),
        Field("cod_provincia", 12, 13),
        Field("cod_municipio", 14, 16),
        Field("num_distrito", 17, 18),
        Field("cod_seccion", 19, 22),
        Field("cod_mesa", 23, 23),
        Field("censo_ine", 24, 30, FieldKind.INT),
        Field("censo_escrutinio", 31, 37, FieldKind.INT),
        Field("censo_cere_escrutinio", 38, 44, FieldKind.INT),
        Field("total_votantes_cere", 45, 51, FieldKind.INT),
        Field("votantes_avance_1", 52, 58, FieldKind.INT),
        Field("votantes_avance_2", 59, 65, FieldKind.INT),
        Field("votos_blanco", 66, 72, FieldKind.INT),
        Field("votos_nulos", 73, 79, FieldKind.INT),
        Field("votos_candidaturas", 80, 86, FieldKind.INT),
        Field("votos_afirmativos", 87, 93, FieldKind.INT),
        Field("votos_negativos", 94, 100, FieldKind.INT),
        Field("oficial", 101, 101),
    ],
    "10": [
        Field("tipo_eleccion", 1, 2),
        Field("anio", 3, 6, FieldKind.INT),
        Field("mes", 7, 8, FieldKind.INT),
        Field("vuelta", 9, 9, FieldKind.INT),
        Field("cod_autonomia", 10, 11),
        Field("cod_provincia", 12, 13),
        Field("cod_municipio", 14, 16),
        Field("num_distrito", 17, 18),
        Field("cod_seccion", 19, 22),
        Field("cod_mesa", 23, 23),
        Field("cod_candidatura", 24, 29),
        Field("votos", 30, 36, FieldKind.INT),
    ],
}

FILE_LABELS = {
    "01": "control",
    "02": "identificacion",
    "03": "candidaturas",
    "04": "candidatos",
    "05": "municipios",
    "06": "municipios_candidaturas",
    "07": "ambitos",
    "08": "ambitos_candidaturas",
    "09": "mesas",
    "10": "mesas_candidaturas",
}


def read_fixed_width(path: Path) -> pd.DataFrame:
    prefix = path.name[:2]
    layout = FIELD_LAYOUTS.get(prefix)
    if layout is None:
        raise KeyError(f"No hay layout configurado para {path.name}")
    colspecs = [field.colspec for field in layout]
    names = [field.name for field in layout]
    df = pd.read_fwf(path, colspecs=colspecs, names=names, dtype=str, encoding=ENCODING)
    for column in df.columns:
        df[column] = df[column].fillna("").str.strip()
    numeric_fields = [field.name for field in layout if field.requires_numeric]
    if numeric_fields:
        numeric = df.loc[:, numeric_fields].replace("", pd.NA)
        df.loc[:, numeric_fields] = (
            numeric.apply(pd.to_numeric, errors="coerce").astype("Int64")
        )
    return df


def should_include(path: Path, selectors: set[str]) -> bool:
    if not selectors:
        return True
    match (path.name.upper(), path.stem.upper(), path.name[:2].upper()):
        case name, stem, prefix:
            return any(candidate in selectors for candidate in (name, stem, prefix))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extrae ficheros DATUM de ancho fijo a pandas / CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--datum-dir",
        type=Path,
        default=DEFAULT_DATUM_DIR,
        help="Directorio con los .DAT.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Si se indica, guarda un CSV por fichero en este directorio.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        help="Filtra por prefijo (05) o nombre exacto (05022307.DAT).",
    )
    parser.add_argument(
        "--head",
        type=int,
        default=0,
        help="Muestra N primeras filas de cada fichero.",
    )
    args = parser.parse_args()

    datum_dir: Path = args.datum_dir
    if not datum_dir.exists():
        raise SystemExit(f"No encuentro el directorio {datum_dir}")

    selectors = {item.upper() for item in (args.only or [])}
    output_dir = args.output_dir
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    dat_files = sorted(datum_dir.rglob("*.DAT"))
    if not dat_files:
        raise SystemExit(f"No hay .DAT en {datum_dir}")

    for path in dat_files:
        if not should_include(path, selectors):
            continue
        prefix = path.name[:2]
        label = FILE_LABELS.get(prefix, "datos")
        df = read_fixed_width(path)
        print(f"\n{path.name} ({label}): {len(df):,} filas × {len(df.columns)} columnas")
        if args.head:
            print(df.head(args.head).to_string(index=False))
        if output_dir:
            csv_path = output_dir / f"{path.stem.lower()}_{label}.csv"
            df.to_csv(csv_path, index=False)
            print(f"Guardado en {csv_path}")


if __name__ == "__main__":
    main()
