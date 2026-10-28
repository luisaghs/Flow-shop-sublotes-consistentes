# Mapa del proyecto: qué es cada archivo, qué anexar y qué semillas se usaron

## 1. Lo esencial (si solo van a mirar tres archivos)

| Archivo | Qué es |
|---|---|
| `final_sc_hfsagls_S2_4.py` | **El modelo**: el algoritmo genético final, con los parámetros calibrados. Es el código del trabajo de grado. |
| `BD_HFS.xlsx` | **Los datos** del caso de estudio: tiempos, órdenes y calendario. |
| `docs/Trabajo_de_Grado_con_Fase_2_sintetizada.docx` | **El documento** del trabajo de grado con la Fase 2 redactada (versión recomendada, ≈ 13 páginas). |

Todo lo demás son pruebas, experimentos y resultados que respaldan lo que dice la Fase 2.

---

## 2. Qué es cada archivo, según la sección de la Fase 2

### Documentos del trabajo de grado (`docs/`)

| Archivo | Qué es | ¿Lo usan? |
|---|---|---|
| `Trabajo_de_Grado_con_Fase_2_sintetizada.docx` | Borrador con la Fase 2 sintetizada | **Sí, versión recomendada** |
| `Trabajo_de_Grado_con_Fase_2.docx` | La misma Fase 2 en versión extensa (≈ 23 páginas) | Solo para consultar detalles |
| `fase2_referencias.md` | Referencias nuevas que cita la Fase 2 | Sí, para completar la bibliografía (verificarlas) |
| `fase3_guia_metodologica.md` | Propuesta para la Fase 3 | Sí, para la Fase 3 |
| `guia_apropiacion_calibracion.md` | Cómo entender, reproducir y declarar la calibración | Sí, para prepararse |
| `fase2_guia_metodologica.md`, `fase2_validacion_milp.md`, `fase2_calibracion.md` | Notas de trabajo previas a la redacción | Solo de consulta |
| `fase2_docx/`, `fase2_figuras/` | Programas que generan el documento Word y el diagrama de flujo | No (herramientas internas) |

### Código y resultados (`fase2/`), por sección del documento

| Sección de la Fase 2 (versión sintetizada) | Programa | Resultados |
|---|---|---|
| 4.2.3 Verificación (el decodificador cumple el modelo) | `verificar_factibilidad.py` | Se imprime en pantalla (0 violaciones) |
| 4.2.3 Validación con instancias reducidas (Tabla 11) | `validacion_milp.py` | `salida_validacion/` (`resultados_validacion_todas.csv`; AG con parámetros calibrados en `ag_parametros_calibrados.txt`) |
| 4.2.4 Calibración: diseño factorial, ANOVA, ampliación y criterio de parada (Tablas 13–15, Figura 5) | `calibracion_ag.py` | `salida_calibracion/` (`informe_calibracion.md`, `corridas_*.csv`, `resumen_*.csv`, `anova.csv`, `efectos_principales.png`) |
| 4.2.4 Rehacer el ANOVA en Excel | — | `salida_calibracion/anova_calibracion_excel.xlsx` |
| 4.2.5 Programación obtenida (Tablas 16–18, Figura 6) | `solucion_final.py` | `salida_solucion/` (`replicas.csv`, `mejor_solucion.json`, `gantt_solucion.png`) |
| Comprobar que la calibración se repite igual | `verificar_reproduccion.py` | Se imprime en pantalla |

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
| Validación con instancias reducidas | 4.2.3 | **1 a 10** (en cada una de las 9 instancias) | 10 réplicas por instancia |
| Verificación del decodificador | 4.2.3 | 1 | Para generar los 200 cromosomas aleatorios |
| Calibración: diseño factorial (27 combinaciones) | 4.2.4 | **1001 a 1005** | La réplica r usa 1000 + r en todas las combinaciones |
| Calibración: ampliación del rango | 4.2.4 | **1001 a 1005** | Las mismas, para comparar con la configuración actual |
| Calibración: criterio de parada | 4.2.4 | **1101 a 1110** | 10 réplicas por criterio |
| Programación obtenida (10 réplicas) | 4.2.5 | **1201 a 1210** | **La programación propuesta es la de la semilla 1206** |
| Valor por defecto del modelo | — | **1206** | Al ejecutar `final_sc_hfsagls_S2_4.py` se obtiene la programación propuesta |

**Importante:**

- Las semillas de la solución final (1201–1210) son distintas de las de la calibración,
  así que la programación propuesta no se obtuvo con las mismas corridas usadas para
  ajustar los parámetros.
- El modelo ya trae la semilla 1206: al ejecutar `python final_sc_hfsagls_S2_4.py` se
  obtiene exactamente la programación del documento (ΣTj = 0 h, Cmax = 630,17 h).
  Para obtener otra réplica, cambien el valor de `'semilla'` en `GA_PARAMS`.
- Las corridas exploratorias de las guías (`docs/fase3_guia_metodologica.md`) usaron
  otras semillas (1 y 2) y no forman parte del documento.

---

## 5. Cómo ejecutar cada cosa (desde la carpeta del repositorio)

```bash
pip install pandas openpyxl matplotlib scipy pulp highspy

python final_sc_hfsagls_S2_4.py                                   # el modelo
cd fase2
python verificar_factibilidad.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python validacion_milp.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python calibracion_ag.py diseno ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
python verificar_reproduccion.py ../final_sc_hfsagls_S2_4.py ../BD_HFS.xlsx
cd ..
python fase2/solucion_final.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx 10
```
