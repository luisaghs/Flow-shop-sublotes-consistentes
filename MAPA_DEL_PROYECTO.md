# Mapa del proyecto: qué es cada archivo, qué anexar y qué semillas se usaron

## 1. Lo esencial (si solo van a mirar tres archivos)

| Archivo | Qué es |
|---|---|
| `final_sc_hfsagls_S2_4.py` | **El modelo**: el algoritmo genético final, con los parámetros calibrados. Es el código del trabajo de grado. |
| `BD_HFS.xlsx` | **Los datos** del caso de estudio: tiempos, órdenes y calendario. |
| `docs/Trabajo_de_Grado_con_Fases_2_y_3.docx` | **El documento** del trabajo de grado: Fase 1 actualizada, Fases 2 y 3, análisis de resultados, conclusiones y recomendaciones. |
| `Anexos_digitales/` | **El anexo digital para entregar**: datos, modelo, programas y resultados de verificación, calibración, validación, solución propuesta y Fase 3, con `LEEME.md` (contenido, orden de ejecución, semillas) y `requisitos.txt`. Se arma con `python docs/armar_anexos_digitales.py`; no se edita a mano. |

Todo lo demás son pruebas, experimentos y resultados que respaldan lo que dicen las Fases 2 y 3. Para entregar, usar la carpeta `Anexos_digitales/`, que reúne lo que respalda el documento.

---

## 2. Qué es cada archivo, según la sección de la Fase 2

### Documentos del trabajo de grado (`docs/`)

| Archivo | Qué es | ¿Lo usan? |
|---|---|---|
| `Trabajo_de_Grado_con_Fases_2_y_3.docx` | Borrador con la Fase 1 actualizada, las Fases 2 y 3, el análisis de resultados, las conclusiones y las recomendaciones | **Sí** |
| `fase2_referencias.md` | Referencias nuevas que cita la Fase 2 | Sí, para completar la bibliografía (verificarlas) |
| `fase3_guia_metodologica.md` | Propuesta para la Fase 3 | Sí, para la Fase 3 |
| `guia_apropiacion_calibracion.md` | Cómo entender, reproducir y declarar la calibración | Sí, para prepararse |
| `fase2_guia_metodologica.md`, `fase2_validacion_milp.md`, `fase2_calibracion.md` | Notas de trabajo previas a la redacción | Solo de consulta |
| `fase2_docx/`, `fase1_figuras/`, `fase2_figuras/` | Programas que generan el documento Word y los diagramas de flujo (Figura 1 del sistema y diagrama del AG) | No (herramientas internas) |

### Código y resultados (`fase2/`), por sección del documento

| Sección de la Fase 2 (versión sintetizada) | Programa | Resultados |
|---|---|---|
| 4.2.3 Verificación (el decodificador cumple el modelo) | `verificar_factibilidad.py` | Se imprime en pantalla (0 violaciones) |
| 4.2.3 Validación con instancias reducidas (Tabla 11) | `validacion_milp.py` | `salida_validacion/` (`resultados_validacion_todas.csv`; AG con parámetros calibrados en `ag_parametros_calibrados.txt`) |
| 4.2.4 Calibración: diseño factorial, ANOVA y criterio de parada | `calibracion_ag.py` | `salida_calibracion/` (`informe_calibracion.md`, `corridas_*.csv`, `resumen_*.csv`, `anova.csv`, `efectos_principales.png`, `interacciones.png`; `LEEME.md` describe cada archivo y `control/` guarda los archivos internos del proceso) |
| 4.2.4 Rehacer el ANOVA en Excel | `anova_excel.py` | `salida_calibracion/anova_calibracion_excel.xlsx` |
| 4.2.5 Programación obtenida | `solucion_final.py` | `salida_solucion/` (`replicas.csv`, `mejor_solucion.json`, `gantt_solucion.png`) |
| Comprobar que la calibración se repite igual | `verificar_reproduccion.py` | Se imprime en pantalla |
| 4.3 Fase 3: comparación con el sistema actual | `fase3/experimentos_fase3.py` | `fase3/salida_fase3/` (`informe_fase3.md`, `corridas_ag.csv`, `deterministas.csv`, `comparacion_base.png`) |

Todos los programas de `fase2/` usan el modelo `final_sc_hfsagls_S2_4.py` y `BD_HFS.xlsx`; no son otros modelos.

---

## 3. Qué anexar

| Anexo | Contenido | Archivo |
|---|---|---|
| **Anexo X: código del modelo** | El algoritmo genético completo | `final_sc_hfsagls_S2_4.py` |
| **Anexo Y: resultados de la calibración** | Tabla de las 27 combinaciones del diseño factorial (la Fase 2 muestra solo las mejores y las peores) | `fase2/salida_calibracion/resumen_combinaciones.csv` (pasarlo a tabla en Word) |
| Anexo digital (opcional, recomendado) | Datos, programas de validación y calibración y sus resultados, para que el jurado pueda reproducirlos | `BD_HFS.xlsx` y la carpeta `fase2/` completa (o el enlace al repositorio) |

**No anexen** `docs/fase2_docx/`, `docs/fase2_figuras/` ni las notas `.md` de `docs/`: son herramientas y notas internas.

Si el código del modelo es muy largo para el anexo impreso (≈ 980 líneas), una opción
habitual es imprimir las funciones principales (decodificador `simular_hfs`, operadores
`cruce` y `mutar`, y `algoritmo_genetico`) y entregar el archivo completo en el anexo
digital. Confirmen el formato con su director.

---

## 4. Semillas utilizadas

El algoritmo genético es aleatorio. La semilla fija la secuencia de números aleatorios,
de modo que **con la misma semilla se obtiene exactamente el mismo resultado**.

| Experimento | Sección | Semillas | Notas |
|---|---|---|---|
| Validación con instancias reducidas | 4.2.3 | **1 a 10** (en cada una de las 6 instancias) | 10 réplicas por instancia |
| Verificación del decodificador | 4.2.3 | 1 | Para generar los 200 cromosomas aleatorios |
| Calibración: diseño factorial (27 combinaciones) | 4.2.4 | **1001 a 1005** | La réplica r usa 1000 + r en todas las combinaciones |
| Calibración: criterio de parada | 4.2.4 | **1101 a 1110** | 10 réplicas por criterio (50 y 100 generaciones sin mejora) |
| Programación obtenida (10 réplicas) | 4.2.5 | **1201 a 1210** | **La programación propuesta es la de la semilla 1203** |
| Fase 3: escenario base (AG con B̄ = 10 y con B = 6) | 4.3 | **3001 a 3030** | 30 réplicas por configuración |
| Fase 3: sensibilidad y escenarios de exigencia | 4.3 | **3001 a 3010** | 10 réplicas por caso |
| Valor por defecto del modelo | — | **1203** | Al ejecutar `final_sc_hfsagls_S2_4.py` se obtiene la programación propuesta |

**Importante:**

- Las semillas de la solución final (1201–1210) son distintas de las de la calibración,
  así que la programación propuesta no se obtuvo con las mismas corridas usadas para
  ajustar los parámetros.
- El modelo ya trae la semilla 1203: al ejecutar `python final_sc_hfsagls_S2_4.py` se
  obtiene exactamente la programación del documento (ΣTj = 0 h, sin órdenes tardías,
  Cmax = 571,96 h).
  Para obtener otra réplica, cambien el valor de `'semilla'` en `GA_PARAMS`.
- La validación con instancias reducidas se corrió con los parámetros calibrados
  (`python validacion_milp.py ag ...` repite solo el AG).

---

## 5. Cómo ejecutar cada cosa (desde la carpeta del repositorio)

```bash
pip install pandas openpyxl matplotlib scipy pulp highspy

python final_sc_hfsagls_S2_4.py                                   # el modelo
cd fase2
python verificar_factibilidad.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python validacion_milp.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python calibracion_ag.py diseno ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx --instancia real
python calibracion_ag.py parada ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx --instancia real
python anova_excel.py
python verificar_reproduccion.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
cd ..
python fase2/solucion_final.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx 10
python fase3/experimentos_fase3.py correr final_sc_hfsagls_S2_4.py BD_HFS.xlsx   # Fase 3 (≈ 3 h)
```
