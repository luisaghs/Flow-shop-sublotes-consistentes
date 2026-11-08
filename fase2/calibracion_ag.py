# -*- coding: utf-8 -*-
"""
CALIBRACIÓN DE LOS PARÁMETROS DEL ALGORITMO GENÉTICO (FASE 2)
=============================================================================

Experimento 1 — diseño factorial completo (3 factores × 3 niveles = 27
combinaciones) sobre la instancia real de BD_HFS.xlsx:

    población         : 50, 100, 150
    probabilidad cruce: 0,7  0,8  0,9
    prob. mutación    : 0,1  0,3  0,5

  * Cada corrida tiene el MISMO presupuesto de cómputo: un número fijo de
    individuos generados (población × generaciones). Así una población grande
    no gana solo por usar más evaluaciones.
  * Números aleatorios comunes: la réplica r usa la misma semilla en todas las
    combinaciones, de modo que las diferencias se deben a los parámetros.
  * Respuesta principal: ΣTj [h]; secundaria: RPD del Cmax. Las pruebas de
    rangos usan Z = 1000·ΣTj + Cmax, que ordena igual que el objetivo
    lexicográfico (primero ΣTj, luego Cmax).
  * Análisis: ANOVA (efectos principales e interacciones dobles), gráficos de
    medias con intervalos LSD al 95 %, supuestos (Shapiro-Wilk, Levene),
    Kruskal-Wallis y comparación pareada (Wilcoxon) con la configuración actual.

Experimento 2 — criterio de parada: con la configuración seleccionada se compara la
parada tras 50 y 100 generaciones sin mejora (10 réplicas, semillas 1101 a 1110)
en calidad y tiempo, con una prueba de Wilcoxon pareada de una cola.

Opción no usada en el trabajo — ampliación: si la mejor combinación queda en el
borde del rango, la acción 'ampliacion' permite probar niveles más allá con las
mismas semillas. En la calibración del trabajo no se ejecutó: se adoptó la mejor
combinación dentro del rango del diseño.

Salidas en salida_calibracion/ (ver LEEME.md de esa carpeta): resultados en la
carpeta principal y archivos de control del proceso en salida_calibracion/control/.

Uso:
  python calibracion_ag.py diseno   ruta/modelo.py ruta/BD_HFS.xlsx [--replicas 5]
                                    [--presupuesto 30000] [--procesos 4]
  python calibracion_ag.py parada   ruta/modelo.py ruta/BD_HFS.xlsx
                                    [--config 150,0.9,0.5] [--replicas 10]
  python calibracion_ag.py analizar
  python calibracion_ag.py ampliacion ruta/modelo.py ruta/BD_HFS.xlsx   (opcional, no usada)

  Agregar --prueba para una corrida corta de verificación (otra carpeta).
  Si una corrida se interrumpe, al volver a ejecutar el mismo comando se
  continúa desde donde quedó (las corridas terminadas se guardan en un CSV).

Requiere: pandas, openpyxl, matplotlib; scipy para los valores p
(statsmodels es opcional, solo para contrastar el ANOVA).
"""

import os
import sys
import time
import argparse
import itertools
import importlib.util
import multiprocessing as mp

os.environ.setdefault('MPLBACKEND', 'Agg')

import pandas as pd

try:
    from scipy import stats
except ImportError:                     # sin scipy no hay valores p
    stats = None

# ---------------------------------------------------------------------------
# Configuración del experimento
# ---------------------------------------------------------------------------

FACTORES = {
    'poblacion'    : [50, 100, 150],
    'prob_cruce'   : [0.7, 0.8, 0.9],
    'prob_mutacion': [0.1, 0.3, 0.5],
}
NOMBRE_FACTOR = {'poblacion': 'Población', 'prob_cruce': 'Prob. de cruce',
                 'prob_mutacion': 'Prob. de mutación'}
CONFIG_ACTUAL = {'poblacion': 150, 'prob_cruce': 0.9, 'prob_mutacion': 0.5}

REPLICAS = 5
PRESUPUESTO = 30000            # individuos generados por corrida
SEMILLA_BASE = 1000            # réplica r → semilla SEMILLA_BASE + r
PESO_TARDANZA = 1000.0         # Z = PESO·ΣTj + Cmax (orden lexicográfico)


PARADA_NIVELES = [50, 100]   # generaciones sin mejora (experimento 2)
PARADA_MAX_GEN = 1000
PARADA_REPLICAS = 10

# Instancias de calibración: factor aplicado a la ventana d_j − r_j de cada orden.
# Se calibra con el caso de estudio ('real'). El mecanismo admite otras instancias
# (por ejemplo, {'exigente': 0.8}) por si se quiere calibrar con varias.
INSTANCIAS_CAL = {'real': 1.0}
SUFIJO = {'real': '', 'exigente': '_exigente'}
NOMBRE_INSTANCIA = {'real': 'Caso de estudio',
                    'exigente': 'Instancia exigente (fechas de entrega 20 % más ajustadas)'}
INSTANCIA = 'real'

DIR_BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Ejecución de una corrida (en un proceso de trabajo)
# ---------------------------------------------------------------------------

_M = None          # módulo del modelo cargado en cada proceso
_SEMILLA_IND = None


def _iniciar_proceso(ruta_modelo, ruta_bd, factor_fechas=1.0):
    """Carga el modelo y los datos una sola vez por proceso. factor_fechas < 1
    ajusta las fechas de entrega: d_j ← r_j + factor·(d_j − r_j)."""
    global _M, _SEMILLA_IND
    import io
    import contextlib
    spec = importlib.util.spec_from_file_location('modelo_ag', ruta_modelo)
    _M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_M)
    with contextlib.redirect_stdout(io.StringIO()):
        _M.cargar_datos(ruta_bd)
    if factor_fechas != 1.0:
        for j in _M.TRABAJOS:
            _M.DUE_DATE[j] = _M.RELEASE[j] + factor_fechas * (_M.DUE_DATE[j] - _M.RELEASE[j])
    regla = _M.mejor_de(_M.evaluar_reglas())
    _SEMILLA_IND = _M.individuo_regla_ls(regla['secuencia'])


def _correr(tarea):
    """Corre el AG con los parámetros de la tarea y retorna sus indicadores."""
    params = dict(_M.GA_PARAMS)
    params.update(tarea['params'])
    params['semilla'] = tarea['semilla']
    _M.GA_PARAMS.clear()
    _M.GA_PARAMS.update(params)
    t0 = time.time()
    mejor, hist = _M.algoritmo_genetico(verbose=False, individuo_semilla=_SEMILLA_IND)
    seg = time.time() - t0
    ind = _M.calcular_indicadores(_M.simular_hfs(mejor)[0])
    final = hist[-1] if hist else (ind['suma_Ti'], ind['Cmax'])
    gen_mejor = next((g + 1 for g, h in enumerate(hist) if h == final), 0)
    return {**tarea['clave'], 'semilla': tarea['semilla'],
            'suma_T': ind['suma_Ti'], 'Cmax': ind['Cmax'], 'tardias': ind['num_tardy'],
            'generaciones': len(hist), 'gen_mejor': gen_mejor,
            'individuos_mejor': gen_mejor * params['poblacion'], 'segundos': seg}


def _ejecutar(tareas, ruta_csv, ruta_modelo, ruta_bd, procesos):
    """Corre las tareas pendientes en paralelo y guarda cada resultado al terminar."""
    hechas = set()
    if os.path.isfile(ruta_csv):
        previas = pd.read_csv(ruta_csv)
        hechas = {tuple(r) for r in previas[list(tareas[0]['clave']) + ['semilla']]
                  .astype(str).itertuples(index=False)} if len(previas) else set()
    pendientes = [t for t in tareas
                  if tuple(str(v) for v in [*t['clave'].values(), t['semilla']]) not in hechas]
    print(f"  Corridas: {len(tareas)} | ya hechas: {len(tareas) - len(pendientes)} | "
          f"pendientes: {len(pendientes)} | procesos: {procesos}", flush=True)
    if not pendientes:
        return
    t0 = time.time()
    with mp.Pool(procesos, initializer=_iniciar_proceso,
                 initargs=(ruta_modelo, ruta_bd, INSTANCIAS_CAL[INSTANCIA])) as pool:
        for k, res in enumerate(pool.imap_unordered(_correr, pendientes), start=1):
            pd.DataFrame([res]).to_csv(ruta_csv, mode='a', index=False,
                                       header=not os.path.isfile(ruta_csv),
                                       encoding='utf-8')
            transcurrido = time.time() - t0
            restante = transcurrido / k * (len(pendientes) - k)
            print(f"  [{k:>3}/{len(pendientes)}] " +
                  " ".join(f"{c}={v}" for c, v in res.items()
                           if c in tareas[0]['clave']) +
                  f" semilla={res['semilla']} → ΣTj={res['suma_T']:.3f} "
                  f"Cmax={res['Cmax']:.3f} ({res['segundos']:.0f} s) | "
                  f"faltan ≈ {restante / 60:.0f} min", flush=True)

# ---------------------------------------------------------------------------
# Experimentos
# ---------------------------------------------------------------------------

def _tareas_factoriales(factores, replicas, presupuesto):
    nombres = list(factores)
    tareas = []
    for niveles in itertools.product(*factores.values()):
        clave = dict(zip(nombres, niveles))
        gens = max(1, presupuesto // clave['poblacion'])
        for r in range(1, replicas + 1):
            tareas.append({
                'clave': clave,
                'params': {**clave, 'generaciones': gens, 'sin_mejora': 10 ** 9},
                'semilla': SEMILLA_BASE + r,
            })
    return tareas


def _arch(nombre, instancia=None):
    return f"{nombre}{SUFIJO[instancia or INSTANCIA]}.csv"


def experimento_diseno(ruta_modelo, ruta_bd, dir_salida, replicas, presupuesto, procesos):
    tareas = _tareas_factoriales(FACTORES, replicas, presupuesto)
    print(f"\nEXPERIMENTO 1 — {NOMBRE_INSTANCIA[INSTANCIA]}: diseño factorial "
          f"{len(tareas) // replicas} combinaciones × {replicas} réplicas, presupuesto "
          f"{presupuesto} individuos por corrida")
    _ejecutar(tareas, os.path.join(dir_salida, _arch('corridas_diseno')),
              ruta_modelo, ruta_bd, procesos)


def _ctrl(dir_salida, nombre):
    """Archivos de control del proceso (no son resultados): van en la subcarpeta control/."""
    os.makedirs(os.path.join(dir_salida, 'control'), exist_ok=True)
    return os.path.join(dir_salida, 'control', nombre)


def _leer_json(dir_salida, nombre):
    import json
    with open(_ctrl(dir_salida, nombre), encoding='utf-8') as fh:
        return json.load(fh)


def experimento_ampliacion(ruta_modelo, ruta_bd, dir_salida, replicas, presupuesto, procesos):
    """Niveles más allá del borde del diseño, alrededor de la mejor combinación
    (calculados por el análisis del diseño en ampliacion_grilla.json)."""
    grilla = _leer_json(dir_salida, 'ampliacion_grilla.json')
    mejor = grilla.pop('_mejor')
    if all(len(v) == 1 for v in grilla.values()):
        print("La mejor combinación no está en el borde: no se requiere ampliación.")
        return
    tareas = [t for t in _tareas_factoriales(grilla, replicas, presupuesto) if t['clave'] != mejor]
    print(f"\nEXPERIMENTO 1b — {NOMBRE_INSTANCIA[INSTANCIA]}: ampliación {grilla}, {replicas} réplicas")
    _ejecutar(tareas, os.path.join(dir_salida, _arch('corridas_ampliacion')),
              ruta_modelo, ruta_bd, procesos)


def experimento_parada(ruta_modelo, ruta_bd, dir_salida, config, replicas, procesos):
    tareas = []
    for sm in PARADA_NIVELES:
        for r in range(1, replicas + 1):
            tareas.append({
                'clave': {'sin_mejora': sm},
                'params': {**config, 'sin_mejora': sm, 'generaciones': PARADA_MAX_GEN},
                'semilla': SEMILLA_BASE + 100 + r,
            })
    print(f"\nEXPERIMENTO 2 — {NOMBRE_INSTANCIA[INSTANCIA]}: criterio de parada {PARADA_NIVELES} "
          f"generaciones sin mejora, configuración {config}, {replicas} réplicas")
    with open(_ctrl(dir_salida, 'config_parada.txt'), 'w', encoding='utf-8') as fh:
        fh.write(str(config))
    _ejecutar(tareas, os.path.join(dir_salida, _arch('corridas_parada')),
              ruta_modelo, ruta_bd, procesos)

# ---------------------------------------------------------------------------
# Análisis estadístico
# ---------------------------------------------------------------------------
#
# Respuesta principal : ΣTj [h] (ANOVA, gráficos de medias).
# Respuesta secundaria: RPD del Cmax respecto al mejor Cmax entre las corridas
#                       con la mejor ΣTj.
# Pruebas de rangos   : Kruskal-Wallis y Wilcoxon sobre Z = PESO·ΣTj + Cmax. Como
#                       solo usan el orden de los datos, ordenar por Z equivale a
#                       ordenar lexicográficamente (primero ΣTj, luego Cmax).

TOL = 1e-3
ETIQUETA = {'suma_T': 'ΣTj promedio (h)', 'Cmax': 'Cmax promedio (h)'}
NOMBRE_RESP = {'suma_T': 'tardanza total ΣTj', 'Cmax': 'makespan Cmax'}


def _respuesta(df):
    """Respuesta de una instancia: ΣTj si varía entre corridas; si es cero en todas,
    Cmax, que es el criterio secundario del objetivo lexicográfico."""
    return 'suma_T' if df['suma_T'].max() > TOL else 'Cmax'


def _con_z(df):
    df = df.copy()
    df['Z'] = PESO_TARDANZA * df['suma_T'] + df['Cmax']     # orden lexicográfico
    return df


def _resumen(df, claves):
    return (df.groupby(claves)
            .agg(Corridas=('suma_T', 'size'), T_prom=('suma_T', 'mean'), T_desv=('suma_T', 'std'),
                 Tard=('tardias', 'mean'), C_prom=('Cmax', 'mean'), C_desv=('Cmax', 'std'),
                 Seg=('segundos', 'mean'), Gen=('generaciones', 'mean'))
            .reset_index().sort_values(['T_prom', 'C_prom']).reset_index(drop=True))


NOMBRES_RESUMEN = {
    'poblacion': 'Población', 'prob_cruce': 'P. cruce', 'prob_mutacion': 'P. mutación',
    'sin_mejora': 'Gen. sin mejora', 'T_prom': 'ΣTj prom (h)', 'T_desv': 'ΣTj desv',
    'Tard': 'Tardías prom', 'C_prom': 'Cmax prom (h)', 'C_desv': 'Cmax desv',
    'Seg': 'Tiempo prom (s)', 'Gen': 'Generaciones prom', 'rango': 'Posición'}


def anova_balanceado(df, factores, y='suma_T'):
    """
    ANOVA de un diseño factorial balanceado con efectos principales e
    interacciones dobles (la interacción triple queda en el error).
    Retorna (tabla, MSE, gl del error, residuos).
    """
    n_celda = df.groupby(factores).size()
    if n_celda.nunique() != 1:
        raise ValueError("El diseño no está balanceado (faltan corridas en alguna combinación).")
    media = df[y].mean()
    filas = []
    ajuste = pd.Series(media, index=df.index)
    efectos = {}
    for f in factores:
        m = df.groupby(f)[y].transform('mean') - media
        efectos[f] = m
        ajuste += m
        filas.append((NOMBRE_FACTOR.get(f, f), (m ** 2).sum(), df[f].nunique() - 1))
    for f1, f2 in itertools.combinations(factores, 2):
        m = df.groupby([f1, f2])[y].transform('mean') - media - efectos[f1] - efectos[f2]
        ajuste += m
        filas.append((f"{NOMBRE_FACTOR.get(f1, f1)} × {NOMBRE_FACTOR.get(f2, f2)}",
                      (m ** 2).sum(), (df[f1].nunique() - 1) * (df[f2].nunique() - 1)))
    residuos = df[y] - ajuste
    ss_tot = ((df[y] - media) ** 2).sum()
    gl_tot = len(df) - 1
    ss_err = ss_tot - sum(f[1] for f in filas)
    gl_err = gl_tot - sum(f[2] for f in filas)
    mse = ss_err / gl_err
    tabla = []
    for nombre, ss, gl in filas:
        F = (ss / gl) / mse if mse > 0 else float('nan')
        p = stats.f.sf(F, gl, gl_err) if stats is not None and mse > 0 else float('nan')
        tabla.append({'Fuente': nombre, 'SC': ss, 'gl': gl, 'CM': ss / gl, 'F': F, 'valor p': p})
    tabla.append({'Fuente': 'Error', 'SC': ss_err, 'gl': gl_err, 'CM': mse,
                  'F': float('nan'), 'valor p': float('nan')})
    tabla.append({'Fuente': 'Total', 'SC': ss_tot, 'gl': gl_tot, 'CM': float('nan'),
                  'F': float('nan'), 'valor p': float('nan')})
    return pd.DataFrame(tabla), mse, gl_err, residuos


def _intervalo_lsd(mse, gl_err, n):
    """Semiancho del intervalo LSD al 95 %: dos medias cuyos intervalos no se
    traslapan son significativamente distintas."""
    t = stats.t.ppf(0.975, gl_err) if stats is not None else 1.96
    return t * (mse / (2 * n)) ** 0.5


def grafico_medias(df, factores, mse, gl_err, ruta, y='suma_T', etiqueta='ΣTj promedio (h)'):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(factores), figsize=(4.2 * len(factores), 3.8), sharey=True)
    for ax, f in zip(axes, factores):
        g = df.groupby(f)[y]
        medias = g.mean()
        h = _intervalo_lsd(mse, gl_err, g.size().iloc[0])
        ax.errorbar([str(v) for v in medias.index], medias.values, yerr=h, fmt='o-', capsize=6,
                    color='#4E79A7', ecolor='#555555', linewidth=1.5, markersize=7)
        ax.set_title(NOMBRE_FACTOR.get(f, f), fontsize=11)
        ax.grid(axis='y', linestyle=':', alpha=0.6)
    axes[0].set_ylabel(etiqueta)
    fig.suptitle('Efectos principales con intervalos LSD al 95 %', fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150, bbox_inches='tight')
    plt.close(fig)


def grafico_interacciones(df, factores, ruta, y='suma_T', etiqueta='ΣTj promedio (h)'):
    import matplotlib.pyplot as plt
    pares = list(itertools.combinations(factores, 2))
    fig, axes = plt.subplots(1, len(pares), figsize=(4.4 * len(pares), 3.8), sharey=True)
    colores = ['#4E79A7', '#F28E2B', '#59A14F', '#E15759']
    for ax, (f1, f2) in zip(axes, pares):
        tabla = df.groupby([f1, f2])[y].mean().unstack(f2)
        for k, col in enumerate(tabla.columns):
            ax.plot([str(v) for v in tabla.index], tabla[col].values, 'o-',
                    color=colores[k % len(colores)], label=f"{col}")
        ax.set_xlabel(NOMBRE_FACTOR.get(f1, f1))
        ax.legend(title=NOMBRE_FACTOR.get(f2, f2), fontsize=8, title_fontsize=8)
        ax.grid(axis='y', linestyle=':', alpha=0.6)
    axes[0].set_ylabel(etiqueta)
    fig.suptitle('Interacciones dobles', fontsize=12)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150, bbox_inches='tight')
    plt.close(fig)


def _md(df, decimales=3):
    """Tabla en Markdown sin depender de tabulate."""
    def fmt(v):
        if isinstance(v, float):
            if pd.isna(v):
                return '—'
            if 0 < abs(v) < 10 ** -decimales:
                return f"{v:.2e}"
            return f"{v:.{decimales}f}"
        return str(v)
    cab = '| ' + ' | '.join(map(str, df.columns)) + ' |'
    sep = '|' + '---|' * len(df.columns)
    filas = ['| ' + ' | '.join(fmt(v) for v in fila) + ' |' for fila in df.itertuples(index=False)]
    return '\n'.join([cab, sep] + filas)


def _wilcoxon(a, b, col='Z', alternativa='two-sided'):
    """Wilcoxon pareado por semilla (por defecto sobre Z, el orden lexicográfico).
    alternativa='less' prueba si a es menor que b (una cola)."""
    comunes = a.index.intersection(b.index)
    if stats is None or len(comunes) < 5:
        return None, len(comunes)
    da, db = a.loc[comunes, col], b.loc[comunes, col]
    if ((da - db).abs() < 1e-9).all():
        return 1.0, len(comunes)
    return stats.wilcoxon(da, db, alternative=alternativa).pvalue, len(comunes)


def _pf(p):
    return '—' if p is None else f'{p:.4g}'


def _por_semilla(d, c):
    return d[(d[list(c)] == pd.Series(c)).all(axis=1)].set_index('semilla')


def _texto_config(c):
    return (f"población = {int(c['poblacion'])}, cruce = {float(c['prob_cruce']):g}, "
            f"mutación = {float(c['prob_mutacion']):g}")


def _leer(dir_salida, base, inst):
    ruta = os.path.join(dir_salida, _arch(base, inst))
    return _con_z(pd.read_csv(ruta)) if os.path.isfile(ruta) else None


def _posiciones(res):
    """Posición lexicográfica de cada combinación (1 = mejor ΣTj, desempate por Cmax)."""
    r = res.sort_values(['T_prom', 'C_prom']).reset_index(drop=True)
    r['rango'] = range(1, len(r) + 1)
    return r


def _seccion_diseno(dis, inst, dir_salida, informe):
    factores = list(FACTORES)
    y = _respuesta(dis)
    suf = SUFIJO[inst]
    res = _resumen(dis, factores)
    res.to_csv(os.path.join(dir_salida, f'resumen_combinaciones{suf}.csv'), index=False,
               encoding='utf-8-sig')
    informe += [f"## {NOMBRE_INSTANCIA[inst]}", "",
                f"Respuesta analizada: **{NOMBRE_RESP[y]}**" +
                (" (la tardanza fue cero en todas las corridas, así que las configuraciones solo "
                 "se diferencian por el makespan, el criterio secundario)." if y == 'Cmax' else "."),
                "", "Combinaciones ordenadas por ΣTj promedio y luego por Cmax promedio (10 primeras):", "",
                _md(res.drop(columns=['Gen']).head(10).rename(columns=NOMBRES_RESUMEN), 3), ""]
    significativos = set()
    est = {'respuesta': y, 'p_anova': {}, 'p_kruskal': {}, 'p_levene': {}, 'p_shapiro': None}
    if dis.groupby(factores).size().nunique() == 1:
        tabla, mse, gl_err, residuos = anova_balanceado(dis, factores, y=y)
        tabla.to_csv(os.path.join(dir_salida, f'anova{suf}.csv'), index=False, encoding='utf-8-sig')
        informe += [f"ANOVA sobre {NOMBRE_RESP[y]}:", "", _md(tabla, 4), ""]
        for f in factores:
            p = tabla.loc[tabla['Fuente'] == NOMBRE_FACTOR[f], 'valor p'].iloc[0]
            est['p_anova'][f] = float(p)
            if p < 0.05:
                significativos.add(f)
        grafico_medias(dis, factores, mse, gl_err,
                       os.path.join(dir_salida, f'efectos_principales{suf}.png'), y=y, etiqueta=ETIQUETA[y])
        grafico_interacciones(dis, factores, os.path.join(dir_salida, f'interacciones{suf}.png'),
                              y=y, etiqueta=ETIQUETA[y])
        if stats is not None:
            sw = stats.shapiro(residuos)
            est['p_shapiro'] = float(sw.pvalue)
            informe.append(f"- Normalidad de residuos (Shapiro-Wilk): W = {sw.statistic:.4f}, "
                           f"p = {sw.pvalue:.4g}.")
            for f in factores:
                lev = stats.levene(*[g[y].values for _, g in dis.groupby(f)])
                kw = stats.kruskal(*[g[y].values for _, g in dis.groupby(f)])
                est['p_levene'][f], est['p_kruskal'][f] = float(lev.pvalue), float(kw.pvalue)
                informe.append(f"- {NOMBRE_FACTOR[f]}: Levene p = {lev.pvalue:.4g}; "
                               f"Kruskal-Wallis H = {kw.statistic:.3f}, p = {kw.pvalue:.4g}.")
            informe.append("")
    return res, y, significativos, est


def _grilla_ampliacion(mejor, significativos):
    """Niveles adicionales para los factores significativos cuyo mejor nivel quedó en el
    borde del rango probado."""
    extra_max = {'poblacion': lambda v: [v + 50, v + 100], 'prob_cruce': lambda v: [min(1.0, round(v + 0.05, 2))],
                 'prob_mutacion': lambda v: [round(v + 0.2, 2)]}
    extra_min = {'poblacion': lambda v: [max(10, v // 2)], 'prob_cruce': lambda v: [round(v - 0.1, 2)],
                 'prob_mutacion': lambda v: [round(v / 2, 3)]}
    grilla = {}
    for f, niveles in FACTORES.items():
        v = mejor[f]
        extra = []
        if f in significativos and v == max(niveles):
            extra = extra_max[f](v)
        elif f in significativos and v == min(niveles):
            extra = extra_min[f](v)
        grilla[f] = sorted(set([v] + [e for e in extra if e != v]))
    return grilla


def analizar(dir_salida):
    import json
    factores = list(FACTORES)
    informe = ["# Calibración de los parámetros del algoritmo genético", "",
               f"Instancias de calibración: {', '.join(NOMBRE_INSTANCIA[i] for i in INSTANCIAS_CAL)}. "
               "Si hay más de una, la configuración se elige por su posición promedio.", ""]
    resumenes, respuestas, signif, disenos = {}, {}, set(), {}
    decisiones = {'instancias': {}, 'vs_anterior': {}, 'ampliacion': None, 'parada': None}
    for inst in INSTANCIAS_CAL:
        dis = _leer(dir_salida, 'corridas_diseno', inst)
        if dis is None:
            continue
        disenos[inst] = dis
        res, y, sig, est = _seccion_diseno(dis, inst, dir_salida, informe)
        decisiones['instancias'][inst] = est
        resumenes[inst], respuestas[inst] = res, y
        signif |= sig
    if not resumenes:
        print("No hay resultados del diseño todavía.")
        return

    # ── Selección combinada por posición promedio
    comb = None
    for inst, res in resumenes.items():
        r = _posiciones(res)[factores + ['rango', 'T_prom', 'C_prom']]
        r = r.rename(columns={'rango': f'pos_{inst}', 'T_prom': f'T_{inst}', 'C_prom': f'C_{inst}'})
        comb = r if comb is None else comb.merge(r, on=factores)
    cols_pos = [c for c in comb.columns if c.startswith('pos_')]
    comb['pos_prom'] = comb[cols_pos].mean(axis=1)
    orden = ['pos_prom'] + (['pos_exigente'] if 'pos_exigente' in comb else [])
    comb = comb.sort_values(orden).reset_index(drop=True)
    comb.to_csv(_ctrl(dir_salida, 'seleccion_combinada.csv'), index=False, encoding='utf-8-sig')
    mejor = {f: (int(comb.loc[0, f]) if f == 'poblacion' else float(comb.loc[0, f])) for f in factores}
    informe += ["## Selección combinada", "",
                "Posición de cada combinación en cada instancia (1 = mejor) y posición promedio "
                "(10 primeras):", "", _md(comb.head(10), 2), "",
                f"- Mejor combinación del diseño: {_texto_config(mejor)}."]
    for inst, dis in disenos.items():
        a, b = _por_semilla(dis, mejor), _por_semilla(dis, CONFIG_ACTUAL)
        if mejor != CONFIG_ACTUAL and len(b):
            p, n = _wilcoxon(a, b)
            decisiones['vs_anterior'][inst] = p
            informe.append(f"- Frente a la configuración anterior del código ({_texto_config(CONFIG_ACTUAL)}), "
                           f"{inst}: Wilcoxon p = {_pf(p)}.")
    grilla = _grilla_ampliacion(mejor, signif)
    informe.append(f"- Factores significativos en al menos una instancia: "
                   f"{', '.join(NOMBRE_FACTOR[f] for f in sorted(signif)) or 'ninguno'}.")
    en_borde = [f for f in factores if len(grilla[f]) > 1]
    informe.append("- " + (f"La mejor combinación está en el borde para: "
                           f"{', '.join(NOMBRE_FACTOR[f] for f in en_borde)}."
                           if en_borde else "No hay factores significativos en el borde; no se amplía."))
    informe.append("")
    decisiones.update(mejor_diseno=mejor, significativos=sorted(signif), en_borde=en_borde,
                      grilla={k: v for k, v in grilla.items()})
    with open(_ctrl(dir_salida, 'ampliacion_grilla.json'), 'w', encoding='utf-8') as fh:
        json.dump({**grilla, '_mejor': mejor}, fh)

    # ── Ampliación
    seleccion = mejor
    amps = {inst: _leer(dir_salida, 'corridas_ampliacion', inst) for inst in disenos}
    if en_borde and all(a is not None for a in amps.values()):
        informe += ["## Ampliación del rango", ""]
        comb2, datos = None, {}
        decisiones['ampliacion'] = {'tablas': {}, 'p': {}, 'candidata': None, 'cambia': False}
        for inst, dis in disenos.items():
            d = pd.concat([_por_semilla(dis, mejor).reset_index(), amps[inst]], ignore_index=True)
            datos[inst] = d
            r = _posiciones(_resumen(d, factores))
            decisiones['ampliacion']['tablas'][inst] = r.to_dict('records')
            informe += [f"{NOMBRE_INSTANCIA[inst]}:", "",
                        _md(r.drop(columns=['Gen']).rename(columns=NOMBRES_RESUMEN), 3), ""]
            r = r[factores + ['rango']].rename(columns={'rango': f'pos_{inst}'})
            comb2 = r if comb2 is None else comb2.merge(r, on=factores)
        comb2['pos_prom'] = comb2[[c for c in comb2.columns if c.startswith('pos_')]].mean(axis=1)
        comb2 = comb2.sort_values('pos_prom').reset_index(drop=True)
        cand = {f: (int(comb2.loc[0, f]) if f == 'poblacion' else float(comb2.loc[0, f])) for f in factores}
        if cand != mejor:
            mejor_en, peor_en = [], []
            for inst, d in datos.items():
                a, b = _por_semilla(d, cand), _por_semilla(d, mejor)
                p, _ = _wilcoxon(a, b)
                decisiones['ampliacion']['p'][inst] = p
                informe.append(f"- {_texto_config(cand)} frente a {_texto_config(mejor)}, {inst}: "
                               f"Wilcoxon p = {_pf(p)}.")
                if p is not None and p < 0.05:
                    (mejor_en if a['Z'].mean() < b['Z'].mean() else peor_en).append(inst)
            decisiones['ampliacion']['candidata'] = cand
            if mejor_en and not peor_en:
                seleccion = cand
                decisiones['ampliacion']['cambia'] = True
                informe.append(f"- Se selecciona {_texto_config(cand)}: mejora significativa en "
                               f"{', '.join(mejor_en)} sin empeorar en la otra instancia.")
            else:
                informe.append("- La mejora no es significativa; se conserva la mejor combinación del "
                               "diseño (parsimonia).")
        else:
            informe.append("- La mejor combinación del diseño sigue siendo la mejor.")
        informe.append("")
    elif en_borde:
        informe += ["No se evaluaron niveles fuera del rango del diseño; se adopta la mejor "
                    "combinación dentro de ese rango.", ""]
    with open(_ctrl(dir_salida, 'config_seleccionada.txt'), 'w', encoding='utf-8') as fh:
        fh.write(f"{int(seleccion['poblacion'])},{float(seleccion['prob_cruce']):g},"
                 f"{float(seleccion['prob_mutacion']):g}\n")
    informe += [f"**Configuración seleccionada: {_texto_config(seleccion)}.**", ""]
    decisiones['seleccion'] = seleccion

    # ── Criterio de parada
    pars = {inst: _leer(dir_salida, 'corridas_parada', inst) for inst in disenos}
    if any(p is not None for p in pars.values()):
        informe += ["## Criterio de parada", ""]
        if os.path.isfile(_ctrl(dir_salida, 'config_parada.txt')):
            informe += [f"Configuración: {open(_ctrl(dir_salida, 'config_parada.txt'), encoding='utf-8').read().strip()}", ""]
        else:                                   # sin archivo de control: la configuración seleccionada
            informe += [f"Configuración: {seleccion}", ""]
        mejora_sig = {}
        decisiones['parada'] = {'tablas': {}, 'p': {}}
        for inst, par in pars.items():
            if par is None:
                continue
            rp = _resumen(par, ['sin_mejora']).sort_values('sin_mejora')
            rp.to_csv(os.path.join(dir_salida, f'resumen_parada{SUFIJO[inst]}.csv'), index=False,
                      encoding='utf-8-sig')
            decisiones['parada']['tablas'][inst] = rp.to_dict('records')
            informe += [f"{NOMBRE_INSTANCIA[inst]}:", "", _md(rp.rename(columns=NOMBRES_RESUMEN), 3), ""]
            niveles = sorted(par['sin_mejora'].unique())
            for a_, b_ in zip(niveles, niveles[1:]):
                A = par[par['sin_mejora'] == a_].set_index('semilla')
                Bq = par[par['sin_mejora'] == b_].set_index('semilla')
                # Con la misma semilla, la corrida con el criterio mayor continúa la
                # trayectoria de la corrida con el criterio menor: nunca termina peor.
                # Por eso la prueba es de una cola (¿el criterio mayor mejora?).
                p, _ = _wilcoxon(Bq, A, alternativa='less')
                mejor_b = p is not None and p < 0.05 and Bq['Z'].mean() < A['Z'].mean()
                mejora_sig[(inst, b_)] = mejor_b
                decisiones['parada']['p'][f'{inst}:{a_}->{b_}'] = p
                informe.append(f"- {a_} → {b_} generaciones sin mejora: Wilcoxon de una cola p = {_pf(p)}"
                               f"{' (mejora significativa)' if mejor_b else ''}.")
            informe.append("")
        niveles = sorted(PARADA_NIVELES)
        elegido = niveles[0]
        for b_ in niveles[1:]:
            if any(mejora_sig.get((inst, b_), False) for inst in pars):
                elegido = b_
            else:
                break
        informe += [f"**Criterio de parada recomendado: {elegido} generaciones sin mejora** "
                    + ("(el menor nivel a partir del cual aumentar no mejora de forma significativa)."
                       if elegido != niveles[-1] else
                       "(mejora de forma significativa frente a los niveles menores; no se "
                       "evaluaron niveles mayores)."), ""]
        decisiones['parada']['elegido'] = int(elegido)
        with open(_ctrl(dir_salida, 'parada_seleccionada.txt'), 'w', encoding='utf-8') as fh:
            fh.write(f"{elegido}\n")

    with open(os.path.join(dir_salida, 'decisiones.json'), 'w', encoding='utf-8') as fh:
        json.dump(decisiones, fh, ensure_ascii=False, indent=1, default=float)
    ruta_inf = os.path.join(dir_salida, 'informe_calibracion.md')
    with open(ruta_inf, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(informe) + '\n')
    print('\n'.join(informe))
    print(f"\nInforme guardado en {ruta_inf}")

# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    global INSTANCIA, PARADA_NIVELES, PARADA_MAX_GEN
    ap = argparse.ArgumentParser(description='Calibración de parámetros del AG')
    ap.add_argument('accion', choices=['diseno', 'ampliacion', 'parada', 'analizar'])
    ap.add_argument('modelo', nargs='?', default='final_sc_hfsagls_S2_4.py')
    ap.add_argument('bd', nargs='?', default='BD_HFS.xlsx')
    ap.add_argument('--instancia', choices=['real', 'exigente', 'ambas'], default='ambas')
    ap.add_argument('--replicas', type=int, default=None)
    ap.add_argument('--presupuesto', type=int, default=PRESUPUESTO)
    ap.add_argument('--procesos', type=int, default=os.cpu_count() or 1)
    ap.add_argument('--config', type=str, default=None,
                    help='población,cruce,mutación para el experimento de parada (p. ej. 150,0.9,0.5)')
    ap.add_argument('--prueba', action='store_true',
                    help='corrida corta de verificación en salida_calibracion_prueba/')
    a = ap.parse_args()

    dir_salida = os.path.join(DIR_BASE, 'salida_calibracion_prueba' if a.prueba
                              else 'salida_calibracion')
    os.makedirs(dir_salida, exist_ok=True)
    presupuesto = a.presupuesto
    if a.prueba:
        FACTORES.update(poblacion=[20, 40], prob_cruce=[0.8, 0.9], prob_mutacion=[0.3, 0.5])
        CONFIG_ACTUAL.update(poblacion=40, prob_cruce=0.9, prob_mutacion=0.5)
        PARADA_NIVELES, PARADA_MAX_GEN = [5, 10], 30
        presupuesto = 400
    modelo, bd = os.path.abspath(a.modelo), os.path.abspath(a.bd)
    instancias = list(INSTANCIAS_CAL) if a.instancia == 'ambas' else [a.instancia]

    for inst in instancias:
        INSTANCIA = inst
        if a.accion == 'diseno':
            experimento_diseno(modelo, bd, dir_salida, a.replicas or (2 if a.prueba else REPLICAS),
                               presupuesto, a.procesos)
        elif a.accion == 'ampliacion':
            experimento_ampliacion(modelo, bd, dir_salida, a.replicas or (2 if a.prueba else REPLICAS),
                                   presupuesto, a.procesos)
        elif a.accion == 'parada':
            texto = a.config or open(_ctrl(dir_salida, 'config_seleccionada.txt'),
                                     encoding='utf-8').read().strip()
            p, c, m = texto.split(',')
            config = {'poblacion': int(p), 'prob_cruce': float(c), 'prob_mutacion': float(m)}
            experimento_parada(modelo, bd, dir_salida, config,
                               a.replicas or (2 if a.prueba else PARADA_REPLICAS), a.procesos)
    analizar(dir_salida)


if __name__ == '__main__':
    main()
