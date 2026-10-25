# -*- coding: utf-8 -*-
"""
VALIDACIÓN DEL MODELO MATEMÁTICO (MILP) CON INSTANCIAS PEQUEÑAS
=============================================================================

1. Resuelve de forma exacta el MILP de la Fase 2 (sublotes consistentes,
   liberaciones, alistamiento anticipatorio en troquelado, objetivo
   lexicográfico ΣTj → Cmax) para instancias pequeñas construidas con los
   tiempos reales de BD_HFS.xlsx. Solver: HiGHS (libre) a través de PuLP.
   Se usan dos formulaciones: F1, la del documento (antecesor inmediato), y
   F2, una equivalente de precedencia general con menos variables binarias.
2. Verifica que la solución del MILP cumple todas las restricciones.
3. Corre el algoritmo genético sobre las mismas instancias (varias semillas)
   y mide la brecha frente al óptimo.
4. Pasa la solución óptima del MILP por el decodificador del AG para comprobar
   que los dos modelos calculan los mismos tiempos.

Uso:
  python validacion_milp.py ruta/final_sc_hfsagls_S2_4.py ruta/BD_HFS.xlsx [I1,I2,...]
  python validacion_milp.py resumen        # une los resultados de todas las instancias

Requiere: pip install pulp highspy pandas openpyxl matplotlib
"""

import os
import sys
import time
import random
import importlib.util
from typing import Dict, List, Tuple

os.environ.setdefault('MPLBACKEND', 'Agg')

import pandas as pd
import pulp

EPS = 1e-5
SETUP_MIN = 4.98                 # alistamiento en troquelado [min]
LIMITE_TIEMPO_S = 600            # límite por fase del MILP [s]
SEMILLAS_AG = list(range(1, 11)) # 10 réplicas del AG por instancia
GRAFICAR = ['I3', 'I5']          # instancias con Gantt MILP vs AG
DIR_SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salida_validacion')

# ---------------------------------------------------------------------------
# Instancias de prueba (tiempos reales; cantidades y fechas reducidas)
# ---------------------------------------------------------------------------
# Órdenes: (orden, referencia, cantidad [docenas], r_j [h], d_j [h])
ORDENES_BASE = [
    ('J1', 'C01', 8, 0.0, 15.0),
    ('J2', 'V03', 6, 0.0, 12.0),
    ('J3', 'C04', 5, 2.0, 14.0),
    ('J4', 'C01', 7, 3.0, 20.0),
    ('J5', 'V02', 6, 5.0, 22.0),
]
# Con más máquinas (MAQ_B) se usan fechas de entrega más ajustadas para que el
# óptimo tenga tardanza positiva y la instancia discrimine entre métodos
ORDENES_B = [(j, p, q, r, d) for (j, p, q, r, _), d in zip(ORDENES_BASE, (9.0, 7.0, 8.0, 12.0, 14.0))]
MAQ_A = {'Troquelado': ['M1', 'M2'], 'Ensamble': ['M5', 'M16'],
         'Costura': ['M20'], 'Volteado': ['M29']}
MAQ_B = {'Troquelado': ['M1', 'M2'], 'Ensamble': ['M5', 'M12', 'M16'],
         'Costura': ['M20', 'M21'], 'Volteado': ['M29']}

INSTANCIAS = [
    # nombre, órdenes, B̄ (sublotes por orden), máquinas por etapa
    # Pequeñas: el MILP demuestra el óptimo
    ('I1', ORDENES_B[:4], 1, MAQ_B),       # sin sublotes (lote completo)
    ('I2', ORDENES_B[:5], 1, MAQ_B),       # sin sublotes (lote completo)
    ('I3', ORDENES_BASE[:3], 2, MAQ_A),
    ('I4', ORDENES_B[:3], 2, MAQ_B),
    ('I5', ORDENES_BASE[:4], 2, MAQ_A),
    # Medianas: el MILP llega al límite de tiempo
    ('I6', ORDENES_B[:4], 2, MAQ_B),
    ('I7', ORDENES_BASE[:3], 3, MAQ_A),
    ('I8', ORDENES_B[:4], 3, MAQ_B),
    ('I9', ORDENES_B[:5], 3, MAQ_B),
]

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def cargar_modulo(ruta: str):
    spec = importlib.util.spec_from_file_location('modelo_ag', ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tiempos_reales(M, ruta_bd: str) -> Tuple[Dict, List[str]]:
    """(referencia, máquina) → min/docena y nombres de etapa en orden."""
    M.cargar_datos(ruta_bd)
    return dict(M.TIEMPO_MIN_DOCENA), [M.NOMBRE_ETAPA[s] for s in M.ETAPAS]


def escribir_excel(ruta: str, ordenes, maquinas, t_min, etapas):
    """Libro con el mismo formato de BD_HFS.xlsx para alimentar el AG."""
    refs = sorted({o[1] for o in ordenes})
    filas = [{'Codigo producto': p, 'Maquina': m, 'Etapa': e,
              'min x docena': t_min[(p, m)]}
             for p in refs for e in etapas for m in maquinas[e]]
    trab = [{'Orden de trabajo': j, 'Codigo Producto': p, 'Cantidad (docenas)': q,
             'r_j Liberación': r, 'd_j horas': d} for (j, p, q, r, d) in ordenes]
    with pd.ExcelWriter(ruta) as w:
        pd.DataFrame(filas).to_excel(w, sheet_name='Tiempo de procesamiento', index=False)
        pd.DataFrame(trab).to_excel(w, sheet_name='Trabajos', index=False)


def num_sublotes(q: int, b_max: int, q_min: int = 1) -> int:
    """B_j = máx{1, mín{B̄, ⌊Q_j / q_min⌋}} (igual que en el documento)."""
    return max(1, min(b_max, q // q_min))

# ---------------------------------------------------------------------------
# Modelo MILP
# ---------------------------------------------------------------------------

def _var(prob, nombre, low=None, up=None, cat='Continuous'):
    """Variable compatible con PuLP 2.x (LpVariable) y PuLP 4.x (add_variable)."""
    if hasattr(prob, 'add_variable'):
        return prob.add_variable(nombre, lowBound=low, upBound=up, cat=cat)
    return pulp.LpVariable(nombre, lowBound=low, upBound=up, cat=cat)


def _resolver(prob, limite, arranque=False):
    """Resuelve con HiGHS (PuLP 2.x o 4.x).
    Retorna (hay solución, óptimo demostrado, cota inferior, segundos)."""
    t0 = time.time()
    res = prob.solve(pulp.HiGHS(msg=False, timeLimit=limite, gapRel=0.0, warmStart=arranque))
    seg = time.time() - t0
    obj = pulp.value(prob.objective)
    if hasattr(res, 'status'):                       # PuLP 4.x
        hay = bool(res.has_solution)
        cota = res.best_bound if res.best_bound is not None else obj
        optimo = hay and res.status.name == 'Optimal' and seg < limite - 1
    else:                                            # PuLP 2.x
        estado = pulp.LpStatus[res]
        hay = estado == 'Optimal' or (prob.sol_status in (1, 2) if hasattr(prob, 'sol_status') else False)
        cota = obj
        optimo = estado == 'Optimal' and seg < limite - 1
    return hay, optimo, cota, seg


def resolver_milp(ordenes, b_max, maquinas, t_min, etapas, cota_sum_t=None,
                  limite=LIMITE_TIEMPO_S, formulacion='inmediata'):
    """
    formulacion = 'inmediata' : formulación del documento (Gürsoy Yılmaz y Yılmaz,
                                2022), con variables de antecesor inmediato z_ii'sm.
                  'precedencia': formulación equivalente con variables de
                                precedencia general u_ii's (menos binarias). Es exacta
                                porque el alistamiento cumple la desigualdad triangular.
    cota_sum_t: ΣTj de una solución factible conocida (regla de despacho).
    Sirve para acotar el horizonte: en el óptimo, todo C_j ≤ máx d_j + cota_sum_t.
    """
    J = [o[0] for o in ordenes]
    ref = {o[0]: o[1] for o in ordenes}
    Q = {o[0]: o[2] for o in ordenes}
    r = {o[0]: o[3] for o in ordenes}
    d = {o[0]: o[4] for o in ordenes}
    B = {j: num_sublotes(Q[j], b_max) for j in J}
    S_ = list(range(1, len(etapas) + 1))
    Ms = {s: maquinas[etapas[s - 1]] for s in S_}
    N = [(j, b) for j in J for b in range(1, B[j] + 1)]
    a = {(j, m): t_min[(ref[j], m)] / 60.0 for j in J for s in S_ for m in Ms[s]}
    sigma = SETUP_MIN / 60.0

    def setup(i, k):                         # σ_ii' en troquelado
        return 0.0 if ref[i[0]] == ref[k[0]] else sigma

    # Horizonte: con una solución factible conocida, C_j ≤ máx d_j + ΣTj conocida;
    # sin ella, liberación máxima + todo el trabajo en la máquina más lenta.
    if cota_sum_t is not None:
        horizonte = max(d.values()) + cota_sum_t
    else:
        horizonte = max(r.values()) + len(N) * sigma + \
            sum(Q[j] * max(a[(j, m)] for m in Ms[s]) for j in J for s in S_)
    p_max = max(a[(j, m)] * Q[j] for j in J for s in S_ for m in Ms[s])
    H = horizonte + sigma + p_max            # constante grande del big-M

    prob = pulp.LpProblem('HFS_sublotes_consistentes', pulp.LpMinimize)
    nom = lambda i: '0' if i == 0 else f"{i[0]}_{i[1]}"
    x = {i: _var(prob, f"x_{nom(i)}", 1, None, 'Integer') for i in N}
    y = {(i, s, m): _var(prob, f"y_{nom(i)}_{s}_{m}", cat='Binary')
         for i in N for s in S_ for m in Ms[s]}
    nodos0 = [0] + N
    if formulacion == 'inmediata':
        z = {(i, k, s, m): _var(prob, f"z_{nom(i)}_{nom(k)}_{s}_{m}", cat='Binary')
             for s in S_ for m in Ms[s] for i in nodos0 for k in N if i != k}
    else:
        pares = [(N[p], N[q]) for p in range(len(N)) for q in range(p + 1, len(N))]
        z = {(i, k, s): _var(prob, f"u_{nom(i)}_{nom(k)}_{s}", cat='Binary')
             for s in S_ for (i, k) in pares}
    St = {(i, s): _var(prob, f"S_{nom(i)}_{s}", 0) for i in N for s in S_}
    C = {(i, s): _var(prob, f"C_{nom(i)}_{s}", 0, horizonte) for i in N for s in S_}
    T = {j: _var(prob, f"T_{j}", 0) for j in J}
    Cmax = _var(prob, 'Cmax', 0)

    # (1)-(2) Tamaños de sublote: suman Q_j, mínimo q_min = 1 (cota inferior de x)
    for j in J:
        prob += pulp.lpSum(x[(j, b)] for b in range(1, B[j] + 1)) == Q[j]
        # Ruptura de simetría: los sublotes de una orden son intercambiables,
        # así que se numeran de mayor a menor tamaño
        for b in range(1, B[j]):
            prob += x[(j, b)] >= x[(j, b + 1)]
    # (3) Cada sublote en exactamente una máquina por etapa
    for i in N:
        for s in S_:
            prob += pulp.lpSum(y[(i, s, m)] for m in Ms[s]) == 1
    # (4) Tiempo de proceso
    for (j, b) in N:
        for s in S_:
            for m in Ms[s]:
                prob += C[((j, b), s)] >= St[((j, b), s)] + a[(j, m)] * x[(j, b)] \
                    - H * (1 - y[((j, b), s, m)])
            # Desigualdad válida (refuerza la relajación lineal): el sublote dura
            # al menos lo que tarda en la máquina más rápida de la etapa
            prob += C[((j, b), s)] >= St[((j, b), s)] + \
                min(a[(j, m)] for m in Ms[s]) * x[(j, b)]
    # (5) Liberación y (6) precedencia entre etapas del mismo sublote
    for (j, b) in N:
        prob += St[((j, b), 1)] >= r[j]
        for s in S_[:-1]:
            prob += St[((j, b), s + 1)] >= C[((j, b), s)]
    if formulacion == 'inmediata':
        # (7)-(9) Secuencia en cada máquina
        for s in S_:
            for m in Ms[s]:
                for k in N:   # un antecesor inmediato (puede ser el inicio 0)
                    prob += pulp.lpSum(z[(i, k, s, m)] for i in nodos0 if i != k) == y[(k, s, m)]
                for i in N:   # a lo sumo un sucesor
                    prob += pulp.lpSum(z[(i, k, s, m)] for k in N if k != i) <= y[(i, s, m)]
                prob += pulp.lpSum(z[(0, k, s, m)] for k in N) <= 1   # a lo sumo un primero
        # (10)-(12) No solapamiento y alistamiento (anticipatorio) en troquelado
        for s in S_:
            for m in Ms[s]:
                for i in N:
                    for k in N:
                        if i == k:
                            continue
                        su = setup(i, k) if s == 1 else 0.0
                        prob += St[(k, s)] >= C[(i, s)] + su - H * (1 - z[(i, k, s, m)])
                if s == 1:
                    for k in N:
                        prob += St[(k, 1)] >= sigma * z[(0, k, 1, m)]
    else:
        # Precedencia general: si i y k comparten máquina, u = 1 → i antes que k.
        # Si i precede a k (aunque no sea inmediatamente) y cambian de referencia,
        # entre ambos hay al menos un alistamiento, así que la restricción es exacta.
        for (i, k, s), u in z.items():
            su_ik = setup(i, k) if s == 1 else 0.0
            su_ki = setup(k, i) if s == 1 else 0.0
            for m in Ms[s]:
                ambos = y[(i, s, m)] + y[(k, s, m)]
                prob += St[(k, s)] >= C[(i, s)] + su_ik - H * (3 - u - ambos)
                prob += St[(i, s)] >= C[(k, s)] + su_ki - H * (2 + u - ambos)
        # Montaje inicial: todo sublote de troquelado empieza después de σ (el
        # primero de cada máquina lo exige; los demás empiezan aún más tarde)
        for k in N:
            prob += St[(k, 1)] >= sigma
    # (13)-(14) Tardanza y makespan
    s_ult = S_[-1]
    for (j, b) in N:
        prob += T[j] >= C[((j, b), s_ult)] - d[j]
        prob += Cmax >= C[((j, b), s_ult)]

    n_bin = len(y) + len(z)
    n_res = prob.numConstraints() if hasattr(prob, "numConstraints") else len(prob.constraints)

    # Objetivo lexicográfico: fase 1 ΣTj, fase 2 Cmax con ΣTj fijada
    prob.setObjective(pulp.lpSum(T.values()))
    hay1, opt1, cota_t, seg1 = _resolver(prob, limite)
    base = {'J': J, 'ref': ref, 'Q': Q, 'r': r, 'd': d, 'B': B, 'N': N, 'Ms': Ms,
            'a': a, 'sigma': sigma, 'n_bin': n_bin, 'n_res': n_res}
    if not hay1:
        print(f"    MILP fase 1 (ΣTj): {seg1:.1f} s, sin solución factible")
        return {**base, 'hay_solucion': False, 'sum_T': None, 'Cmax': None, 'seg': seg1,
                'estado': f"Sin solución factible en {limite} s", 'x': {}, 'ops': {}}
    sum_t = pulp.value(prob.objective)
    prob += pulp.lpSum(T.values()) <= sum_t + 1e-4
    prob.setObjective(Cmax)
    hay2, opt2, cota_c, seg2 = _resolver(prob, limite, arranque=True)
    seg = seg1 + seg2
    print(f"    MILP fase 1 (ΣTj): {seg1:.1f} s | fase 2 (Cmax): {seg2:.1f} s")
    if opt1 and opt2:
        estado = 'Óptimo'
    else:
        estado = (f"Límite de tiempo: ΣTj {'óptima' if opt1 else f'cota inferior {cota_t:.3f}'}; "
                  f"Cmax {'óptimo' if opt2 else f'cota inferior {cota_c:.3f}'}")

    sol_x = {i: int(round(x[i].value())) for i in N}
    ops = {}
    for (j, b) in N:
        for s in S_:
            m = max(Ms[s], key=lambda mm: y[((j, b), s, mm)].value())
            ini = St[((j, b), s)].value()
            ops[(j, b, s)] = (m, ini, ini + a[(j, m)] * sol_x[(j, b)])
    # ΣTj y Cmax se recalculan con fin = inicio + duración (las variables C del
    # MILP solo están acotadas por abajo y pueden quedar con holgura)
    sol = {**base, 'hay_solucion': True, 'x': sol_x, 'ops': ops, 'seg': seg,
           'estado': estado, 'optimo_t': opt1, 'optimo_c': opt2,
           'cota_t': cota_t, 'cota_c': cota_c}
    sol['sum_T'], sol['Cmax'], _ = indicadores(sol, ops)
    return sol

# ---------------------------------------------------------------------------
# Verificación independiente de una programación
# ---------------------------------------------------------------------------

def indicadores(sol, ops) -> Tuple[float, float, int]:
    s_ult = max(sol['Ms'])
    Cj = {j: max(ops[(j, b, s_ult)][2] for b in range(1, sol['B'][j] + 1)) for j in sol['J']}
    T = {j: max(0.0, Cj[j] - sol['d'][j]) for j in sol['J']}
    return sum(T.values()), max(Cj.values()), sum(1 for t in T.values() if t > EPS)


def verificar(sol, ops) -> List[str]:
    err = []
    for j in sol['J']:
        tam = [sol['x'][(j, b)] for b in range(1, sol['B'][j] + 1)]
        if sum(tam) != sol['Q'][j]:
            err.append(f"suma de sublotes de {j}")
        if min(tam) < 1:
            err.append(f"sublote menor al mínimo en {j}")
    for (j, b, s), (m, ini, fin) in ops.items():
        if m not in sol['Ms'][s]:
            err.append(f"máquina {m} no pertenece a la etapa {s}")
        if abs((fin - ini) - sol['a'][(j, m)] * sol['x'][(j, b)]) > EPS:
            err.append(f"duración de {j}-{b} en etapa {s}")
        if s == 1 and ini < sol['r'][j] - EPS:
            err.append(f"{j}-{b} inicia antes de su liberación")
        if s > 1 and ini < ops[(j, b, s - 1)][2] - EPS:
            err.append(f"{j}-{b} inicia la etapa {s} antes de terminar la {s - 1}")
    por_maq = {}
    for (j, b, s), (m, ini, fin) in ops.items():
        por_maq.setdefault((s, m), []).append((ini, fin, j))
    for (s, m), lst in por_maq.items():
        lst.sort()
        for k, (ini, fin, j) in enumerate(lst):
            libre = lst[k - 1][1] if k else 0.0
            su = 0.0
            if s == 1 and (k == 0 or sol['ref'][lst[k - 1][2]] != sol['ref'][j]):
                su = sol['sigma']
            if ini < libre + su - EPS:
                err.append(f"solape o alistamiento faltante en {m} (t = {ini:.3f})")
    return err

# ---------------------------------------------------------------------------
# Algoritmo genético sobre la instancia
# ---------------------------------------------------------------------------

def correr_ag(M, ruta_xlsx, b_max, semillas):
    M.cargar_datos(ruta_xlsx)
    M.NUM_SUBLOTES = b_max
    regla = M.mejor_de(M.evaluar_reglas())
    resultados = []
    for sem in semillas:
        M.GA_PARAMS['semilla'] = sem
        t0 = time.time()
        mejor, _ = M.algoritmo_genetico(
            verbose=False, individuo_semilla=M.individuo_regla_ls(regla['secuencia']))
        ind = M.calcular_indicadores(M.simular_hfs(mejor)[0])
        resultados.append((ind['suma_Ti'], ind['Cmax'], time.time() - t0, mejor))
    return regla, resultados


def decodificar_solucion_milp(M, sol):
    """Pasa los tamaños y las secuencias del MILP por el decodificador del AG."""
    props = {}
    for j in sol['J']:
        tam = [sol['x'][(j, b)] for b in range(1, sol['B'][j] + 1)]
        libres = sum(tam) - len(tam)
        props[j] = ([(t - 1) / libres for t in tam] if libres > 0
                    else [1.0 / len(tam)] * len(tam))
    posiciones = {s: [(j, b) for (j, b, ss), _ in sorted(sol['ops'].items(),
                                                         key=lambda kv: kv[1][1]) if ss == s]
                  for s in sol['Ms']}
    ind = {'k': dict(sol['B']), 'proporciones': props, 'posiciones': posiciones}
    C, gantt = M.simular_hfs(ind)
    r = M.calcular_indicadores(C)
    return r['suma_Ti'], r['Cmax']

# ---------------------------------------------------------------------------
# Gantt comparativo
# ---------------------------------------------------------------------------

def graficar_comparacion(M, sol, ind_ag, ruta):
    """Gantt de la solución óptima del MILP (arriba) y del mejor AG (abajo)."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    def barras_milp():
        ops = [(j, b, s, m, ini, fin) for (j, b, s), (m, ini, fin) in sol['ops'].items()]
        setups = []
        por_maq = {}
        for (j, b, s, m, ini, fin) in ops:
            if s == 1:
                por_maq.setdefault(m, []).append((ini, fin, j))
        for m, lst in por_maq.items():
            lst.sort()
            for k, (ini, fin, j) in enumerate(lst):
                if k == 0 or sol['ref'][lst[k - 1][2]] != sol['ref'][j]:
                    libre = lst[k - 1][1] if k else 0.0
                    setups.append((m, libre, libre + sol['sigma']))
        return ops, setups

    def barras_ag():
        C, g = M.simular_hfs(ind_ag)
        ops = [(j, b, s, m, ini, fin) for s in M.ETAPAS for (j, b, m, ini, fin) in g[s]]
        setups = [(m, ini, fin) for (_, m, ini, fin) in g['alistamientos']]
        return ops, setups

    maquinas = [m for s in sorted(sol['Ms']) for m in sol['Ms'][s]]
    pos = {m: i for i, m in enumerate(reversed(maquinas))}
    colores = ['#4E79A7', '#F28E2B', '#59A14F', '#E15759', '#B07AA1']
    color = {j: colores[i % len(colores)] for i, j in enumerate(sol['J'])}
    paneles = [('MILP (óptimo)', barras_milp()), ('Algoritmo genético (mejor réplica)', barras_ag())]
    fig, axes = plt.subplots(2, 1, figsize=(13, 0.45 * len(maquinas) * 2 + 2), sharex=True)
    for ax, (titulo, (ops, setups)) in zip(axes, paneles):
        s_ult = max(sol['Ms'])
        Cj = {}
        for (j, b, s, m, ini, fin) in ops:
            ax.barh(pos[m], fin - ini, left=ini, height=0.7, color=color[j],
                    edgecolor='white', linewidth=0.6)
            ax.text((ini + fin) / 2, pos[m], f"{j}-{b}", ha='center', va='center',
                    fontsize=7, color='white', fontweight='bold', clip_on=True)
            if s == s_ult:
                Cj[j] = max(Cj.get(j, 0.0), fin)
        for (m, ini, fin) in setups:
            ax.barh(pos[m], fin - ini, left=ini, height=0.7, color='white',
                    edgecolor='#555555', hatch='////', linewidth=0.4)
        sum_t = sum(max(0.0, Cj[j] - sol['d'][j]) for j in sol['J'])
        ax.set_title(f"{titulo}:  ΣTj = {sum_t:.3f} h  |  Cmax = {max(Cj.values()):.3f} h",
                     fontsize=10, loc='left')
        for j in sol['J']:
            ax.axvline(sol['d'][j], color=color[j], linestyle='--', linewidth=1, alpha=0.8)
        ax.set_yticks(list(pos.values()))
        ax.set_yticklabels([f"E{s} {m}" for s in sorted(sol['Ms']) for m in sol['Ms'][s]][::-1],
                           fontsize=8)
        ax.grid(axis='x', linestyle=':', alpha=0.5)
    axes[-1].set_xlabel('Tiempo (horas laborables)')
    leyenda = [mpatches.Patch(color=color[j], label=f"{j} ({sol['ref'][j]}, d = {sol['d'][j]:g} h)")
               for j in sol['J']]
    leyenda.append(mpatches.Patch(facecolor='white', edgecolor='#555555', hatch='////',
                                  label='Alistamiento'))
    fig.legend(handles=leyenda, loc='lower center', ncol=len(leyenda), fontsize=8,
               bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(ruta, dpi=150, bbox_inches='tight')
    plt.close(fig)

# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def _fmt(v, dec=4):
    return '—' if v is None else f"{v:.{dec}f}"


def main(ruta_modelo, ruta_bd, nombres=None):
    os.makedirs(DIR_SALIDA, exist_ok=True)
    M = cargar_modulo(ruta_modelo)
    t_min, etapas = tiempos_reales(M, ruta_bd)

    filas = []
    for nombre, ordenes, b_max, maquinas in INSTANCIAS:
        if nombres and nombre not in nombres:
            continue
        n_maq = '-'.join(str(len(maquinas[e])) for e in etapas)
        print(f"\n=== Instancia {nombre}: {len(ordenes)} órdenes, B̄ = {b_max}, "
              f"máquinas por etapa {n_maq} ===", flush=True)

        # 1. Reglas de despacho y AG (10 semillas) con el código original
        ruta_x = os.path.join(DIR_SALIDA, f"{nombre}.xlsx")
        escribir_excel(ruta_x, ordenes, maquinas, t_min, etapas)
        regla, res = correr_ag(M, ruta_x, b_max, SEMILLAS_AG)
        print(f"  Mejor regla ({regla['regla']}): ΣTj = {regla['suma_Ti']:.4f} | "
              f"Cmax = {regla['Cmax']:.4f}")
        for sem, (t, c, sg, _) in zip(SEMILLAS_AG, res):
            print(f"    AG semilla {sem:>2}: ΣTj = {t:.4f} | Cmax = {c:.4f} | {sg:.1f} s")

        # 2. MILP con las dos formulaciones
        sols = {}
        for form, etiqueta in [('inmediata', 'F1 antecesor inmediato (documento)'),
                               ('precedencia', 'F2 precedencia general')]:
            sol = resolver_milp(ordenes, b_max, maquinas, t_min, etapas,
                                cota_sum_t=regla['suma_Ti'], formulacion=form)
            sol['violaciones'] = len(verificar(sol, sol['ops'])) if sol['hay_solucion'] else None
            sols[form] = sol
            print(f"  MILP {etiqueta}: ΣTj = {_fmt(sol['sum_T'])} | Cmax = {_fmt(sol['Cmax'])} | "
                  f"{sol['estado']} | {sol['seg']:.1f} s | {sol['n_bin']} binarias | "
                  f"violaciones = {sol['violaciones']}", flush=True)

        # 3. Referencia: la mejor solución del MILP (lexicográfica)
        con_sol = [sl for sl in sols.values() if sl['hay_solucion']]
        ref = min(con_sol, key=lambda sl: (round(sl['sum_T'], 6), round(sl['Cmax'], 6))) \
            if con_sol else None
        optimo_t = any(sl['hay_solucion'] and sl.get('optimo_t') for sl in sols.values())
        optimo_tc = any(sl['hay_solucion'] and sl.get('optimo_t') and sl.get('optimo_c')
                        for sl in sols.values())

        if ref is not None:
            pd.DataFrame([{'Orden': j, 'Sublote': b, 'Docenas': ref['x'][(j, b)], 'Etapa': s,
                           'Máquina': m, 'Inicio (h)': round(ini, 4), 'Fin (h)': round(fin, 4)}
                          for (j, b, s), (m, ini, fin) in sorted(
                              ref['ops'].items(), key=lambda kv: (kv[0][2], kv[1][1]))]
                         ).to_csv(os.path.join(DIR_SALIDA, f"programacion_milp_{nombre}.csv"),
                                  index=False, encoding='utf-8-sig')
            dec_t, dec_c = decodificar_solucion_milp(M, ref)
            print(f"  Solución MILP en el decodificador del AG: ΣTj = {dec_t:.4f} | Cmax = {dec_c:.4f}")
            if nombre in GRAFICAR:
                mejor_ind = min(res, key=lambda v: (round(v[0], 6), round(v[1], 6)))[3]
                graficar_comparacion(M, ref, mejor_ind,
                                     os.path.join(DIR_SALIDA, f"gantt_milp_vs_ag_{nombre}.png"))
        else:
            dec_t = dec_c = None

        # 4. Comparación AG frente a la referencia
        mejor_ag = min(res, key=lambda v: (round(v[0], 6), round(v[1], 6)))
        prom_t = sum(v[0] for v in res) / len(res)
        prom_c = sum(v[1] for v in res) / len(res)
        if ref is not None:
            igual_t = sum(1 for v in res if v[0] <= ref['sum_T'] + 1e-3)
            igual_tc = sum(1 for v in res if v[0] <= ref['sum_T'] + 1e-3
                           and v[1] <= ref['Cmax'] + 1e-3)
        f1, f2 = sols['inmediata'], sols['precedencia']
        filas.append({
            'Instancia': nombre, 'Órdenes': len(ordenes), 'B̄': b_max,
            'Sublotes': len(f1['N']), 'Máquinas': n_maq,
            'F1 binarias': f1['n_bin'], 'F1 ΣTj': f1['sum_T'], 'F1 Cmax': f1['Cmax'],
            'F1 estado': f1['estado'], 'F1 s': round(f1['seg'], 1), 'F1 violaciones': f1['violaciones'],
            'F2 binarias': f2['n_bin'], 'F2 ΣTj': f2['sum_T'], 'F2 Cmax': f2['Cmax'],
            'F2 estado': f2['estado'], 'F2 s': round(f2['seg'], 1), 'F2 violaciones': f2['violaciones'],
            'ΣTj óptima demostrada': optimo_t, '(ΣTj, Cmax) óptimo demostrado': optimo_tc,
            'Decod. ΣTj': dec_t, 'Decod. Cmax': dec_c,
            'Regla': regla['regla'], 'Regla ΣTj': regla['suma_Ti'], 'Regla Cmax': regla['Cmax'],
            'AG mejor ΣTj': mejor_ag[0], 'AG mejor Cmax': mejor_ag[1],
            'AG prom ΣTj': prom_t, 'AG prom Cmax': prom_c,
            'AG ≤ MILP en ΣTj': f"{igual_t}/{len(res)}" if ref else '—',
            'AG ≤ MILP en (ΣTj, Cmax)': f"{igual_tc}/{len(res)}" if ref else '—',
            'AG s prom': round(sum(v[2] for v in res) / len(res), 1),
        })

    df = pd.DataFrame(filas)
    sufijo = '_'.join(nombres) if nombres else 'todas'
    ruta_csv = os.path.join(DIR_SALIDA, f"resultados_validacion_{sufijo}.csv")
    df.to_csv(ruta_csv, index=False, encoding='utf-8-sig')
    print("\n" + df.to_string(index=False))
    print(f"\nResultados guardados en {ruta_csv}")
    return df


def consolidar():
    """Une los resultados de cada instancia en una tabla (CSV y Markdown)."""
    import glob
    archivos = sorted(glob.glob(os.path.join(DIR_SALIDA, 'resultados_validacion_I*.csv')),
                      key=lambda f: int(''.join(c for c in os.path.basename(f) if c.isdigit())))
    df = pd.concat([pd.read_csv(f) for f in archivos], ignore_index=True)
    df.to_csv(os.path.join(DIR_SALIDA, 'resultados_validacion_todas.csv'),
              index=False, encoding='utf-8-sig')

    def f(v, d=3):
        return '—' if pd.isna(v) else f"{v:.{d}f}"

    def estado(e, sg):
        return 'óptimo' if e == 'Óptimo' else ('sin solución' if str(e).startswith('Sin') else 'límite')

    lineas = ['| Inst. | Sublotes | Máq. | F1 ΣTj | F1 Cmax | F1 estado (s) | F2 ΣTj | F2 Cmax | '
              'F2 estado (s) | Regla ΣTj | AG mejor ΣTj | AG mejor Cmax | AG prom ΣTj | '
              'AG ≤ MILP (ΣTj) | AG s |',
              '|' + '---|' * 15]
    for _, r in df.iterrows():
        lineas.append(
            f"| {r['Instancia']} | {r['Sublotes']} (B̄={r['B̄']}) | {r['Máquinas']} | "
            f"{f(r['F1 ΣTj'])} | {f(r['F1 Cmax'])} | {estado(r['F1 estado'], r['F1 s'])} ({r['F1 s']:.0f}) | "
            f"{f(r['F2 ΣTj'])} | {f(r['F2 Cmax'])} | {estado(r['F2 estado'], r['F2 s'])} ({r['F2 s']:.0f}) | "
            f"{f(r['Regla ΣTj'])} | {f(r['AG mejor ΣTj'])} | {f(r['AG mejor Cmax'])} | "
            f"{f(r['AG prom ΣTj'])} | {r['AG ≤ MILP en ΣTj']} | {r['AG s prom']:.1f} |")
    tabla = '\n'.join(lineas)
    with open(os.path.join(DIR_SALIDA, 'resultados_validacion_todas.md'), 'w', encoding='utf-8') as fh:
        fh.write(tabla + '\n')
    print(tabla)
    return df


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'resumen':
    consolidar()
    sys.exit()

if __name__ == '__main__':
    # Tercer argumento opcional: instancias separadas por comas (p. ej. I1,I2)
    main(sys.argv[1] if len(sys.argv) > 1 else 'final_sc_hfsagls_S2_4.py',
         sys.argv[2] if len(sys.argv) > 2 else 'BD_HFS.xlsx',
         sys.argv[3].split(',') if len(sys.argv) > 3 else None)
