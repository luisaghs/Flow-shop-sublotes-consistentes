# -*- coding: utf-8 -*-
"""
FASE 3 — EVALUACIÓN DEL MODELO PROPUESTO FRENTE AL SISTEMA ACTUAL
=============================================================================

Sistema actual (representación calibrada): regla FIFO por etapa — en troquelado
las órdenes se atienden por orden de liberación y en cada etapa siguiente los
sublotes se atienden en el orden en que llegan de la etapa anterior —, con cada
orden dividida en B partes iguales y la máquina elegida por la regla ECT.
B se calibró con la tasa histórica de incumplimiento (≈ 45 %): B = 4 y 5 dan
70 % y B = 6 a 8 dan 40 %. Escenario base: B = 6, el menor número de partes con
el porcentaje más cercano al histórico. Sensibilidad: 5 y 7 partes.

Modelo propuesto: el algoritmo genético calibrado (final_sc_hfsagls_S2_4.py).

Experimentos (todos con semillas nuevas, distintas de las de la Fase 2):
  base       : AG con B̄ = 10 y AG con B = 6 (misma división que el sistema
               actual), 30 réplicas cada uno (semillas 3001–3030).
  sensib.    : AG con B = 5 y 7 (sistema actual con 5 y 7 partes), 10 réplicas
               (semillas 3001–3010). No se evalúan más de 10 sublotes por orden por
               la complejidad logística y de control que implican.
  exigencia  : fechas de entrega 10 % y 20 % más ajustadas y demanda 10 % y 20 %
               mayor; sistema actual (B = 6) frente a AG (B̄ = 10), 10 réplicas.

Uso:
  python experimentos_fase3.py correr ruta/modelo.py ruta/BD_HFS.xlsx [--procesos 4] [--grupo base]
  python experimentos_fase3.py analizar ruta/modelo.py ruta/BD_HFS.xlsx

Cada corrida se guarda al terminar en salida_fase3/corridas_ag.csv; si se
interrumpe, al repetir el comando continúa con las que faltan.
"""
import os
import io
import sys
import time
import argparse
import contextlib
import importlib.util
import multiprocessing as mp

os.environ.setdefault('MPLBACKEND', 'Agg')
import pandas as pd

try:
    from scipy import stats
except ImportError:
    stats = None

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salida_fase3')
B_ACTUAL_BASE = 6
B_ACTUAL_SENS = (B_ACTUAL_BASE - 1, B_ACTUAL_BASE, B_ACTUAL_BASE + 1)
SEM_BASE = list(range(3001, 3031))
SEM_SENS = list(range(3001, 3011))

# Escenarios: nombre → (factor sobre la ventana d_j − r_j, factor sobre la demanda)
ESCENARIOS = {
    'base':       (1.0, 1.0),
    'fechas_-10': (0.9, 1.0),
    'fechas_-20': (0.8, 1.0),
    'demanda_+10': (1.0, 1.1),
    'demanda_+20': (1.0, 1.2),
}
DESCRIPCION = {
    'base': 'Caso de estudio',
    'fechas_-10': 'Fechas de entrega 10 % más ajustadas',
    'fechas_-20': 'Fechas de entrega 20 % más ajustadas',
    'demanda_+10': 'Demanda 10 % mayor',
    'demanda_+20': 'Demanda 20 % mayor',
}

# Corridas del AG: (grupo, escenario, B del AG, semillas)
PLAN = (
    [('base', 'base', 10, SEM_BASE), ('base', 'base', B_ACTUAL_BASE, SEM_BASE)]
    + [('sensibilidad', 'base', B, SEM_SENS) for B in (B_ACTUAL_BASE - 1, B_ACTUAL_BASE + 1)]
    + [('exigencia', e, 10, SEM_SENS) for e in ESCENARIOS if e != 'base']
)

# ---------------------------------------------------------------------------
# Modelo y escenarios
# ---------------------------------------------------------------------------

_M = None
_BASE = None


def cargar(ruta_modelo, ruta_bd):
    spec = importlib.util.spec_from_file_location('modelo_ag', ruta_modelo)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with contextlib.redirect_stdout(io.StringIO()):
        M.cargar_datos(ruta_bd)
    base = {'DUE_DATE': dict(M.DUE_DATE), 'DEMANDA': dict(M.DEMANDA)}
    return M, base


def aplicar_escenario(M, base, escenario):
    """Ajusta fechas de entrega y demanda según el escenario (sobre los datos base)."""
    f_d, f_q = ESCENARIOS[escenario]
    M.DUE_DATE.clear(); M.DEMANDA.clear()
    for j in M.TRABAJOS:
        r = M.RELEASE[j]
        M.DUE_DATE[j] = r + f_d * (base['DUE_DATE'][j] - r)
        M.DEMANDA[j] = float(round(base['DEMANDA'][j] * f_q))


def indicadores(M, ind):
    """Indicadores de desempeño de una programación."""
    C, g = M.simular_hfs(ind)
    r = M.calcular_indicadores(C)
    n = len(M.TRABAJOS)
    cmax = r['Cmax']
    ocup = {}
    for s in M.ETAPAS:
        ocupado = sum(f - i for (_, _, _, i, f) in g[s])
        ocup[s] = 100.0 * ocupado / (len(M.MAQUINAS_POR_ETAPA[s]) * cmax)
    al = g['alistamientos']
    return {
        'tardias': r['num_tardy'], 'pct_tardias': 100.0 * r['num_tardy'] / n,
        'suma_T': r['suma_Ti'], 'T_prom': r['suma_Ti'] / n, 'T_max': r['Tmax'],
        'suma_E': r['suma_Ei'], 'Cmax': cmax, 'flujo_medio': r['media_Fi'],
        'ocup_troquelado': ocup[M.ETAPAS[0]], 'ocup_ensamble': ocup[M.ETAPAS[1]],
        'ocup_costura': ocup[M.ETAPAS[2]], 'ocup_volteado': ocup[M.ETAPAS[3]],
        'alistamientos': len(al), 'h_alistamiento': sum(f - i for (_, _, i, f) in al),
    }


def individuo_fifo_por_etapa(M, B):
    """Sistema actual: FIFO por etapa con B partes iguales por orden."""
    M.NUM_SUBLOTES = B
    ind = M.individuo_regla_ls(list(M.TRABAJOS))         # troquelado: orden de liberación
    orden = {j: k for k, j in enumerate(M.TRABAJOS)}
    for s in M.ETAPAS[1:]:
        _, g = M.simular_hfs(ind)
        llegada = {(j, b): f for (j, b, m, i, f) in g[s - 1]}
        ind['posiciones'][s] = sorted(ind['posiciones'][s],
                                      key=lambda x: (llegada[x], orden[x[0]], x[1]))
    return ind


def individuo_regla(M, B, regla):
    M.NUM_SUBLOTES = B
    return M.individuo_regla_ls(M.secuencias_reglas()[regla])

# ---------------------------------------------------------------------------
# Corridas del AG en paralelo
# ---------------------------------------------------------------------------

def _init(rm, rb):
    global _M, _BASE
    _M, _BASE = cargar(rm, rb)


def _correr(tarea):
    grupo, escenario, B, semilla = tarea
    aplicar_escenario(_M, _BASE, escenario)
    _M.NUM_SUBLOTES = B
    _M.GA_PARAMS['semilla'] = semilla                   # demás parámetros: los calibrados
    regla = _M.mejor_de(_M.evaluar_reglas())
    t0 = time.time()
    mejor, hist = _M.algoritmo_genetico(verbose=False,
                                        individuo_semilla=_M.individuo_regla_ls(regla['secuencia']))
    seg = time.time() - t0
    return {'grupo': grupo, 'escenario': escenario, 'B': B, 'semilla': semilla,
            'generaciones': len(hist), 'segundos': seg, **indicadores(_M, mejor)}


def correr(rm, rb, procesos, grupos=None):
    os.makedirs(DIR, exist_ok=True)
    ruta = os.path.join(DIR, 'corridas_ag.csv')
    hechas = set()
    if os.path.isfile(ruta):
        prev = pd.read_csv(ruta)
        hechas = set(zip(prev['escenario'], prev['B'], prev['semilla']))
    tareas = [(g, e, B, s) for (g, e, B, sems) in PLAN if not grupos or g in grupos
              for s in sems if (e, B, s) not in hechas]
    # Evitar duplicados (tareas repetidas con el mismo escenario, B y semilla)
    tareas = list(dict.fromkeys(tareas))
    print(f"Corridas pendientes: {len(tareas)} | procesos: {procesos}", flush=True)
    if not tareas:
        return
    t0 = time.time()
    with mp.Pool(procesos, initializer=_init, initargs=(rm, rb)) as pool:
        for k, res in enumerate(pool.imap_unordered(_correr, tareas), start=1):
            pd.DataFrame([res]).to_csv(ruta, mode='a', index=False,
                                       header=not os.path.isfile(ruta))
            falta = (time.time() - t0) / k * (len(tareas) - k)
            print(f"[{k:>3}/{len(tareas)}] {res['escenario']} B={res['B']} semilla={res['semilla']}"
                  f" → tardías={res['tardias']} ΣT={res['suma_T']:.1f} Cmax={res['Cmax']:.1f}"
                  f" ({res['segundos']:.0f} s) | faltan ≈ {falta / 60:.0f} min", flush=True)

# ---------------------------------------------------------------------------
# Programaciones deterministas (sistema actual y reglas)
# ---------------------------------------------------------------------------

def deterministas(rm, rb):
    M, base = cargar(rm, rb)
    filas = []
    for e in ESCENARIOS:
        aplicar_escenario(M, base, e)
        for B in B_ACTUAL_SENS + (10,):
            if e != 'base' and B != B_ACTUAL_BASE:
                continue
            filas.append({'escenario': e, 'metodo': 'Actual (FIFO por etapa)', 'B': B,
                          **indicadores(M, individuo_fifo_por_etapa(M, B))})
            if e == 'base':
                for regla in ('EDD', 'FIFO', 'SPT', 'LPT', 'MST', 'CR'):
                    filas.append({'escenario': e, 'metodo': f'Regla {regla}', 'B': B,
                                  **indicadores(M, individuo_regla(M, B, regla))})
            else:
                filas.append({'escenario': e, 'metodo': 'Regla EDD', 'B': B,
                              **indicadores(M, individuo_regla(M, B, 'EDD'))})
    df = pd.DataFrame(filas)
    df.to_csv(os.path.join(DIR, 'deterministas.csv'), index=False, encoding='utf-8-sig')
    return df

# ---------------------------------------------------------------------------
# Análisis
# ---------------------------------------------------------------------------

IND = [('pct_tardias', '% órdenes tardías'), ('suma_T', 'Tardanza total ΣTj (h)'),
       ('T_prom', 'Tardanza promedio (h)'), ('T_max', 'Tardanza máxima (h)'),
       ('suma_E', 'Adelanto total ΣEj (h)'), ('Cmax', 'Makespan Cmax (h)'),
       ('flujo_medio', 'Tiempo de flujo medio (h)'), ('ocup_troquelado', 'Ocupación troquelado (%)'),
       ('alistamientos', 'Alistamientos en troquelado')]


def _f(x, d=1):
    return '—' if pd.isna(x) else f"{x:,.{d}f}".replace(',', '§').replace('.', ',').replace('§', '.')


def _md(df):
    cab = '| ' + ' | '.join(df.columns) + ' |'
    return '\n'.join([cab, '|' + '---|' * len(df.columns)]
                     + ['| ' + ' | '.join(str(v) for v in r) + ' |' for r in df.itertuples(index=False)])


def _comparar(ag, valor_actual, col):
    """Resumen de las réplicas del AG frente a un valor determinista."""
    x = ag[col].astype(float)
    n = len(x)
    media, desv = x.mean(), x.std(ddof=1) if n > 1 else 0.0
    ic = (stats.t.ppf(0.975, n - 1) * desv / n ** 0.5) if (stats and n > 1) else float('nan')
    p = float('nan')
    if stats is not None and n >= 5 and (x - valor_actual).abs().sum() > 0:
        try:
            p = stats.wilcoxon(x - valor_actual).pvalue
        except ValueError:
            pass
    mejora = 100.0 * (valor_actual - media) / valor_actual if valor_actual else float('nan')
    return media, desv, ic, x.min(), x.max(), p, mejora


def analizar(rm, rb):
    os.makedirs(DIR, exist_ok=True)
    det = deterministas(rm, rb)
    ag = pd.read_csv(os.path.join(DIR, 'corridas_ag.csv'))
    act = lambda e, B: det[(det.escenario == e) & (det.B == B)
                           & (det.metodo == 'Actual (FIFO por etapa)')].iloc[0]
    inf = ['# Fase 3 — Resultados de la evaluación', '']

    # 1. Escenario base: sistema actual frente al AG
    a6 = act('base', B_ACTUAL_BASE)
    bb = B_ACTUAL_BASE
    for B in (10, B_ACTUAL_BASE):
        g = ag[(ag.escenario == 'base') & (ag.B == B)]
        if g.empty:
            continue
        filas = []
        for col, nombre in IND:
            media, desv, ic, mn, mx, p, mej = _comparar(g, a6[col], col)
            filas.append([nombre, _f(a6[col]), f"{_f(media)} ± {_f(ic)}", _f(desv), _f(mn), _f(mx),
                          _f(mej) + ' %', '—' if pd.isna(p) else (f'{p:.2g}' if p >= 1e-4 else '< 0,0001')])
        tab = pd.DataFrame(filas, columns=['Indicador', f'Actual (B = {bb})', f'AG media ± IC 95 %',
                                           'Desv.', 'Mín.', 'Máx.', 'Mejora', 'Wilcoxon p'])
        inf += [f"## 1.{'a' if B == 10 else 'b'} Escenario base: sistema actual (B = {bb}) frente al "
                f"AG con {'B̄ = 10' if B == 10 else f'B = {bb}'} ({len(g)} réplicas)", '', _md(tab), '']

    # 2. Descomposición de la mejora (escenario base)
    pasos = [(f'Sistema actual: FIFO por etapa, B = {bb}', a6['pct_tardias'], a6['suma_T'], a6['Cmax'])]
    edd6 = det[(det.escenario == 'base') & (det.B == bb) & (det.metodo == 'Regla EDD')].iloc[0]
    pasos.append((f'Cambiar solo la regla: EDD, B = {bb}', edd6['pct_tardias'], edd6['suma_T'], edd6['Cmax']))
    edd10 = det[(det.escenario == 'base') & (det.B == 10) & (det.metodo == 'Regla EDD')].iloc[0]
    pasos.append(('Regla EDD con B̄ = 10 (sin AG)', edd10['pct_tardias'], edd10['suma_T'], edd10['Cmax']))
    for B, txt in ((bb, f'Optimizar con la misma división: AG, B = {bb}'),
                   (10, 'Además, dividir más: AG, B̄ = 10')):
        g = ag[(ag.escenario == 'base') & (ag.B == B)]
        if not g.empty:
            pasos.append((txt + ' (media)', g.pct_tardias.mean(), g.suma_T.mean(), g.Cmax.mean()))
    tab = pd.DataFrame([[p[0], _f(p[1]) + ' %', _f(p[2]), _f(p[3])] for p in pasos],
                       columns=['Paso', '% tardías', 'ΣTj (h)', 'Cmax (h)'])
    inf += ['## 2. Descomposición de la mejora (escenario base)', '', _md(tab), '']

    # 3. Sensibilidad a la representación del sistema actual
    filas = []
    g10 = ag[(ag.escenario == 'base') & (ag.B == 10)]
    for B in B_ACTUAL_SENS:
        a = act('base', B)
        gB = ag[(ag.escenario == 'base') & (ag.B == B)]
        filas.append([f'B = {B}', f"{_f(a.pct_tardias, 0)} % / {_f(a.suma_T)}",
                      '—' if gB.empty else f"{_f(gB.pct_tardias.mean(), 0)} % / {_f(gB.suma_T.mean())}",
                      '—' if g10.empty else f"{_f(g10.pct_tardias.mean(), 0)} % / {_f(g10.suma_T.mean())}"])
    tab = pd.DataFrame(filas, columns=['Sistema actual', 'Actual: % tardías / ΣTj',
                                       'AG misma B: % tardías / ΣTj (media)',
                                       'AG B̄ = 10: % tardías / ΣTj (media)'])
    inf += ['## 3. Sensibilidad al número de partes del sistema actual', '', _md(tab), '']

    # 4. Sensibilidad al número de sublotes del modelo propuesto
    filas = []
    for B in B_ACTUAL_SENS + (10,):
        g = ag[(ag.escenario == 'base') & (ag.B == B)]
        if not g.empty:
            filas.append([B, len(g), _f(g.pct_tardias.mean(), 0) + ' %', _f(g.suma_T.mean()),
                          _f(g.Cmax.mean()), _f(g.segundos.mean() / 60)])
    inf += ['## 4. Sensibilidad al número de sublotes del modelo propuesto', '',
            _md(pd.DataFrame(filas, columns=['B̄', 'Réplicas', '% tardías', 'ΣTj prom. (h)',
                                             'Cmax prom. (h)', 'Tiempo prom. (min)'])), '']

    # 5. Escenarios de exigencia
    filas = []
    for e in ESCENARIOS:
        a = act(e, B_ACTUAL_BASE)
        g = ag[(ag.escenario == e) & (ag.B == 10)]
        if g.empty:
            continue
        _, _, _, _, _, p, mej = _comparar(g, a['suma_T'], 'suma_T')
        filas.append([DESCRIPCION[e], f"{_f(a.pct_tardias, 0)} % / {_f(a.suma_T)}",
                      f"{_f(g.pct_tardias.mean(), 0)} % / {_f(g.suma_T.mean())}", _f(mej) + ' %',
                      '—' if pd.isna(p) else f'{p:.2g}'])
    inf += [f'## 5. Escenarios de exigencia (actual B = {bb} frente a AG B̄ = 10)', '',
            _md(pd.DataFrame(filas, columns=['Escenario', 'Actual: % tardías / ΣTj',
                                             'AG: % tardías / ΣTj (media)', 'Mejora ΣTj',
                                             'Wilcoxon p'])), '']

    # 6. Reglas de despacho (referencia, escenario base)
    r6 = det[(det.escenario == 'base') & (det.B == bb)][['metodo', 'pct_tardias', 'suma_T', 'Cmax']]
    r6 = r6.assign(pct_tardias=r6.pct_tardias.map(lambda v: _f(v, 0) + ' %'),
                   suma_T=r6.suma_T.map(_f), Cmax=r6.Cmax.map(_f))
    r6.columns = [f'Método (B = {bb})', '% tardías', 'ΣTj (h)', 'Cmax (h)']
    inf += [f'## 6. Reglas de despacho de referencia (escenario base, B = {bb})', '', _md(r6), '']

    grafico_base(ag, a6)
    with open(os.path.join(DIR, 'informe_fase3.md'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(inf) + '\n')
    print('\n'.join(inf))


def grafico_base(ag, a6):
    import matplotlib.pyplot as plt
    g6 = ag[(ag.escenario == 'base') & (ag.B == B_ACTUAL_BASE)]
    g10 = ag[(ag.escenario == 'base') & (ag.B == 10)]
    if g6.empty and g10.empty:
        return
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    for ax, col, tit in ((axes[0], 'suma_T', 'Tardanza total ΣTj (h)'),
                         (axes[1], 'pct_tardias', '% de órdenes tardías')):
        datos, etiquetas = [], []
        for g, et in ((g6, f'AG, B = {B_ACTUAL_BASE}'), (g10, 'AG, B̄ = 10')):
            if not g.empty:
                datos.append(g[col].values); etiquetas.append(et)
        ax.boxplot(datos, labels=etiquetas, widths=0.5)
        ax.axhline(a6[col], color='#E15759', ls='--', lw=1.5, label=f'Sistema actual (B = {B_ACTUAL_BASE})')
        ax.set_title(tit, fontsize=10); ax.grid(axis='y', ls=':', alpha=0.5)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(DIR, 'comparacion_base.png'), dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('accion', choices=['correr', 'analizar'])
    ap.add_argument('modelo')
    ap.add_argument('bd')
    ap.add_argument('--procesos', type=int, default=os.cpu_count() or 1)
    ap.add_argument('--grupo', action='append', choices=['base', 'sensibilidad', 'exigencia'])
    a = ap.parse_args()
    rm, rb = os.path.abspath(a.modelo), os.path.abspath(a.bd)
    if a.accion == 'correr':
        correr(rm, rb, a.procesos, a.grupo)
    analizar(rm, rb)


if __name__ == '__main__':
    main()
