# Fase 2 — Guía para el desarrollo metodológico

**Objetivo específico 2:** *Construir un modelo matemático definiendo los operadores
adecuados para representar y resolver el problema de programación en el entorno
de producción Flow shop híbrido.*

El objetivo tiene dos verbos que conviene separar en la redacción:

| Parte del objetivo | Qué la cumple | Estado en el borrador |
|---|---|---|
| **Representar** el problema | Modelo matemático MILP (conjuntos, parámetros, variables, función objetivo, restricciones) | Avanzado, necesita correcciones (sección 2.2) |
| **Resolver** el problema con "operadores adecuados" | Algoritmo genético: codificación, decodificación, aptitud, población inicial, selección, cruce, mutación, parada | Implementado en el código, falta redactarlo |
| Demostrar que lo construido es correcto y está bien ajustado | Verificación, validación y calibración | Falta |

La Fase 2 debería terminar con un **método de solución verificado y calibrado** y
una solución de ejemplo. La comparación contra el sistema actual (indicadores,
pruebas estadísticas, mejora porcentual) es materia de la Fase 3.

---

## 1. Estructura propuesta para la Fase 2

1. **Clasificación del problema** (ya existe; completar el campo β).
2. **Modelo matemático (MILP)**: supuestos de la división en sublotes, conjuntos,
   parámetros, variables, función objetivo y restricciones explicadas.
3. **Complejidad del modelo y justificación del algoritmo genético.**
4. **Diseño del algoritmo genético**
   1. Representación de la solución (cromosoma de dos niveles)
   2. Decodificación (construcción de la programación)
   3. Función de aptitud
   4. Población inicial y reglas de despacho
   5. Selección
   6. Cruce
   7. Mutación
   8. Elitismo, reemplazo y criterio de parada
   9. Diagrama de flujo del algoritmo
5. **Implementación computacional.**
6. **Verificación y validación del modelo.**
7. **Definición del número de sublotes.**
8. **Calibración de los parámetros del algoritmo genético.**
9. **Solución obtenida** (Gantt, tamaños de sublotes, indicadores), como cierre de la fase.

A continuación se detalla qué escribir en cada sección.

---

## 2. Qué escribir en cada sección

### 2.1 Clasificación del problema

El borrador define α y γ, pero deja β sin llenar. Propuesta, con la notación de
Ruiz y Vázquez-Rodríguez (2010):

> FH4, (P4, R15, P9, P8) | r_j, lot streaming con sublotes consistentes,
> S_sd (etapa 1, alistamiento anticipatorio) | lex(ΣT_j, C_max)

- **r_j**: fechas de liberación.
- **Sublotes consistentes**: cada orden se divide en B_j sublotes que conservan su
  tamaño en todas las etapas (Gürsoy Yılmaz y Yılmaz, 2022).
- **S_sd en troquelado**: alistamiento que depende de la secuencia (solo hay
  alistamiento si cambia la referencia). Es *anticipatorio* porque se puede hacer
  mientras la máquina espera el sublote (Allahverdi et al., 2008).
- **γ**: objetivo lexicográfico, primero ΣT_j y como desempate C_max.

Corregir de paso en la Fase 1: la cuarta etapa es **P8**, no "(P4)", y el párrafo
que dice "Troquelado, ensamble, costura y volteado cuentan con máquinas paralelas
idénticas" no debe incluir ensamble.

### 2.2 Modelo matemático (MILP): correcciones al borrador

El planteamiento sigue bien a Gürsoy Yılmaz y Yılmaz (2022). Para cerrarlo:

1. **Párrafo introductorio.** Hoy dice que el MILP "parte de un estado inicial
   determinado por heurísticas" y que el AG "realiza una búsqueda local". Separar
   las dos cosas:
   - el MILP es la **representación formal** del problema (y sirve para resolver
     de forma exacta instancias pequeñas);
   - el AG es el **método de solución** para la instancia real. Es una búsqueda
     poblacional global, no local. Las reglas de despacho solo **siembran** la
     población inicial.
   - El código usa FIFO, EDD, SPT, LPT, MST y CR. LIFO no está implementada:
     quitarla del texto o agregarla al código.
2. **Parámetro r_j.** Dice "horas acumuladas al final del día de entrega"; debe
   decir "horas acumuladas al **inicio del día de liberación**" (así está en la
   Fase 1 y en el código).
3. **Falta la tabla de variables** (el título dice "Conjuntos, parámetros y
   variables"):

   | Variable | Tipo | Significado |
   |---|---|---|
   | x_jb | Entera ≥ 0 | Tamaño del sublote b de la orden j [docenas] |
   | y_ism | Binaria | 1 si el sublote i se procesa en la máquina m de la etapa s |
   | z_ii'sm | Binaria | 1 si i precede inmediatamente a i' en la máquina m de la etapa s (i = 0: inicio) |
   | S_is, C_is | Continua ≥ 0 | Inicio y fin del sublote i en la etapa s [h] |
   | T_j | Continua ≥ 0 | Tardanza de la orden j [h] |
   | C_max | Continua ≥ 0 | Makespan [h] |

4. **Restricciones de secuencia.**
   - Predecesor: la suma debe incluir el sublote ficticio 0:
     Σ_{i ∈ N ∪ {0}, i ≠ i'} z_ii'sm = y_i'sm.
   - Sucesor: Σ_{i'} z_ii'sm ≤ y_**i**sm (hoy aparece y_i'sm).
   - Texto: "cada máquina tiene **a lo sumo** un primer sublote" (la ecuación usa
     ≤ 1; el texto dice "al menos").
5. **No solapamiento en etapas ≥ 2.** Está escrita con S_(i'1) y m ∈ M₁; debe ser
   S_i's ≥ C_is − H(1 − z_ii'sm), ∀ s ≥ 2, m ∈ M_s.
6. **Restricción 6 de la Fase 1 (respetar el horizonte).** Como se permite la
   tardanza, el modelo no puede exigir que todo termine antes de 672 h (la regla
   EDD termina en 817 h). Aclarar que H es solo la constante grande del big-M y
   que el horizonte define el calendario, no una restricción dura.
7. **Numerar las ecuaciones** (hoy aparecen "()") y explicar cada bloque con una
   frase, como ya se hizo con la de tiempo de proceso.

### 2.3 Complejidad del modelo y justificación del AG

Conviene cuantificar el tamaño del MILP para la instancia real. Esto justifica con
números por qué se usa una metaheurística:

- 10 órdenes × 10 sublotes = **N = 100 sublotes**; 36 máquinas.
- y_ism: 100 × 36 = **3.600 binarias**.
- z_ii'sm: 36 máquinas × (100 × 99 + 100) = **360.000 binarias**.
- Unas **356.000 restricciones big-M** solo de no solapamiento.

Un modelo de este tamaño con big-M no se resuelve de forma exacta en un tiempo
razonable. Esto enlaza con lo que ya dice el marco teórico (Haq et al., 2010; el
HFS es NP-hard).

### 2.4 Diseño del algoritmo genético

Esta es la parte central de "definir los operadores adecuados". Para cada
operador: **qué hace, cómo se aplica (con un ejemplo pequeño) y por qué se eligió**.
Todo está ya en el código (`final_sc_hfsagls_S2_4.py`):

| Componente | Lo que hace el código | Ejemplo o figura sugerida |
|---|---|---|
| Representación | Cromosoma de **dos niveles**. Nivel 1: proporciones de los tamaños de sublote de cada orden. Nivel 2: secuencia de los 100 sublotes en cada una de las 4 etapas | Cromosoma de 2 órdenes × 3 sublotes |
| Paso a docenas | Proporciones → docenas enteras, mínimo 1 docena, suma = Q_j (método del mayor residuo) | J09 (210 docenas) en 10 sublotes |
| Asignación de máquina | No va en el cromosoma: el decodificador elige la máquina con **menor tiempo de terminación (ECT)** | Comparar ECT entre M5 (lenta) y M16 (rápida) en ensamble |
| Decodificación | Esquema serial etapa por etapa. Troquelado: el sublote va después del último de la máquina y se suma el alistamiento si cambia la referencia. Etapas 2 a 4: el sublote ocupa el primer hueco libre. Cada sublote pasa a la etapa siguiente al terminar | Pseudocódigo + mini Gantt |
| Aptitud | Lexicográfica: (ΣT_j, C_max) | — |
| Población inicial | 150 individuos: 149 aleatorios + 1 semilla (la mejor regla de despacho con sublotes iguales) | Tabla de las 6 reglas |
| Selección | Torneo de tamaño 3 | — |
| Cruce nivel 1 | Aritmético: λ·p1 + (1 − λ)·p2, con λ aleatorio por orden; el segundo hijo usa 1 − λ | Ejemplo numérico |
| Cruce nivel 2 | LOX (cruce de orden lineal) en cada etapa | Figura con padre 1, padre 2 e hijo |
| Mutación nivel 2 | Intercambio de dos sublotes en la secuencia de una etapa (prob. 0,30) | — |
| Mutación nivel 1 | Perturbación normal (σ = 0,15) de la proporción de un sublote y renormalización (prob. 0,40 por orden) | — |
| Elitismo y parada | Pasa el mejor individuo; parada a las 50 generaciones sin mejora o a las 1.000 | — |

Puntos a explicar en el texto:

- **Diferencias con Gürsoy Yılmaz y Yılmaz (2022).** El artículo usa un cromosoma
  de tres niveles, con la máquina en el tercero. Aquí la máquina la decide la regla
  ECT. Justificación: el espacio de búsqueda es más pequeño y no se generan
  asignaciones dominadas, como poner un sublote en una máquina lenta de ensamble
  cuando hay una rápida libre. Ruiz y Maroto (2006) usan la misma idea en HFS.
  (El README del repositorio todavía describe la versión de tres niveles;
  actualizarlo.)
- **Por qué LOX:** el nivel 2 es una permutación. LOX produce siempre secuencias
  válidas (sin repetidos ni faltantes) y conserva el orden relativo de los padres
  (Falkenauer y Bouffouix, 1991).
- **Por qué cruce aritmético en el nivel 1:** las proporciones son continuas y deben
  sumar 1; la combinación convexa conserva esa propiedad (Michalewicz, 1996).
- **Alistamiento anticipatorio:** explicar que el decodificador calcula el inicio
  como máx(libre + alistamiento, llegada del sublote), igual que el MILP.
- **Diagrama de flujo del AG:** inicialización → evaluación → (selección → cruce →
  mutación → evaluación → elitismo) → ¿criterio de parada? → mejor solución.

Las referencias de esta sección son sugerencias: verificar las citas antes de usarlas.

### 2.5 Implementación computacional

- Lenguaje y librerías: Python 3, pandas (lectura del Excel), matplotlib (Gantt).
- Datos de entrada: `BD_HFS.xlsx` con tres hojas (tiempos de procesamiento por
  referencia y máquina, trabajos, calendario laboral). Una tabla con las columnas.
- Módulos del programa: lectura de datos → reglas de despacho → AG → reportes y Gantt.
- Equipo usado y tiempos: en una prueba, cada evaluación de un cromosoma tomó
  ~2,4 ms y una corrida completa del AG entre 2 y 4 minutos.

### 2.6 Verificación y validación

Esta sección es la que suele faltar en los trabajos de grado y la que más pregunta
el jurado: ¿cómo saben que el modelo hace lo que dicen?

1. **Verificación del decodificador frente a las restricciones del MILP.** El
   script `fase2/verificar_factibilidad.py` revisa cada programación: suma de
   sublotes = Q_j, tamaño mínimo, una máquina por sublote y etapa, duración =
   a_jm · x_jb, inicio ≥ r_j, precedencia entre etapas, no solapamiento y
   alistamientos en troquelado. Resultado de la prueba: **0 violaciones en 200
   cromosomas aleatorios** y en las programaciones de las reglas de despacho.
   Esto demuestra que las soluciones del AG son factibles para el MILP.
2. **Validación del MILP con instancias reducidas (hecha).** El MILP está
   programado en `fase2/validacion_milp.py` (PuLP + HiGHS) y se resolvió para
   cinco instancias pequeñas con los tiempos reales. Se comparó con el AG sobre
   las mismas instancias. Procedimiento, formulación corregida y resultados en
   [`docs/fase2_validacion_milp.md`](fase2_validacion_milp.md).
3. **Traza manual.** Calcular a mano los tiempos de 2 o 3 sublotes de un Gantt y
   compararlos con la salida del programa.
4. **Curva de convergencia** de la mejor ΣT_j y del promedio de la población por
   generación (el código ya guarda el historial).
5. **Validación frente a la realidad (prepara la Fase 3).** El planteamiento dice
   que hoy hay un **45 % de incumplimiento**. Al simular la práctica actual (FIFO)
   el resultado depende mucho de cómo se represente la división del trabajo:

   | Escenario simulado | ΣT_j (h) | Órdenes tardías |
   |---|---|---|
   | FIFO, cada orden como un solo lote (B = 1) | 8.490 | 10 de 10 |
   | FIFO, 10 sublotes iguales | 242 | 2 de 10 |

   Ninguno reproduce el 45 %. Antes de la Fase 3 hay que **documentar cómo divide
   y mueve hoy la empresa las órdenes entre puestos** (paquetes, docenas,
   tareas) y comprobar que la simulación del sistema actual se acerca al
   desempeño histórico. Si no, la comparación de la Fase 3 queda débil.

### 2.7 Definición del número de sublotes (B̄)

El borrador fija B̄ = 10 sin justificarlo, y es la decisión que **más pesa** en el
resultado. ΣT_j de las reglas de despacho según el número de sublotes:

| B̄ | FIFO | EDD | CR | SPT |
|---|---|---|---|---|
| 1 | 8.490 | 8.316 | 8.741 | 8.353 |
| 2 | 3.051 | 3.203 | 3.743 | 2.939 |
| 5 | 704 | 495 | 798 | 809 |
| 10 | 242 | 145 | 244 | 254 |
| 20 | 141 | 17 | 131 | 66 |
| 40 | 89 | **0** | 99 | **0** |

Con 40 sublotes una regla simple como EDD ya elimina la tardanza. Por eso:

- B̄ y q_min deben salir de la **operación real**: tamaño mínimo práctico de
  transferencia entre puestos, manejo de paquetes, control de producción. No es
  conveniente elegirlos para que el resultado se vea mejor.
- Presentar un **análisis de sensibilidad** de B̄ (por ejemplo 5, 10, 20) con el AG
  y con las reglas. Muestra en qué rango el AG aporta valor frente a una regla
  simple, y es un aporte práctico para la empresa.

### 2.8 Calibración de parámetros del AG

**Hecha:** procedimiento, resultados y texto sugerido en
[`docs/fase2_calibracion.md`](fase2_calibracion.md) (script
`fase2/calibracion_ag.py`). Se confirmó la configuración del código (población
150, cruce 0,9, mutación 0,5) y se recomienda subir la parada a 100 generaciones
sin mejora. La propuesta original era:

- **Diseño factorial**, por ejemplo 3 factores × 3 niveles = 27 combinaciones:
  población (50, 100, 150), probabilidad de cruce (0,7; 0,8; 0,9) y probabilidad
  de mutación (0,1; 0,3; 0,5). Si el tiempo no alcanza, usar un arreglo ortogonal
  de Taguchi L9.
- **Réplicas:** 5 a 10 por combinación, con semillas distintas.
- **Análisis:** ANOVA (o Kruskal-Wallis si no hay normalidad) sobre la variable de
  respuesta, y gráficas de efectos principales (Ruiz, Maroto y Alcaraz, 2006).
- **Variable de respuesta.** Ojo: en la instancia real el AG llega a ΣT_j = 0 en
  la mayoría de las corridas (abajo), así que ΣT_j sola no distingue entre
  configuraciones. Usar una respuesta combinada, por ejemplo la desviación
  porcentual relativa (RPD) de C_max entre corridas con ΣT_j = 0, o
  ΣT_j · 1000 + C_max.
- **Probar también el criterio de parada** (50 frente a 100 generaciones sin
  mejora): la corrida con semilla 2 se detuvo en la generación 243 con
  ΣT_j = 3,32 h, mientras que otras siguieron mejorando hasta la 500.
- **Presupuesto de tiempo:** 27 × 5 = 135 corridas × ~3 min ≈ 7 h en un núcleo,
  menos de 2 h si se corren 4 en paralelo.

### 2.9 Solución obtenida (cierre de la fase)

Con los parámetros calibrados: tabla de tamaños de sublotes, tabla por orden
(d_j, C_j, T_j, E_j), indicadores globales, Gantt y curva de convergencia.
Reportar **varias corridas** (mejor, promedio, desviación estándar), no una sola.

---

## 3. Resultados de la prueba con los datos actuales

Corrida del código entregado (`final_sc_hfsagls_S2_4.py`) con `BD_HFS.xlsx`
y los parámetros actuales:

| Método | ΣT_j (h) | C_max (h) | Órdenes tardías |
|---|---|---|---|
| Mejor regla (EDD, 10 sublotes iguales) | 145,00 | 817,00 | 1 |
| AG, semilla 42 (la del código) | 3,30 | 675,30 | 1 |
| AG, semilla 1 | 0,00 | 648,35 | 0 |
| AG, semilla 2 | 3,32 | 675,32 | 1 |
| AG, semilla 3 | 0,00 | 650,05 | 0 |
| AG, semilla 4 | 0,00 | 651,90 | 0 |

Conclusiones para la redacción:

- El AG mejora mucho a las reglas de despacho (de 145 h a 0–3,3 h).
- El resultado depende de la semilla: hay que reportar **varias réplicas**
  (30 es lo usual para la Fase 3) con estadísticos, no la corrida de la semilla 42.
- Como la tardanza se puede eliminar, el desempate por C_max y los indicadores
  secundarios (adelanto, tiempo de flujo, alistamientos) ganan importancia en la
  discusión.

---

## 4. Límite entre la Fase 2 y la Fase 3

| Fase 2 (objetivo 2) | Fase 3 (objetivo 3) |
|---|---|
| Modelo MILP, operadores del AG, implementación | Representación del sistema actual (FIFO + práctica real de la empresa) |
| Verificación de factibilidad y validación con instancia pequeña | 30 réplicas del AG frente al sistema actual y las demás reglas |
| Definición de B̄ y calibración de parámetros | Indicadores: ΣT_j, número de tardías, T_max, C_max, ΣE_j, flujo medio, utilización, alistamientos |
| Solución de ejemplo con los parámetros calibrados | Pruebas estadísticas (por ejemplo Wilcoxon), % de mejora, análisis de sensibilidad y discusión |
