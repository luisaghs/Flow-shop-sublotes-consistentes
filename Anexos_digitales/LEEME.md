# Anexo digital del trabajo de grado

Programación de un Flow Shop híbrido de cuatro etapas con sublotes consistentes
mediante un algoritmo genético que minimiza la tardanza total.

Esta carpeta contiene los datos, el modelo y los programas con los que se obtuvieron
todos los resultados del documento, junto con esos resultados. **Ningún resultado se
editó a mano: cada archivo lo genera el programa de su carpeta.**

## Contenido

| Carpeta | Qué contiene | Qué respalda en el documento |
|---|---|---|
| `1_Datos` | `BD_HFS.xlsx`: órdenes de trabajo, tiempos estándar por máquina y referencia, y calendario laboral | Caso de estudio y datos del modelo |
| `2_Modelo` | `final_sc_hfsagls_S2_4.py`: lectura de datos, decodificador y algoritmo genético con los parámetros calibrados; al terminar muestra un diagrama de Gantt por etapa y la ruta de la orden de entrega más temprana | Modelo, algoritmo propuesto y diagramas de Gantt |
| `3_Verificacion` | `verificar_factibilidad.py`: comprueba que las programaciones del algoritmo cumplen todas las restricciones del modelo matemático | Verificación del modelo |
| `4_Calibracion` | `reglas_por_sublotes.py`, `calibracion_ag.py`, `anova_excel.py`, `verificar_reproduccion.py` y `salida_calibracion/` (reglas según el número de sublotes, 135 corridas del diseño factorial, 20 del criterio de parada, ANOVA, pruebas, figuras e informe; ver su `LEEME.md`) | Calibración de los parámetros |
| `5_Validacion` | `validacion_milp.py` y `salida_validacion/`: seis instancias reducidas resueltas de forma exacta (HiGHS) y con el algoritmo | Validación del modelo |
| `6_Solucion_propuesta` | `solucion_final.py` y `salida_solucion/`: 10 réplicas finales, la mejor solución (semilla 1203), su convergencia y su diagrama de Gantt. `experimentos_revision.py` y `salida_revision/`: el algoritmo con B̄ = 15 y con población inicial sin EDD (10 réplicas cada uno). `Gantt_en_Colab.ipynb`: cuaderno de Google Colab que genera los diagramas de Gantt a partir de la solución guardada | Programación propuesta, B̄ = 15 y mejora frente a EDD |
| `7_Fase3_Comparacion` | `experimentos_fase3.py` y `salida_fase3/`: 120 corridas del algoritmo, sistema actual y reglas de despacho en cinco escenarios, informe y figura | Comparación con el sistema actual (Fase 3) |

## Archivos principales de resultados

| Carpeta | Archivo | Contenido |
|---|---|---|
| `4_Calibracion/salida_calibracion` | `reglas_por_sublotes.csv` | Tardanza y órdenes tardías de las reglas de despacho con 1, 2, 5, 10 y 15 sublotes por orden (Tabla 9) |
| | `corridas_diseno.csv` | Las 135 corridas del diseño factorial 3³ × 5 réplicas |
| | `anova.csv`, `anova_calibracion_excel.xlsx` | ANOVA de la tardanza total (el Excel lo calcula con fórmulas) |
| | `corridas_parada.csv`, `resumen_parada.csv` | Criterio de parada: 50 frente a 100 generaciones sin mejora |
| | `informe_calibracion.md` | Informe completo con las pruebas de supuestos y las decisiones |
| `5_Validacion/salida_validacion` | `resultados_validacion_todas.csv` / `.md` | Resultados de las seis instancias (solución exacta, reglas y algoritmo) |
| | `I1.xlsx` … `I6.xlsx` | Datos de cada instancia reducida |
| | `programacion_milp_I1.csv` … | Programación de la solución exacta de cada instancia |
| | `gantt_milp_vs_ag_I3.png` | Gantt de la solución exacta frente a la del algoritmo en I3 |
| `6_Solucion_propuesta/salida_solucion` | `replicas.csv` | Las 10 réplicas finales (semillas 1201 a 1210) |
| | `mejor_solucion.json` | Cromosoma de la mejor solución (tamaños de sublote y secuencias) |
| | `gantt_solucion.png`, `convergencia.png` | Gantt de la programación propuesta y convergencia del algoritmo |
| `7_Fase3_Comparacion/salida_fase3` | `corridas_ag.csv` | Las 120 corridas del algoritmo en la Fase 3 |
| | `deterministas.csv` | Sistema actual y reglas de despacho en cada escenario |
| | `informe_fase3.md`, `comparacion_base.png` | Resumen estadístico y comparación del escenario base |

## Cómo reproducir los resultados

1. Instalar Python 3.13 y las librerías: `pip install -r requisitos.txt`
2. Ejecutar los comandos **desde esta carpeta** (`Anexos_digitales`), en este orden:

| Paso | Comando | Tiempo aproximado* |
|---|---|---|
| Ejecutar el modelo (programación propuesta) | `python 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx` | 10 min |
| Verificación | `python 3_Verificacion/verificar_factibilidad.py 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx` | segundos |
| Número de sublotes: reglas de despacho | `python 4_Calibracion/reglas_por_sublotes.py 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx` | segundos |
| Calibración: diseño factorial | `python 4_Calibracion/calibracion_ag.py diseno 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx --instancia real` | 1 h |
| Calibración: criterio de parada | `python 4_Calibracion/calibracion_ag.py parada 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx --instancia real --config 150,0.9,0.5` | 35 min |
| Calibración: ANOVA en Excel | `python 4_Calibracion/anova_excel.py` | segundos |
| Validación | `python 5_Validacion/validacion_milp.py 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx` | 1 h 45 min |
| Réplicas finales | `python 6_Solucion_propuesta/solucion_final.py 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx 10` | 20 min |
| B̄ = 15 y población sin EDD | `python 6_Solucion_propuesta/experimentos_revision.py 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx` | 1 h |
| Fase 3 | `python 7_Fase3_Comparacion/experimentos_fase3.py correr 2_Modelo/final_sc_hfsagls_S2_4.py 1_Datos/BD_HFS.xlsx` | 2 h 45 min |

\* Con 4 procesos en paralelo; los programas usan todos los núcleos disponibles.
La validación incluye los límites de tiempo del solver (600 s por fase).

Cada programa guarda sus resultados en la carpeta `salida_…` que está a su lado y
reemplaza los archivos que encuentre. Si una corrida larga se interrumpe, al repetir el
mismo comando continúa desde donde quedó.

## Semillas (reproducibilidad)

El algoritmo genético es aleatorio; cada corrida usa una semilla fija. Con la misma
semilla, el mismo código y los mismos datos se obtiene exactamente el mismo resultado;
solo cambia el tiempo de cómputo según el computador.

| Experimento | Semillas |
|---|---|
| Calibración: diseño factorial | 1001 a 1005 (la misma réplica usa la misma semilla en las 27 combinaciones) |
| Calibración: criterio de parada | 1101 a 1110 |
| Validación (algoritmo en cada instancia) | 1 a 10 |
| Réplicas finales | 1201 a 1210; la programación propuesta es la de la semilla 1203 |
| B̄ = 15 y población sin EDD | 1201 a 1210 (las mismas de las réplicas finales) |
| Fase 3: escenario base | 3001 a 3030 |
| Fase 3: sensibilidad y escenarios de exigencia | 3001 a 3010 |

`4_Calibracion/verificar_reproduccion.py` repite corridas de la calibración y comprueba
que dan el mismo resultado que el guardado.

## Parámetros del algoritmo

Los parámetros calibrados están escritos en `2_Modelo/final_sc_hfsagls_S2_4.py`
(diccionario `GA_PARAMS`): población 150, probabilidad de cruce 0,9, probabilidad de
mutación 0,5, parada tras 100 generaciones sin mejora (máximo 1000) y semilla 1203.
Repetir la calibración no cambia ese archivo: si se obtuviera otra configuración,
habría que escribirla allí.
