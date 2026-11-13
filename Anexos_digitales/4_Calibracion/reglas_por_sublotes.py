# -*- coding: utf-8 -*-
"""
Tardanza total y órdenes tardías de las reglas de despacho según el número de sublotes
por orden (Tabla 9 del documento). Cada orden se divide en B sublotes iguales y se
programa con el decodificador del modelo (sin algoritmo genético).

Uso (desde la raíz del repositorio):
  python fase2/reglas_por_sublotes.py [final_sc_hfsagls_S2_4.py] [BD_HFS.xlsx]
Salida: fase2/salida_calibracion/reglas_por_sublotes.csv
"""
import os, sys, io, contextlib, importlib.util
os.environ.setdefault('MPLBACKEND', 'Agg')
import pandas as pd

VALORES_B = (1, 2, 5, 10, 15)
REGLAS = ('FIFO', 'EDD', 'CR', 'SPT', 'LPT')
DIR = os.environ.get('SALIDA_CALIBRACION') or \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salida_calibracion')


def main(ruta_modelo, ruta_bd):
    spec = importlib.util.spec_from_file_location('modelo', ruta_modelo)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with contextlib.redirect_stdout(io.StringIO()):
        M.cargar_datos(ruta_bd)
    filas = []
    for B in VALORES_B:
        M.NUM_SUBLOTES = B
        sec = M.secuencias_reglas()
        for rg in REGLAS:
            r = M.calcular_indicadores(M.simular_hfs(M.individuo_regla_ls(sec[rg]))[0])
            filas.append({'B': B, 'Regla': rg, 'Tardanza total (h)': round(r['suma_Ti'], 2),
                          'Órdenes tardías': r['num_tardy'], 'Tardanza máxima (h)': round(r['Tmax'], 2),
                          'Makespan (h)': round(r['Cmax'], 2)})
    df = pd.DataFrame(filas)
    os.makedirs(DIR, exist_ok=True)
    ruta = os.path.join(DIR, 'reglas_por_sublotes.csv')
    df.to_csv(ruta, index=False, encoding='utf-8-sig')
    print(df.pivot(index='B', columns='Regla', values='Tardanza total (h)').round(0).to_string())
    print('Guardado en', ruta)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'final_sc_hfsagls_S2_4.py',
         sys.argv[2] if len(sys.argv) > 2 else 'BD_HFS.xlsx')
