# Documentación de Ficheros RAW (.DAT)

Este directorio contiene los datos electorales en bruto procedentes de InfoElectoral. Los ficheros siguen una nomenclatura específica `XXYYZZZZ.DAT` donde:

*   **XX**: Identificador del tipo de fichero (contenido).
*   **YY**: Tipo de elección (02 para Congreso).
*   **ZZZZ**: Año y mes (AAMM).

## Tipos de Ficheros (XX)

Estos son los códigos principales utilizados en la estructura de ficheros:

| Código | Descripción | Contenido Principal |
| :--- | :--- | :--- |
| **01** | **Control** | Fichero de control de ficheros adjuntos. |
| **02** | **Identificación** | Identificación del proceso electoral (fechas, horarios). |
| **03** | **Candidaturas** | Relación de partidos/coaliciones que se presentan. Incluye siglas, nombre completo y códigos. |
| **04** | **Candidatos** | Listas de personas físicas que componen las candidaturas (nombres, DNI, orden en la lista). |
| **05** | **Municipios** | Datos globales a nivel municipal (censo, participación, votos nulos/blancos totales por municipio). |
| **06** | **Resultados Municipios** | Votos por candidatura desagregados por municipio. |
| **07** | **Ámbitos Superiores** | Datos globales a nivel provincial y autonómico (agregados). |
| **08** | **Resultados Ámbitos** | Votos por candidatura desagregados por provincia/comunidad. |
| **09** | **Mesas (Datos Generales)** | La unidad mínima. Censo, participación, votos nulos y blancos por cada mesa electoral. |
| **10** | **Mesas (Candidaturas)** | Votos obtenidos por cada candidatura en cada mesa electoral específica. |

## Estructura detallada por Tipo de Fichero

A continuación se detalla la posición de cada campo extraído por el ETL actual (`etl/extract.py`).
*(Nota: Índices 1-based, inclusivos)*

### Fichero 01: Control
Indica qué ficheros acompañan a este envío.
**Ejemplo**: `0220160611111111111000000`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificación común | `022016061` |
| Adjunta 01 | 10 | 1 | Siempre 1 | `1` |
| Adjunta 02 | 11 | 1 | 1=Si, 0=No | `1` |
| Adjunta 03 | 12 | 1 | 1=Si, 0=No | `1` |
| Adjunta 04 | 13 | 1 | 1=Si, 0=No | `1` |
| Adjunta 05 | 14 | 1 | 1=Si, 0=No | `1` |
| Adjunta 06 | 15 | 1 | 1=Si, 0=No | `1` |
| Adjunta 07 | 16 | 1 | 1=Si, 0=No | `1` |
| Adjunta 08 | 17 | 1 | 1=Si, 0=No | `1` |
| Adjunta 09 | 18 | 1 | 1=Si, 0=No | `1` |
| Adjunta 10 | 19 | 1 | 1=Si, 0=No | `1` |
| Adjunta 11 | 20 | 1 | (Municipales < 250 hab) | `0` |
| Adjunta 12 | 21 | 1 | (Municipales < 250 hab) | `0` |
| Adjunta 05 (PJ) | 22 | 1 | Partidos Judiciales | `0` |
| Adjunta 06 (PJ) | 23 | 1 | Partidos Judiciales | `0` |
| Adjunta 07 (Dip) | 24 | 1 | Diputaciones | `0` |
| Adjunta 08 (Dip) | 25 | 1 | Diputaciones | `0` |

### Fichero 02: Identificación Proceso
Datos generales de la elección.
**Ejemplo**: `022016061N992606201609:0020:0014:0018:00`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificación común | `022016061` |
| Tipo Ámbito | 10 | 1 | N=Nacional, A=Autonómico | `N` |
| Ámbito Territorial | 11-12 | 2 | Código ámbito | `99` |
| Fecha (DDMMAAAA) | 13-20 | 8 | Fecha elección | `26062016` |
| Hora Apertura | 21-25 | 5 | HH:MM | `09:00` |
| Hora Cierre | 26-30 | 5 | HH:MM | `20:00` |
| Hora Avance 1 | 31-35 | 5 | HH:MM | `14:00` |
| Hora Avance 2 | 36-40 | 5 | HH:MM | `18:00` |

### Fichero 03: Candidaturas
Definición de partidos, coaliciones y agrupaciones.
**Ejemplo**: `02201606000001ALCD                                              ALIANZA DE CENTRO DEMOCRTICO                                                                                                                         000001000001000001`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo Elección | 1-2 | 2 | 02 = Congreso | `02` |
| Año | 3-6 | 4 | | `2016` |
| Mes | 7-8 | 2 | | `06` |
| **Código Candidatura** | 9-14 | 6 | ID único del partido | `000001` |
| Siglas | 15-64 | 50 | Siglas cortas | `ALCD` |
| Denominación | 65-214 | 150 | Nombre completo | `ALIANZA DE CENTRO...` |
| Código Padre Prov | 215-220 | 6 | ID agrupación provincial | `000001` |
| Código Padre Auto | 221-226 | 6 | ID agrupación autonómica | `000001` |
| Código Padre Nac | 227-232 | 6 | ID agrupación nacional | `000001` |

### Fichero 04: Relación de Candidatos
Fichero de ancho fijo. **Ejemplo**: `022016061049999000013001T`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| **ID Geo** | 10-15 | 6 | Prov(2)+Dist(1)+Muni(3) | `04`+`9`+`999` |
| **Código Cand.** | 16-21 | 6 | ID Partido | `00001` |
| Orden | 22-24 | 3 | Posición en lista | `3` |
| Tipo | 25-25 | 1 | (T)itular / (S)uplente | `T` |
| Nombre | 26-50 | 25 | Nombre pila | |
| Apellidos | 51-100 | 50 | 1er y 2º Apellido | |
| DNI | 110-119 | 10 | | |
| Elegido | 120-120 | 1 | S/N (obtiene escaño) | |

### Fichero 05: Datos Municipios
Datos del censo y participación a nivel municipal.
**Ejemplo**: `022016061010400199Abla                                                                                                001301300000001342000020000106200001062000000000000000000000462000006050000000500000009000008090000000000000000000S`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificación común | `022016061` |
| Cód CCAA | 10-11 | 2 | Código Comunidad Autónoma | `01` |
| Cód. Provincia | 12-13 | 2 | Código INE Provincia | `04` |
| Cód. Municipio | 14-16 | 3 | Código INE Municipio | `001` |
| Cód. Distrito Mun. | 17-18 | 2 | Distrito municipal (99 = Total) | `99` |
| Nombre | 19-118 | 100 | Nombre oficial municipio | `Abla` |
| Cód. Dist. Electoral | 119-119 | 1 | Distrito Electoral | `0` |
| Cód. Part. Judicial | 120-122 | 3 | Partido Judicial | `013` |
| Cód. Diputación | 123-125 | 3 | Diputación Provincial | `013` |
| Cód. Comarca | 126-128 | 3 | Comarca | `000` |
| Población | 129-136 | 8 | Población de derecho | `00001342` |
| Num Mesas | 137-141 | 5 | Número de mesas | `00002` |
| Censo INE | 142-149 | 8 | Censo electoral INE | `00001062` |
| Censo Escrutinio | 150-157 | 8 | Censo escrutinio | `00001062` |
| Censo CERE | 158-165 | 8 | Censo Extranjeros | `00000000` |
| Votantes CERE | 166-173 | 8 | Votantes Extranjeros | `00000000` |
| Avance 1 | 174-181 | 8 | Participación 14:00 | `00000000` |
| Avance 2 | 182-189 | 8 | Participación 18:00 | `00000462` |
| Votos Blancos | 190-197 | 8 | Votos en blanco | `00000006` |
| Votos Nulos | 198-205 | 8 | Votos nulos | `00000005` |
| Votos Candidaturas | 206-213 | 8 | Votos a candidaturas | `00000000` |
| Escaños | 214-219 | 6 | Escaños (si aplica) | `000009` |
| Votos SI (Ref) | 220-227 | 8 | Votos Afirmativos (Ref) | `00000809` |
| Votos NO (Ref) | 228-235 | 8 | Votos Negativos (Ref) | `00000000` |
| Oficial | 236-236 | 1 | Datos Oficiales (S/N) | `S` |

### Fichero 06: Resultados Municipios
Votos por candidatura a nivel municipal.
**Ejemplo**: `022016061010019900001300000062000`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificación común | `022016061` |
| Cód Provincia | 10-11 | 2 | Código Provincia | `01` |
| Cód Municipio | 12-14 | 3 | Código Municipio | `001` |
| Distrito | 15-16 | 2 | Distrito (99=Total) | `99` |
| Cód Candidatura | 17-22 | 6 | ID Candidatura | `000013` |
| Votos | 23-30 | 8 | Votos obtenidos | `00000062` |
| Candidatos | 31-35 | 5 | Candidatos obtenidos | `000` |

### Fichero 07: Ámbitos Superiores (Provincia/CCAA)
Resultados agregados a nivel superior.
**Ejemplo**: `02201606102229Huesca                                            00222909003930017354400173546000000000000000000059418000813550000120400001134001156800000030000000000000000S`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificación común | `022016061` |
| Cód CCAA | 10-11 | 2 | Código INE Comunidad | `02` |
| Cód Provincia | 12-13 | 2 | Código INE Provincia | `22` |
| Cód Distrito | 14 | 1 | Distrito Electoral | `9` |
| Nombre | 15-64 | 50 | Nombre del ámbito | `Huesca` |
| Población | 65-72 | 8 | Población de derecho | `00222909` |
| Num Mesas | 73-77 | 5 | Número de mesas | `00393` |
| Censo INE | 78-85 | 8 | Censo total | `00173544` |
| Censo Escrutinio | 86-93 | 8 | Censo escrutinio | `00173546` |
| Censo CERE | 94-101 | 8 | Censo CERE | `00000000` |
| Votantes CERE | 102-109 | 8 | Votantes CERE | `00000000` |
| Avance 1 | 110-117 | 8 | Participación 1 | `00000000` |
| Avance 2 | 118-125 | 8 | Participación 2 | `00059418` |
| Votos Blanco | 126-133 | 8 | Total votos en blanco | `00001204` |
| Votos Nulos | 134-141 | 8 | Total votos nulos | `00001134` |
| Votos Cands. | 142-149 | 8 | Total votos a candidaturas | `0011568` |
| Escaños | 150-155 | 6 | Escaños a repartir | `000003` |
| Votos SI (Ref) | 156-163 | 8 | Votos Sí (Ref) | `00000000` |
| Votos NO (Ref) | 164-171 | 8 | Votos No (Ref) | `00000000` |
| Oficial | 172 | 1 | Datos Oficiales (S/N) | `S` |

### Fichero 08: Resultados Ámbito
Votos por partido a nivel provincial/autonómico.
**Ejemplo**: `022016061011190000490000076700000`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificación común | `022016061` |
| Cód CCAA | 10-11 | 2 | Código CCAA | `01` |
| Cód Provincia | 12-13 | 2 | Código Provincia | `11` |
| Cód Distrito | 14 | 1 | Distrito Electoral | `9` |
| **Cód Candidatura**| 15-20 | 6 | ID Partido | `000049` |
| Votos | 21-28 | 8 | Votos obtenidos | `00000767` |
| Candidatos | 29-33 | 5 | Num. candidatos presentados | `00000` |

### Fichero 09: Mesas (Cabecera)
Identificación de las mesas electorales.
**Ejemplo**: `022016061010400302002 B00005160000516000000000000000000166000022000000020000001000031000000000000000S`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificador común | `022016061` |
| Cód CCAA | 10-11 | 2 | Código CCAA | `01` |
| Cód Provincia | 12-13 | 2 | Código Provincia | `04` |
| Cód Municipio | 14-16 | 3 | Código Municipio | `003` |
| Distrito | 17-18 | 2 | Distrito municipal | `02` |
| Sección | 19-22 | 4 | Sección censal | `002 ` |
| Mesa | 23-23 | 1 | Letra mesa (A, B, U) | `B` |
| Censo INE | 24-30 | 7* | Censo INE (ajustado 7/8?) | `0000516` |
| Censo Escrutinio | 31-37 | 7* | Censo Escrutinio | `0000516` |
| Censo CERE | 38-44 | 7* | Censo CERE | `0000000` |
| Votantes CERE | 45-51 | 7* | Votantes CERE | `0000000` |
| Avance 1 | 52-58 | 7* | Participación 1er avance | `0000000` |
| Avance 2 | 59-65 | 7* | Participación 2do avance | `0000166` |
| Votos Blancos | 66-72 | 7* | Votos Blancos | `0000022` |
| Votos Nulos | 73-79 | 7* | Votos Nulos | `0000000` |
| Votos Candidaturas | 80-86 | 7* | Votos a partidos | `0000000` |
| Votos SI | 87-93 | 7* | Votos Sí (Ref) | `0000010` |
| Votos NO | 94-100 | 7* | Votos No (Ref) | `0000310` |
| Oficial | 101-101 | 1 | Datos Oficiales | `0` |

*(Nota: En algunos ficheros de Mesas las longitudes de los contadores pueden ser de 7 u 8 dígitos dependiendo de la versión del formato, el ejemplo muestra bloques de 7 dígitos).*

### Fichero 10: Mesas (Votos)
Votos por candidatura en cada mesa.
**Ejemplo**: `022016061010400201001 A0000280000001`

| Campo | Posición | Longitud | Descripción | Valor Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| Tipo, Año, Mes, Vuelta | 1-9 | 9 | Identificación común | `022016061` |
| Cód CCAA | 10-11 | 2 | Código CCAA | `01` |
| Cód Provincia | 12-13 | 2 | Código Provincia | `04` |
| Cód Municipio | 14-16 | 3 | Código Municipio | `003` |
| Distrito | 17-18 | 2 | Distrito municipal | `02` |
| Sección | 19-22 | 4 | Sección censal | `002 ` |
| Mesa | 23-23 | 1 | Letra mesa (A, B, U) | `A` |
| **Cód Candidatura**| 24-29 | 6 | ID Partido | `000028` |
| Votos | 30-36 | 7 | Votos obtenidos | `0000001` |

## Estructura de Directorios

Cada elección se encuentra en una subcarpeta con el formato `02{AÑO}{MES}_MESA`.
Ejemplo: `02201911_MESA` contiene los datos del Congreso (02) de Noviembre de 2019.
