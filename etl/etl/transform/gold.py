from __future__ import annotations

from typing import Dict, Iterable, List

from ...domain.models import (
    GoldHemicicloRow,
    SilverAmbitoRow,
    SilverCandidaturaRow,
    SilverResultadoRow,
)
from ...config.constants import CODIGO_TOTAL
from .common import ambito_key


def _process_scope_rows(
    ambito: SilverAmbitoRow,
    results: List[SilverResultadoRow],
    candidatura_map: Dict[str, SilverCandidaturaRow],
    nivel_ambito: str,
) -> Iterable[GoldHemicicloRow]:
    """
    Helper to generate Gold rows for a specific scope (National or Provincial).
    """
    total_valid_votes = ambito.votos_candidaturas or 0
    # Determine cod_provincia: for 'provincia' we use the one from ambito, else None (for 'nacional')
    target_cod_prov = ambito.cod_provincia if nivel_ambito == "provincia" else None
    target_cod_ccaa = ambito.cod_ccaa if nivel_ambito == "region" else None 

    for res in results:
        if res.cod_candidatura not in candidatura_map:
            continue

        votos = res.votos or 0
        porcentaje = (
            (votos / total_valid_votes) if total_valid_votes and votos else None
        )

        yield GoldHemicicloRow(
            nivel_ambito=nivel_ambito,
            cod_ccaa=target_cod_ccaa,
            cod_provincia=target_cod_prov,
            nombre_ambito=ambito.nombre_ambito,
            cod_candidatura=res.cod_candidatura,
            votos=votos,
            escanos=res.candidatos or 0,
            porcentaje_voto=porcentaje,
        )


def build_gold_hemiciclo_rows(
    ambitos: Iterable[SilverAmbitoRow],
    resultados: Iterable[SilverResultadoRow],
    candidaturas: Iterable[SilverCandidaturaRow],
) -> List[GoldHemicicloRow]:
    """
    Generates gold hemiciclo table records (national and provincial).
    """
    ambito_map = {ambito_key(amb): amb for amb in ambitos}
    candidatura_map = {c.codigo: c for c in candidaturas}
    
    # Pre-group results by key for fast access
    resultados_por_clave: Dict[tuple[int, str, str, str], list[SilverResultadoRow]] = {}
    for res in resultados:
        key = (res.vuelta, res.cod_ccaa, res.cod_provincia, res.cod_distrito)
        resultados_por_clave.setdefault(key, []).append(res)
    
    rows: list[GoldHemicicloRow] = []

    # 1. National hemicycle
    nacional_key = (1, CODIGO_TOTAL, CODIGO_TOTAL, "9")
    if nacional_key in ambito_map:
        rows.extend(
            _process_scope_rows(
                ambito=ambito_map[nacional_key],
                results=resultados_por_clave.get(nacional_key, []),
                candidatura_map=candidatura_map,
                nivel_ambito="nacional",
            )
        )
        ambito_map.pop(nacional_key)
    # 2. Provincial and regional aggregated results
    for ambito in ambito_map.values():
        if ambito.cod_distrito != "9":
            continue
            
        nivel_ambito = "region" if ambito.cod_provincia == CODIGO_TOTAL else "provincia"
        key = ambito_key(ambito)
        rows.extend(
            _process_scope_rows(
                ambito=ambito,
                results=resultados_por_clave.get(key, []),
                candidatura_map=candidatura_map,
                nivel_ambito=nivel_ambito,
            )
        )

    return rows
