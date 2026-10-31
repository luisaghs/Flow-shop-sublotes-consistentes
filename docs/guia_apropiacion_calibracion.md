# Cómo apropiarse de la calibración y poder dar fe de ella

## 0. Punto de partida (con honestidad)

Las 155 corridas de la calibración (135 del diseño factorial y 20 del criterio de parada) y su análisis estadístico se ejecutaron con un
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
| Supuestos | Normalidad (Shapiro-Wilk) y varianzas iguales (Levene) | El ANOVA los requiere; los residuos son normales (p = 0,27), pero la varianza no fue homogénea en población y mutación (Levene, p < 0,05) |
| Prueba no paramétrica | Kruskal-Wallis | Confirma el ANOVA sin suponer normalidad ni varianzas iguales |
| Resultado | Población (p = 0,0006), mutación (p < 0,0001) y su interacción (p = 0,002) son significativas; el cruce no (p = 0,18) | Más población y más mutación reducen la tardanza; el efecto de la mutación depende del tamaño de la población |
| Selección | Población 100, cruce 0,8 y mutación 0,5 (ΣT_j promedio 70,7 h) | Es la combinación con menor tardanza promedio; con cruce 0,9 el resultado es prácticamente igual (71,7 h) |
| Rango | La mutación 0,5 quedó en el borde del rango | No se evaluaron niveles fuera del rango; se adoptó la mejor combinación dentro de él. Es una limitación que conviene reconocer |
| Criterio de parada | 50 y 100 generaciones sin mejora, 10 réplicas (semillas 1101–1110) | Con 100 la tardanza baja de 99,4 h a 71,2 h (−28 %) y nunca empeora; Wilcoxon de una cola, p = 0,031. Cuesta unos 1,6 min más por corrida |
| Prueba de una cola | Se probó si 100 mejora a 50 (no si son distintos) | Con la misma semilla, la corrida de 100 continúa la de 50: no puede terminar peor, así que la dirección se conoce de antemano |

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

El script repite las 5 corridas de la configuración elegida (100; 0,8; 0,5) y las
compara con las guardadas. El resultado esperado es "5 de 5 corridas reproducidas
exactamente". Con `--combinacion 50,0.7,0.1` pueden probar cualquier otra combinación.

### 2.2 Reproducción completa (≈ 2–3 horas en Colab; se puede pausar)

```bash
python calibracion_ag.py diseno ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx --instancia real
python calibracion_ag.py parada ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx --instancia real
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
(142,06; 118,90 y 107,32 h), la media general (122,76 h) y n = 45 por nivel:
SC = 45 · Σ (media_nivel − media general)² ≈ 28.162.

El programa que arma este Excel es `fase2/anova_excel.py`.

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
- **¿Por qué la probabilidad de cruce es 0,8 si no fue significativa?** Se eligió la
  combinación completa con menor tardanza promedio. Como el cruce no influye de forma
  significativa, con 0,9 el resultado es prácticamente el mismo (70,7 h frente a 71,7 h).
- **La mutación quedó en el borde del rango (0,5), ¿cómo saben que es la mejor?** No se
  sabe fuera del rango: el estudio se limitó a los niveles usuales en la literatura y se
  adoptó la mejor combinación dentro de ellos. Se reconoce como limitación; tasas de
  mutación mucho mayores acercan el AG a una búsqueda aleatoria.
- **¿Por qué una prueba de una cola en el criterio de parada?** Con la misma semilla, la
  corrida con 100 generaciones sin mejora es la de 50 continuada, así que no puede
  terminar peor; solo cabe preguntar si mejora. Con la prueba de dos colas y solo 5
  diferencias distintas de cero, el valor p mínimo posible era 0,0625.
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
