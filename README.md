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
| Trabajos | Orden de trabajo, Codigo Producto, Cantidad (pares o docenas), r_j Liberación (o Fecha de liberación), d_j horas (o Fechas de entrega) |
| Disponibilidad | Fecha, Horas disponibles, Horas acumuladas final día — convierte horas laborables en fechas (festivos con 0 horas) |

Las etapas se toman en el orden en que aparecen en la hoja de tiempos.

## Modelo

* **Sublotes consistentes**: cada orden se divide en 10 sublotes de tamaño
  variable (múltiplos de media docena), y cada sublote mantiene su tamaño en
  todas las etapas. Un sublote pasa a la etapa siguiente en cuanto termina.
* Cromosoma de dos niveles: (1) proporciones de los tamaños de sublote de
  cada orden, (2) secuencia de los sublotes en cada etapa. La máquina la
  elige el decodificador con la regla del menor tiempo de terminación (ECT).
* Alistamiento de 4,98 min en troquelado por cambio de referencia.
* Población inicial aleatoria, sembrada con la mejor regla de despacho
  (FIFO, EDD, SPT, LPT, MST, CR).
* Cruce: aritmético con peso aleatorio λ en los tamaños y cruce de orden
  (OX) dentro de cada etapa en las secuencias. Mutación por intercambio de
  dos sublotes y perturbación normal de los tamaños.
* Objetivo: ΣTj (tardanza total) con desempate por Cmax.
