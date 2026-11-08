# -*- coding: utf-8 -*-
"""
VERIFICAR QUE LA CALIBRACIÓN SE PUEDE REPRODUCIR
=============================================================================
Vuelve a correr, en su propio computador, las corridas de una combinación del
diseño factorial (las mismas semillas y el mismo presupuesto) y compara la
tardanza total y el makespan con los valores guardados en
salida_calibracion/corridas_diseno.csv.

El algoritmo usa una semilla fija por corrida: con el mismo código y los
mismos datos, cada corrida debe dar exactamente el mismo resultado. Solo
cambia el tiempo de cómputo, que depende del computador.

Uso (en Colab o en su computador):
  python verificar_reproduccion.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx
  python verificar_reproduccion.py modelo.py BD_HFS.xlsx --combinacion 50,0.7,0.1 --replicas 1,2

Tiempo aproximado: 1,5 a 3 minutos por corrida.
"""
import os
import sys
import time
import argparse

os.environ.setdefault('MPLBACKEND', 'Agg')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import calibracion_ag as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('modelo')
    ap.add_argument('bd')
    ap.add_argument('--combinacion', default='150,0.9,0.5',
                    help='población,cruce,mutación (por defecto la configuración elegida)')
    ap.add_argument('--replicas', default='1,2,3,4,5', help='réplicas a repetir, p. ej. 1,2')
    a = ap.parse_args()

    p, c, m = a.combinacion.split(',')
    clave = {'poblacion': int(p), 'prob_cruce': float(c), 'prob_mutacion': float(m)}
    replicas = [int(r) for r in a.replicas.split(',')]
    guardadas = pd.read_csv(os.path.join(C.DIR_BASE, 'salida_calibracion', 'corridas_diseno.csv'))

    C._iniciar_proceso(os.path.abspath(a.modelo), os.path.abspath(a.bd))
    print(f"Combinación {clave}, presupuesto {C.PRESUPUESTO} cromosomas por corrida\n")
    print(f"{'Réplica':>7} | {'Semilla':>7} | {'ΣTj guardada':>12} | {'ΣTj nueva':>10} | "
          f"{'Cmax guardado':>13} | {'Cmax nuevo':>10} | {'¿Igual?':>7} | Tiempo")
    iguales = 0
    for r in replicas:
        semilla = C.SEMILLA_BASE + r
        tarea = {'clave': clave, 'semilla': semilla,
                 'params': {**clave, 'generaciones': C.PRESUPUESTO // clave['poblacion'],
                            'sin_mejora': 10 ** 9}}
        t0 = time.time()
        nuevo = C._correr(tarea)
        fila = guardadas[(guardadas['poblacion'] == clave['poblacion'])
                         & (abs(guardadas['prob_cruce'] - clave['prob_cruce']) < 1e-9)
                         & (abs(guardadas['prob_mutacion'] - clave['prob_mutacion']) < 1e-9)
                         & (guardadas['semilla'] == semilla)]
        if fila.empty:
            print(f"{r:>7} | {semilla:>7} | no está en el CSV")
            continue
        g = fila.iloc[0]
        igual = abs(g['suma_T'] - nuevo['suma_T']) < 1e-6 and abs(g['Cmax'] - nuevo['Cmax']) < 1e-6
        iguales += igual
        print(f"{r:>7} | {semilla:>7} | {g['suma_T']:>12.4f} | {nuevo['suma_T']:>10.4f} | "
              f"{g['Cmax']:>13.4f} | {nuevo['Cmax']:>10.4f} | {'sí' if igual else 'NO':>7} | "
              f"{time.time() - t0:.0f} s")
    print(f"\n{iguales} de {len(replicas)} corridas reproducidas exactamente.")
    if iguales < len(replicas):
        print("Si hay diferencias, revise que usa la misma versión del modelo y del Excel. Con "
              "otra versión de Python los números pueden cambiar un poco; en ese caso, repita el "
              "experimento completo y compare las conclusiones (qué factores son significativos y "
              "cuál es la mejor combinación).")


if __name__ == '__main__':
    main()
