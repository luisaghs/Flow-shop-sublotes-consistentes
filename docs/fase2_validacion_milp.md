# Fase 2 — Validación del modelo matemático con instancias pequeñas

Script: `fase2/validacion_milp.py` · Resultados: `fase2/salida_validacion/`

## 1. Propósito

La instancia real (10 órdenes, 100 sublotes, 36 máquinas) no se puede resolver de
forma exacta. Por eso el modelo matemático se resuelve en instancias pequeñas,
construidas con los **tiempos reales** de `BD_HFS.xlsx`, para responder tres preguntas:

1. **¿El modelo matemático está bien formulado?**
2. **¿El algoritmo genético encuentra el óptimo?**
3. **¿Hasta qué tamaño sirve el método exacto?**

## 2. Procedimiento

1. **Instancias.** Seis instancias con cinco órdenes de prueba y un mismo
   subconjunto de ocho máquinas: M1 y M2 (troquelado), M5, M12 y M16 (ensamble;
   lenta, intermedia y rápida), M20 y M21 (costura) y M29 (volteado). J1 y J4 son la
   misma referencia (C01), para comprobar que el alistamiento solo se aplica cuando
   cambia la referencia.
2. **Modelo exacto.** Cada instancia se resuelve con HiGHS (solver libre) desde PuLP,
   con la formulación del documento (variables de antecesor inmediato, sección 3).
   El objetivo lexicográfico se resuelve en dos fases: (a) min ΣT_j; (b) min C_max
   sujeto a ΣT_j ≤ ΣT_j*. Límite de 600 s por fase.
3. **Verificación.** La solución del modelo exacto se revisa con un verificador
   independiente: suma de sublotes, tamaño mínimo, una máquina por sublote y etapa,
   duración, liberación, precedencia entre etapas, no solapamiento y alistamiento en
   troquelado.
4. **Algoritmo genético.** Se corre el código del modelo (`final_sc_hfsagls_S2_4.py`,
   parámetros calibrados) sobre la misma instancia, con **10 semillas** (1 a 10).

### Órdenes de prueba

| Orden | Referencia | Docenas | r_j (h) | d_j (h) |
|---|---|---|---|---|
| J1 | C01 | 8 | 0 | 9 |
| J2 | V03 | 6 | 0 | 7 |
| J3 | C04 | 5 | 2 | 8 |
| J4 | C01 | 7 | 3 | 12 |
| J5 | V02 | 6 | 5 | 14 |

### Instancias

| Instancia | Órdenes | Sublotes por orden | Sublotes totales |
|---|---|---|---|
| I1 | J1–J4 | 1 (sin dividir) | 4 |
| I2 | J1–J5 | 1 (sin dividir) | 5 |
| I3 | J1–J3 | 2 | 6 |
| I4 | J1–J4 | 2 | 8 |
| I5 | J1–J4 | 3 | 12 |
| I6 | J1–J5 | 3 | 15 |

## 3. Formulación (la del documento)

Notación: i = (j, b) ∈ N sublotes; 0 = inicio de secuencia; s ∈ S etapas
(s = 1 troquelado, |S| = 4); m ∈ M_s máquinas; a_jm en h/docena; σ = 4,98/60 h.

**Variables:** x_jb ∈ ℤ⁺ (docenas), y_ism ∈ {0,1}, z_ii'sm ∈ {0,1}, S_is, C_is,
T_j, C_max ≥ 0.

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

**Refuerzos** (no cambian el óptimo, solo aceleran el solver): cota del horizonte con la
tardanza de la mejor regla de despacho (C_is ≤ máx_j d_j + ΣT⁰), ruptura de simetría
(x_jb ≥ x_j,b+1) y la desigualdad válida C_is ≥ S_is + mín_m a_jm · x_jb.

## 4. Resultados

ΣT_j y C_max en horas; entre paréntesis, segundos de cómputo del modelo exacto.
«AG ≤ exacta» cuenta en cuántas de las 10 réplicas el algoritmo obtuvo una ΣT_j igual
o menor que la solución exacta.

| Inst. | Sublotes | Binarias | Exacta: ΣT_j / C_max | Estado | Mejor regla ΣT_j | AG mejor: ΣT_j / C_max | AG prom. ΣT_j | AG ≤ exacta | AG (s) |
|---|---|---|---|---|---|---|---|---|---|
| I1 | 4 | 160 | 28,190 / 19,836 | óptima (1) | 30,439 | 28,190 / 19,836 | 28,306 | 7/10 | 1,4 |
| I2 | 5 | 240 | 34,374 / 21,794 | óptima (15) | 37,635 | 34,374 / 21,794 | 34,428 | 9/10 | 1,7 |
| I3 | 6 | 336 | 3,861 / 12,082 | óptima (132) | 4,149 | 3,861 / 12,082 | 3,861 | 10/10 | 1,9 |
| I4 | 8 | 576 | 5,928 / 13,942 | mejor encontrada (1.200) | 6,682 | 5,928 / 13,942 | 6,020 | 8/10 | 2,8 |
| I5 | 12 | 1.248 | — | sin solución (600) | 2,341 | 1,214 / 12,114 | 1,336 | — | 4,3 |
| I6 | 15 | 1.920 | — | sin solución (600) | 2,666 | 1,214 / 13,857 | 1,457 | — | 5,1 |

Detalle por réplica: `fase2/salida_validacion/log_I*.txt` y
`resultados_validacion_todas.csv`. Programación de la solución exacta:
`programacion_milp_I*.csv` (I1 a I4). Figura: `gantt_milp_vs_ag_I3.png`. Corrida de una
hora en I5 e I6: registros del solver `highs_60min_I5.log` y `highs_60min_I6.log`, y
resumen de las soluciones encontradas en `corrida_60min.csv`.

## 5. Interpretación

1. **El modelo está bien formulado.** Ninguna solución del modelo exacto violó las
   restricciones al pasarla por el verificador, y el algoritmo genético, que evalúa sus
   programaciones con una simulación del sistema y no con las ecuaciones del modelo, llegó
   a los mismos óptimos en I1, I2 e I3.
2. **El algoritmo genético encuentra el óptimo.** En las tres instancias con óptimo
   demostrado, la mejor réplica alcanzó la tardanza óptima, y 26 de 30 réplicas la
   alcanzaron; la mayor diferencia promedio fue de 0,12 h (I1).
3. **El método exacto no escala.** Demostró el óptimo hasta 6 sublotes; con 8 alcanzó el
   límite sin demostrarlo y con 12 y 15 no encontró ninguna programación factible en
   10 minutos. El algoritmo resolvió cada instancia en menos de 6 s: en I4 igualó la
   mejor solución del solver (20 minutos) y en I5 e I6 obtuvo 1,214 h de tardanza.
   Con un límite de una hora (solo la fase de tardanza), el modelo encontró su primera
   programación factible para I5 a los 17,6 minutos (15,234 h) y terminó con 4,092 h, sin
   demostrar el óptimo; en I6 no encontró ninguna. La instancia real implicaría unas
   363.600 variables binarias.
4. **Efecto de los sublotes.** Con cuatro órdenes, la tardanza pasa de 28,19 h sin
   dividir (I1) a 5,93 h con dos sublotes (I4) y 1,21 h con tres (I5); con cinco
   órdenes, de 34,37 h (I2) a 1,21 h (I6).

## 6. Cómo reproducirlo

```bash
pip install pulp highspy pandas openpyxl matplotlib
python fase2/validacion_milp.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx          # todas
python fase2/validacion_milp.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx I1,I2    # algunas
python fase2/validacion_milp.py resumen                                       # une los resultados
python fase2/validacion_milp.py largo final_sc_hfsagls_S2_4.py BD_HFS.xlsx I5,I6 3600  # corrida de una hora
```

El script es compatible con PuLP 2.x (la versión usual en Colab) y con PuLP 4.x. Las
instancias, el límite de tiempo y las semillas se cambian al inicio del archivo
(`INSTANCIAS`, `LIMITE_TIEMPO_S`, `SEMILLAS_AG`). La variable de entorno
`SALIDA_VALIDACION` permite guardar los resultados en otra carpeta.
