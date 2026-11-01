# Fase 2 — Calibración de los parámetros del algoritmo genético

Script: `fase2/calibracion_ag.py` · Resultados: `fase2/salida_calibracion/`

## 1. Propósito

El desempeño de un algoritmo genético depende de sus parámetros. Si se fijan
"a ojo", el jurado puede preguntar por qué esos valores y no otros. La calibración
responde con un diseño de experimentos: se prueban combinaciones de parámetros
sobre la instancia real y se elige la mejor con un análisis estadístico (Ruiz,
Maroto y Alcaraz, 2006; Montgomery, 2017).

## 2. Diseño del experimento

### 2.1 Experimento 1: diseño factorial completo 3³

| Factor | Niveles |
|---|---|
| Tamaño de la población | 50, 100, 150 |
| Probabilidad de cruce | 0,7; 0,8; 0,9 |
| Probabilidad de mutación | 0,1; 0,3; 0,5 |

- **27 combinaciones × 5 réplicas = 135 corridas** sobre la instancia real
  (10 órdenes, B̄ = 10, 100 sublotes). La configuración inicial del código
  (150; 0,9; 0,5) es uno de los puntos del diseño, así que queda comparada
  directamente.
- **Parámetros fijos:** torneo de tamaño 3, probabilidad de intercambio en la
  secuencia 0,30, probabilidad de perturbar los tamaños 0,40, desviación de la
  perturbación 0,15, elitismo de un individuo y población inicial sembrada con la
  mejor regla de despacho.
- **Mismo presupuesto de cómputo por corrida:** 30.000 individuos generados
  (población × generaciones): 600 generaciones con población 50, 300 con 100 y
  200 con 150. Si el criterio fuera "generaciones sin mejora", una población
  grande usaría más evaluaciones y la comparación sería injusta.
- **Números aleatorios comunes:** la réplica r usa la misma semilla (1000 + r) en
  las 27 combinaciones. Las diferencias entre combinaciones se deben a los
  parámetros y no al azar de la semilla.

### 2.2 Variable de respuesta

- **Respuesta principal:** la tardanza total ΣT_j (h) de la mejor solución de la
  corrida, que es el objetivo del modelo.
- **Respuesta secundaria:** desviación porcentual relativa del makespan,
  RPD = 100·(C_max − C_max*)/C_max*, con C_max* el mejor makespan entre las
  corridas que lograron la mejor tardanza.
- **Pruebas de rangos** (Kruskal-Wallis, Wilcoxon): se aplican sobre
  Z = 1000·ΣT_j + C_max. Como solo usan el orden de los datos, ordenar por Z
  equivale a ordenar según el objetivo lexicográfico (primero ΣT_j, luego C_max).

### 2.3 Análisis estadístico

1. ANOVA multifactorial con efectos principales e interacciones dobles.
2. Gráfico de medias con intervalos LSD al 95 %: si los intervalos de dos niveles
   no se traslapan, la diferencia es significativa.
3. Supuestos: normalidad de residuos (Shapiro-Wilk) y homogeneidad de varianzas
   (Levene). Si no se cumplen, la conclusión se apoya en Kruskal-Wallis.
4. Comparación pareada por semilla (Wilcoxon) entre la mejor combinación y la
   configuración actual.

### 2.4 Rango de los niveles

Los niveles se tomaron de los valores usuales en la literatura de AG para
programación de la producción. Si la mejor combinación queda en el borde del
rango, no se evalúan niveles fuera de él: se adopta la mejor combinación dentro
del rango y se reconoce como limitación.

### 2.5 Experimento 2: criterio de parada

Con la mejor combinación se compara la parada por 50 y 100 generaciones sin
mejora (máximo 1.000 generaciones), con 10 réplicas cada una (semillas
1101–1110). Se miden la calidad (ΣT_j, C_max) y el tiempo. Con la misma semilla,
la corrida con 100 generaciones continúa la trayectoria de la de 50 y no puede
terminar peor; por eso la comparación usa la prueba de Wilcoxon de una cola
(¿100 mejora a 50?).

## 3. Resultados

Datos de cada corrida: `corridas_diseno.csv` y `corridas_parada.csv`. Informe
completo: `informe_calibracion.md`.

### 3.1 Experimento 1: diseño factorial (135 corridas)

Mejores y peores combinaciones (promedio de 5 réplicas):

| Población | p_c | p_m | ΣT_j prom. (h) | ΣT_j desv. (h) | Tardías prom. | C_max prom. (h) |
|---|---|---|---|---|---|---|
| **150** | **0,9** | **0,5** | **0,28** | **0,63** | **0,2** | **597,3** |
| 100 | 0,9 | 0,3 | 2,72 | 6,08 | 0,2 | 600,9 |
| 150 | 0,9 | 0,1 | 4,04 | 5,62 | 0,4 | 600,6 |
| 150 | 0,9 | 0,3 | 5,85 | 11,34 | 0,4 | 604,4 |
| 150 | 0,8 | 0,3 | 7,78 | 17,18 | 0,6 | 609,2 |
| … | | | | | | |
| 100 | 0,8 | 0,1 | 56,29 | 33,61 | 1,6 | 653,1 |
| 50 | 0,8 | 0,1 | 63,19 | 16,17 | 2,0 | 660,1 |
| 50 | 0,7 | 0,1 | 67,73 | 18,96 | 2,0 | 663,7 |

41 de las 135 corridas llegaron a tardanza cero.

ANOVA sobre la tardanza total:

| Fuente | SC | gl | CM | F | p |
|---|---|---|---|---|---|
| Población | 12.509,2 | 2 | 6.254,6 | 18,80 | < 0,0001 |
| Prob. de cruce | 2.604,8 | 2 | 1.302,4 | 3,91 | 0,023 |
| Prob. de mutación | 24.596,7 | 2 | 12.298,3 | 36,96 | < 0,0001 |
| Población × cruce | 1.859,7 | 4 | 464,9 | 1,40 | 0,239 |
| Población × mutación | 5.475,5 | 4 | 1.368,9 | 4,11 | 0,004 |
| Cruce × mutación | 1.586,5 | 4 | 396,6 | 1,19 | 0,318 |
| Error | 38.595,7 | 116 | 332,7 | | |
| Total | 87.228,2 | 134 | | | |

- Los residuos no son normales (Shapiro-Wilk W = 0,975, p = 0,014) y la varianza no
  es homogénea entre niveles de mutación (Levene p < 0,0001; población p = 0,059,
  cruce p = 0,090). Ambas fallas se deben a que muchas corridas llegan a tardanza
  cero, el mínimo posible.
- Por eso la conclusión se confirma con Kruskal-Wallis: población H = 21,0,
  p < 0,0001; mutación H = 28,0, p < 0,0001; cruce H = 4,6, p = 0,10. El efecto del
  cruce, significativo en el ANOVA, es débil.
- Medias por nivel: población 50/100/150 → 37,3 / 22,3 / 14,1 h; mutación
  0,1/0,3/0,5 → 43,1 / 19,5 / 11,2 h; cruce 0,7/0,8/0,9 → 27,3 / 28,1 / 18,4 h.
- **Se selecciona población 150, cruce 0,9 y mutación 0,5**, la combinación con
  menor tardanza promedio (4 de 5 réplicas sin tardanza). Coincide con la
  configuración inicial del código.
- La combinación quedó en el borde del rango probado en los tres factores; no se
  evaluaron niveles fuera del rango.

### 3.2 Experimento 2: criterio de parada (20 corridas)

| Generaciones sin mejora | ΣT_j prom. (h) | ΣT_j desv. (h) | Tardías prom. | C_max prom. (h) | Generaciones prom. | Tiempo prom. |
|---|---|---|---|---|---|---|
| 50 | 0,72 | 2,28 | 0,1 | 596,4 | 405 | 3,9 min |
| **100** | **0,00** | **0,00** | **0,0** | **591,4** | **739** | **7,9 min** |

- Con 100 generaciones sin mejora las 10 réplicas quedan sin tardanza; con 50, una
  queda con 7,2 h. El makespan promedio baja de 596,4 h a 591,4 h.
- La mejora es significativa según el objetivo lexicográfico (primero ΣT_j, luego
  C_max): Wilcoxon de una cola, p = 0,008.
- **Se adopta 100 generaciones sin mejora.** No se evaluaron criterios mayores.

### 3.3 Configuración final del algoritmo genético

| Parámetro | Valor | Origen |
|---|---|---|
| Tamaño de la población | 150 | Calibrado (exp. 1) |
| Probabilidad de cruce | 0,9 | Calibrado (efecto débil; forma parte de la mejor combinación) |
| Probabilidad de mutación | 0,5 | Calibrado (exp. 1) |
| Criterio de parada | 100 generaciones sin mejora (máx. 1.000) | Calibrado (exp. 2) |
| Torneo, prob. de intercambio, prob. de perturbación, desviación | 3; 0,30; 0,40; 0,15 | Fijos (valores del código) |

Estos valores ya están en `GA_PARAMS` de `final_sc_hfsagls_S2_4.py`.

**Alcance.** La calibración se hizo sobre la instancia real (10 órdenes,
B̄ = 10) con 5 réplicas por combinación. Si la Fase 3 cambia el número de
sublotes u otras condiciones de forma importante, conviene repetir al menos el
experimento 2 (es corto) para confirmar el criterio de parada.

## 4. Texto sugerido para el documento

El texto de la Fase 2 lo genera `docs/fase2_docx/generar_fase2_sintesis.py` a
partir de estos resultados, así que siempre coincide con ellos.

## 5. Cómo reproducirlo

```bash
pip install pandas openpyxl matplotlib scipy
cd fase2
# Experimento 1 (≈ 65 min con 4 núcleos; ≈ 4 h con 1)
python calibracion_ag.py diseno ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx --instancia real
# Experimento 2 (usa la mejor combinación del experimento 1, o --config 150,0.9,0.5)
python calibracion_ag.py parada ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx --instancia real
# Solo volver a generar el informe y las figuras
python calibracion_ag.py analizar
```

- Cada corrida se guarda en `corridas_diseno.csv` / `corridas_parada.csv` en
  cuanto termina. Si la sesión se corta (por ejemplo en Colab), al ejecutar el
  mismo comando se continúa con las corridas que faltan.
- `--procesos N` define cuántas corridas van en paralelo (por defecto, todos los
  núcleos). `--replicas` y `--presupuesto` cambian el tamaño del experimento.
- `--prueba` hace una corrida corta de verificación en otra carpeta.
- Factores, niveles y parámetros del experimento se cambian al inicio del archivo
  (`FACTORES`, `REPLICAS`, `PRESUPUESTO`, `PARADA_NIVELES`).
