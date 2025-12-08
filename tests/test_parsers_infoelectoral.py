from __future__ import annotations

from pathlib import Path

from etl_congreso.parsers_infoelectoral import (
    parse_ambitos_superiores,
    parse_candidatos,
    parse_candidaturas,
    parse_resultados_ambito_candidatura,
)


def _blank_line(length: int = 232) -> list[str]:
    return [" "] * length


def _put(line: list[str], start: int, end: int, value: str, align: str = "left") -> None:
    span = end - start + 1
    if align == "right":
        text = value.rjust(span, "0")
    else:
        text = value.ljust(span)
    line[start - 1 : end] = list(text[:span])


def _write_line(tmp_path: Path, filename: str, line: str) -> Path:
    path = tmp_path / filename
    path.write_text(line, encoding="cp1252")
    return path


def test_parse_candidaturas(tmp_path: Path) -> None:
    line = _blank_line()
    _put(line, 1, 2, "02")
    _put(line, 3, 6, "2019", align="right")
    _put(line, 7, 8, "11", align="right")
    _put(line, 9, 14, "000123", align="right")
    _put(line, 15, 64, "ABC")
    _put(line, 65, 214, "Alianza Buen Cambio")
    _put(line, 215, 220, "000001", align="right")
    _put(line, 221, 226, "000002", align="right")
    _put(line, 227, 232, "000003", align="right")
    path = _write_line(tmp_path, "03021911.DAT", "".join(line))

    records = parse_candidaturas(path)
    assert len(records) == 1
    record = records[0]
    assert record.codigo == "000123"
    assert record.siglas == "ABC"
    assert record.denominacion == "Alianza Buen Cambio"
    assert record.cabecera_nacional == "000003"


def test_parse_candidatos(tmp_path: Path) -> None:
    line = _blank_line()
    _put(line, 1, 2, "02")
    _put(line, 3, 6, "2023", align="right")
    _put(line, 7, 8, "07", align="right")
    _put(line, 9, 9, "1")
    _put(line, 10, 11, "28")
    _put(line, 12, 12, "9")
    _put(line, 13, 15, "999", align="right")
    _put(line, 16, 21, "000010", align="right")
    _put(line, 22, 24, "001", align="right")
    _put(line, 25, 25, "T")
    _put(line, 26, 50, "Maria")
    _put(line, 51, 75, "Lopez")
    _put(line, 76, 100, "Garcia")
    _put(line, 101, 101, "F")
    _put(line, 102, 103, "01", align="right")
    _put(line, 104, 105, "02", align="right")
    _put(line, 106, 109, "1980", align="right")
    _put(line, 110, 119, "12345678X")
    _put(line, 120, 120, "S")
    path = _write_line(tmp_path, "04022307.DAT", "".join(line))

    records = parse_candidatos(path)
    assert len(records) == 1
    record = records[0]
    assert record.elegido is True
    assert record.fecha_nacimiento.year == 1980
    assert record.orden == 1


def test_parse_ambitos_y_resultados(tmp_path: Path) -> None:
    amb_line = _blank_line()
    _put(amb_line, 1, 2, "02")
    _put(amb_line, 3, 6, "2023", align="right")
    _put(amb_line, 7, 8, "07", align="right")
    _put(amb_line, 9, 9, "1")
    _put(amb_line, 10, 11, "99")
    _put(amb_line, 12, 13, "99")
    _put(amb_line, 14, 14, "9")
    _put(amb_line, 15, 64, "Total Nacional")
    _put(amb_line, 65, 72, "00001000", align="right")
    _put(amb_line, 126, 133, "00000050", align="right")
    _put(amb_line, 134, 141, "00000010", align="right")
    _put(amb_line, 142, 149, "00000200", align="right")
    _put(amb_line, 150, 155, "000350", align="right")
    _put(amb_line, 172, 172, "S")
    amb_path = _write_line(tmp_path, "07022307.DAT", "".join(amb_line))

    res_line = _blank_line(33)
    _put(res_line, 1, 2, "02")
    _put(res_line, 3, 6, "2023", align="right")
    _put(res_line, 7, 8, "07", align="right")
    _put(res_line, 9, 9, "1")
    _put(res_line, 10, 11, "99")
    _put(res_line, 12, 13, "99")
    _put(res_line, 14, 14, "9")
    _put(res_line, 15, 20, "000010", align="right")
    _put(res_line, 21, 28, "00001234", align="right")
    _put(res_line, 29, 33, "00012", align="right")
    res_path = _write_line(tmp_path, "08022307.DAT", "".join(res_line))

    ambitos = parse_ambitos_superiores(amb_path)
    resultados = parse_resultados_ambito_candidatura(res_path)

    assert ambitos[0].datos_oficiales is True
    assert ambitos[0].escanos == 350
    assert resultados[0].votos == 1234
    assert resultados[0].candidatos == 12

