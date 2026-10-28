# Cómo apropiarse de la calibración y poder dar fe de ella

## 0. Punto de partida (con honestidad)

Las 190 corridas de la calibración y su análisis estadístico se ejecutaron con un
asistente de IA (Claude) en una sesión de trabajo, a partir de su código, sus datos y
sus decisiones. Para poder decir con verdad "realizamos la calibración", hay que
cumplir tres condiciones:

1. **Entenderla:** saber explicar y defender cada decisión del diseño.
2. **Reproducirla:** correrla ustedes en su computador y obtener los mismos resultados.
3. **Declarar la herramienta:** informar el uso de IA según el reglamento de la
   universidad y lo que acuerden con su director.

Este documento los guía en las tres.

---

## 1. Entender cada decisión

| Decisión | Qué se hizo | Por qué (lo que deben poder explicar) |
|---|---|---|
| Qué se calibra | Población, probabilidad de cruce y probabilidad de mutación | Son los parámetros que más influyen en un AG; los demás quedaron fijos en los valores del código |
| Diseño | Factorial completo 3³ = 27 combinaciones | Permite estimar los efectos principales y las interacciones (Montgomery, 2017) |
| Niveles | 50/100/150; 0,7/0,8/0,9; 0,1/0,3/0,5 | Rangos usuales en la literatura de AG para programación de la producción |
| Réplicas | 5 por combinación (135 corridas) | El AG es aleatorio: una sola corrida no basta para comparar |
| Presupuesto fijo | 30.000 cromosomas por corrida | Si se parara por "generaciones sin mejora", la población grande evaluaría más soluciones y ganaría solo por eso |
| Semillas comunes | La réplica r usa la semilla 1000 + r en las 27 combinaciones | Es un bloqueo: las combinaciones se comparan con el mismo "azar" y la diferencia se debe a los parámetros |
| Respuesta | Tardanza total ΣT_j | Es el objetivo del modelo; el makespan se usa como criterio secundario |
| Análisis | ANOVA con efectos principales e interacciones dobles | Identifica qué factores afectan la tardanza |
| Supuestos | Normalidad (Shapiro-Wilk) y varianzas iguales (Levene) | El ANOVA los requiere; la varianza no fue homogénea |
| Prueba no paramétrica | Kruskal-Wallis | Confirma el ANOVA sin suponer normalidad ni varianzas iguales |
| Ampliación | Población 200 y 250, mutación 0,7 | El mejor resultado quedó en el borde del rango; había que comprobar que el óptimo no estaba más allá |
| Parsimonia | Se conservó población 150 | La población 200 no fue significativamente mejor (Wilcoxon, p = 0,81) |
| Criterio de parada | 50, 100 y 200 generaciones sin mejora | Con 100 mejora el makespan de forma significativa frente a 50; con 200 no hay mejora y el tiempo crece 33 % |

**Ejercicio:** cada integrante explica la tabla anterior en voz alta a otra persona
sin leerla. Si alguna fila no se puede explicar, repásenla con el informe
(`fase2/salida_calibracion/informe_calibracion.md`) o con el director.

---

## 2. Reproducir los resultados en su computador

El algoritmo usa una semilla fija por corrida, así que con el mismo código y los mismos
datos **cada corrida da exactamente el mismo resultado** en cualquier computador (solo
cambia el tiempo). Esto ya se comprobó: dos corridas repetidas dieron los mismos
valores hasta el cuarto decimal.

### 2.1 Verificación rápida (≈ 10–15 minutos)

En Google Colab o en su computador, con la carpeta `fase2/` del repositorio, el modelo
(`final_sc_hfsagls_S2_4.py`) y `BD_HFS.xlsx`:

```bash
pip install pandas openpyxl matplotlib scipy
cd fase2
python verificar_reproduccion.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
```

El script repite las 5 corridas de la configuración elegida (150; 0,9; 0,5) y las
compara con las guardadas. El resultado esperado es "5 de 5 corridas reproducidas
exactamente". Con `--combinacion 50,0.7,0.1` pueden probar cualquier otra combinación.

### 2.2 Reproducción completa (≈ 2–3 horas en Colab; se puede pausar)

```bash
python calibracion_ag.py diseno ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
python calibracion_ag.py ampliacion ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
python calibracion_ag.py parada ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
```

- Antes de empezar, cambien en `calibracion_ag.py` la carpeta de salida (o copien
  `fase2/` a otra ubicación) para no mezclar sus resultados con los existentes.
- Cada corrida se guarda al terminar. Si Colab se desconecta, vuelvan a ejecutar el
  mismo comando y el script continúa desde donde quedó.
- Al final comparen su `informe_calibracion.md` con el existente.

### 2.3 Dejar evidencia

Guarden en una carpeta propia (Drive o repositorio): la fecha, el computador usado, la
salida de cada comando, los CSV generados y el tiempo total. Esa evidencia respalda que
la calibración se ejecutó y se verificó bajo su responsabilidad. Si lo corren en su
equipo, actualicen en el documento la descripción del computador y los tiempos.

---

## 3. Rehacer el ANOVA ustedes mismos

El archivo `fase2/salida_calibracion/anova_calibracion_excel.xlsx` contiene:

- **Corridas:** los 135 resultados.
- **ANOVA:** la tabla completa calculada **solo con fórmulas de Excel** (PROMEDIO.SI,
  CONTAR.SI, PROMEDIO.SI.CONJUNTO, DESVIA2, DISTR.F). Pueden seguir cada celda: medias
  por nivel, sumas de cuadrados, grados de libertad, valores F y valores p. El resultado
  coincide exactamente con la tabla del documento.

Si en sus cursos usaron Minitab o Statgraphics, importen
`salida_calibracion/corridas_diseno.csv` y corran *Estadísticas → ANOVA → Modelo lineal
general* con los tres factores y sus interacciones dobles: deben obtener la misma tabla.
Hacerlo con la herramienta que dominan es la mejor forma de poder defenderlo.

**Ejercicio:** calculen a mano la SC de la población con las tres medias por nivel
(46,70; 28,70 y 12,39 h), la media general (29,27 h) y n = 45 por nivel:
SC = 45 · Σ (media_nivel − media general)² ≈ 26.514.

---

## 4. Preguntas probables del jurado

- **¿Por qué no fijaron los parámetros con valores de la literatura?** Porque el
  desempeño de un AG depende del problema; la calibración ajusta los parámetros a la
  instancia de la empresa con evidencia estadística.
- **¿Por qué el mismo presupuesto en todas las corridas?** Para comparar
  configuraciones con el mismo esfuerzo de cómputo.
- **¿Por qué 5 réplicas?** El AG es aleatorio; con 5 réplicas por combinación (45 por
  nivel de cada factor) el ANOVA detectó diferencias claras. Más réplicas aumentan el
  tiempo sin cambiar la conclusión.
- **No se cumplió la homogeneidad de varianzas, ¿el ANOVA es válido?** Por eso se
  confirmó con Kruskal-Wallis, que no requiere ese supuesto y dio la misma conclusión.
- **¿Por qué la probabilidad de cruce es 0,9 si no fue significativa?** Al no influir de
  forma significativa, se tomó el nivel con menor tardanza promedio.
- **La mejor combinación quedó en el borde, ¿cómo saben que es la mejor?** Se amplió el
  rango (población 200 y 250, mutación 0,7) y ninguna opción fue mejor.
- **¿Los resultados se pueden repetir?** Sí: con las mismas semillas, cada corrida da
  exactamente el mismo resultado (sección 2).

---

## 5. Declarar el uso de la herramienta

Revisen el reglamento de trabajos de grado de la Universidad del Valle y las
indicaciones de su director sobre el uso de inteligencia artificial generativa, y
coméntenle cómo la usaron. Una declaración breve en la metodología o en los
agradecimientos suele ser suficiente, por ejemplo:

> *En el desarrollo computacional del trabajo se utilizó un asistente de inteligencia
> artificial (Claude, Anthropic) como apoyo para la programación de los scripts de
> validación y calibración y para la ejecución de los experimentos. El diseño de los
> experimentos, la verificación de los resultados, su reproducción y su interpretación
> fueron realizados y validados por los autores.*

La última frase solo es cierta si completan las secciones 1 a 3; ajústenla a lo que
efectivamente hicieron.

---

## Lista de chequeo

- [ ] Cada integrante puede explicar la tabla de la sección 1.
- [ ] Corrieron `verificar_reproduccion.py` y obtuvieron 5 de 5 corridas iguales.
- [ ] (Recomendado) Reprodujeron el diseño completo en su computador y guardaron la evidencia.
- [ ] Revisaron el ANOVA en Excel o en Minitab/Statgraphics.
- [ ] Prepararon las respuestas de la sección 4.
- [ ] Hablaron con el director y redactaron la declaración de uso de IA.
