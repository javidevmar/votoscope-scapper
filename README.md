# ETL Congreso (InfoElectoral)

Guía rápida y paso a paso para ejecutar la ETL de elecciones al Congreso incluida en `etl_congreso/`.

## 1. Qué hace
- Lee los ficheros InfoElectoral `.DAT` ya presentes en `RAW/Congreso/02<YYYY><MM>_MESA` (0302, 0402, 0702, 0802).
- Construye geografía real: carga provincias y municipios oficiales (más de 8k) desde `RAW/diccionario25.xlsx` y `RAW/25codislas.xlsx`, generando alias por idioma (es/ca/gl/eu) según la CCAA.
- Reconciliación de candidaturas -> partidos por siglas (crea partidos nuevos si no existen) y vincula cada partido con la elección.
- Crea la elección nacional si falta (`eleccion`, tipo `Generales`, ámbito estatal).
- Calcula hemiciclos nacional y provinciales y los inserta/actualiza en `gold_congreso_hemiciclo`.

## 2. Requisitos previos
- Python 3.11+ con `psycopg` instalado en el intérprete que uses (ej. `/opt/anaconda3/bin/python -m pip install "psycopg[binary]"`).
- Supabase local en marcha (`supabase db start`) y `SUPABASE_DB_URL` o `DATABASE_URL` apuntando al Postgres (por defecto `postgresql://postgres:postgres@127.0.0.1:54322/postgres`).
- Datos `.DAT` y diccionarios ya colocados en `1poller-scrapper/RAW`.

## 3. Ejecución paso a paso
1. Posiciónate en `1poller-scrapper`.
2. Asegura la variable de conexión, por ejemplo:
   ```bash
   export SUPABASE_DB_URL="postgresql://postgres:postgres@127.0.0.1:54322/postgres"
   ```
3. Lanza la ETL para cada elección soportada:
   ```bash
   python -m etl_congreso.run_congreso_etl --election congreso_2019_11
   python -m etl_congreso.run_congreso_etl --election congreso_2023_07
   ```
4. El proceso es idempotente: si vuelves a ejecutarlo, hace upsert de geografía, partidos y hemiciclo sin duplicar.

## 4. Qué ocurre internamente (resumen de etapas)
1) **Parsing** (`parsers_infoelectoral.py`): lee los `.DAT` de ancho fijo y produce registros de candidaturas, candidatos, ámbitos y resultados.
2) **Geografía** (`geography_sources.py`): fusiona `diccionario25.xlsx`, `25codislas.xlsx` y los nombres de 0702 para obtener provincias y municipios con alias multilingüe.
3) **Transformación** (`transformers_congreso.py`): prepara los datos para carga (cálculo de porcentajes de voto para hemiciclo).
4) **Carga** (`loaders_postgres.py`):
   - Crea/actualiza provincias y municipios + alias.
   - Crea/relaciona la elección y los partidos (por siglas).
   - Inserta/actualiza `gold_congreso_hemiciclo` con escaños y votos por ámbito.

## 5. Extender o depurar
- Añadir nuevas elecciones: declara la entrada en `etl_congreso/config.py` con `aa/mm`, fecha y rutas; coloca los `.DAT` en `RAW/Congreso/02<YYYY><MM>_MESA`.
- Si cambian campos en InfoElectoral, ajusta `parsers_infoelectoral.py`.
- Si aparecen nuevos idiomas o diccionarios, amplía la lógica de alias en `geography_sources.py`.
