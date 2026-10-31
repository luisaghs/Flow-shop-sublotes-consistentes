# Fase 3 — Guía para el desarrollo metodológico

**Objetivo específico 3:** *Evaluar la calidad de las soluciones obtenidas basadas en
los indicadores evaluados mediante la comparación del desempeño del modelo propuesto
respecto al sistema de programación actual.*

## 1. El problema

Para comparar contra "el sistema de programación actual" hay que poder simularlo.
Hoy se sabe:

| Aspecto del sistema actual | ¿Se conoce? | Fuente |
|---|---|---|
| Regla de prioridad: las órdenes se atienden por orden de llegada (FIFO) | Sí | Planteamiento del problema |
| Desempeño: ≈ 45 % de órdenes entregadas tarde, ≈ 10 % adelantadas | Sí | Registros históricos |
| Cómo se reparte cada orden entre las máquinas y cuántas docenas pasan juntas de una etapa a otra | **No** | — |

El dato que falta pesa mucho: según cómo se represente la división de las órdenes,
la FIFO simulada da desde 30 % hasta 100 % de órdenes tardías (Tabla 1).

## 2. Recomendación: no cambiar el objetivo; cambiar cómo se representa el sistema actual

El objetivo se puede cumplir sin conocer el detalle de la división de las órdenes,
con un procedimiento estándar en simulación: **construir un modelo del sistema
actual con lo que se sabe y calibrar lo que no se sabe con el dato histórico**
(validación operacional del modelo; Sargent, 2013; Law, 2015). Después, se
comprueba que la conclusión se mantiene en todo el rango de valores plausibles.

En concreto:

1. **Modelo del sistema actual: FIFO por etapa.** En troquelado, las órdenes se
   atienden por orden de liberación; en cada etapa siguiente, los sublotes se
   atienden en el orden en que llegan de la etapa anterior. Cada orden se divide en
   *B* partes iguales y la máquina se elige con la regla del menor tiempo de
   terminación. Solo *B* es desconocido.
2. **Calibración de *B*:** se elige el número de partes con el que la FIFO
   simulada reproduce la tasa histórica de incumplimiento (≈ 45 %).
3. **Análisis de sensibilidad:** la comparación se repite para los valores de *B*
   vecinos. Si el modelo propuesto es mejor en todos, la conclusión no depende del
   dato desconocido.

### Tabla 1. Calibración: FIFO por etapa con *B* partes iguales por orden

| *B* | Órdenes tardías | ΣT_j (h) | C_max (h) |
|---|---|---|---|
| 2 | 10 (100 %) | 3.030,6 | 1.016,7 |
| 3 | 9 (90 %) | 1.591,0 | 815,1 |
| 4 | 7 (70 %) | 795,3 | 700,0 |
| 5 | 7 (70 %) | 548,0 | 655,6 |
| **6** | **4 (40 %)** | **393,8** | **617,1** |
| 7 | 4 (40 %) | 345,7 | 596,8 |
| 8 | 4 (40 %) | 297,5 | 585,2 |
| 9 | 3 (30 %) | 276,5 | 575,7 |
| 10 | 3 (30 %) | 257,7 | 559,5 |

- Con 10 órdenes, el porcentaje de tardías solo puede tomar valores de 10 en 10. El
  45 % histórico queda entre 70 % (B = 4 o 5) y 40 % (B = 6 a 8); el valor más
  cercano es 40 %.
- **Escenario base: B = 6**, el menor número de partes que da el porcentaje más
  cercano al histórico. Elegir el menor es la opción conservadora: no le atribuye
  al sistema actual más división de la necesaria.
- **Sensibilidad en B = 5 (70 %) y B = 7 (40 %)**, que rodean al valor elegido.
- Hay que decir en el documento que es una representación calibrada, no una
  observación directa de cómo se reparte el trabajo.

## 3. Dos fuentes de mejora

El modelo propuesto usa B̄ = 10 sublotes de tamaño variable; el sistema actual,
según la calibración, 6 partes iguales. Si solo se compara "actual contra
propuesto", la mejora mezcla tres cosas: cambiar la regla de prioridad, dividir más
las órdenes y optimizar con el AG. Conviene presentar una **descomposición de la
mejora** en el escenario base:

| Paso | Configuración | Tardías | ΣT_j (h) | C_max (h) | Qué mide |
|---|---|---|---|---|---|
| 0 | FIFO por etapa, B = 6 (actual) | 4 | 393,8 | 617,1 | Línea base |
| 1 | EDD, B = 6 | 6 | 386,9 | 778,2 | Cambiar solo la regla |
| 2 | AG, B = 6 | Fase 3 | Fase 3 | Fase 3 | Optimizar con la misma división |
| 3 | EDD, B̄ = 10 | 2 | 99,0 | 681,3 | Dividir más con una regla simple |
| 4 | AG, B̄ = 10 | Fase 3 | Fase 3 | Fase 3 | Dividir más y optimizar |

Lectura de los pasos ya calculados:

- Cambiar solo la regla (FIFO → EDD) con la misma división casi no cambia la
  tardanza total (387 h frente a 394 h) y aumenta las órdenes tardías de 4 a 6.
- Dividir más las órdenes con una regla simple (EDD con 10 sublotes) reduce la
  tardanza a 99 h, pero aún deja 2 órdenes tardías y alarga el makespan.
- Los pasos 2 y 4 miden lo que aporta el AG; se calculan con 30 réplicas.

### Línea base en los escenarios de exigencia

| Escenario | Sistema actual (B = 6): tardías / ΣT_j | EDD con B̄ = 10: tardías / ΣT_j |
|---|---|---|
| Caso de estudio | 4 / 393,8 h | 2 / 99,0 h |
| Fechas 10 % más ajustadas | 7 / 592,2 h | 4 / 255,1 h |
| Fechas 20 % más ajustadas | 8 / 868,3 h | 6 / 502,3 h |
| Demanda 10 % mayor | 7 / 661,7 h | 3 / 233,0 h |
| Demanda 20 % mayor | 7 / 1.018,0 h | 6 / 445,4 h |

## 4. Estructura propuesta para la Fase 3

1. **Representación del sistema actual.** Supuestos (FIFO por etapa, sublotes
   iguales, ECT), qué se conoce y qué no.
2. **Calibración con el dato histórico.** Tabla 1, elección de B = 6 y sensibilidad
   en 5 y 7. Limitaciones: el 45 % es una tasa histórica de largo plazo y la
   instancia tiene 10 órdenes.
3. **Indicadores de desempeño**, con su fórmula:
   - % de órdenes tardías (comparable directamente con el 45 % histórico);
   - tardanza total ΣT_j, tardanza promedio y tardanza máxima T_max;
   - adelanto total ΣE_j (el planteamiento menciona 10 % de adelantos);
   - makespan C_max y tiempo de flujo medio;
   - ocupación por etapa y número y tiempo de alistamientos en troquelado.
4. **Diseño de la comparación:**
   - AG con 30 réplicas (semillas 3001–3030) frente al sistema actual, que es
     determinístico;
   - también frente a las otras reglas de despacho como referencias.
5. **Análisis estadístico:**
   - media, desviación estándar, mínimo, máximo e intervalo de confianza del 95 %
     de cada indicador del AG;
   - prueba de Wilcoxon de una muestra (mediana del AG frente al valor del sistema
     actual);
   - porcentaje de mejora de cada indicador.
6. **Resultados del escenario base** y **descomposición de la mejora** (sección 3).
7. **Análisis de sensibilidad:**
   - *B* del sistema actual: 5, 6 y 7 (robustez frente al dato desconocido);
   - B̄ del modelo propuesto: 5, 6, 7, 10 y 20 (cuánto conviene dividir);
   - escenarios de exigencia: fechas de entrega 10 % y 20 % más ajustadas, y
     demanda 10 % y 20 % mayor;
   - opcional: robustez frente a tiempos de proceso con variación de ±10 %, en
     simulación Monte Carlo de la programación propuesta.
8. **Discusión, limitaciones y recomendaciones para la empresa.**

El programa `fase3/experimentos_fase3.py` ya está ajustado a este diseño.

## 5. Si es posible, conseguir un dato más de la planta

La calibración es defendible por sí sola, pero un dato directo la refuerza mucho.
Con una conversación corta con el jefe de producción o el supervisor bastaría:

- ¿Una orden se trabaja en varios puestos a la vez o en uno solo por etapa?
- ¿El material pasa a la etapa siguiente por paquetes? ¿De cuántas docenas,
  aproximadamente?
- ¿Se espera a terminar toda la orden en una etapa antes de pasarla a la siguiente?

Si la respuesta indica, por ejemplo, paquetes de unas 90 docenas (B ≈ 6 para una
orden promedio de 524 docenas), coincide con la calibración y se puede citar como validación
cualitativa. Si las órdenes de BD_HFS.xlsx son órdenes reales con fechas de
terminación registradas, también se pueden comparar esas fechas con las simuladas.

## 6. ¿Conviene cambiar el objetivo 3?

**Recomendación: mantenerlo.** La comparación "respecto al sistema de programación
actual" sigue siendo posible con un sistema actual representado y calibrado, y
conserva la conexión con el planteamiento del problema (el 45 % de incumplimiento),
que es la justificación del trabajo.

Si el director o el comité prefieren que la redacción refleje el método, un ajuste
menor sería suficiente:

> *Evaluar la calidad de las soluciones del modelo propuesto mediante indicadores de
> desempeño, comparándolas con un escenario representativo de la programación actual
> de la empresa, calibrado con su desempeño histórico, y con reglas de despacho
> clásicas.*

No se recomienda cambiar el objetivo a "comparar solo contra reglas de despacho":
se pierde el vínculo con el problema de la empresa. Cualquier cambio de redacción
debe consultarse con el director según el reglamento del programa.

### Referencias sugeridas (verificar)

- Law, A. M. (2015). *Simulation modeling and analysis* (5.ª ed.). McGraw-Hill.
- Sargent, R. G. (2013). Verification and validation of simulation models.
  *Journal of Simulation, 7*(1), 12–24. https://doi.org/10.1057/jos.2012.20
