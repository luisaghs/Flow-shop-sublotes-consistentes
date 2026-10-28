# Fase 2 — Validación del modelo matemático con instancias pequeñas

Script: `fase2/validacion_milp.py` · Resultados: `fase2/salida_validacion/`

## 1. Propósito

La instancia real (10 órdenes, 100 sublotes, 36 máquinas) no se puede resolver de
forma exacta. Por eso el MILP se valida con instancias pequeñas, construidas con
los **tiempos reales** de `BD_HFS.xlsx`, para responder tres preguntas:

1. **¿El MILP está bien formulado?** Sus soluciones óptimas deben cumplir todas las
   restricciones del sistema, revisadas con un verificador independiente.
2. **¿El AG representa el mismo problema?** El AG y el MILP deben calcular los
   mismos tiempos y la misma tardanza para una misma programación.
3. **¿Qué tan buenas son las soluciones del AG?** Se mide la brecha frente al
   óptimo demostrado y se compara el tiempo de cómputo de los dos métodos.

## 2. Procedimiento

1. **Instancias.** Se toman 3 a 5 órdenes con referencias reales, cantidades
   reducidas (5 a 8 docenas) y un subconjunto de las máquinas de cada etapa. En
   ensamble siempre hay máquinas de grupos con velocidades distintas (M5 lenta,
   M12 intermedia, M16 rápida), y J1 y J4 son la misma referencia (C01), para
   probar que el alistamiento solo se aplica cuando cambia la referencia.
2. **MILP.** Cada instancia se resuelve con HiGHS (solver libre) desde PuLP, con
   dos formulaciones:
   - **F1**: la formulación del documento (antecesor inmediato, sección 3);
   - **F2**: una formulación equivalente con variables de precedencia general
     (sección 3.1), que usa muchas menos variables binarias y sirve para obtener
     óptimos de referencia.

   El objetivo lexicográfico se resuelve en dos fases: (a) min ΣT_j;
   (b) min C_max sujeto a ΣT_j ≤ ΣT_j*. Límite de 600 s por fase. Las
   instancias se corrieron de 4 en 4 en paralelo, en un equipo de 4 núcleos.
3. **Verificación.** La solución del MILP se revisa con un verificador
   independiente: suma de sublotes, tamaño mínimo, una máquina por sublote y
   etapa, duración, liberación, precedencia entre etapas, no solapamiento y
   alistamiento en troquelado.
4. **AG.** Se corre el código del AG sin cambios (`final_sc_hfsagls_S2_4.py`,
   parámetros actuales) sobre la misma instancia, con **10 semillas**.
5. **Comparación cruzada.** Los tamaños y secuencias óptimos del MILP se pasan por
   el decodificador del AG.

### Instancias

| Instancia | Grupo | Órdenes | B̄ | Sublotes | Máquinas por etapa (T-E-C-V) | d_j (h) |
|---|---|---|---|---|---|---|
| I1 | Pequeña | J1–J4 | 1 | 4 | 2-3-2-1 (B) | 9, 7, 8, 12 |
| I2 | Pequeña | J1–J5 | 1 | 5 | 2-3-2-1 (B) | 9, 7, 8, 12, 14 |
| I3 | Pequeña | J1–J3 | 2 | 6 | 2-2-1-1 (A) | 15, 12, 14 |
| I4 | Pequeña | J1–J3 | 2 | 6 | 2-3-2-1 (B) | 9, 7, 8 |
| I5 | Pequeña | J1–J4 | 2 | 8 | 2-2-1-1 (A) | 15, 12, 14, 20 |
| I6 | Mediana | J1–J4 | 2 | 8 | 2-3-2-1 (B) | 9, 7, 8, 12 |
| I7 | Mediana | J1–J3 | 3 | 9 | 2-2-1-1 (A) | 15, 12, 14 |
| I8 | Mediana | J1–J4 | 3 | 12 | 2-3-2-1 (B) | 9, 7, 8, 12 |
| I9 | Mediana | J1–J5 | 3 | 15 | 2-3-2-1 (B) | 9, 7, 8, 12, 14 |

- Máquinas (A): M1, M2 · M5, M16 · M20 · M29.
- Máquinas (B): M1, M2 · M5, M12, M16 · M20, M21 · M29.
- Órdenes: J1 = C01 (8 docenas, r = 0), J2 = V03 (6, r = 0), J3 = C04 (5, r = 2),
  J4 = C01 (7, r = 3), J5 = V02 (6, r = 5).
- Con más máquinas (B) se usan fechas más ajustadas para que el óptimo tenga
  tardanza positiva y la instancia distinga entre métodos.
- I1 e I2 son las mismas órdenes de I6 e I9 pero **sin dividir en sublotes**
  (B̄ = 1). Comparándolas se ve el efecto del lot streaming.
- Los libros de Excel de cada instancia quedan en
  `fase2/salida_validacion/I*.xlsx`, con el formato de `BD_HFS.xlsx`.

## 3. Formulación usada (con las correcciones de la guía)

Notación: i = (j, b) ∈ N sublotes; 0 = inicio de secuencia; s ∈ S etapas
(s = 1 troquelado, |S| = 4); m ∈ M_s máquinas; a_jm en h/docena; σ = 4,98/60 h.

**Variables:** x_jb ∈ ℤ⁺ (docenas), y_ism ∈ {0,1}, z_ii'sm ∈ {0,1}, S_is, C_is,
T_j, C_max ≥ 0.

Las expresiones están en formato LaTeX, que el editor de ecuaciones de Word acepta.

$$\operatorname{lex\,min}\Big(\textstyle\sum_{j\in J} T_j,\; C_{\max}\Big) \tag{1}$$

$$\textstyle\sum_{b=1}^{B_j} x_{jb} = Q_j \qquad \forall j \tag{2}$$

$$x_{jb} \ge q^{\min} \qquad \forall j,\, b \tag{3}$$

$$\textstyle\sum_{m\in M_s} y_{ism} = 1 \qquad \forall i,\, s \tag{4}$$

$$C_{is} \ge S_{is} + a_{jm}\,x_{jb} - H\,(1-y_{ism}) \qquad \forall i=(j,b),\, s,\, m\in M_s \tag{5}$$

$$S_{i1} \ge r_j \qquad \forall i=(j,b) \tag{6}$$

$$S_{i,s+1} \ge C_{is} \qquad \forall i,\, s<|S| \tag{7}$$

$$\textstyle\sum_{i\in N\cup\{0\},\, i\ne i'} z_{ii'sm} = y_{i'sm} \qquad \forall s,\, m\in M_s,\, i' \tag{8}$$

$$\textstyle\sum_{i'\in N,\, i'\ne i} z_{ii'sm} \le y_{ism} \qquad \forall s,\, m\in M_s,\, i \tag{9}$$

$$\textstyle\sum_{i'\in N} z_{0i'sm} \le 1 \qquad \forall s,\, m\in M_s \tag{10}$$

$$S_{i'1} \ge C_{i1} + \sigma_{ii'} - H\,(1-z_{ii'1m}) \qquad \forall m\in M_1,\, i\ne i' \tag{11}$$

$$S_{i'1} \ge \sigma\, z_{0i'1m} \qquad \forall m\in M_1,\, i' \tag{12}$$

$$S_{i's} \ge C_{is} - H\,(1-z_{ii'sm}) \qquad \forall s\ge 2,\, m\in M_s,\, i\ne i' \tag{13}$$

$$T_j \ge C_{(j,b),|S|} - d_j \qquad \forall j,\, b \tag{14}$$

$$C_{\max} \ge C_{i,|S|} \qquad \forall i \tag{15}$$

con σ_ii' = σ si p_j ≠ p_j' y 0 en caso contrario.

### 3.1 Formulación equivalente F2 (precedencia general)

Reemplaza las variables z_ii'sm y las restricciones (8)–(13) por una variable
u_ii's ∈ {0,1} por cada par de sublotes i < i' y etapa s
(u = 1 si i va antes que i' cuando comparten máquina):

$$S_{i's} \ge C_{is} + \sigma_{ii'}^{s} - H\,(3 - u_{ii's} - y_{ism} - y_{i'sm}) \qquad \forall i<i',\, s,\, m\in M_s \tag{8'}$$

$$S_{is} \ge C_{i's} + \sigma_{i'i}^{s} - H\,(2 + u_{ii's} - y_{ism} - y_{i'sm}) \qquad \forall i<i',\, s,\, m\in M_s \tag{9'}$$

$$S_{i1} \ge \sigma \qquad \forall i \tag{10'}$$

con σ^s_ii' = σ_ii' en troquelado y 0 en las demás etapas. Es exacta porque el
alistamiento cumple la desigualdad triangular: si i va antes que k en la misma
máquina (aunque no sea inmediatamente) y sus referencias son distintas, entre los
dos hay al menos un cambio de referencia. Por eso S_k ≥ C_i + σ siempre se cumple
en la programación real. La restricción (10') basta para el montaje inicial,
porque los sublotes que no son primeros empiezan aún más tarde.

En el documento la formulación principal sigue siendo F1. F2 se puede mencionar
como herramienta de validación, y sirve como evidencia de que el modelo está
bien planteado: dos formulaciones distintas llegan al mismo óptimo.

### 3.2 Refuerzos del modelo

Ninguno cambia el óptimo; solo aceleran el solver.

- **Cota del horizonte.** Si una solución factible conocida (la mejor regla de
  despacho) tiene tardanza total ΣT⁰, en el óptimo ningún sublote termina después
  de máx_j d_j + ΣT⁰. Con esa cota se define C_is ≤ máx_j d_j + ΣT⁰ y una H mucho
  menor. En I3 el tiempo de F1 bajó de 384 s a ~120 s.
- **Ruptura de simetría.** Los sublotes de una orden son intercambiables, así que
  se exige x_jb ≥ x_j,b+1.
- **Desigualdad válida.** C_is ≥ S_is + mín_m a_jm · x_jb.

## 4. Resultados

### 4.1 Tabla general

ΣT_j y C_max en horas; entre paréntesis, segundos de cómputo. "Óptimo" significa
que HiGHS demostró la optimalidad de las dos fases dentro del límite de 600 s por
fase. "AG ≤ MILP" cuenta en cuántas de las 10 réplicas el AG obtuvo una ΣT_j igual
o menor que la mejor solución del MILP.

| Inst. | Sublotes | F1 (documento): ΣT_j / C_max | F2: ΣT_j / C_max | Mejor regla (EDD) ΣT_j | AG mejor: ΣT_j / C_max | AG promedio ΣT_j | AG ≤ MILP | AG (s) |
|---|---|---|---|---|---|---|---|---|
| I1 | 4 (B̄ = 1) | 28,190 / 19,836 · óptimo (1) | 28,190 / 19,836 · óptimo (2) | 30,439 | 28,190 / 19,836 | 28,306 | 7/10 | 0,9 |
| I2 | 5 (B̄ = 1) | 34,374 / 21,794 · óptimo (21) | 34,374 / 21,794 · óptimo (4) | 37,635 | 34,374 / 21,794 | 34,428 | 9/10 | 1,1 |
| I3 | 6 (B̄ = 2) | 0,955 / 15,955 · óptimo (121) | 0,955 / 15,955 · óptimo (4) | 2,067 | 0,955 / 15,955 | 1,169 | 4/10 | 1,4 |
| I4 | 6 (B̄ = 2) | 3,861 / 12,082 · óptimo (168) | 3,861 / 12,082 · óptimo (60) | 4,149 | 3,861 / 12,082 | 3,861 | 10/10 | 1,3 |
| I5 | 8 (B̄ = 2) | 1,113 / 20,158 · límite (1.144) | 1,113 / 20,158 · óptimo (34) | 3,325 | 1,113 / 20,158 | 1,247 | 7/10 | 2,3 |
| I6 | 8 (B̄ = 2) | 6,379 / 13,983 · límite (1.200) | 5,928 / 13,942 · límite (807) | 6,682 | 5,928 / 13,942 | 6,080 | 7/10 | 2,1 |
| I7 | 9 (B̄ = 3) | 0,000 / 14,747 · límite (723) | 0,000 / 14,399 · óptimo (587) | 0,404 | 0,000 / 14,496 | 0,000 | 10/10 | 2,9 |
| I8 | 12 (B̄ = 3) | sin solución factible (600) | 3,142 / 12,780 · límite (1.200) | 2,341 | 1,214 / 12,114 | 1,336 | 10/10 | 3,8 |
| I9 | 15 (B̄ = 3) | sin solución factible (600) | 8,077 / 15,847 · límite (1.200) | 2,666 | 1,214 / 13,857 | 1,468 | 10/10 | 4,0 |

Detalle por réplica y por instancia: `fase2/salida_validacion/log_I*.txt` y
`resultados_validacion_todas.csv`. Programación de la mejor solución del MILP:
`programacion_milp_I*.csv`.

### 4.2 Tamaño del modelo F1

| Sublotes | 4 | 5 | 6 | 8 | 9 | 12 | 15 | 100 (instancia real) |
|---|---|---|---|---|---|---|---|---|
| Variables binarias F1 | 160 | 240 | 252–336 | 432–576 | 540 | 1.248 | 1.920 | ≈ 363.600 |
| Resultado en 10 min | óptimo | óptimo | óptimo | límite | límite | sin solución | sin solución | — |

### 4.3 Verificación cruzada con el decodificador del AG

Los tamaños y secuencias de la mejor solución del MILP se pasaron por el
decodificador del AG:

- **I1, I2, I6 e I7:** el decodificador reproduce exactamente la misma ΣT_j y el
  mismo C_max del MILP. Los dos modelos calculan los tiempos de proceso, la
  precedencia entre etapas, la liberación y el alistamiento de la misma forma.
- **I3, I4 e I5:** el decodificador da un valor algo peor con esas secuencias
  (por ejemplo, I3: 1,279 frente a 0,955 h). La causa es la regla ECT. En el
  óptimo de I3, el MILP envía el sublote J2-2 a la máquina lenta M5 de ensamble
  para dejar libre la rápida M16, que J2-1 necesita poco después. El decodificador
  siempre asigna la máquina que termina primero y no puede "reservar" una
  máquina. Aun así, el AG alcanza el valor óptimo en esas tres instancias con
  otros cromosomas.

### 4.4 Figuras

- `fase2/salida_validacion/gantt_milp_vs_ag_I3.png`
- `fase2/salida_validacion/gantt_milp_vs_ag_I5.png`

Cada figura muestra el Gantt óptimo del MILP (arriba) y el mejor del AG (abajo),
con los alistamientos rayados y las fechas de entrega como líneas punteadas.
Sirven como figura del documento.

## 5. Interpretación (texto sugerido para el documento)

**1. El modelo matemático está bien formulado.** Las soluciones del MILP en las
nueve instancias pasaron el verificador independiente sin ninguna violación. En
las cuatro instancias donde la formulación F1 demostró el óptimo (I1 a I4), la
formulación F2, construida con otra lógica de secuenciación, llegó exactamente al
mismo óptimo. En I5, F2 demostró el óptimo y F1 encontró esa misma solución,
aunque no alcanzó a demostrarlo.

**2. El AG y el MILP representan el mismo problema.** Al decodificar la solución
del MILP con el decodificador del AG se obtienen los mismos tiempos en las
instancias donde la asignación coincide con la regla ECT. Las diferencias en
I3–I5 se explican por esa regla y no por un error de cálculo.

**3. El AG encuentra soluciones óptimas o cercanas.**

- En las seis instancias con ΣT_j óptima demostrada (I1–I5 e I7), la mejor de las
  10 réplicas del AG alcanzó la tardanza óptima en todos los casos.
- En total, 47 de 60 réplicas (78 %) llegaron al óptimo de ΣT_j. La mayor
  diferencia promedio fue de 0,21 h (I3).
- El único caso en que el AG no alcanzó el óptimo lexicográfico fue el C_max de
  I7: 14,496 frente a 14,399 h, es decir, 0,7 % por encima con la tardanza en cero.
- El decodificador sí puede representar esa programación óptima, así que la
  diferencia corresponde a la búsqueda. Esto apoya la calibración propuesta.

**4. El método exacto no escala; el AG sí.**

- Con la formulación del documento, el número de binarias crece de forma
  cuadrática con los sublotes.
- El MILP demostró el óptimo hasta 6 sublotes. Con 12 y 15 sublotes, HiGHS no
  encontró ni una solución factible en 10 minutos.
- En las instancias medianas (I6, I8, I9), el AG igualó o superó en segundos la
  mejor solución que el solver obtuvo en 20 minutos (I9: 1,214 frente a 8,077 h).
- La instancia real tiene 100 sublotes y unas 363.600 binarias. Esto justifica con
  evidencia propia el uso del algoritmo genético.

**5. Efecto del lot streaming.** I1 e I6 son las mismas cuatro órdenes:

| Configuración | ΣT_j |
|---|---|
| Sin dividir (I1) | 28,19 h (óptimo) |
| Dos sublotes por orden (I6) | 5,93 h |
| Tres sublotes por orden (I8) | 1,21 h |

Con cinco órdenes, la tardanza baja de 34,37 h (I2) a 1,21 h (I9). Esto es
coherente con lo que reporta la literatura sobre sublotes consistentes (Gürsoy
Yılmaz y Yılmaz, 2022) y anticipa la discusión de la Fase 3.

**Párrafo sugerido para el documento:**

> Para validar el modelo matemático se construyeron nueve instancias de prueba
> con los tiempos estándar de la empresa, de 4 a 15 sublotes. Se resolvieron con
> el solver HiGHS en dos formulaciones equivalentes: la propuesta, de antecesor
> inmediato, y una de precedencia general. Todas las soluciones cumplieron las
> restricciones del sistema, y las dos formulaciones coincidieron en el óptimo
> en todas las instancias donde ambas lo demostraron. Sobre las mismas
> instancias, el algoritmo genético alcanzó la tardanza óptima en su mejor
> réplica en los seis casos con óptimo conocido (78 % de las réplicas), en menos
> de 3 segundos por corrida. En cambio, el modelo exacto dejó de encontrar
> soluciones factibles en 10 minutos a partir de 12 sublotes. Estos resultados
> confirman que el modelo representa correctamente el sistema y que el
> algoritmo genético es un método adecuado para resolverlo a la escala real.

## 6. Cómo reproducirlo

```bash
pip install pulp highspy pandas openpyxl matplotlib
cd fase2
python validacion_milp.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx          # todas
python validacion_milp.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx I1,I2    # algunas
```

El script es compatible con PuLP 2.x (la versión usual en Colab) y con PuLP 4.x.
Las instancias, el límite de tiempo y las semillas se cambian al inicio del archivo
(`INSTANCIAS`, `LIMITE_TIEMPO_S`, `SEMILLAS_AG`).

## Nota: corrida del AG con los parámetros calibrados

Las tablas anteriores muestran el AG con la parada original (50 generaciones sin
mejora). Con el modelo final (100 generaciones sin mejora) la mejor solución del AG
es idéntica en las nueve instancias y las conclusiones no cambian. Solo varían: I6,
promedio 6,020 h y 8/10 réplicas en la referencia; I9, promedio 1,457 h; y los tiempos
(3–11 s por corrida). Detalle en `fase2/salida_validacion/ag_parametros_calibrados.txt`.
Los documentos del trabajo de grado usan estos valores.
