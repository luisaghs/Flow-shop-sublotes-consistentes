# Calibración de los parámetros del algoritmo genético

Instancias de calibración: Caso de estudio. Si hay más de una, la configuración se elige por su posición promedio.

## Caso de estudio

Respuesta analizada: **tardanza total ΣTj**.

Combinaciones ordenadas por ΣTj promedio y luego por Cmax promedio (10 primeras):

| Población | P. cruce | P. mutación | Corridas | ΣTj prom (h) | ΣTj desv | Tardías prom | Cmax prom (h) | Cmax desv | Tiempo prom (s) |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 0.800 | 0.500 | 5 | 70.702 | 22.358 | 1.800 | 587.930 | 13.401 | 121.311 |
| 100 | 0.900 | 0.500 | 5 | 71.722 | 21.496 | 1.800 | 591.227 | 13.784 | 117.088 |
| 150 | 0.800 | 0.300 | 5 | 75.295 | 10.347 | 2.000 | 590.051 | 5.255 | 104.903 |
| 150 | 0.900 | 0.100 | 5 | 81.767 | 36.011 | 2.000 | 593.691 | 17.412 | 108.101 |
| 100 | 0.700 | 0.500 | 5 | 85.130 | 32.342 | 2.000 | 596.451 | 16.316 | 130.120 |
| 150 | 0.900 | 0.500 | 5 | 86.399 | 14.649 | 2.200 | 600.862 | 11.344 | 117.430 |
| 100 | 0.700 | 0.300 | 5 | 96.766 | 56.360 | 2.400 | 598.048 | 24.403 | 134.422 |
| 150 | 0.900 | 0.300 | 5 | 98.572 | 34.541 | 1.800 | 601.654 | 15.044 | 111.970 |
| 50 | 0.700 | 0.500 | 5 | 101.344 | 24.396 | 2.000 | 602.478 | 9.631 | 112.829 |
| 100 | 0.900 | 0.300 | 5 | 110.741 | 61.773 | 2.000 | 606.449 | 26.383 | 110.779 |

ANOVA sobre tardanza total ΣTj:

| Fuente | SC | gl | CM | F | valor p |
|---|---|---|---|---|---|
| Población | 28162.2757 | 2 | 14081.1378 | 7.8274 | 0.0006 |
| Prob. de cruce | 6195.6054 | 2 | 3097.8027 | 1.7220 | 0.1832 |
| Prob. de mutación | 74133.3231 | 2 | 37066.6616 | 20.6045 | 2.20e-08 |
| Población × Prob. de cruce | 9235.7975 | 4 | 2308.9494 | 1.2835 | 0.2805 |
| Población × Prob. de mutación | 32477.9471 | 4 | 8119.4868 | 4.5134 | 0.0020 |
| Prob. de cruce × Prob. de mutación | 2941.6875 | 4 | 735.4219 | 0.4088 | 0.8020 |
| Error | 208679.0394 | 116 | 1798.9572 | — | — |
| Total | 361825.6757 | 134 | — | — | — |

- Normalidad de residuos (Shapiro-Wilk): W = 0.9877, p = 0.2723.
- Población: Levene p = 0.01986; Kruskal-Wallis H = 11.236, p = 0.003632.
- Prob. de cruce: Levene p = 0.1408; Kruskal-Wallis H = 2.888, p = 0.236.
- Prob. de mutación: Levene p = 0.02625; Kruskal-Wallis H = 24.751, p = 4.22e-06.

## Selección combinada

Posición de cada combinación en cada instancia (1 = mejor) y posición promedio (10 primeras):

| poblacion | prob_cruce | prob_mutacion | pos_real | T_real | C_real | pos_prom |
|---|---|---|---|---|---|---|
| 100 | 0.80 | 0.50 | 1 | 70.70 | 587.93 | 1.00 |
| 100 | 0.90 | 0.50 | 2 | 71.72 | 591.23 | 2.00 |
| 150 | 0.80 | 0.30 | 3 | 75.30 | 590.05 | 3.00 |
| 150 | 0.90 | 0.10 | 4 | 81.77 | 593.69 | 4.00 |
| 100 | 0.70 | 0.50 | 5 | 85.13 | 596.45 | 5.00 |
| 150 | 0.90 | 0.50 | 6 | 86.40 | 600.86 | 6.00 |
| 100 | 0.70 | 0.30 | 7 | 96.77 | 598.05 | 7.00 |
| 150 | 0.90 | 0.30 | 8 | 98.57 | 601.65 | 8.00 |
| 50 | 0.70 | 0.50 | 9 | 101.34 | 602.48 | 9.00 |
| 100 | 0.90 | 0.30 | 10 | 110.74 | 606.45 | 10.00 |

- Mejor combinación del diseño: población = 100, cruce = 0.8, mutación = 0.5.
- Frente a la configuración anterior del código (población = 150, cruce = 0.9, mutación = 0.5), real: Wilcoxon p = 0.1875.
- Factores significativos en al menos una instancia: Población, Prob. de mutación.
- La mejor combinación está en el borde para: Prob. de mutación.

No se evaluaron niveles fuera del rango del diseño; se adopta la mejor combinación dentro de ese rango.

**Configuración seleccionada: población = 100, cruce = 0.8, mutación = 0.5.**

## Criterio de parada

Configuración: {'poblacion': 100, 'prob_cruce': 0.8, 'prob_mutacion': 0.5}

Caso de estudio:

| Gen. sin mejora | Corridas | ΣTj prom (h) | ΣTj desv | Tardías prom | Cmax prom (h) | Cmax desv | Tiempo prom (s) | Generaciones prom |
|---|---|---|---|---|---|---|---|---|
| 50 | 10 | 99.448 | 56.787 | 2.200 | 599.684 | 24.643 | 207.030 | 507.400 |
| 100 | 10 | 71.167 | 39.752 | 2.100 | 588.005 | 17.448 | 304.184 | 780.800 |

- 50 → 100 generaciones sin mejora: Wilcoxon de una cola p = 0.03125 (mejora significativa).

**Criterio de parada recomendado: 100 generaciones sin mejora** (mejora de forma significativa frente a los niveles menores; no se evaluaron niveles mayores).

