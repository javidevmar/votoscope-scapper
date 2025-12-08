from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd

from .constants import TIPO_ELECCION_CONGRESO
from .models import (
    AmbitoSuperiorRecord,
    GeographyData,
    MunicipioInput,
    ProvinceInput,
)

# Mapeo de códigos oficiales de comunidad autónoma (InfoElectoral/INE) a los códigos existentes en BD con nombre oficial
OFFICIAL_TO_DB_AUTONOMY = {
    "01": ("01", "Andalucía"),
    "02": ("02", "Aragón"),
    "03": ("03", "Principado de Asturias"),
    "04": ("04", "Islas Baleares"),
    "05": ("05", "Canarias"),
    "06": ("06", "Cantabria"),
    "07": ("07", "Castilla y León"),
    "08": ("08", "Castilla-La Mancha"),
    "09": ("09", "Cataluña"),
    "10": ("10", "Comunidad Valenciana"),
    "11": ("11", "Extremadura"),
    "12": ("12", "Galicia"),
    "13": ("14", "Comunidad de Madrid"),
    "14": ("15", "Región de Murcia"),
    "15": ("16", "Comunidad Foral de Navarra"),
    "16": ("17", "País Vasco"),
    "17": ("13", "La Rioja"),
    "18": ("51", "Ceuta"),
    "19": ("52", "Melilla"),
}


def _translate_auto_code(official_code: str) -> str:
    return OFFICIAL_TO_DB_AUTONOMY.get(official_code, (official_code, ""))[0]


def load_diccionario25(path: Path) -> Tuple[List[MunicipioInput], Dict[str, str]]:
    """
    Lee diccionario25.xlsx para obtener cod_auto oficial, provincia, municipio y nombre.
    Devuelve lista de municipios y un mapping prov->auto_code(BD).
    """
    df_raw = pd.read_excel(path, sheet_name="dic25", header=None)
    header = df_raw.iloc[1]
    data = df_raw.iloc[2:]
    data.columns = header
    municipios: list[MunicipioInput] = []
    prov_to_auto: dict[str, str] = {}
    for _, row in data.iterrows():
        try:
            prov = str(int(row["CPRO"])).zfill(2)
            mun = str(int(row["CMUN"])).zfill(3)
            auto_official = str(int(row["CODAUTO"])).zfill(2)
        except (ValueError, TypeError):
            continue
        auto_db = _translate_auto_code(auto_official)
        prov_to_auto.setdefault(prov, auto_db)
        nombre = str(row["NOMBRE"]).strip()
        municipios.append(
            MunicipioInput(
                prov_code=prov,
                muni_code=mun,
                auto_code=auto_db,
                name=nombre,
            )
        )
    return municipios, prov_to_auto


def load_codislas(path: Path, prov_to_auto: Dict[str, str]) -> Tuple[List[MunicipioInput], Dict[str, str]]:
    """
    Lee 25codislas.xlsx (hojas 07/35/38) para completar municipios en islas y nombres de provincia.
    Devuelve lista de municipios (pueden sobrescribir) y nombres de provincia.
    """
    municipios: list[MunicipioInput] = []
    province_names: dict[str, str] = {}
    for sheet in ("07", "35", "38"):
        df_raw = pd.read_excel(path, sheet_name=sheet, header=None)
        # Fila 1: nombre de la provincia en el idioma oficial
        province_label = str(df_raw.iloc[1, 0]).strip()
        header = df_raw.iloc[2]
        data = df_raw.iloc[3:]
        data.columns = header
        for _, row in data.iterrows():
            try:
                prov = str(int(row["CPRO"])).zfill(2)
                mun = str(int(row["CMUN"])).zfill(3)
            except (ValueError, TypeError, KeyError):
                continue
            auto_code = prov_to_auto.get(prov)
            if not auto_code:
                continue
            nombre = str(row["NOMBRE"]).strip()
            municipios.append(
                MunicipioInput(
                    prov_code=prov,
                    muni_code=mun,
                    auto_code=auto_code,
                    name=nombre,
                )
            )
            # Guardar nombre de provincia para alias si no existe
            if prov not in province_names:
                province_names[prov] = province_label
    return municipios, province_names


def build_provinces_from_ambitos(
    ambitos: Iterable[AmbitoSuperiorRecord],
    prov_to_auto: Dict[str, str],
    province_names_extra: Dict[str, str],
) -> List[ProvinceInput]:
    provinces: dict[str, ProvinceInput] = {}
    for ambito in ambitos:
        if ambito.tipo_eleccion != TIPO_ELECCION_CONGRESO:
            continue
        if ambito.cod_provincia == "99" or ambito.cod_distrito != "9":
            continue
        prov = ambito.cod_provincia
        auto = prov_to_auto.get(prov)
        if not auto:
            continue
        if prov in province_names_extra:
            name = province_names_extra[prov]
        else:
            name = ambito.nombre_ambito
        provinces[prov] = ProvinceInput(
            ine_code=prov,
            auto_code=auto,
            name=name,
        )
    # Provincias de islas que quizá no aparezcan en 0702
    for prov, names in province_names_extra.items():
        if prov in provinces:
            continue
        auto = prov_to_auto.get(prov)
        if not auto:
            continue
        provinces[prov] = ProvinceInput(ine_code=prov, auto_code=auto, name=names)
    return list(provinces.values())


def collect_geography_data(
    diccionario_path: Path,
    codislas_path: Path,
    ambitos: Iterable[AmbitoSuperiorRecord],
) -> GeographyData:
    municipios_base, prov_to_auto = load_diccionario25(diccionario_path)
    municipios_islas, province_names_extra = load_codislas(codislas_path, prov_to_auto)

    municipios_map: dict[tuple[str, str], MunicipioInput] = {}
    for muni in municipios_base + municipios_islas:
        municipios_map[(muni.prov_code, muni.muni_code)] = muni

    provincias = build_provinces_from_ambitos(ambitos, prov_to_auto, province_names_extra)
    autonomias = {v[0]: v[1] for v in OFFICIAL_TO_DB_AUTONOMY.values()}
    return GeographyData(
        autonomias=autonomias,
        provinces=list(provincias),
        municipios=list(municipios_map.values()),
    )
