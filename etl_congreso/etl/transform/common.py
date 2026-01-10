from __future__ import annotations
from typing import Tuple

from ...domain.models import SilverAmbitoRow

def _ambito_key(row: SilverAmbitoRow) -> Tuple[int, str, str, str]:
    return row.vuelta, row.cod_ccaa, row.cod_provincia, row.cod_distrito
