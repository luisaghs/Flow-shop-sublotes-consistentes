# -*- coding: utf-8 -*-
"""
Experimentos solicitados en la revisión del documento (10 réplicas cada uno, semillas
1201 a 1210, parámetros calibrados del modelo):

  A  B̄ = 10, población sembrada con la regla EDD   (configuración del trabajo)
  B  B̄ = 15, población sembrada con la regla EDD   (¿por qué no 15 sublotes?)
  C  B̄ = 10, población inicial solo aleatoria       (¿cuánto aporta EDD y cuánto el AG?)

Para cada corrida se guarda el resultado final, la solución inicial (mejor de la
generación 0) y la convergencia (mejor ΣTj y Cmax por generación).

Uso: python experimentos_revision.py ruta/modelo.py ruta/BD_HFS.xlsx [procesos]
Salida: fase2/salida_revision/corridas.csv y convergencia.json. Si se interrumpe, al
repetir el comando continúa con las corridas que falten.
"""
import os, sys, json, time, io, contextlib, importlib.util
import multiprocessing as mp
os.environ.setdefault('MPLBACKEND', 'Agg')
import pandas as pd

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salida_revision')
SEMILLAS = list(range(1201, 1211))
CONFIGS = {'A': {'B': 10, 'edd': True}, 'B': {'B': 15, 'edd': True}, 'C': {'B': 10, 'edd': False}}
_M = None


def _init(rm, rb):
    global _M
    spec = importlib.util.spec_from_file_location('modelo_ag', rm)
    _M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_M)
    with contextlib.redirect_stdout(io.StringIO()):
        _M.cargar_datos(rb)


def _correr(tarea):
    conf, semilla = tarea
    c = CONFIGS[conf]
    _M.NUM_SUBLOTES = c['B']
    _M.GA_PARAMS['semilla'] = semilla
    regla = _M.mejor_de(_M.evaluar_reglas())
    sem = _M.individuo_regla_ls(regla['secuencia']) if c['edd'] else None
    t0 = time.time()
    mejor, hist = _M.algoritmo_genetico(verbose=False, individuo_semilla=sem)
    seg = time.time() - t0
    C, _ = _M.simular_hfs(mejor)
    ind = _M.calcular_indicadores(C)
    gen_cero = next((g for g, (t, _) in enumerate(hist) if t <= 1e-9), None)
    fila = {'config': conf, 'B': c['B'], 'siembra_EDD': c['edd'], 'semilla': semilla,
            'regla': regla['regla'], 'regla_suma_T': regla['suma_Ti'], 'regla_Cmax': regla['Cmax'],
            'regla_tardias': regla['num_tardy'],
            'ini_suma_T': hist[0][0], 'ini_Cmax': hist[0][1],
            'suma_T': ind['suma_Ti'], 'Cmax': ind['Cmax'], 'tardias': ind['num_tardy'], 'Tmax': ind['Tmax'],
            'gen_tardanza_cero': gen_cero, 'generaciones': len(hist), 'segundos': round(seg, 1)}
    return fila, [[round(t, 4), round(cm, 4)] for t, cm in hist]


def main(rm, rb, procesos):
    os.makedirs(DIR, exist_ok=True)
    ruta_csv, ruta_json = os.path.join(DIR, 'corridas.csv'), os.path.join(DIR, 'convergencia.json')
    hechas = pd.read_csv(ruta_csv) if os.path.isfile(ruta_csv) else pd.DataFrame()
    conv = json.load(open(ruta_json, encoding='utf-8')) if os.path.isfile(ruta_json) else {}
    listas = set(zip(hechas['config'], hechas['semilla'])) if len(hechas) else set()
    tareas = [(c, s) for c in CONFIGS for s in SEMILLAS if (c, s) not in listas]
    print(f'Corridas pendientes: {len(tareas)}', flush=True)
    with mp.Pool(procesos, initializer=_init, initargs=(rm, rb)) as pool:
        for k, (fila, hist) in enumerate(pool.imap_unordered(_correr, tareas), start=1):
            pd.DataFrame([fila]).to_csv(ruta_csv, mode='a', index=False, header=not os.path.isfile(ruta_csv),
                                        encoding='utf-8-sig' if not os.path.isfile(ruta_csv) else 'utf-8')
            conv[f"{fila['config']}_{fila['semilla']}"] = hist
            with open(ruta_json, 'w', encoding='utf-8') as fh:
                json.dump(conv, fh)
            print(f"[{k}/{len(tareas)}] {fila['config']} semilla {fila['semilla']}: ΣTj = {fila['suma_T']:.2f}, "
                  f"Cmax = {fila['Cmax']:.2f}, {fila['segundos']:.0f} s", flush=True)
    d = pd.read_csv(ruta_csv)
    print(d.groupby('config')[['suma_T', 'Cmax', 'tardias', 'segundos']].mean().round(2))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else (os.cpu_count() or 1))
