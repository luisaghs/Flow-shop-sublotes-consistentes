# Fase 3 — Guía para el desarrollo metodológico

**Objetivo específico 3:** *Evaluar la calidad de las soluciones obtenidas basadas en
los indicadores evaluados mediante la comparación del desempeño del modelo propuesto
respecto al sistema de programación actual.*

> **Actualizada con los datos corregidos** (J01 = 580 docenas, entrega el 25/08/2026).
> Las cifras con la base anterior quedan en el historial del repositorio.

## 1. El problema

Para comparar contra "el sistema de programación actual" hay que poder simularlo.
Hoy se sabe:

| Aspecto del sistema actual | ¿Se conoce? | Fuente |
|---|---|---|
| Regla de prioridad: las órdenes se atienden por orden de llegada (FIFO) | Sí | Planteamiento del problema |
| Desempeño: ≈ 45 % de órdenes entregadas tarde, ≈ 10 % adelantadas | Sí | Registros históricos |
| Cómo se reparte cada orden entre las máquinas y cuántas docenas pasan juntas de una etapa a otra | **No** | — |

El dato que falta pesa mucho: según cómo se represente la división de las órdenes,
la FIFO simulada da desde 20 % hasta 90 % de órdenes tardías (Tabla 1).

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
| 2 | 9 (90 %) | 2.207,0 | 1.016,7 |
| 3 | 7 (70 %) | 1.009,0 | 815,1 |
| **4** | **5 (50 %)** | **322,9** | **700,0** |
| 5 | 3 (30 %) | 184,3 | 655,6 |
| 6 | 2 (20 %) | 150,3 | 617,1 |
| 10 | 2 (20 %) | 104,3 | 559,5 |

- Con 10 órdenes, el porcentaje de tardías solo puede tomar valores de 10 en 10.
  El valor más cercano al 45 % histórico es **B = 4 (50 %)**: cada orden se divide en
  cuatro partes, una por troqueladora, lo que es una práctica plausible en planta.
- **Escenario base: B = 4**, con **sensibilidad en B = 3 (70 %) y B = 5 (30 %)**.
- Hay que decir en el documento que es una representación calibrada, no una
  observación directa de cómo se reparte el trabajo.

### Tabla 2. Prueba preliminar: AG frente al sistema actual

Resultados exploratorios (5 semillas, calculados antes de corregir la fecha de
entrega de J01); en la Fase 3 se recalculan con 30 réplicas.

| Escenario | Sistema actual: tardías / ΣT_j | AG con la misma división: tardías / ΣT_j |
|---|---|---|
| B = 4 | 5 (50 %) / 322,9 h | 1–2 (10–20 %) / 98–125 h |
| B̄ = 10 (modelo propuesto) | 2 (20 %) / 104,3 h | 0 (0 %) / 0,0 h |

## 3. Dos fuentes de mejora y el papel de la regla EDD

El modelo propuesto usa B̄ = 10 sublotes de tamaño variable; el sistema actual,
según la calibración, 4 partes iguales. Si solo se compara "actual contra
propuesto", la mejora mezcla tres cosas: cambiar la regla de prioridad, dividir más
las órdenes y optimizar con el AG. Conviene presentar una **descomposición de la
mejora** en el escenario base:

| Paso | Configuración | Tardías | ΣT_j (h) | C_max (h) | Qué mide |
|---|---|---|---|---|---|
| 0 | FIFO por etapa, B = 4 (actual) | 5 | 322,9 | 700,0 | Línea base |
| 1 | EDD, B = 4 | 4 | 355,8 | 825,2 | Cambiar solo la regla |
| 2 | AG, B = 4 | 1–2 | ≈ 98–125 | ≈ 720–765 | Optimizar con la misma división |
| 3 | EDD, B̄ = 10 | 0 | 0,0 | 650,1 | Dividir más con una regla simple |
| 4 | AG, B̄ = 10 | 0 | 0,0 | ≈ 550–565 | Dividir más y optimizar |

(Los pasos 2 y 4 son preliminares; en la Fase 3 se calculan con 30 réplicas.)

**Punto clave para la discusión:** con los datos corregidos, la regla EDD con 10
sublotes iguales ya cumple todas las fechas de entrega del caso de estudio. Por eso
hay que mostrar con claridad qué aporta el AG:

- **Con la misma división que hoy usa la empresa (4 partes)**, la regla EDD no mejora
  al sistema actual, mientras que el AG baja de 5 a 1–2 órdenes tardías.
- **Con 10 sublotes**, el AG mantiene la tardanza en cero y reduce el makespan cerca de
  un 14 % frente a la regla, lo que libera capacidad antes.
- **Cuando el sistema está más exigido** (fechas más ajustadas o más demanda), la regla
  deja órdenes tardías y el AG las reduce. Así se observó en la calibración con fechas
  20 % más ajustadas (la regla deja 238 h de tardanza y el AG unas 70–80 h); los
  escenarios de exigencia de la Fase 3 lo miden.
- El AG parte de la mejor regla y nunca entrega una solución peor que ella.

Para la empresa esto también es útil: una mejora inmediata y sin software es dividir
más las órdenes y priorizar por fecha de entrega; el AG es el que garantiza el mejor
resultado cuando la carga sube o las fechas se ajustan.

## 4. Estructura propuesta para la Fase 3

1. **Representación del sistema actual.** Supuestos (FIFO por etapa, sublotes
   iguales, ECT), qué se conoce y qué no.
2. **Calibración con el dato histórico.** Tabla 1, elección de B = 4 y sensibilidad
   en 3 y 5. Limitaciones: el 45 % es una tasa histórica de largo plazo y la
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
   - *B* del sistema actual: 3, 4 y 5 (robustez frente al dato desconocido);
   - B̄ del modelo propuesto: 4, 10 y 20 (cuánto conviene dividir);
   - escenarios de exigencia: fechas de entrega 10 % y 30 % más ajustadas, y
     demanda 10 % y 20 % mayor. No se usa la de fechas 20 % más ajustadas, porque
     con ella se calibró el AG en la Fase 2;
   - opcional: robustez frente a tiempos de proceso con variación de ±10 %, en
     simulación Monte Carlo de la programación propuesta.
8. **Discusión, limitaciones y recomendaciones para la empresa** (incluido el papel
   de la regla EDD, sección 3).

El programa `fase3/experimentos_fase3.py` ya está ajustado a este diseño.

## 5. Si es posible, conseguir un dato más de la planta

La calibración es defendible por sí sola, pero un dato directo la refuerza mucho.
Con una conversación corta con el jefe de producción o el supervisor bastaría:

- ¿Una orden se trabaja en varios puestos a la vez o en uno solo por etapa?
- ¿El material pasa a la etapa siguiente por paquetes? ¿De cuántas docenas,
  aproximadamente?
- ¿Se espera a terminar toda la orden en una etapa antes de pasarla a la siguiente?

Si la respuesta indica, por ejemplo, paquetes de unas 150 docenas (B ≈ 4 para una
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
