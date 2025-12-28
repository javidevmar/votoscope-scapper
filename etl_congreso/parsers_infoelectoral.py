from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, List

from .constants import ENCODING_INFOELECTORAL
from .models import (
    AmbitoSuperiorRecord,
    CandidatoRecord,
    CandidaturaRecord,
    MesaRecord,
    MesaVotoRecord,
    ResultadoAmbitoCandidaturaRecord,
)


def _slice(line: str, start: int, end: int) -> str:
    """Extrae un campo de posiciones 1-indexed [start, end]."""
    return line[start - 1 : end]


def _to_int(raw: str) -> int | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _to_bool(flag: str) -> bool:
    return flag.strip().upper() == "S"


def _parse_date(day: str, month: str, year: str) -> date | None:
    if not (day.strip() and month.strip() and year.strip()):
        return None
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def _read_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding=ENCODING_INFOELECTORAL, errors="ignore") as handle:
        for line in handle:
            yield line.rstrip("\n")


def parse_candidaturas(path: Path) -> List[CandidaturaRecord]:
    """
    Parsea el fichero 0302aamm.dat de candidaturas.
    """
    records: list[CandidaturaRecord] = []
    for line in _read_lines(path):
        records.append(
            CandidaturaRecord(
                tipo_eleccion=_slice(line, 1, 2),
                anio=_slice(line, 3, 6),
                mes=_slice(line, 7, 8),
                codigo=_slice(line, 9, 14).strip(),
                siglas=_slice(line, 15, 64).strip(),
                denominacion=_slice(line, 65, 214).strip(),
                cabecera_provincial=_slice(line, 215, 220).strip(),
                cabecera_autonomica=_slice(line, 221, 226).strip(),
                cabecera_nacional=_slice(line, 227, 232).strip(),
            )
        )
    return records


def parse_candidatos(path: Path) -> List[CandidatoRecord]:
    """
    Parsea el fichero 0402aamm.dat de relación de candidatos.
    """
    records: list[CandidatoRecord] = []
    for line in _read_lines(path):
        fecha_nac = _parse_date(
            _slice(line, 102, 103),
            _slice(line, 104, 105),
            _slice(line, 106, 109),
        )
        records.append(
            CandidatoRecord(
                tipo_eleccion=_slice(line, 1, 2),
                anio=_slice(line, 3, 6),
                mes=_slice(line, 7, 8),
                vuelta=_slice(line, 9, 9),
                cod_provincia=_slice(line, 10, 11).strip(),
                cod_distrito=_slice(line, 12, 12).strip(),
                cod_municipio=_slice(line, 13, 15).strip(),
                cod_candidatura=_slice(line, 16, 21).strip(),
                orden=_to_int(_slice(line, 22, 24)) or 0,
                tipo_candidato=_slice(line, 25, 25).strip(),
                nombre=_slice(line, 26, 50).strip(),
                primer_apellido=_slice(line, 51, 75).strip(),
                segundo_apellido=_slice(line, 76, 100).strip(),
                sexo=_slice(line, 101, 101).strip(),
                fecha_nacimiento=fecha_nac,
                dni=_slice(line, 110, 119).strip(),
                elegido=_to_bool(_slice(line, 120, 120)),
            )
        )
    return records


def parse_ambitos_superiores(path: Path) -> List[AmbitoSuperiorRecord]:
    """
    Parsea el fichero 0702aamm.dat con datos comunes de ámbitos superiores al municipio.
    """
    records: list[AmbitoSuperiorRecord] = []
    for line in _read_lines(path):
        records.append(
            AmbitoSuperiorRecord(
                tipo_eleccion=_slice(line, 1, 2),
                anio=_slice(line, 3, 6),
                mes=_slice(line, 7, 8),
                vuelta=_slice(line, 9, 9),
                cod_ccaa=_slice(line, 10, 11).strip(),
                cod_provincia=_slice(line, 12, 13).strip(),
                cod_distrito=_slice(line, 14, 14).strip(),
                nombre_ambito=_slice(line, 15, 64).strip(),
                poblacion_derecho=_to_int(_slice(line, 65, 72)),
                num_mesas=_to_int(_slice(line, 73, 77)),
                censo_ine=_to_int(_slice(line, 78, 85)),
                censo_escrutinio=_to_int(_slice(line, 86, 93)),
                censo_cere=_to_int(_slice(line, 94, 101)),
                total_votantes_cere=_to_int(_slice(line, 102, 109)),
                votantes_avance_1=_to_int(_slice(line, 110, 117)),
                votantes_avance_2=_to_int(_slice(line, 118, 125)),
                votos_blanco=_to_int(_slice(line, 126, 133)),
                votos_nulos=_to_int(_slice(line, 134, 141)),
                votos_candidaturas=_to_int(_slice(line, 142, 149)),
                escanos=_to_int(_slice(line, 150, 155)),
                votos_afirmativos=_to_int(_slice(line, 156, 163)),
                votos_negativos=_to_int(_slice(line, 164, 171)),
                datos_oficiales=_to_bool(_slice(line, 172, 172)),
            )
        )
    return records


def parse_resultados_ambito_candidatura(
    path: Path,
) -> List[ResultadoAmbitoCandidaturaRecord]:
    """
    Parsea el fichero 0802aamm.dat con resultados por candidatura en ámbito superior.
    """
    records: list[ResultadoAmbitoCandidaturaRecord] = []
    for line in _read_lines(path):
        records.append(
            ResultadoAmbitoCandidaturaRecord(
                tipo_eleccion=_slice(line, 1, 2),
                anio=_slice(line, 3, 6),
                mes=_slice(line, 7, 8),
                vuelta=_slice(line, 9, 9),
                cod_ccaa=_slice(line, 10, 11).strip(),
                cod_provincia=_slice(line, 12, 13).strip(),
                cod_distrito=_slice(line, 14, 14).strip(),
                cod_candidatura=_slice(line, 15, 20).strip(),
                votos=_to_int(_slice(line, 21, 28)),
                candidatos=_to_int(_slice(line, 29, 33)),
            )
        )
    return records


def parse_mesas(path: Path) -> List[MesaRecord]:
    """
    Parsea el fichero 0902aamm.dat con datos comunes de mesas.
    Solo usa los códigos de identificación de mesa.
    """
    records: list[MesaRecord] = []
    for line in _read_lines(path):
        records.append(
            MesaRecord(
                cod_provincia=_slice(line, 12, 13).strip(),
                cod_municipio=_slice(line, 14, 16).strip(),
                cod_distrito=_slice(line, 17, 18).strip(),
                cod_seccion=_slice(line, 19, 22).strip(),
                cod_mesa=_slice(line, 23, 23).strip(),
            )
        )
    return records


def parse_mesas_candidaturas(path: Path) -> List[MesaVotoRecord]:
    """
    Parsea el fichero 1002aamm.dat con votos por candidatura en cada mesa.
    """
    records: list[MesaVotoRecord] = []
    for line in _read_lines(path):
        votos = _to_int(_slice(line, 30, 36)) or 0
        records.append(
            MesaVotoRecord(
                cod_provincia=_slice(line, 12, 13).strip(),
                cod_municipio=_slice(line, 14, 16).strip(),
                cod_distrito=_slice(line, 17, 18).strip(),
                cod_seccion=_slice(line, 19, 22).strip(),
                cod_mesa=_slice(line, 23, 23).strip(),
                cod_candidatura=_slice(line, 24, 29).strip(),
                votos=votos,
            )
        )
    return records


def parse_datos_municipios(path: Path) -> List[dict[str, str]]:
    """
    Parsea el fichero 0502aamm.dat (datos de municipios).
    Devuelve lista de dicts con keys: cod_provincia, cod_municipio, nombre.
    """
    records: list[dict[str, str]] = []
    for line in _read_lines(path):
        # Basado en análisis debug:
        # prov: 12-13 (1-based)
        # muni: 14-16 (1-based)
        # nombre: 19-end (approx)
        rec = {
            "cod_provincia": _slice(line, 12, 13).strip(),
            "cod_municipio": _slice(line, 14, 16).strip(),
            "nombre": _slice(line, 19, 118).strip(),  # Tomamos ancho generoso
        }
        records.append(rec)
    return records
