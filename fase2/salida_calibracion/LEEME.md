# Resultados de la calibración del algoritmo genético

Todos los archivos de esta carpeta los genera el código; ninguno se edita a mano.

| Paso | Comando (desde la raíz del proyecto) | Tiempo aproximado |
|---|---|---|
| 0. Reglas de despacho según el número de sublotes (Tabla 9) | `python fase2/reglas_por_sublotes.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx` | segundos |
| 1. Diseño factorial 3³ × 5 réplicas (135 corridas) | `python fase2/calibracion_ag.py diseno final_sc_hfsagls_S2_4.py BD_HFS.xlsx --instancia real` | 1 h con 4 procesos (3,9 h en uno solo) |
| 2. Criterio de parada (50 y 100 generaciones sin mejora, 20 corridas) | `python fase2/calibracion_ag.py parada final_sc_hfsagls_S2_4.py BD_HFS.xlsx --instancia real` | 35 min con 4 procesos (2 h en uno solo) |
| 3. Análisis (ANOVA, pruebas, figuras, informe) | `python fase2/calibracion_ag.py analizar` | segundos |
| 4. ANOVA en Excel con fórmulas | `python fase2/anova_excel.py` | segundos |

Los pasos 1 y 2 ejecutan el análisis al terminar. Cada corrida usa una semilla fija
(diseño: 1001 a 1005; parada: 1101 a 1110), por lo que al repetirlas se obtienen los
mismos resultados; solo cambia el tiempo de cómputo.

## Resultados (respaldan el documento)

| Archivo | Contenido |
|---|---|
| `reglas_por_sublotes.csv` | Tardanza total, órdenes tardías, tardanza máxima y makespan de FIFO, EDD, CR, SPT y LPT con 1, 2, 5, 10 y 15 sublotes iguales por orden (Tabla 9). |
| `corridas_diseno.csv` | Las 135 corridas del diseño factorial: parámetros, semilla, ΣTj, Cmax, órdenes tardías, generaciones y tiempo. |
| `resumen_combinaciones.csv` | Promedio y desviación de las 5 réplicas de cada una de las 27 combinaciones. |
| `anova.csv` | Tabla ANOVA de la tardanza total (efectos principales e interacciones dobles). |
| `anova_calibracion_excel.xlsx` | El mismo ANOVA calculado con fórmulas de Excel a partir de las 135 corridas. |
| `efectos_principales.png` | Gráfico de medias de cada factor con intervalos LSD al 95 %. |
| `interacciones.png` | Gráficos de las interacciones dobles. |
| `corridas_parada.csv` | Las 20 corridas del experimento del criterio de parada. |
| `resumen_parada.csv` | Promedios de cada criterio de parada. |
| `informe_calibracion.md` | Informe completo: tablas, ANOVA, Shapiro-Wilk, Levene, Kruskal-Wallis, Wilcoxon y decisiones. |
| `decisiones.json` | Las decisiones en formato de datos (las lee el generador del documento). |

## `control/` (archivos internos del proceso)

No son resultados: el programa los usa para pasar información de un paso al siguiente.

| Archivo | Uso |
|---|---|
| `config_seleccionada.txt` | Configuración elegida en el diseño; la lee el paso 2. |
| `config_parada.txt` | Configuración con la que se corrió el paso 2; se cita en el informe. |
| `parada_seleccionada.txt` | Criterio de parada elegido (100). |
| `seleccion_combinada.csv` | Posición de cada combinación; con una sola instancia repite `resumen_combinaciones.csv`. |
| `ampliacion_grilla.json` | Niveles que se probarían en la opción de ampliación del rango, que no se usó en el trabajo. |
| `log_cadena.txt` | Registro de la ejecución de los pasos 1 a 3. |
