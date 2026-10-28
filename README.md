# HFS con lot streaming — sublotes consistentes (GA)

Programación de un Hybrid Flow Shop para la producción de guantes industriales
con **sublotes consistentes** (escenario 2 de Gürsoy Yılmaz & Yılmaz, 2022,
*Computers & Industrial Engineering* 173, 108745) y un algoritmo genético.

## Versión final del modelo

**`final_sc_hfsagls_S2_4.py`** es el modelo final (algoritmo genético) y
**`BD_HFS.xlsx`** los datos del caso de estudio. Con ellos se obtuvieron todos los
resultados de la Fase 2. Los parámetros del AG son los calibrados (población 150,
cruce 0,9, mutación 0,5, parada tras 100 generaciones sin mejora).

La versión anterior (`final_sc_hfsagls.py`, cromosoma de tres niveles) se retiró;
sigue disponible en el historial de git.

## Uso

```bash
pip install pandas openpyxl matplotlib
python final_sc_hfsagls_S2_4.py               # usa BD_HFS.xlsx del mismo directorio
python final_sc_hfsagls_S2_4.py otra_ruta/BD_HFS.xlsx
```

En Google Colab: suba `final_sc_hfsagls_S2_4.py` y `BD_HFS.xlsx` al panel de
archivos (`/content`) y ejecute `!python final_sc_hfsagls_S2_4.py`.

## Datos de entrada (`BD_HFS.xlsx`)

| Hoja | Columnas usadas |
|---|---|
| Tiempo de procesamiento | Codigo producto, Maquina, Etapa, min x docena (o h x docena) |
| Trabajos | Orden de trabajo, Codigo Producto, Cantidad (docenas), r_j Liberación, Fechas de entrega, d_j horas |
| Disponibilidad | Fecha, Horas disponibles, Horas acumuladas — convierte horas laborables en fechas |

Las etapas se toman en el orden en que aparecen en la hoja de tiempos.

## Modelo

* **Sublotes consistentes**: los sublotes de una orden pueden tener tamaños
  distintos, pero cada sublote mantiene su tamaño en todas las etapas
  (10 sublotes por orden, mínimo 1 docena).
* Cromosoma de dos niveles: (1) proporciones de los tamaños de sublote de cada
  orden, (2) secuencia de los sublotes en cada etapa. La máquina la asigna el
  decodificador con la regla del menor tiempo de terminación (ECT).
* Alistamiento de 4,98 min en troquelado cuando cambia la referencia.
* Población inicial aleatoria sembrada con la mejor regla de despacho
  (FIFO, EDD, SPT, LPT, MST, CR).
* Selección por torneo; cruce aritmético (nivel 1) y LOX (nivel 2); mutación por
  perturbación de tamaños e intercambio de sublotes; elitismo.
* Objetivo: tardanza total ΣTj, con desempate por Cmax.

## Fase 2: guía metodológica y validación

| Archivo | Contenido |
|---|---|
| `docs/fase2_guia_metodologica.md` | Estructura propuesta para la Fase 2, correcciones al MILP, diseño del AG, calibración |
| `docs/fase2_validacion_milp.md` | Validación del MILP con 9 instancias pequeñas frente al AG (procedimiento, formulación y resultados) |
| `fase2/verificar_factibilidad.py` | Comprueba que las programaciones del decodificador cumplen las restricciones del MILP |
| `fase2/validacion_milp.py` | Resuelve el MILP con HiGHS (dos formulaciones), lo verifica y lo compara con el AG |
| `fase2/salida_validacion/` | Instancias (`I*.xlsx`), registros, programaciones óptimas, tablas y Gantt |
| `docs/fase2_calibracion.md` | Calibración de los parámetros del AG (diseño factorial, ampliación, criterio de parada) |
| `fase2/calibracion_ag.py` | Corre los experimentos de calibración en paralelo y genera ANOVA, figuras e informe |
| `fase2/salida_calibracion/` | Corridas, resúmenes, ANOVA, figuras e `informe_calibracion.md` |
| `fase2/salida_calibracion/anova_calibracion_excel.xlsx` | ANOVA de la calibración calculado con fórmulas de Excel |
| `fase2/verificar_reproduccion.py` | Repite corridas de la calibración y comprueba que dan los mismos resultados |
| `docs/guia_apropiacion_calibracion.md` | Cómo entender, reproducir y declarar la calibración |
| `docs/Trabajo_de_Grado_con_Fase_2_sintetizada.docx` | Borrador con la Fase 2 sintetizada (≈ 13 páginas) e incluye el pseudocódigo del AG |
| `docs/Trabajo_de_Grado_con_Fase_2.docx` | Borrador con la Fase 2 en versión extensa (≈ 23 páginas) |
| `docs/fase2_referencias.md` | Referencias nuevas citadas en la Fase 2 (verificar antes de usar) |
| `docs/fase2_docx/` | Generador del documento (`generar_fase2.py`) y utilidades |
| `fase2/solucion_final.py`, `fase2/salida_solucion/` | 10 réplicas del AG calibrado y la mejor programación (tablas, Gantt, convergencia) |

```bash
pip install pulp highspy pandas openpyxl matplotlib scipy
cd fase2
python verificar_factibilidad.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python validacion_milp.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx [I1,I2,...]
python validacion_milp.py resumen
python calibracion_ag.py diseno ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python calibracion_ag.py ampliacion ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python calibracion_ag.py parada ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
```

Para volver a generar la Fase 2 dentro del borrador (por ejemplo, tras nuevas corridas):

```bash
pip install python-docx   # además de pandoc instalado en el sistema
python fase2/solucion_final.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx 10
python docs/fase2_docx/generar_fase2.py borrador.docx salida.docx final_sc_hfsagls_S2_4.py BD_HFS.xlsx
python docs/fase2_docx/generar_fase2_sintesis.py borrador.docx salida.docx final_sc_hfsagls_S2_4.py BD_HFS.xlsx
```
