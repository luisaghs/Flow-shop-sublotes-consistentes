# -*- coding: utf-8 -*-
"""
Figuras de la programación propuesta (mejor solución, semilla 1203) para el documento:
  gantt_etapa1.png … gantt_etapa4.png : diagrama de Gantt de cada etapa
  ruta_J07.png                        : ruta de los sublotes de una orden por las etapas

Las figuras las dibuja el modelo (final_sc_hfsagls_S2_4.py, sección 13); este programa
solo carga la mejor solución guardada y las guarda sin título (el título va en la
leyenda de la figura del documento).

Uso (desde la raíz del repositorio): python docs/fase2_figuras/gantt_por_etapa.py [orden]
"""
import os
import sys
import io
import json
import contextlib
import importlib.util

os.environ.setdefault('MPLBACKEND', 'Agg')

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIR = os.path.dirname(os.path.abspath(__file__))


def cargar():
    spec = importlib.util.spec_from_file_location('modelo', os.path.join(RAIZ, 'final_sc_hfsagls_S2_4.py'))
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with contextlib.redirect_stdout(io.StringIO()):
        M.cargar_datos(os.path.join(RAIZ, 'BD_HFS.xlsx'))
    mejor = json.load(open(os.path.join(RAIZ, 'fase2', 'salida_solucion', 'mejor_solucion.json'),
                           encoding='utf-8'))
    ind = mejor['individuo']
    ind = {'k': {j: int(v) for j, v in ind['k'].items()}, 'proporciones': ind['proporciones'],
           'posiciones': {int(s): [tuple(x) for x in v] for s, v in ind['posiciones'].items()}}
    return M, ind


def main():
    orden = sys.argv[1] if len(sys.argv) > 1 else 'J07'
    M, ind = cargar()
    for nombre, fig in M.figuras_gantt(ind, orden_ruta=orden, titulo=False).items():
        archivo = f'gantt_{nombre}.png' if nombre.startswith('etapa') else f'{nombre}.png'
        fig.savefig(os.path.join(DIR, archivo), dpi=200, bbox_inches='tight')
    print('Figuras guardadas en', DIR)


if __name__ == '__main__':
    main()
