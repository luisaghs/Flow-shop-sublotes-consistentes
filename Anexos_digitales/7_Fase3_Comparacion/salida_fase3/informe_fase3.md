# Fase 3 — Resultados de la evaluación

## 1.a Escenario base: sistema actual (B = 6) frente al AG con B̄ = 10 (30 réplicas)

| Indicador | Actual (B = 6) | AG media ± IC 95 % | Desv. | Mín. | Máx. | Mejora | Wilcoxon p |
|---|---|---|---|---|---|---|---|
| % órdenes tardías | 40,0 | 1,3 ± 1,3 | 3,5 | 0,0 | 10,0 | 96,7 % | < 0,0001 |
| Tardanza total ΣTj (h) | 393,8 | 1,5 ± 1,9 | 5,1 | 0,0 | 22,9 | 99,6 % | < 0,0001 |
| Tardanza promedio (h) | 39,4 | 0,1 ± 0,2 | 0,5 | 0,0 | 2,3 | 99,6 % | < 0,0001 |
| Tardanza máxima (h) | 150,9 | 1,5 ± 1,9 | 5,1 | 0,0 | 22,9 | 99,0 % | < 0,0001 |
| Adelanto total ΣEj (h) | 603,3 | 515,7 ± 36,2 | 96,9 | 297,1 | 735,6 | 14,5 % | < 0,0001 |
| Makespan Cmax (h) | 617,1 | 591,6 ± 5,7 | 15,3 | 562,1 | 633,9 | 4,1 % | < 0,0001 |
| Tiempo de flujo medio (h) | 394,3 | 363,9 ± 3,6 | 9,7 | 341,8 | 385,6 | 7,7 % | < 0,0001 |
| Ocupación troquelado (%) | 75,0 | 78,2 ± 0,7 | 2,0 | 73,0 | 82,3 | -4,4 % | < 0,0001 |
| Alistamientos en troquelado | 36,0 | 57,3 ± 3,2 | 8,5 | 42,0 | 78,0 | -59,1 % | < 0,0001 |

## 1.b Escenario base: sistema actual (B = 6) frente al AG con B = 6 (30 réplicas)

| Indicador | Actual (B = 6) | AG media ± IC 95 % | Desv. | Mín. | Máx. | Mejora | Wilcoxon p |
|---|---|---|---|---|---|---|---|
| % órdenes tardías | 40,0 | 21,3 ± 1,3 | 3,5 | 20,0 | 30,0 | 46,7 % | < 0,0001 |
| Tardanza total ΣTj (h) | 393,8 | 91,8 ± 3,9 | 10,4 | 74,3 | 113,4 | 76,7 % | < 0,0001 |
| Tardanza promedio (h) | 39,4 | 9,2 ± 0,4 | 1,0 | 7,4 | 11,3 | 76,7 % | < 0,0001 |
| Tardanza máxima (h) | 150,9 | 70,9 ± 2,3 | 6,0 | 56,2 | 80,9 | 53,0 % | < 0,0001 |
| Adelanto total ΣEj (h) | 603,3 | 302,2 ± 20,2 | 54,2 | 213,5 | 433,4 | 49,9 % | < 0,0001 |
| Makespan Cmax (h) | 617,1 | 681,9 ± 2,3 | 6,0 | 667,2 | 691,9 | -10,5 % | < 0,0001 |
| Tiempo de flujo medio (h) | 394,3 | 394,3 ± 2,0 | 5,3 | 382,8 | 404,7 | 0,0 % | 0.97 |
| Ocupación troquelado (%) | 75,0 | 67,8 ± 0,2 | 0,6 | 66,9 | 69,3 | 9,5 % | < 0,0001 |
| Alistamientos en troquelado | 36,0 | 39,7 ± 1,3 | 3,4 | 35,0 | 46,0 | -10,2 % | < 0,0001 |

## 2. Descomposición de la mejora (escenario base)

| Paso | % tardías | ΣTj (h) | Cmax (h) |
|---|---|---|---|
| Sistema actual: FIFO por etapa, B = 6 | 40,0 % | 393,8 | 617,1 |
| Cambiar solo la regla: EDD, B = 6 | 60,0 % | 386,9 | 778,2 |
| Regla EDD con B̄ = 10 (sin AG) | 20,0 % | 99,0 | 681,3 |
| Optimizar con la misma división: AG, B = 6 (media) | 21,3 % | 91,8 | 681,9 |
| Además, dividir más: AG, B̄ = 10 (media) | 1,3 % | 1,5 | 591,6 |

## 3. Sensibilidad al número de partes del sistema actual

| Sistema actual | Actual: % tardías / ΣTj | AG misma B: % tardías / ΣTj (media) | AG B̄ = 10: % tardías / ΣTj (media) |
|---|---|---|---|
| B = 5 | 70 % / 548,0 | 46 % / 407,8 | 1 % / 1,5 |
| B = 6 | 40 % / 393,8 | 21 % / 91,8 | 1 % / 1,5 |
| B = 7 | 40 % / 345,7 | 10 % / 37,7 | 1 % / 1,5 |

## 4. Sensibilidad al número de sublotes del modelo propuesto

| B̄ | Réplicas | % tardías | ΣTj prom. (h) | Cmax prom. (h) | Tiempo prom. (min) |
|---|---|---|---|---|---|
| 5 | 10 | 46 % | 407,8 | 655,0 | 2,6 |
| 6 | 30 | 21 % | 91,8 | 681,9 | 3,8 |
| 7 | 10 | 10 % | 37,7 | 648,7 | 4,5 |
| 10 | 30 | 1 % | 1,5 | 591,6 | 6,6 |

## 5. Escenarios de exigencia (actual B = 6 frente a AG B̄ = 10)

| Escenario | Actual: % tardías / ΣTj | AG: % tardías / ΣTj (media) | Mejora ΣTj | Wilcoxon p |
|---|---|---|---|---|
| Caso de estudio | 40 % / 393,8 | 1 % / 1,5 | 99,6 % | 2e-07 |
| Fechas de entrega 10 % más ajustadas | 70 % / 592,2 | 19 % / 74,2 | 87,5 % | 0.002 |
| Fechas de entrega 20 % más ajustadas | 80 % / 868,3 | 48 % / 232,3 | 73,2 % | 0.002 |
| Demanda 10 % mayor | 70 % / 661,7 | 16 % / 55,0 | 91,7 % | 0.002 |
| Demanda 20 % mayor | 70 % / 1.018,0 | 32 % / 214,1 | 79,0 % | 0.002 |

## 6. Reglas de despacho de referencia (escenario base, B = 6)

| Método (B = 6) | % tardías | ΣTj (h) | Cmax (h) |
|---|---|---|---|
| Actual (FIFO por etapa) | 40 % | 393,8 | 617,1 |
| Regla EDD | 60 % | 386,9 | 778,2 |
| Regla FIFO | 40 % | 474,7 | 623,0 |
| Regla SPT | 40 % | 759,8 | 795,1 |
| Regla LPT | 60 % | 830,9 | 638,4 |
| Regla MST | 70 % | 812,5 | 641,9 |
| Regla CR | 60 % | 583,2 | 607,5 |

