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
| **100** | **0,8** | **0,5** | **70,7** | **22,4** | **1,8** | **587,9** |
| 100 | 0,9 | 0,5 | 71,7 | 21,5 | 1,8 | 591,2 |
| 150 | 0,8 | 0,3 | 75,3 | 10,3 | 2,0 | 590,1 |
| 150 | 0,9 | 0,1 | 81,8 | 36,0 | 2,0 | 593,7 |
| 100 | 0,7 | 0,5 | 85,1 | 32,3 | 2,0 | 596,5 |
| … | | | | | | |
| 100 | 0,9 | 0,1 | 176,4 | 28,6 | 2,6 | 631,2 |
| 100 | 0,7 | 0,1 | 185,9 | 25,8 | 3,0 | 632,3 |
| 50 | 0,8 | 0,1 | 193,9 | 26,0 | 3,0 | 637,7 |

ANOVA sobre la tardanza total:

| Fuente | SC | gl | CM | F | p |
|---|---|---|---|---|---|
| Población | 28.162,3 | 2 | 14.081,1 | 7,83 | 0,0006 |
| Prob. de cruce | 6.195,6 | 2 | 3.097,8 | 1,72 | 0,183 |
| Prob. de mutación | 74.133,3 | 2 | 37.066,7 | 20,60 | < 0,0001 |
| Población × cruce | 9.235,8 | 4 | 2.308,9 | 1,28 | 0,281 |
| Población × mutación | 32.477,9 | 4 | 8.119,5 | 4,51 | 0,002 |
| Cruce × mutación | 2.941,7 | 4 | 735,4 | 0,41 | 0,802 |
| Error | 208.679,0 | 116 | 1.799,0 | | |
| Total | 361.825,7 | 134 | | | |

- Los residuos son normales: Shapiro-Wilk W = 0,988, p = 0,272.
- La varianza no es homogénea entre niveles de población (Levene p = 0,020) ni
  de mutación (p = 0,026); por eso se confirma con Kruskal-Wallis:
  población H = 11,2, p = 0,004; mutación H = 24,8, p < 0,0001; cruce H = 2,9,
  p = 0,236. La conclusión es la misma que la del ANOVA.
- Medias por nivel: población 50/100/150 → 142,1 / 118,9 / 107,3 h; mutación
  0,1/0,3/0,5 → 154,1 / 116,5 / 97,7 h; cruce 0,7/0,8/0,9 → 129,7 / 125,0 /
  113,6 h.
- Más mutación reduce la tardanza, y su efecto depende del tamaño de la
  población (interacción significativa).
- **Se selecciona población 100, cruce 0,8 y mutación 0,5**, la combinación con
  menor tardanza promedio. Frente a la configuración inicial del código
  (150; 0,9; 0,5) la diferencia no es significativa (Wilcoxon, p = 0,19).
- La mutación 0,5 quedó en el borde del rango probado; no se evaluaron niveles
  mayores.

### 3.2 Experimento 2: criterio de parada (20 corridas)

| Generaciones sin mejora | ΣT_j prom. (h) | ΣT_j desv. (h) | Tardías prom. | C_max prom. (h) | Generaciones prom. | Tiempo prom. |
|---|---|---|---|---|---|---|
| 50 | 99,4 | 56,8 | 2,2 | 599,7 | 507 | 3,5 min |
| **100** | **71,2** | **39,8** | **2,1** | **588,0** | **781** | **5,1 min** |

- En 5 de las 10 réplicas, seguir hasta 100 generaciones sin mejora encontró una
  solución mejor; en las otras 5 el resultado fue el mismo.
- La mejora es significativa (Wilcoxon de una cola, p = 0,031). Con la prueba de
  dos colas y solo 5 diferencias distintas de cero, el valor p mínimo posible
  sería 0,0625.
- **Se adopta 100 generaciones sin mejora.** No se evaluaron criterios mayores.

### 3.3 Configuración final del algoritmo genético

| Parámetro | Valor | Origen |
|---|---|---|
| Tamaño de la población | 100 | Calibrado (exp. 1) |
| Probabilidad de cruce | 0,8 | Calibrado (sin efecto significativo; forma parte de la mejor combinación) |
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
# Experimento 2 (usa la mejor combinación del experimento 1, o --config 100,0.8,0.5)
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
