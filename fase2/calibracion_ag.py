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

Experimento 1b — ampliación: si la mejor combinación queda en el borde del
rango, se prueban niveles más allá (población 200 y 250, mutación 0,7) con las
mismas semillas. Solo se cambia la configuración si la mejora es significativa.

Experimento 2 — criterio de parada: con la configuración seleccionada se compara la
parada por generaciones sin mejora (50, 100, 200) en calidad y tiempo.

Uso:
  python calibracion_ag.py diseno   ruta/modelo.py ruta/BD_HFS.xlsx [--replicas 5]
                                    [--presupuesto 30000] [--procesos 4]
  python calibracion_ag.py ampliacion ruta/modelo.py ruta/BD_HFS.xlsx
  python calibracion_ag.py parada   ruta/modelo.py ruta/BD_HFS.xlsx
                                    [--config 150,0.9,0.5] [--replicas 10]
  python calibracion_ag.py analizar

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

# Experimento 1b: ampliación del rango si la mejor combinación queda en el borde
AMPLIACION = {'poblacion': [150, 200, 250], 'prob_cruce': [0.9], 'prob_mutacion': [0.5, 0.7]}

PARADA_NIVELES = [50, 100, 200]   # generaciones sin mejora (experimento 2)
PARADA_MAX_GEN = 1000
PARADA_REPLICAS = 10

DIR_BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Ejecución de una corrida (en un proceso de trabajo)
# ---------------------------------------------------------------------------

_M = None          # módulo del modelo cargado en cada proceso
_SEMILLA_IND = None


def _iniciar_proceso(ruta_modelo, ruta_bd):
    """Carga el modelo y los datos una sola vez por proceso."""
    global _M, _SEMILLA_IND
    import io
    import contextlib
    spec = importlib.util.spec_from_file_location('modelo_ag', ruta_modelo)
    _M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_M)
    with contextlib.redirect_stdout(io.StringIO()):
        _M.cargar_datos(ruta_bd)
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
    with mp.Pool(procesos, initializer=_iniciar_proceso, initargs=(ruta_modelo, ruta_bd)) as pool:
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


def experimento_diseno(ruta_modelo, ruta_bd, dir_salida, replicas, presupuesto, procesos):
    tareas = _tareas_factoriales(FACTORES, replicas, presupuesto)
    print(f"\nEXPERIMENTO 1 — diseño factorial {len(tareas) // replicas} combinaciones × "
          f"{replicas} réplicas, presupuesto {presupuesto} individuos por corrida")
    _ejecutar(tareas, os.path.join(dir_salida, 'corridas_diseno.csv'),
              ruta_modelo, ruta_bd, procesos)


def experimento_ampliacion(ruta_modelo, ruta_bd, dir_salida, replicas, presupuesto, procesos):
    """Niveles más allá del borde del diseño (mismas semillas y presupuesto)."""
    tareas = [t for t in _tareas_factoriales(AMPLIACION, replicas, presupuesto)
              if t['clave'] != CONFIG_ACTUAL]          # ese punto ya está en el diseño
    print(f"\nEXPERIMENTO 1b — ampliación del rango {AMPLIACION}, {replicas} réplicas")
    _ejecutar(tareas, os.path.join(dir_salida, 'corridas_ampliacion.csv'),
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
    print(f"\nEXPERIMENTO 2 — criterio de parada {PARADA_NIVELES} generaciones sin mejora, "
          f"configuración {config}, {replicas} réplicas")
    with open(os.path.join(dir_salida, 'config_parada.txt'), 'w', encoding='utf-8') as fh:
        fh.write(str(config))
    _ejecutar(tareas, os.path.join(dir_salida, 'corridas_parada.csv'),
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


def _preparar(df, t_mejor, c_mejor):
    df = df.copy()
    df['Z'] = PESO_TARDANZA * df['suma_T'] + df['Cmax']
    df['RPD_Cmax'] = 100.0 * (df['Cmax'] - c_mejor) / c_mejor
    df['llega_mejor_T'] = df['suma_T'] <= t_mejor + TOL
    return df


def _resumen(df, claves):
    r = (df.groupby(claves)
         .agg(Corridas=('suma_T', 'size'),
              T_prom=('suma_T', 'mean'), T_desv=('suma_T', 'std'), T_max=('suma_T', 'max'),
              Pct=('llega_mejor_T', lambda s: 100.0 * s.mean()),
              C_prom=('Cmax', 'mean'), RPD_C=('RPD_Cmax', 'mean'),
              Seg=('segundos', 'mean'), Gen=('generaciones', 'mean'),
              Ind=('individuos_mejor', 'mean'))
         .reset_index().sort_values(['T_prom', 'C_prom']))
    return r


NOMBRES_RESUMEN = {
    'poblacion': 'Población', 'prob_cruce': 'P. cruce', 'prob_mutacion': 'P. mutación',
    'sin_mejora': 'Gen. sin mejora', 'T_prom': 'ΣTj prom (h)', 'T_desv': 'ΣTj desv',
    'T_max': 'ΣTj máx', 'Pct': '% con mejor ΣTj', 'C_prom': 'Cmax prom (h)',
    'RPD_C': 'RPD Cmax (%)', 'Seg': 'Tiempo prom (s)', 'Gen': 'Generaciones prom',
    'Ind': 'Individuos hasta el mejor'}


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


def _wilcoxon(a, b):
    """Wilcoxon pareado por semilla sobre Z (orden lexicográfico)."""
    comunes = a.index.intersection(b.index)
    if stats is None or len(comunes) < 5:
        return None, len(comunes)
    da, db = a.loc[comunes, 'Z'], b.loc[comunes, 'Z']
    if ((da - db).abs() < 1e-9).all():
        return 1.0, len(comunes)
    return stats.wilcoxon(da, db).pvalue, len(comunes)


def _texto_config(c):
    return (f"población = {int(c['poblacion'])}, cruce = {float(c['prob_cruce']):g}, "
            f"mutación = {float(c['prob_mutacion']):g}")


def analizar(dir_salida):
    factores = list(FACTORES)
    leer = lambda n: (pd.read_csv(os.path.join(dir_salida, n))
                      if os.path.isfile(os.path.join(dir_salida, n)) else None)
    dis, amp, par = leer('corridas_diseno.csv'), leer('corridas_ampliacion.csv'), \
        leer('corridas_parada.csv')
    if dis is None:
        print("No hay resultados del diseño todavía.")
        return
    todas = pd.concat([d for d in (dis, amp, par) if d is not None], ignore_index=True)
    t_mejor = todas['suma_T'].min()
    c_mejor = todas.loc[todas['suma_T'] <= t_mejor + TOL, 'Cmax'].min()
    dis = _preparar(dis, t_mejor, c_mejor)

    informe = ["# Calibración de los parámetros del algoritmo genético", ""]
    informe += [f"- Mejor solución encontrada en todos los experimentos: ΣTj = {t_mejor:.4f} h, "
                f"Cmax = {c_mejor:.4f} h.",
                "- Respuesta principal: ΣTj (h). Respuesta secundaria: RPD del Cmax = "
                "100·(Cmax − Cmax*)/Cmax*, con Cmax* el mejor Cmax entre las corridas con la "
                "mejor ΣTj.",
                "- Pruebas de rangos (Kruskal-Wallis, Wilcoxon) sobre el orden lexicográfico "
                f"(Z = {PESO_TARDANZA:g}·ΣTj + Cmax).", ""]

    # ── 1. Diseño factorial ──
    res = _resumen(dis, factores)
    res.to_csv(os.path.join(dir_salida, 'resumen_combinaciones.csv'), index=False,
               encoding='utf-8-sig')
    n_rep = dis.groupby(factores).size()
    informe += [f"## 1. Diseño factorial: {dis.groupby(factores).ngroups} combinaciones × "
                f"{n_rep.min()} réplicas ({len(dis)} corridas)", "",
                "Ordenado por ΣTj promedio y luego por Cmax promedio.", "",
                _md(res.drop(columns=['Corridas', 'Gen']).rename(columns=NOMBRES_RESUMEN), 3), ""]

    if n_rep.nunique() == 1:
        tabla_anova, mse, gl_err, residuos = anova_balanceado(dis, factores)
        tabla_anova.to_csv(os.path.join(dir_salida, 'anova.csv'), index=False, encoding='utf-8-sig')
        informe += ["## 2. ANOVA sobre ΣTj (efectos principales e interacciones dobles)", "",
                    _md(tabla_anova, 4), ""]
        grafico_medias(dis, factores, mse, gl_err, os.path.join(dir_salida, 'efectos_principales.png'))
        grafico_interacciones(dis, factores, os.path.join(dir_salida, 'interacciones.png'))
        informe += ["Figuras: `efectos_principales.png` (medias de ΣTj con intervalos LSD al "
                    "95 %; si dos intervalos no se traslapan, los niveles difieren) e "
                    "`interacciones.png`.", ""]
        if stats is not None:
            sw = stats.shapiro(residuos)
            informe += ["## 3. Supuestos del ANOVA y prueba no paramétrica", "",
                        f"- Normalidad de residuos (Shapiro-Wilk): W = {sw.statistic:.4f}, "
                        f"p = {sw.pvalue:.4g}."]
            for f in factores:
                lev = stats.levene(*[g['suma_T'].values for _, g in dis.groupby(f)])
                informe.append(f"- Homogeneidad de varianzas entre niveles de {NOMBRE_FACTOR[f]} "
                               f"(Levene): W = {lev.statistic:.4f}, p = {lev.pvalue:.4g}.")
            informe += ["- Kruskal-Wallis (no paramétrica, orden lexicográfico); es la prueba de "
                        "referencia si algún supuesto anterior tiene p < 0,05:"]
            for f in factores:
                kw = stats.kruskal(*[g['Z'].values for _, g in dis.groupby(f)])
                informe.append(f"  - {NOMBRE_FACTOR[f]}: H = {kw.statistic:.3f}, p = {kw.pvalue:.4g}")
            informe.append("")
        try:                                   # contraste opcional con statsmodels
            import statsmodels.formula.api as smf
            import statsmodels.api as sm
            modelo = smf.ols('suma_T ~ (C(poblacion) + C(prob_cruce) + C(prob_mutacion))**2',
                             data=dis).fit()
            sm.stats.anova_lm(modelo, typ=2).to_csv(
                os.path.join(dir_salida, 'anova_statsmodels.csv'), encoding='utf-8-sig')
        except Exception:
            pass
    else:
        informe += ["## 2. ANOVA", "", "Faltan corridas en alguna combinación; se omite el ANOVA.", ""]

    # ── 4. Mejor combinación frente a la configuración actual ──
    por_semilla = lambda d, c: d[(d[list(c)] == pd.Series(c)).all(axis=1)].set_index('semilla')
    mejor = res.iloc[0]
    clave_mejor = {f: mejor[f] for f in factores}
    actual = por_semilla(dis, CONFIG_ACTUAL)
    informe += ["## 4. Mejor combinación del diseño frente a la configuración actual", "",
                f"- Mejor combinación: {_texto_config(clave_mejor)} "
                f"(ΣTj promedio = {mejor['T_prom']:.3f} h, Cmax promedio = {mejor['C_prom']:.3f} h)."]
    if len(actual):
        informe.append(f"- Configuración actual: {_texto_config(CONFIG_ACTUAL)} "
                       f"(ΣTj promedio = {actual['suma_T'].mean():.3f} h).")
    if clave_mejor == CONFIG_ACTUAL:
        informe.append("- La configuración actual es la mejor combinación del diseño.")
        en_borde = [NOMBRE_FACTOR[f] for f in factores
                    if CONFIG_ACTUAL[f] in (min(FACTORES[f]), max(FACTORES[f]))]
        if en_borde:
            informe.append(f"- Está en el borde del rango probado en: {', '.join(en_borde)}. "
                           "Por eso se amplía el rango (experimento 1b).")
    else:
        p, n = _wilcoxon(por_semilla(dis, clave_mejor), actual)
        if p is not None:
            informe.append(f"- Wilcoxon pareado por semilla ({n} pares): p = {p:.4g}. " +
                           ("Diferencia significativa al 5 %." if p < 0.05 else
                            "Diferencia no significativa al 5 %."))
    informe.append("")

    # ── 5. Ampliación del rango ──
    seleccion = clave_mejor
    if amp is not None and len(amp):
        amp = _preparar(amp, t_mejor, c_mejor)
        base = por_semilla(dis, CONFIG_ACTUAL).reset_index()
        comb = pd.concat([amp, base[amp.columns.intersection(base.columns)]], ignore_index=True)
        comb = comb[comb['semilla'].isin(amp['semilla'].unique())]
        ra = _resumen(comb, factores)
        ra.to_csv(os.path.join(dir_salida, 'resumen_ampliacion.csv'), index=False,
                  encoding='utf-8-sig')
        informe += ["## 5. Ampliación del rango (experimento 1b)", "",
                    "Mismas semillas y presupuesto que el diseño; incluye la configuración actual "
                    "como referencia.", "",
                    _md(ra.drop(columns=['Gen']).rename(columns=NOMBRES_RESUMEN), 3), ""]
        if stats is not None and comb.groupby(factores).ngroups > 1:
            kw = stats.kruskal(*[g['Z'].values for _, g in comb.groupby(factores)])
            informe.append(f"- Kruskal-Wallis entre estas combinaciones: H = {kw.statistic:.3f}, "
                           f"p = {kw.pvalue:.4g}.")
        for _, f in ra.iterrows():
            c = {k: f[k] for k in factores}
            if c == CONFIG_ACTUAL:
                continue
            p, n = _wilcoxon(por_semilla(comb, c), por_semilla(comb, CONFIG_ACTUAL))
            if p is not None:
                informe.append(f"- {_texto_config(c)} frente a la actual: Wilcoxon p = {p:.4g}.")
        mejor_a = ra.iloc[0]
        cand = {k: mejor_a[k] for k in factores}
        # Se cambia la configuración solo si la mejora es significativa
        if cand != CONFIG_ACTUAL:
            p, _ = _wilcoxon(por_semilla(comb, cand), por_semilla(comb, CONFIG_ACTUAL))
            if p is not None and p < 0.05:
                seleccion = cand
                informe.append(f"- Se selecciona {_texto_config(cand)}: mejora significativa "
                               "frente a la actual.")
            else:
                informe.append(f"- La mejor de la ampliación ({_texto_config(cand)}) no mejora "
                               "de forma significativa a la actual; se conserva la actual "
                               "(principio de parsimonia).")
        else:
            informe.append("- La configuración actual sigue siendo la mejor.")
        informe.append("")
    with open(os.path.join(dir_salida, 'config_seleccionada.txt'), 'w', encoding='utf-8') as fh:
        fh.write(f"{int(seleccion['poblacion'])},{float(seleccion['prob_cruce']):g},"
                 f"{float(seleccion['prob_mutacion']):g}\n")

    # ── 6. Criterio de parada ──
    if par is not None and len(par):
        par = _preparar(par, t_mejor, c_mejor)
        cfg = ''
        if os.path.isfile(os.path.join(dir_salida, 'config_parada.txt')):
            cfg = open(os.path.join(dir_salida, 'config_parada.txt'), encoding='utf-8').read().strip()
        rp = _resumen(par, ['sin_mejora']).sort_values('sin_mejora')
        rp.to_csv(os.path.join(dir_salida, 'resumen_parada.csv'), index=False, encoding='utf-8-sig')
        informe += ["## 6. Criterio de parada (experimento 2)", "", f"Configuración: {cfg}", "",
                    _md(rp.drop(columns=['Ind']).rename(columns=NOMBRES_RESUMEN), 3), ""]
        if stats is not None and par['sin_mejora'].nunique() > 1:
            kw = stats.kruskal(*[g['Z'].values for _, g in par.groupby('sin_mejora')])
            informe.append(f"- Kruskal-Wallis entre criterios: H = {kw.statistic:.3f}, "
                           f"p = {kw.pvalue:.4g}.")
            niveles = sorted(par['sin_mejora'].unique())
            for a_, b_ in zip(niveles, niveles[1:]):
                p, n = _wilcoxon(par[par['sin_mejora'] == a_].set_index('semilla'),
                                 par[par['sin_mejora'] == b_].set_index('semilla'))
                if p is not None:
                    informe.append(f"- {a_} frente a {b_} generaciones sin mejora: "
                                   f"Wilcoxon p = {p:.4g}.")
            informe.append("")

    ruta_inf = os.path.join(dir_salida, 'informe_calibracion.md')
    with open(ruta_inf, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(informe) + '\n')
    print('\n'.join(informe))
    print(f"\nInforme guardado en {ruta_inf}")

# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description='Calibración de parámetros del AG')
    ap.add_argument('accion', choices=['diseno', 'ampliacion', 'parada', 'analizar'])
    ap.add_argument('modelo', nargs='?', default='final_sc_hfsagls_S2_4.py')
    ap.add_argument('bd', nargs='?', default='BD_HFS.xlsx')
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
    global PARADA_NIVELES, PARADA_MAX_GEN
    presupuesto = a.presupuesto
    if a.prueba:
        FACTORES.update(poblacion=[20, 40], prob_cruce=[0.8, 0.9], prob_mutacion=[0.3, 0.5])
        CONFIG_ACTUAL.update(poblacion=40, prob_cruce=0.9, prob_mutacion=0.5)
        AMPLIACION.update(poblacion=[40, 60], prob_cruce=[0.9], prob_mutacion=[0.5, 0.7])
        PARADA_NIVELES, PARADA_MAX_GEN = [5, 10], 30
        presupuesto = 400
    modelo, bd = os.path.abspath(a.modelo), os.path.abspath(a.bd)

    if a.accion == 'diseno':
        experimento_diseno(modelo, bd, dir_salida, a.replicas or (2 if a.prueba else REPLICAS),
                           presupuesto, a.procesos)
    elif a.accion == 'ampliacion':
        experimento_ampliacion(modelo, bd, dir_salida, a.replicas or (2 if a.prueba else REPLICAS),
                               presupuesto, a.procesos)
    elif a.accion == 'parada':
        if a.config:
            texto = a.config
        else:                              # la seleccionada por el análisis
            analizar(dir_salida)
            texto = open(os.path.join(dir_salida, 'config_seleccionada.txt'),
                         encoding='utf-8').read().strip()
        p, c, m = texto.split(',')
        config = {'poblacion': int(p), 'prob_cruce': float(c), 'prob_mutacion': float(m)}
        experimento_parada(modelo, bd, dir_salida, config,
                           a.replicas or (2 if a.prueba else PARADA_REPLICAS), a.procesos)
    analizar(dir_salida)


if __name__ == '__main__':
    main()
