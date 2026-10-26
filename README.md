# HFS con lot streaming — sublotes consistentes (GA)

Programación de un Hybrid Flow Shop para la producción de guantes industriales
con **sublotes consistentes** (escenario 2 de Gürsoy Yılmaz & Yılmaz, 2022,
*Computers & Industrial Engineering* 173, 108745) y un algoritmo genético.

## Uso

```bash
pip install pandas openpyxl matplotlib
python final_sc_hfsagls.py            # usa BD_HFS.xlsx del mismo directorio
python final_sc_hfsagls.py otra_ruta/BD_HFS.xlsx
```

En Google Colab: sube `BD_HFS.xlsx` al panel de archivos (`/content`) y ejecuta
el script.

## Datos de entrada (`BD_HFS.xlsx`)

| Hoja | Columnas usadas |
|---|---|
| Tiempo de procesamiento | Codigo producto, Maquina, Etapa, min x docena (o h x docena) |
| Trabajos | Orden de trabajo, Codigo Producto, Cantidad (pares/docenas), Fecha de liberación, Fechas de entrega, Horas disponibles |
| Disponibilidad (opcional) | Fecha, Horas disponibles, Horas acumuladas — convierte horas laborables en fechas |

Las etapas se toman en el orden en que aparecen en la hoja de tiempos. Las
fechas de entrega son las **Horas disponibles** de cada trabajo.

## Modelo

* **Sublotes consistentes**: los sublotes de un lote pueden tener tamaños
  distintos, pero cada sublote mantiene su tamaño en todas las etapas.
* Cromosoma de tres niveles: (1) tamaños de sublote, (2) orden de los
  sublotes en cada etapa, (3) máquina de cada sublote en cada etapa.
* Escenario 2: población inicial con asignación aleatoria.
* Cruce de uno (C1) o dos puntos (C2) por etapas y mutación por intercambio,
  además de mutaciones sobre el número y el tamaño de los sublotes.
* Objetivo: ΣTi (tardanza total) con desempate por Cmax, o Cmax
  (`FUNCION_OBJETIVO`).

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
| `docs/Trabajo_de_Grado_con_Fase_2_sintetizada.docx` | Borrador con la Fase 2 sintetizada (≈ 13 páginas) e incluye el pseudocódigo del AG |
| `docs/Trabajo_de_Grado_con_Fase_2.docx` | Borrador con la Fase 2 en versión extensa (≈ 23 páginas) |
| `docs/fase2_referencias.md` | Referencias nuevas citadas en la Fase 2 (verificar antes de usar) |
| `docs/fase2_docx/` | Generador del documento (`generar_fase2.py`) y utilidades |
| `fase2/solucion_final.py`, `fase2/salida_solucion/` | 10 réplicas del AG calibrado y la mejor programación (tablas, Gantt, convergencia) |

```bash
pip install pulp highspy pandas openpyxl matplotlib scipy
cd fase2
python verificar_factibilidad.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
python validacion_milp.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx [I1,I2,...]
python validacion_milp.py resumen
python calibracion_ag.py diseno ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
python calibracion_ag.py ampliacion ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
python calibracion_ag.py parada ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
```

Para volver a generar la Fase 2 dentro del borrador (por ejemplo, tras nuevas corridas):

```bash
pip install python-docx   # además de pandoc instalado en el sistema
python fase2/solucion_final.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx 10
python docs/fase2_docx/generar_fase2.py borrador.docx salida.docx ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
python docs/fase2_docx/generar_fase2_sintesis.py borrador.docx salida.docx ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
```
