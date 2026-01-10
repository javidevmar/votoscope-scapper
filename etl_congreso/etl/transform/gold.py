from __future__ import annotations

from typing import Dict, Iterable, List

from ...domain.models import (
    GoldHemicicloRow,
    SilverAmbitoRow,
    SilverCandidaturaRow,
    SilverResultadoRow,
)
from ...config.constants import CODIGO_TOTAL
from .common import _ambito_key


def build_gold_hemiciclo_rows(
    ambitos: Iterable[SilverAmbitoRow],
    resultados: Iterable[SilverResultadoRow],
    candidaturas: Iterable[SilverCandidaturaRow],
) -> List[GoldHemicicloRow]:
    """
    Generates gold hemiciclo table records (national and provincial).
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

    # 1. National hemicycle
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

    # 2. Provincial hemicycle (province totals cod_distrito=9)
    for ambito in ambito_map.values():
        if ambito.cod_provincia == CODIGO_TOTAL or ambito.cod_distrito != "9":
            continue
        
        total_votos_validos = ambito.votos_candidaturas or 0
        key = _ambito_key(ambito)
        
        results_prov = resultados_por_clave.get(key, [])
        for res in results_prov:
            candidatura = candidatura_map.get(res.cod_candidatura)
            if not candidatura:
                continue
            
            votos = res.votos or 0
            escanos = res.candidatos or 0
            
            porcentaje_prov = (
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
                    porcentaje_voto=porcentaje_prov,
                )
            )

    return rows
