# Calibración de los parámetros del algoritmo genético

Instancias de calibración: Caso de estudio. Si hay más de una, la configuración se elige por su posición promedio.

## Caso de estudio

Respuesta analizada: **tardanza total ΣTj**.

Combinaciones ordenadas por ΣTj promedio y luego por Cmax promedio (10 primeras):

| Población | P. cruce | P. mutación | Corridas | ΣTj prom (h) | ΣTj desv | Tardías prom | Cmax prom (h) | Cmax desv | Tiempo prom (s) |
|---|---|---|---|---|---|---|---|---|---|
| 150 | 0.900 | 0.500 | 5 | 0.281 | 0.627 | 0.200 | 597.320 | 10.961 | 113.071 |
| 100 | 0.900 | 0.300 | 5 | 2.719 | 6.080 | 0.200 | 600.933 | 16.714 | 111.362 |
| 150 | 0.900 | 0.100 | 5 | 4.039 | 5.621 | 0.400 | 600.584 | 18.989 | 103.337 |
| 150 | 0.900 | 0.300 | 5 | 5.849 | 11.338 | 0.400 | 604.353 | 23.201 | 109.498 |
| 150 | 0.800 | 0.300 | 5 | 7.776 | 17.178 | 0.600 | 609.173 | 23.303 | 104.846 |
| 50 | 0.900 | 0.500 | 5 | 8.720 | 8.827 | 0.600 | 616.994 | 12.420 | 114.373 |
| 50 | 0.700 | 0.500 | 5 | 8.825 | 5.304 | 1.000 | 619.825 | 5.304 | 105.211 |
| 150 | 0.800 | 0.500 | 5 | 9.038 | 12.041 | 0.600 | 611.782 | 21.460 | 109.385 |
| 100 | 0.700 | 0.500 | 5 | 9.295 | 13.134 | 0.600 | 606.748 | 28.862 | 105.119 |
| 100 | 0.800 | 0.500 | 5 | 10.196 | 17.895 | 0.600 | 606.171 | 28.674 | 110.820 |

ANOVA sobre tardanza total ΣTj:

| Fuente | SC | gl | CM | F | valor p |
|---|---|---|---|---|---|
| Población | 12509.1997 | 2 | 6254.5998 | 18.7983 | 8.48e-08 |
| Prob. de cruce | 2604.8372 | 2 | 1302.4186 | 3.9144 | 0.0226 |
| Prob. de mutación | 24596.6922 | 2 | 12298.3461 | 36.9628 | 3.81e-13 |
| Población × Prob. de cruce | 1859.7461 | 4 | 464.9365 | 1.3974 | 0.2392 |
| Población × Prob. de mutación | 5475.4518 | 4 | 1368.8629 | 4.1141 | 0.0037 |
| Prob. de cruce × Prob. de mutación | 1586.5309 | 4 | 396.6327 | 1.1921 | 0.3180 |
| Error | 38595.7318 | 116 | 332.7218 | — | — |
| Total | 87228.1896 | 134 | — | — | — |

- Normalidad de residuos (Shapiro-Wilk): W = 0.9750, p = 0.01362.
- Población: Levene p = 0.05892; Kruskal-Wallis H = 20.954, p = 2.817e-05.
- Prob. de cruce: Levene p = 0.08998; Kruskal-Wallis H = 4.596, p = 0.1005.
- Prob. de mutación: Levene p = 1.158e-05; Kruskal-Wallis H = 27.969, p = 8.446e-07.

## Selección combinada

Posición de cada combinación en cada instancia (1 = mejor) y posición promedio (10 primeras):

| poblacion | prob_cruce | prob_mutacion | pos_real | T_real | C_real | pos_prom |
|---|---|---|---|---|---|---|
| 150 | 0.90 | 0.50 | 1 | 0.28 | 597.32 | 1.00 |
| 100 | 0.90 | 0.30 | 2 | 2.72 | 600.93 | 2.00 |
| 150 | 0.90 | 0.10 | 3 | 4.04 | 600.58 | 3.00 |
| 150 | 0.90 | 0.30 | 4 | 5.85 | 604.35 | 4.00 |
| 150 | 0.80 | 0.30 | 5 | 7.78 | 609.17 | 5.00 |
| 50 | 0.90 | 0.50 | 6 | 8.72 | 616.99 | 6.00 |
| 50 | 0.70 | 0.50 | 7 | 8.82 | 619.82 | 7.00 |
| 150 | 0.80 | 0.50 | 8 | 9.04 | 611.78 | 8.00 |
| 100 | 0.70 | 0.50 | 9 | 9.29 | 606.75 | 9.00 |
| 100 | 0.80 | 0.50 | 10 | 10.20 | 606.17 | 10.00 |

- Mejor combinación del diseño: población = 150, cruce = 0.9, mutación = 0.5.
- Factores significativos en al menos una instancia: Población, Prob. de cruce, Prob. de mutación.
- La mejor combinación está en el borde para: Población, Prob. de cruce, Prob. de mutación.

No se evaluaron niveles fuera del rango del diseño; se adopta la mejor combinación dentro de ese rango.

**Configuración seleccionada: población = 150, cruce = 0.9, mutación = 0.5.**

## Criterio de parada

Configuración: {'poblacion': 150, 'prob_cruce': 0.9, 'prob_mutacion': 0.5}

Caso de estudio:

| Gen. sin mejora | Corridas | ΣTj prom (h) | ΣTj desv | Tardías prom | Cmax prom (h) | Cmax desv | Tiempo prom (s) | Generaciones prom |
|---|---|---|---|---|---|---|---|---|
| 50 | 10 | 0.721 | 2.280 | 0.100 | 596.388 | 9.981 | 233.415 | 405.000 |
| 100 | 10 | 0.000 | 0.000 | 0.000 | 591.367 | 7.155 | 473.679 | 739.400 |

- 50 → 100 generaciones sin mejora: Wilcoxon de una cola p = 0.007812 (mejora significativa).

**Criterio de parada recomendado: 100 generaciones sin mejora** (mejora de forma significativa frente a los niveles menores; no se evaluaron niveles mayores).

