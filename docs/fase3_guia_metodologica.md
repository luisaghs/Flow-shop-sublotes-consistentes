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
la FIFO simulada da desde 20 % hasta 100 % de órdenes tardías (Tabla 1).

## 2. Recomendación: no cambiar el objetivo; cambiar cómo se representa el sistema actual

El objetivo se puede cumplir sin conocer el detalle de la división de las órdenes,
con un procedimiento estándar en simulación: **construir un modelo del sistema
actual con lo que se sabe y calibrar lo que no se sabe con el dato histórico**
(validación operacional del modelo; Sargent, 2013; Law, 2015). Después, se
comprueba que la conclusión se mantiene en todo el rango de valores plausibles.

En concreto:

1. **Modelo del sistema actual:** regla FIFO, la misma secuencia de órdenes en las
   cuatro etapas, órdenes divididas en *B* partes iguales y la regla del menor
   tiempo de terminación para elegir máquina. Es el mismo decodificador del AG
   aplicado a un cromosoma "FIFO con sublotes iguales". Solo *B* es desconocido.
2. **Calibración de *B*:** se elige el número de partes con el que la FIFO
   simulada reproduce la tasa histórica de incumplimiento (≈ 45 %).
3. **Análisis de sensibilidad:** la comparación se repite para todos los valores
   de *B* compatibles con el dato histórico. Si el modelo propuesto es mejor en
   todos, la conclusión no depende del dato desconocido.

### Tabla 1. Calibración: FIFO simulada con *B* partes iguales por orden

| *B* | Órdenes tardías | ΣT_j (h) | T_max (h) | C_max (h) |
|---|---|---|---|---|
| 1 (orden completa) | 10 (100 %) | 8.489,8 | 1.734,6 | 2.406,6 |
| 2 | 10 (100 %) | 3.051,2 | 531,3 | 1.203,3 |
| 3 | 9 (90 %) | 1.968,7 | 369,8 | 922,5 |
| 4 | 8 (80 %) | 1.145,6 | 296,9 | 807,0 |
| **5** | **6 (60 %)** | **704,2** | **243,1** | **746,6** |
| **6** | **4 (40 %)** | **493,0** | **213,7** | **689,7** |
| **7** | **4 (40 %)** | **392,8** | **181,3** | **665,3** |
| 8 | 3 (30 %) | 329,4 | 174,1 | 636,9 |
| 10 | 2 (20 %) | 242,5 | 135,3 | 620,6 |
| 20 | 2 (20 %) | 141,3 | 81,8 | 560,5 |

- Con 10 órdenes, el porcentaje de tardías solo puede tomar valores de 10 en 10.
  El 45 % histórico queda entre 4 y 5 órdenes tardías, que corresponde a
  **B entre 5 y 7**.
- **Escenario base propuesto: B = 6** (40 %, el más cercano al 45 %), con
  **banda de sensibilidad B = 5 a 7**.
- Hay que decir en el documento que es una representación calibrada, no una
  observación directa de cómo se reparte el trabajo.

### Tabla 2. Prueba preliminar: AG calibrado frente a la FIFO calibrada

Resultados exploratorios con 2 semillas por escenario; en la Fase 3 se usan 30
réplicas.

| Escenario | FIFO actual: tardías / ΣT_j | AG con la misma *B*: tardías / ΣT_j | Reducción de ΣT_j |
|---|---|---|---|
| B = 5 | 6 (60 %) / 704,2 h | 1 (10 %) / 249,2 – 249,4 h | 65 % |
| B = 6 | 4 (40 %) / 493,0 h | 1 (10 %) / 107,7 – 147,8 h | 70 – 78 % |
| B = 7 | 4 (40 %) / 392,8 h | 1 (10 %) / 65,2 – 81,0 h | 79 – 83 % |
| B̄ = 10 (modelo propuesto) | 2 (20 %) / 242,5 h | 0 (0 %) / 0,0 h | 100 % |

**La mejora se mantiene en todo el rango plausible**, así que la conclusión es
robusta frente al dato desconocido.

## 3. Un punto que hay que separar: dos fuentes de mejora

El modelo propuesto usa B̄ = 10 sublotes de tamaño variable; el sistema actual,
según la calibración, unos 6 sublotes iguales. Si solo se compara "actual contra
propuesto", la mejora mezcla dos cosas distintas:

1. **Mejor programación** (secuencia y tamaños optimizados) con la misma división.
2. **Más división** de las órdenes (de 6 a 10 sublotes), que es un cambio operativo.

Para que el jurado vea qué aporta cada una, conviene presentar una
**descomposición de la mejora** en el escenario base:

| Paso | Configuración | Tardías | ΣT_j (h) | Qué mide |
|---|---|---|---|---|
| 0 | FIFO, B = 6 (actual) | 4 | 493,0 | Línea base |
| 1 | EDD, B = 6 | 3 | 344,7 | Efecto de cambiar solo la regla de prioridad |
| 2 | AG, B = 6 | 1 | ≈ 108 – 148 | Efecto de optimizar con la misma división |
| 3 | AG, B̄ = 10 | 0 | 0,0 | Efecto adicional de dividir más las órdenes |

(Valores preliminares; en la Fase 3 los pasos 2 y 3 se calculan con 30 réplicas.)

Esto, además, le sirve a la empresa: muestra que solo con cambiar la forma de
programar, sin cambiar la manera de dividir las órdenes, ya se baja de 4 a 1 orden
tardía.

## 4. Estructura propuesta para la Fase 3

1. **Representación del sistema actual.** Supuestos (FIFO, sublotes iguales,
   misma secuencia en todas las etapas, ECT), qué se conoce y qué no.
2. **Calibración con el dato histórico.** Tabla 1, elección de B = 6 y banda de
   5 a 7. Limitaciones: el 45 % es una tasa histórica de largo plazo y la
   instancia tiene 10 órdenes.
3. **Indicadores de desempeño**, con su fórmula:
   - % de órdenes tardías (comparable directamente con el 45 % histórico);
   - tardanza total ΣT_j, tardanza promedio y tardanza máxima T_max;
   - % de órdenes adelantadas y adelanto total ΣE_j (el planteamiento menciona
     10 % de adelantos);
   - makespan C_max y tiempo de flujo medio;
   - ocupación por etapa y número y tiempo de alistamientos en troquelado.
4. **Diseño de la comparación:**
   - AG con 30 réplicas (semillas distintas) frente a la FIFO calibrada, que es
     determinística;
   - también frente a las otras reglas de despacho (EDD, SPT, LPT, MST, CR) como
     referencias.
5. **Análisis estadístico:**
   - media, desviación estándar, mínimo, máximo e intervalo de confianza del 95 %
     de cada indicador del AG;
   - prueba de Wilcoxon de una muestra (mediana del AG frente al valor de la FIFO);
   - porcentaje de mejora de cada indicador.
6. **Resultados del escenario base** y **descomposición de la mejora** (sección 3).
7. **Análisis de sensibilidad:**
   - *B* del sistema actual: 5, 6 y 7 (robustez frente al dato desconocido);
   - B̄ del modelo propuesto: 5, 10 y 20 (cuánto conviene dividir; conecta con la
     Tabla 16 de la Fase 2);
   - escenarios de exigencia: fechas de entrega 10 % y 20 % más ajustadas, o
     demanda 10 % y 20 % mayor. Como en la instancia real el AG llega a tardanza
     cero, estos escenarios muestran cómo se comporta el modelo cuando el sistema
     está más cargado;
   - opcional: robustez frente a tiempos de proceso con variación de ±10 %, en
     simulación Monte Carlo de la programación propuesta.
8. **Discusión, limitaciones y recomendaciones para la empresa.**

## 5. Si es posible, conseguir un dato más de la planta

La calibración es defendible por sí sola, pero un dato directo la refuerza mucho.
Con una conversación corta con el jefe de producción o el supervisor bastaría:

- ¿Una orden se trabaja en varios puestos a la vez o en uno solo por etapa?
- ¿El material pasa a la etapa siguiente por paquetes? ¿De cuántas docenas,
  aproximadamente?
- ¿Se espera a terminar toda la orden en una etapa antes de pasarla a la siguiente?

Si la respuesta indica, por ejemplo, paquetes de unas 100 docenas (B ≈ 6 para una
orden de 600 docenas), coincide con la calibración y se puede citar como validación
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
