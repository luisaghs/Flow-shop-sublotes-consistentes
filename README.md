# HFS con lot streaming — sublotes consistentes (GA)

Programación de un Hybrid Flow Shop para la producción de guantes industriales
con **sublotes consistentes** (escenario 2 de Gürsoy Yılmaz & Yılmaz, 2022,
*Computers & Industrial Engineering* 173, 108745) y un algoritmo genético.

## Uso

```bash
pip install pandas openpyxl matplotlib
python final_sc_hfsagls.py            # usa BD_HFS.xlsx del mismo directorio
python final_sc_hfsagls.py otra_ruta/BD_HFS.xlsx
```

En Google Colab: sube `BD_HFS.xlsx` al panel de archivos (`/content`) y ejecuta
el script.

## Datos de entrada (`BD_HFS.xlsx`)

| Hoja | Columnas usadas |
|---|---|
| Tiempo de procesamiento | Codigo producto, Maquina, Etapa, min x docena (o h x docena) |
| Trabajos | Orden de trabajo, Codigo Producto, Cantidad (pares/docenas), Fecha de liberación, Fechas de entrega, Horas disponibles |
| Disponibilidad (opcional) | Fecha, Horas disponibles, Horas acumuladas — convierte horas laborables en fechas |

Las etapas se toman en el orden en que aparecen en la hoja de tiempos. Las
fechas de entrega son las **Horas disponibles** de cada trabajo.

## Modelo

* **Sublotes consistentes**: los sublotes de un lote pueden tener tamaños
  distintos, pero cada sublote mantiene su tamaño en todas las etapas.
* Cromosoma de tres niveles: (1) tamaños de sublote, (2) orden de los
  sublotes en cada etapa, (3) máquina de cada sublote en cada etapa.
* Escenario 2: población inicial con asignación aleatoria.
* Cruce de uno (C1) o dos puntos (C2) por etapas y mutación por intercambio,
  además de mutaciones sobre el número y el tamaño de los sublotes.
* Objetivo: ΣTi (tardanza total) con desempate por Cmax, o Cmax
  (`FUNCION_OBJETIVO`).

## Versión escenario 2 (`final_sc_hfsagls_S2.py`)

* Número fijo de sublotes por lote (`NUM_SUBLOTES`, B = 10) con tamaños
  variables y consistentes; posiciones iniciales aleatorias.
* Cruce del nivel 1 (tamaños): aritmético con α ~ U(0,25; 0,75) por lote
  (`GA_PARAMS['alfa_cruce']`). Los dos hijos son complementarios y distintos:
  hijo 1 = α·p1 + (1−α)·p2, hijo 2 = (1−α)·p1 + α·p2.

```bash
python final_sc_hfsagls_S2.py BD_HFS.xlsx
```
