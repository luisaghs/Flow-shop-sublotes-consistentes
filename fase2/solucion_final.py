# -*- coding: utf-8 -*-
"""
Corre el AG con los parámetros calibrados sobre la instancia real (varias
réplicas en paralelo), guarda el resumen por réplica y la mejor solución
(tablas, indicadores, Gantt y curva de convergencia) para el documento.

Uso: python solucion_final.py ruta/modelo.py ruta/BD_HFS.xlsx [réplicas]
"""
import os, sys, json, time, io, contextlib, importlib.util
import multiprocessing as mp
os.environ.setdefault('MPLBACKEND', 'Agg')
import pandas as pd

PARAMS = {'poblacion': 150, 'prob_cruce': 0.9, 'prob_mutacion': 0.5,
          'sin_mejora': 100, 'generaciones': 1000}
SEMILLA_BASE = 1200
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salida_solucion')
_M = None


def _cargar(ruta_modelo, ruta_bd):
    spec = importlib.util.spec_from_file_location('modelo_ag', ruta_modelo)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    with contextlib.redirect_stdout(io.StringIO()):
        m.cargar_datos(ruta_bd)
    return m


def _init(rm, rb):
    global _M
    _M = _cargar(rm, rb)


def _correr(semilla):
    _M.GA_PARAMS.update(PARAMS)
    _M.GA_PARAMS['semilla'] = semilla
    regla = _M.mejor_de(_M.evaluar_reglas())
    t0 = time.time()
    mejor, hist = _M.algoritmo_genetico(verbose=False,
                                        individuo_semilla=_M.individuo_regla_ls(regla['secuencia']))
    seg = time.time() - t0
    ind = _M.calcular_indicadores(_M.simular_hfs(mejor)[0])
    mejor.pop('_eval', None)
    serial = {'k': mejor['k'], 'proporciones': mejor['proporciones'],
              'posiciones': {str(s): [list(x) for x in v] for s, v in mejor['posiciones'].items()}}
    return {'semilla': semilla, 'suma_T': ind['suma_Ti'], 'Cmax': ind['Cmax'],
            'tardias': ind['num_tardy'], 'Tmax': ind['Tmax'], 'generaciones': len(hist),
            'segundos': seg, 'historial': hist, 'individuo': serial}


def main(rm, rb, n):
    os.makedirs(DIR, exist_ok=True)
    with mp.Pool(min(n, os.cpu_count() or 1), initializer=_init, initargs=(rm, rb)) as pool:
        res = pool.map(_correr, [SEMILLA_BASE + r for r in range(1, n + 1)])
    pd.DataFrame([{k: v for k, v in r.items() if k not in ('historial', 'individuo')} for r in res]) \
        .to_csv(os.path.join(DIR, 'replicas.csv'), index=False, encoding='utf-8-sig')
    mejor = min(res, key=lambda r: (round(r['suma_T'], 6), round(r['Cmax'], 6)))
    with open(os.path.join(DIR, 'mejor_solucion.json'), 'w', encoding='utf-8') as fh:
        json.dump(mejor, fh)
    print(pd.read_csv(os.path.join(DIR, 'replicas.csv')).to_string(index=False))
    print('Mejor semilla:', mejor['semilla'])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 10)
