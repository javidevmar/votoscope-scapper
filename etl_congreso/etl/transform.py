from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Tuple

from ..config.constants import CODIGO_TOTAL
from ..domain.models import (
    AmbitoSuperiorRecord,
    CandidatoRecord,
    CandidaturaRecord,
    MesaRecord,
    MesaVotoRecord,
    GoldHemicicloRow,
    ResultadoAmbitoCandidaturaRecord,
    SilverAmbitoRow,
    SilverBundle,
    SilverCandidatoRow,
    SilverCandidaturaRow,
    SilverElectionRow,
    SilverResultadoRow,
)


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
    Convierte los registros parseados en entidades listas para la carga Silver.
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


def _ambito_key(row: SilverAmbitoRow) -> Tuple[int, str, str, str]:
    return row.vuelta, row.cod_ccaa, row.cod_provincia, row.cod_distrito


def build_gold_hemiciclo_rows(
    ambitos: Iterable[SilverAmbitoRow],
    resultados: Iterable[SilverResultadoRow],
    candidaturas: Iterable[SilverCandidaturaRow],
) -> List[GoldHemicicloRow]:
    """
    Genera los registros de la tabla gold de hemiciclo (nacional y provincial).
    """
    ambito_map: Dict[tuple[int, str, str, str], SilverAmbitoRow] = {
        _ambito_key(amb): amb for amb in ambitos
    }
    candidatura_map: Dict[str, SilverCandidaturaRow] = {
        c.codigo: c for c in candidaturas
    }
    rows: list[GoldHemicicloRow] = []

    resultados_por_clave: Dict[tuple[int, str, str, str], list[SilverResultadoRow]] = {}
    for res in resultados:
        key = (res.vuelta, res.cod_ccaa, res.cod_provincia, res.cod_distrito)
        resultados_por_clave.setdefault(key, []).append(res)

    # Hemiciclo nacional
    nacional_key = (1, CODIGO_TOTAL, CODIGO_TOTAL, "9")
    if nacional_key in ambito_map:
        ambito_nacional = ambito_map[nacional_key]
        total_votos_validos = ambito_nacional.votos_candidaturas or 0
        for res in resultados_por_clave.get(nacional_key, []):
            candidatura = candidatura_map.get(res.cod_candidatura)
            if not candidatura:
                continue
            votos = res.votos or 0
            escanos = res.candidatos or 0
            porcentaje = (
                votos / total_votos_validos if total_votos_validos and votos is not None else None
            )
            rows.append(
                GoldHemicicloRow(
                    nivel_ambito="nacional",
                    cod_provincia=None,
                    nombre_ambito=ambito_nacional.nombre_ambito,
                    cod_candidatura=res.cod_candidatura,
                    votos=votos,
                    escanos=escanos,
                    porcentaje_voto=porcentaje,
                )
            )

    # Hemiciclo provincial (totales de provincia cod_distrito=9)
    for ambito in ambito_map.values():
        if ambito.cod_provincia == CODIGO_TOTAL or ambito.cod_distrito != "9":
            continue
        total_votos_validos = ambito.votos_candidaturas or 0
        key = _ambito_key(ambito)
        for res in resultados_por_clave.get(key, []):
            candidatura = candidatura_map.get(res.cod_candidatura)
            if not candidatura:
                continue
            votos = res.votos or 0
            escanos = res.candidatos or 0
            porcentaje = (
                votos / total_votos_validos if total_votos_validos and votos is not None else None
            )
            rows.append(
                GoldHemicicloRow(
                    nivel_ambito="provincia",
                    cod_provincia=ambito.cod_provincia,
                    nombre_ambito=ambito.nombre_ambito,
                    cod_candidatura=res.cod_candidatura,
                    votos=votos,
                    escanos=escanos,
                    porcentaje_voto=porcentaje,
                )
            )

    return rows


def build_mesas(
    mesas_raw: Iterable[MesaRecord],
) -> List[tuple[str, str, str, str, str]]:
    """
    Devuelve tuplas (prov, muni, distrito, seccion, mesa) únicas para carga.
    """
    seen: set[tuple[str, str, str, str, str]] = set()
    mesas: list[tuple[str, str, str, str, str]] = []
    for mesa in mesas_raw:
        # Filtrar totales especiales (99) o municipios 999 que no representan mesas físicas
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
    Devuelve tuplas (prov, muni, distrito, seccion, mesa, cod_candidatura, votos).
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
