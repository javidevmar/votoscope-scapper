from __future__ import annotations

from datetime import date
from typing import Iterable, List, Tuple

from ...domain.models import (
    AmbitoSuperiorRecord,
    CandidatoRecord,
    CandidaturaRecord,
    MesaRecord,
    MesaVotoRecord,
    ResultadoAmbitoCandidaturaRecord,
    SilverAmbitoRow,
    SilverBundle,
    SilverCandidatoRow,
    SilverCandidaturaRow,
    SilverElectionRow,
    SilverResultadoRow,
)
from ...config.constants import CODIGO_TOTAL

def build_silver_bundle(
    descripcion: str,
    tipo_eleccion: str,
    fecha: date,
    aa: str,
    mm: str,
    vuelta: int,
    candidaturas: Iterable[CandidaturaRecord],
    candidatos: Iterable[CandidatoRecord],
    ambitos: Iterable[AmbitoSuperiorRecord],
    resultados: Iterable[ResultadoAmbitoCandidaturaRecord],
) -> SilverBundle:
    """
    Converts parsed records into Silver load ready entities.
    """
    election = SilverElectionRow(
        tipo_eleccion=tipo_eleccion,
        fecha=fecha,
        descripcion=descripcion,
        aa=aa,
        mm=mm,
        vuelta=vuelta,
    )
    candidaturas_silver = [
        SilverCandidaturaRow(
            codigo=item.codigo,
            siglas=item.siglas,
            nombre_largo=item.denominacion,
            cabecera_provincial=item.cabecera_provincial,
            cabecera_autonomica=item.cabecera_autonomica,
            cabecera_nacional=item.cabecera_nacional,
        )
        for item in candidaturas
    ]
    candidatos_silver = [
        SilverCandidatoRow(
            cod_candidatura=item.cod_candidatura,
            provincia_ine=item.cod_provincia,
            distrito_electoral=item.cod_distrito,
            orden_lista=item.orden,
            tipo_candidato=item.tipo_candidato,
            nombre=item.nombre,
            primer_apellido=item.primer_apellido,
            segundo_apellido=item.segundo_apellido,
            sexo=item.sexo,
            fecha_nacimiento=item.fecha_nacimiento,
            dni=item.dni,
            elegido=item.elegido,
        )
        for item in candidatos
    ]
    ambitos_silver = [
        SilverAmbitoRow(
            vuelta=int(item.vuelta or 1),
            cod_ccaa=item.cod_ccaa,
            cod_provincia=item.cod_provincia,
            cod_distrito=item.cod_distrito,
            nombre_ambito=item.nombre_ambito,
            poblacion_derecho=item.poblacion_derecho,
            num_mesas=item.num_mesas,
            censo_ine=item.censo_ine,
            censo_escrutinio=item.censo_escrutinio,
            censo_cere=item.censo_cere,
            total_votantes_cere=item.total_votantes_cere,
            votantes_avance_1=item.votantes_avance_1,
            votantes_avance_2=item.votantes_avance_2,
            votos_blanco=item.votos_blanco,
            votos_nulos=item.votos_nulos,
            votos_candidaturas=item.votos_candidaturas,
            escanos=item.escanos,
            votos_afirmativos=item.votos_afirmativos,
            votos_negativos=item.votos_negativos,
            datos_oficiales=item.datos_oficiales,
        )
        for item in ambitos
    ]
    resultados_silver = [
        SilverResultadoRow(
            vuelta=int(item.vuelta or 1),
            cod_ccaa=item.cod_ccaa,
            cod_provincia=item.cod_provincia,
            cod_distrito=item.cod_distrito,
            cod_candidatura=item.cod_candidatura,
            votos=item.votos,
            candidatos=item.candidatos,
        )
        for item in resultados
    ]
    return SilverBundle(
        election=election,
        candidaturas=candidaturas_silver,
        candidatos=candidatos_silver,
        ambitos=ambitos_silver,
        resultados=resultados_silver,
    )


def build_mesas(
    mesas_raw: Iterable[MesaRecord],
) -> List[tuple[str, str, str, str, str]]:
    """
    Returns unique (prov, muni, distro, section, table) tuples for loading.
    """
    seen: set[tuple[str, str, str, str, str]] = set()
    mesas: list[tuple[str, str, str, str, str]] = []
    for mesa in mesas_raw:
        # Filter special totals (99) or municipalities 999 that do not represent physical tables
        if mesa.cod_provincia == CODIGO_TOTAL or mesa.cod_municipio in ("999", "000"):
            continue
        key = (mesa.cod_provincia, mesa.cod_municipio, mesa.cod_distrito, mesa.cod_seccion, mesa.cod_mesa)
        if key in seen:
            continue
        seen.add(key)
        mesas.append(key)
    return mesas


def build_votos_mesa(
    mesa_votos: Iterable[MesaVotoRecord],
) -> List[tuple[str, str, str, str, str, str, int]]:
    """
    Returns (prov, muni, distro, section, table, candidacy_code, votes) tuples.
    """
    votos_list: list[tuple[str, str, str, str, str, str, int]] = []
    for voto in mesa_votos:
        if voto.cod_provincia == CODIGO_TOTAL or voto.cod_municipio in ("999", "000"):
            continue
        votos_list.append(
            (
                voto.cod_provincia,
                voto.cod_municipio,
                voto.cod_distrito,
                voto.cod_seccion,
                voto.cod_mesa,
                voto.cod_candidatura,
                voto.votos,
            )
        )
    return votos_list
