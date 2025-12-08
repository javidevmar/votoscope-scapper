from __future__ import annotations

from datetime import date

from etl_congreso.models import (
    AmbitoSuperiorRecord,
    CandidatoRecord,
    CandidaturaRecord,
    ResultadoAmbitoCandidaturaRecord,
    SilverAmbitoRow,
    SilverResultadoRow,
)
from etl_congreso.transformers_congreso import (
    build_gold_hemiciclo_rows,
    build_silver_bundle,
)


def test_build_silver_bundle_counts() -> None:
    candidaturas = [
        CandidaturaRecord(
            tipo_eleccion="02",
            anio="2023",
            mes="07",
            codigo="000001",
            siglas="ABC",
            denominacion="Alianza Buen Cambio",
            cabecera_provincial="",
            cabecera_autonomica="",
            cabecera_nacional="",
        )
    ]
    candidatos = [
        CandidatoRecord(
            tipo_eleccion="02",
            anio="2023",
            mes="07",
            vuelta="1",
            cod_provincia="28",
            cod_distrito="9",
            cod_municipio="999",
            cod_candidatura="000001",
            orden=1,
            tipo_candidato="T",
            nombre="Maria",
            primer_apellido="Lopez",
            segundo_apellido="Garcia",
            sexo="F",
            fecha_nacimiento=date(1980, 2, 1),
            dni="12345678X",
            elegido=True,
        )
    ]
    ambitos = [
        AmbitoSuperiorRecord(
            tipo_eleccion="02",
            anio="2023",
            mes="07",
            vuelta="1",
            cod_ccaa="99",
            cod_provincia="99",
            cod_distrito="9",
            nombre_ambito="Total Nacional",
            poblacion_derecho=1000,
            num_mesas=10,
            censo_ine=900,
            censo_escrutinio=900,
            censo_cere=0,
            total_votantes_cere=0,
            votantes_avance_1=0,
            votantes_avance_2=0,
            votos_blanco=0,
            votos_nulos=0,
            votos_candidaturas=800,
            escanos=350,
            votos_afirmativos=0,
            votos_negativos=0,
            datos_oficiales=True,
        )
    ]
    resultados = [
        ResultadoAmbitoCandidaturaRecord(
            tipo_eleccion="02",
            anio="2023",
            mes="07",
            vuelta="1",
            cod_ccaa="99",
            cod_provincia="99",
            cod_distrito="9",
            cod_candidatura="000001",
            votos=500,
            candidatos=200,
        )
    ]

    bundle = build_silver_bundle(
        descripcion="Elecciones de prueba",
        tipo_eleccion="02",
        fecha=date(2023, 7, 23),
        aa="23",
        mm="07",
        vuelta=1,
        candidaturas=candidaturas,
        candidatos=candidatos,
        ambitos=ambitos,
        resultados=resultados,
    )

    assert bundle.election.tipo_eleccion == "02"
    assert len(bundle.candidaturas) == 1
    assert len(bundle.candidatos) == 1
    assert len(bundle.ambitos) == 1
    assert len(bundle.resultados) == 1
    assert bundle.ambitos[0].escanos == 350


def test_build_gold_hemiciclo_rows() -> None:
    ambitos = [
        SilverAmbitoRow(
            vuelta=1,
            cod_ccaa="99",
            cod_provincia="99",
            cod_distrito="9",
            nombre_ambito="Total Nacional",
            poblacion_derecho=0,
            num_mesas=0,
            censo_ine=0,
            censo_escrutinio=0,
            censo_cere=0,
            total_votantes_cere=0,
            votantes_avance_1=0,
            votantes_avance_2=0,
            votos_blanco=0,
            votos_nulos=0,
            votos_candidaturas=1000,
            escanos=0,
            votos_afirmativos=0,
            votos_negativos=0,
            datos_oficiales=True,
        ),
        SilverAmbitoRow(
            vuelta=1,
            cod_ccaa="01",
            cod_provincia="01",
            cod_distrito="9",
            nombre_ambito="Araba",
            poblacion_derecho=0,
            num_mesas=0,
            censo_ine=0,
            censo_escrutinio=0,
            censo_cere=0,
            total_votantes_cere=0,
            votantes_avance_1=0,
            votantes_avance_2=0,
            votos_blanco=0,
            votos_nulos=0,
            votos_candidaturas=400,
            escanos=0,
            votos_afirmativos=0,
            votos_negativos=0,
            datos_oficiales=True,
        ),
    ]
    resultados = [
        SilverResultadoRow(
            vuelta=1,
            cod_ccaa="99",
            cod_provincia="99",
            cod_distrito="9",
            cod_candidatura="000001",
            votos=600,
            candidatos=200,
        ),
        SilverResultadoRow(
            vuelta=1,
            cod_ccaa="99",
            cod_provincia="99",
            cod_distrito="9",
            cod_candidatura="000002",
            votos=400,
            candidatos=150,
        ),
        SilverResultadoRow(
            vuelta=1,
            cod_ccaa="01",
            cod_provincia="01",
            cod_distrito="9",
            cod_candidatura="000001",
            votos=250,
            candidatos=2,
        ),
        SilverResultadoRow(
            vuelta=1,
            cod_ccaa="01",
            cod_provincia="01",
            cod_distrito="9",
            cod_candidatura="000002",
            votos=150,
            candidatos=1,
        ),
    ]
    candidaturas = [
        CandidaturaRecord(
            tipo_eleccion="02",
            anio="2023",
            mes="07",
            codigo="000001",
            siglas="ABC",
            denominacion="",
            cabecera_provincial="",
            cabecera_autonomica="",
            cabecera_nacional="",
        ),
        CandidaturaRecord(
            tipo_eleccion="02",
            anio="2023",
            mes="07",
            codigo="000002",
            siglas="XYZ",
            denominacion="",
            cabecera_provincial="",
            cabecera_autonomica="",
            cabecera_nacional="",
        ),
    ]

    bundle = build_silver_bundle(
        descripcion="",
        tipo_eleccion="02",
        fecha=date(2023, 7, 23),
        aa="23",
        mm="07",
        vuelta=1,
        candidaturas=candidaturas,
        candidatos=[],
        ambitos=[],
        resultados=[],
    )
    gold_rows = build_gold_hemiciclo_rows(
        ambitos=ambitos,
        resultados=resultados,
        candidaturas=bundle.candidaturas,
    )

    assert len(gold_rows) == 4
    nacional = [row for row in gold_rows if row.nivel_ambito == "nacional"]
    provincia = [row for row in gold_rows if row.nivel_ambito == "provincia"]
    assert len(nacional) == 2
    assert len(provincia) == 2
    abc_nacional = next(row for row in nacional if row.cod_candidatura == "000001")
    assert abs((abc_nacional.porcentaje_voto or 0) - 0.6) < 1e-6
    abc_prov = next(row for row in provincia if row.cod_candidatura == "000001")
    assert abs((abc_prov.porcentaje_voto or 0) - 0.625) < 1e-6
