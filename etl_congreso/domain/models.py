from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class ElectionFiles:
    candidaturas: Path
    candidatos: Path
    ambitos_superiores: Path
    resultados_ambito_candidatura: Path
    datos_municipios: Path
    datos_municipios_candidaturas: Path
    datos_mesas: Path
    datos_mesas_candidaturas: Path


@dataclass(slots=True)
class ElectionConfig:
    identifier: str
    fecha: date
    descripcion: str
    tipo_eleccion: str
    aa: str
    mm: str
    vuelta: int
    files: ElectionFiles


@dataclass(slots=True)
class CandidaturaRecord:
    tipo_eleccion: str
    anio: str
    mes: str
    codigo: str
    siglas: str
    denominacion: str
    cabecera_provincial: str
    cabecera_autonomica: str
    cabecera_nacional: str


@dataclass(slots=True)
class CandidatoRecord:
    tipo_eleccion: str
    anio: str
    mes: str
    vuelta: str
    cod_provincia: str
    cod_distrito: str
    cod_municipio: str
    cod_candidatura: str
    orden: int
    tipo_candidato: str
    nombre: str
    primer_apellido: str
    segundo_apellido: str
    sexo: str
    fecha_nacimiento: Optional[date]
    dni: str
    elegido: bool


@dataclass(slots=True)
class AmbitoSuperiorRecord:
    tipo_eleccion: str
    anio: str
    mes: str
    vuelta: str
    cod_ccaa: str
    cod_provincia: str
    cod_distrito: str
    nombre_ambito: str
    poblacion_derecho: Optional[int]
    num_mesas: Optional[int]
    censo_ine: Optional[int]
    censo_escrutinio: Optional[int]
    censo_cere: Optional[int]
    total_votantes_cere: Optional[int]
    votantes_avance_1: Optional[int]
    votantes_avance_2: Optional[int]
    votos_blanco: Optional[int]
    votos_nulos: Optional[int]
    votos_candidaturas: Optional[int]
    escanos: Optional[int]
    votos_afirmativos: Optional[int]
    votos_negativos: Optional[int]
    datos_oficiales: bool


@dataclass(slots=True)
class ResultadoAmbitoCandidaturaRecord:
    tipo_eleccion: str
    anio: str
    mes: str
    vuelta: str
    cod_ccaa: str
    cod_provincia: str
    cod_distrito: str
    cod_candidatura: str
    votos: Optional[int]
    candidatos: Optional[int]


@dataclass(slots=True)
class SilverElectionRow:
    tipo_eleccion: str
    fecha: date
    descripcion: str
    aa: str
    mm: str
    vuelta: int


@dataclass(slots=True)
class SilverCandidaturaRow:
    codigo: str
    siglas: str
    nombre_largo: str
    cabecera_provincial: str
    cabecera_autonomica: str
    cabecera_nacional: str


@dataclass(slots=True)
class SilverCandidatoRow:
    cod_candidatura: str
    provincia_ine: str
    distrito_electoral: str
    orden_lista: int
    tipo_candidato: str
    nombre: str
    primer_apellido: str
    segundo_apellido: str
    sexo: str
    fecha_nacimiento: Optional[date]
    dni: str
    elegido: bool


@dataclass(slots=True)
class SilverAmbitoRow:
    vuelta: int
    cod_ccaa: str
    cod_provincia: str
    cod_distrito: str
    nombre_ambito: str
    poblacion_derecho: Optional[int]
    num_mesas: Optional[int]
    censo_ine: Optional[int]
    censo_escrutinio: Optional[int]
    censo_cere: Optional[int]
    total_votantes_cere: Optional[int]
    votantes_avance_1: Optional[int]
    votantes_avance_2: Optional[int]
    votos_blanco: Optional[int]
    votos_nulos: Optional[int]
    votos_candidaturas: Optional[int]
    escanos: Optional[int]
    votos_afirmativos: Optional[int]
    votos_negativos: Optional[int]
    datos_oficiales: bool


@dataclass(slots=True)
class SilverResultadoRow:
    vuelta: int
    cod_ccaa: str
    cod_provincia: str
    cod_distrito: str
    cod_candidatura: str
    votos: Optional[int]
    candidatos: Optional[int]


@dataclass(slots=True)
class GoldHemicicloRow:
    nivel_ambito: str  # nacional | provincia
    cod_provincia: Optional[str]
    nombre_ambito: str
    cod_candidatura: str
    votos: int
    escanos: int
    porcentaje_voto: Optional[float]


@dataclass(slots=True)
class SilverBundle:
    election: SilverElectionRow
    candidaturas: list[SilverCandidaturaRow]
    candidatos: list[SilverCandidatoRow]
    ambitos: list[SilverAmbitoRow]
    resultados: list[SilverResultadoRow]


@dataclass(slots=True)
class ProvinceInput:
    ine_code: str
    auto_code: str
    name: str


@dataclass(slots=True)
class MunicipioInput:
    prov_code: str
    muni_code: str
    auto_code: str
    name: str


@dataclass(slots=True)
class GeographyData:
    autonomias: dict[str, str]
    provinces: list[ProvinceInput]
    municipios: list[MunicipioInput]


@dataclass(slots=True)
class MesaRecord:
    cod_provincia: str
    cod_municipio: str
    cod_distrito: str
    cod_seccion: str
    cod_mesa: str


@dataclass(slots=True)
class MesaVotoRecord:
    cod_provincia: str
    cod_municipio: str
    cod_distrito: str
    cod_seccion: str
    cod_mesa: str
    cod_candidatura: str
    votos: int
