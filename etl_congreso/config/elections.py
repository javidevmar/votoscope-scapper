from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict

from .constants import TIPO_ELECCION_CONGRESO
from ..domain.models import ElectionConfig, ElectionFiles


BASE_RAW_DIR = Path(__file__).resolve().parent.parent.parent / "RAW" / "Congreso"


def _dat_path(folder: str, aa: str, mm: str, prefix: str) -> Path:
    filename = f"{prefix}{TIPO_ELECCION_CONGRESO}{aa}{mm}.DAT"
    return BASE_RAW_DIR / folder / filename


def _build_config(
    identifier: str,
    fecha: date,
    aa: str,
    mm: str,
    descripcion: str,
) -> ElectionConfig:
    folder = f"{TIPO_ELECCION_CONGRESO}{fecha.year}{mm}_MESA"
    files = ElectionFiles(
        candidaturas=_dat_path(folder, aa, mm, "03"),
        candidatos=_dat_path(folder, aa, mm, "04"),
        ambitos_superiores=_dat_path(folder, aa, mm, "07"),
        resultados_ambito_candidatura=_dat_path(folder, aa, mm, "08"),
        datos_municipios=_dat_path(folder, aa, mm, "05"),
        datos_municipios_candidaturas=_dat_path(folder, aa, mm, "06"),
        datos_mesas=_dat_path(folder, aa, mm, "09"),
        datos_mesas_candidaturas=_dat_path(folder, aa, mm, "10"),
    )
    return ElectionConfig(
        identifier=identifier,
        fecha=fecha,
        descripcion=descripcion,
        tipo_eleccion=TIPO_ELECCION_CONGRESO,
        aa=aa,
        mm=mm,
        vuelta=1,
        files=files,
    )


ELECTIONS: Dict[str, ElectionConfig] = {
    "congreso_2016_06": _build_config(
        identifier="congreso_2016_06",
        fecha=date(2016, 6, 26),
        aa="16",
        mm="06",
        descripcion="Elecciones Generales Congreso junio 2016",
    ),
    "congreso_2019_04": _build_config(
        identifier="congreso_2019_04",
        fecha=date(2019, 4, 28),
        aa="19",
        mm="04",
        descripcion="Elecciones Generales Congreso abril 2019",
    ),
    "congreso_2019_11": _build_config(
        identifier="congreso_2019_11",
        fecha=date(2019, 11, 10),
        aa="19",
        mm="11",
        descripcion="Elecciones Generales Congreso noviembre 2019",
    ),
    "congreso_2023_07": _build_config(
        identifier="congreso_2023_07",
        fecha=date(2023, 7, 23),
        aa="23",
        mm="07",
        descripcion="Elecciones Generales Congreso julio 2023",
    ),
}


def get_election_config(identifier: str) -> ElectionConfig:
    """
    Obtiene la configuración de una elección soportada.
    """
    try:
        return ELECTIONS[identifier]
    except KeyError as exc:
        raise KeyError(f"Elección no soportada: {identifier}") from exc


def available_elections() -> list[str]:
    return sorted(ELECTIONS)
