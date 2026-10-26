# Calibración de los parámetros del algoritmo genético

- Mejor solución encontrada en todos los experimentos: ΣTj = 0.0000 h, Cmax = 622.9505 h.
- Respuesta principal: ΣTj (h). Respuesta secundaria: RPD del Cmax = 100·(Cmax − Cmax*)/Cmax*, con Cmax* el mejor Cmax entre las corridas con la mejor ΣTj.
- Pruebas de rangos (Kruskal-Wallis, Wilcoxon) sobre el orden lexicográfico (Z = 1000·ΣTj + Cmax).

## 1. Diseño factorial: 27 combinaciones × 5 réplicas (135 corridas)

Ordenado por ΣTj promedio y luego por Cmax promedio.

| Población | P. cruce | P. mutación | ΣTj prom (h) | ΣTj desv | ΣTj máx | % con mejor ΣTj | Cmax prom (h) | RPD Cmax (%) | Tiempo prom (s) | Individuos hasta el mejor |
|---|---|---|---|---|---|---|---|---|---|---|
| 150 | 0.900 | 0.500 | 0.000 | 0.000 | 0.000 | 100.000 | 652.294 | 4.710 | 95.353 | 29040.000 |
| 150 | 0.800 | 0.500 | 0.373 | 0.835 | 1.866 | 80.000 | 656.051 | 5.314 | 98.228 | 28020.000 |
| 100 | 0.900 | 0.300 | 1.821 | 4.072 | 9.105 | 80.000 | 651.570 | 4.594 | 88.785 | 25980.000 |
| 150 | 0.900 | 0.300 | 5.044 | 11.279 | 25.221 | 80.000 | 671.341 | 7.768 | 91.845 | 29070.000 |
| 150 | 0.800 | 0.300 | 5.561 | 7.324 | 15.516 | 40.000 | 664.388 | 6.652 | 87.678 | 28230.000 |
| 100 | 0.900 | 0.500 | 10.858 | 15.412 | 35.947 | 20.000 | 681.601 | 9.415 | 94.310 | 28340.000 |
| 150 | 0.700 | 0.100 | 14.680 | 18.803 | 45.120 | 20.000 | 683.111 | 9.657 | 73.683 | 27570.000 |
| 100 | 0.700 | 0.500 | 18.353 | 22.838 | 53.062 | 40.000 | 683.854 | 9.777 | 88.348 | 29760.000 |
| 150 | 0.900 | 0.100 | 19.074 | 16.549 | 35.814 | 20.000 | 690.364 | 10.822 | 86.765 | 25920.000 |
| 150 | 0.700 | 0.300 | 20.790 | 22.183 | 52.771 | 40.000 | 689.289 | 10.649 | 80.731 | 26850.000 |
| 150 | 0.700 | 0.500 | 21.256 | 21.038 | 47.728 | 40.000 | 692.527 | 11.169 | 89.610 | 29760.000 |
| 50 | 0.900 | 0.500 | 22.214 | 13.664 | 34.586 | 20.000 | 692.177 | 11.113 | 95.460 | 28770.000 |
| 150 | 0.800 | 0.100 | 24.736 | 37.852 | 90.972 | 20.000 | 695.405 | 11.631 | 82.106 | 26370.000 |
| 100 | 0.800 | 0.500 | 29.560 | 32.828 | 78.740 | 40.000 | 690.064 | 10.774 | 93.200 | 29760.000 |
| 100 | 0.900 | 0.100 | 29.691 | 27.535 | 64.751 | 20.000 | 700.545 | 12.456 | 87.674 | 25400.000 |
| 50 | 0.700 | 0.500 | 30.187 | 20.993 | 57.113 | 0.000 | 702.187 | 12.720 | 86.285 | 27700.000 |
| 100 | 0.800 | 0.300 | 30.673 | 34.481 | 75.481 | 40.000 | 697.983 | 12.045 | 86.320 | 27900.000 |
| 50 | 0.700 | 0.300 | 33.594 | 24.846 | 56.531 | 0.000 | 705.594 | 13.267 | 78.956 | 28010.000 |
| 50 | 0.800 | 0.500 | 34.796 | 45.050 | 103.271 | 20.000 | 703.538 | 12.936 | 90.891 | 29170.000 |
| 100 | 0.800 | 0.100 | 37.641 | 28.402 | 66.999 | 0.000 | 709.641 | 13.916 | 80.617 | 25820.000 |
| 50 | 0.800 | 0.300 | 45.542 | 41.072 | 88.730 | 20.000 | 717.490 | 15.176 | 86.563 | 22500.000 |
| 100 | 0.700 | 0.100 | 46.860 | 23.970 | 62.399 | 0.000 | 718.860 | 15.396 | 73.410 | 23700.000 |
| 100 | 0.700 | 0.300 | 52.863 | 11.835 | 73.149 | 0.000 | 724.863 | 16.360 | 81.590 | 27720.000 |
| 50 | 0.900 | 0.100 | 59.130 | 36.884 | 103.407 | 0.000 | 731.130 | 17.366 | 85.015 | 23370.000 |
| 50 | 0.900 | 0.300 | 59.572 | 20.364 | 78.728 | 0.000 | 731.572 | 17.437 | 90.492 | 25500.000 |
| 50 | 0.700 | 0.100 | 61.825 | 37.514 | 99.962 | 0.000 | 733.812 | 17.796 | 71.181 | 25910.000 |
| 50 | 0.800 | 0.100 | 73.482 | 22.347 | 99.698 | 0.000 | 745.482 | 19.670 | 79.138 | 27050.000 |

## 2. ANOVA sobre ΣTj (efectos principales e interacciones dobles)

| Fuente | SC | gl | CM | F | valor p |
|---|---|---|---|---|---|
| Población | 26514.5171 | 2 | 13257.2585 | 20.6465 | 2.14e-08 |
| Prob. de cruce | 2702.7590 | 2 | 1351.3795 | 2.1046 | 0.1265 |
| Prob. de mutación | 11110.4881 | 2 | 5555.2440 | 8.6516 | 0.0003 |
| Población × Prob. de cruce | 4076.2745 | 4 | 1019.0686 | 1.5871 | 0.1824 |
| Población × Prob. de mutación | 2254.8371 | 4 | 563.7093 | 0.8779 | 0.4795 |
| Prob. de cruce × Prob. de mutación | 688.1319 | 4 | 172.0330 | 0.2679 | 0.8981 |
| Error | 74484.2719 | 116 | 642.1058 | — | — |
| Total | 121831.2796 | 134 | — | — | — |

Figuras: `efectos_principales.png` (medias de ΣTj con intervalos LSD al 95 %; si dos intervalos no se traslapan, los niveles difieren) e `interacciones.png`.

## 3. Supuestos del ANOVA y prueba no paramétrica

- Normalidad de residuos (Shapiro-Wilk): W = 0.9902, p = 0.4591.
- Homogeneidad de varianzas entre niveles de Población (Levene): W = 12.2236, p = 1.348e-05.
- Homogeneidad de varianzas entre niveles de Prob. de cruce (Levene): W = 1.6522, p = 0.1956.
- Homogeneidad de varianzas entre niveles de Prob. de mutación (Levene): W = 3.6382, p = 0.02897.
- Kruskal-Wallis (no paramétrica, orden lexicográfico); es la prueba de referencia si algún supuesto anterior tiene p < 0,05:
  - Población: H = 30.222, p = 2.737e-07
  - Prob. de cruce: H = 4.498, p = 0.1055
  - Prob. de mutación: H = 14.467, p = 0.0007218

## 4. Mejor combinación del diseño frente a la configuración actual

- Mejor combinación: población = 150, cruce = 0.9, mutación = 0.5 (ΣTj promedio = 0.000 h, Cmax promedio = 652.294 h).
- Configuración actual: población = 150, cruce = 0.9, mutación = 0.5 (ΣTj promedio = 0.000 h).
- La configuración actual es la mejor combinación del diseño.
- Está en el borde del rango probado en: Población, Prob. de cruce, Prob. de mutación. Por eso se amplía el rango (experimento 1b).

## 5. Ampliación del rango (experimento 1b)

Mismas semillas y presupuesto que el diseño; incluye la configuración actual como referencia.

| Población | P. cruce | P. mutación | Corridas | ΣTj prom (h) | ΣTj desv | ΣTj máx | % con mejor ΣTj | Cmax prom (h) | RPD Cmax (%) | Tiempo prom (s) | Individuos hasta el mejor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 150 | 0.900 | 0.500 | 5 | 0.000 | 0.000 | 0.000 | 100.000 | 652.294 | 4.710 | 95.353 | 29040.000 |
| 200 | 0.900 | 0.500 | 5 | 0.000 | 0.000 | 0.000 | 100.000 | 656.597 | 5.401 | 96.600 | 27840.000 |
| 150 | 0.900 | 0.700 | 5 | 0.160 | 0.358 | 0.802 | 80.000 | 663.951 | 6.582 | 101.289 | 24510.000 |
| 250 | 0.900 | 0.500 | 5 | 1.996 | 4.464 | 9.982 | 80.000 | 665.053 | 6.759 | 95.689 | 28150.000 |
| 200 | 0.900 | 0.700 | 5 | 2.992 | 1.974 | 5.537 | 20.000 | 672.140 | 7.896 | 100.746 | 27920.000 |
| 250 | 0.900 | 0.700 | 5 | 8.674 | 3.732 | 12.644 | 0.000 | 680.674 | 9.266 | 99.666 | 22000.000 |

- Kruskal-Wallis entre estas combinaciones: H = 17.093, p = 0.004327.
- población = 200, cruce = 0.9, mutación = 0.5 frente a la actual: Wilcoxon p = 0.8125.
- población = 150, cruce = 0.9, mutación = 0.7 frente a la actual: Wilcoxon p = 0.125.
- población = 250, cruce = 0.9, mutación = 0.5 frente a la actual: Wilcoxon p = 0.4375.
- población = 200, cruce = 0.9, mutación = 0.7 frente a la actual: Wilcoxon p = 0.0625.
- población = 250, cruce = 0.9, mutación = 0.7 frente a la actual: Wilcoxon p = 0.0625.
- La configuración actual sigue siendo la mejor.

## 6. Criterio de parada (experimento 2)

Configuración: {'poblacion': 150, 'prob_cruce': 0.9, 'prob_mutacion': 0.5}

| Gen. sin mejora | Corridas | ΣTj prom (h) | ΣTj desv | ΣTj máx | % con mejor ΣTj | Cmax prom (h) | RPD Cmax (%) | Tiempo prom (s) | Generaciones prom |
|---|---|---|---|---|---|---|---|---|---|
| 50 | 10 | 0.000 | 0.000 | 0.000 | 100.000 | 650.766 | 4.465 | 184.975 | 387.800 |
| 100 | 10 | 0.000 | 0.000 | 0.000 | 100.000 | 644.466 | 3.454 | 300.730 | 632.500 |
| 200 | 10 | 0.000 | 0.000 | 0.000 | 100.000 | 642.749 | 3.178 | 398.919 | 855.300 |

- Kruskal-Wallis entre criterios: H = 3.096, p = 0.2127.
- 50 frente a 100 generaciones sin mejora: Wilcoxon p = 0.01562.
- 100 frente a 200 generaciones sin mejora: Wilcoxon p = 0.0625.

