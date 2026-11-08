# -*- coding: utf-8 -*-
"""
Figuras de la programación propuesta (mejor solución, semilla 1203):
  gantt_etapa1.png … gantt_etapa4.png : diagrama de Gantt de cada etapa, con el eje
                                        de tiempo en horas laborables y las semanas.
  ruta_J07.png                        : recorrido de los sublotes de una orden por
                                        las cuatro etapas (máquina, inicio y fin).

Uso (desde la raíz del repositorio): python docs/fase2_figuras/gantt_por_etapa.py [orden]
"""
import os
import sys
import io
import json
import contextlib
import importlib.util

os.environ.setdefault('MPLBACKEND', 'Agg')
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIR = os.path.dirname(os.path.abspath(__file__))
COLORES = ['#4E79A7', '#F28E2B', '#59A14F', '#E15759', '#B07AA1',
           '#76B7B2', '#EDC948', '#FF9DA7', '#9C755F', '#BAB0AC']
COLOR_ETAPA = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
TINTA, TINTA2, REJILLA = '#222222', '#555555', '#d9d9d9'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': TINTA2,
                     'axes.labelcolor': TINTA, 'xtick.color': TINTA2, 'ytick.color': TINTA2})


def _texto_sobre(hexcolor):
    """Blanco sobre colores oscuros y negro sobre colores claros (legibilidad)."""
    r, g, b = (int(hexcolor[k:k + 2], 16) / 255 for k in (1, 3, 5))
    return 'white' if 0.299 * r + 0.587 * g + 0.114 * b < 0.6 else TINTA


def _coma(x, dec=1):
    return f'{x:.{dec}f}'.replace('.', ',')


def cargar():
    spec = importlib.util.spec_from_file_location('modelo', os.path.join(RAIZ, 'final_sc_hfsagls_S2_4.py'))
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with contextlib.redirect_stdout(io.StringIO()):
        M.cargar_datos(os.path.join(RAIZ, 'BD_HFS.xlsx'))
    mejor = json.load(open(os.path.join(RAIZ, 'fase2', 'salida_solucion', 'mejor_solucion.json'), encoding='utf-8'))
    ind = mejor['individuo']
    ind = {'k': {j: int(v) for j, v in ind['k'].items()}, 'proporciones': ind['proporciones'],
           'posiciones': {int(s): [tuple(x) for x in v] for s, v in ind['posiciones'].items()}}
    C, g = M.simular_hfs(ind)
    tam = {j: M.props_a_docenas(j, ind['proporciones'][j]) for j in M.TRABAJOS}
    return M, C, g, tam


def semanas():
    """Horas acumuladas al final de cada semana laboral (para marcar las semanas en el eje)."""
    c = pd.read_excel(os.path.join(RAIZ, 'BD_HFS.xlsx'), 'Disponibilidad')
    c = c[c['Fecha'].notna()].copy()
    c['acum'] = c['Horas disponibles'].cumsum()
    c['sem'] = (pd.to_datetime(c['Fecha']) - pd.to_datetime(c['Fecha']).min()).dt.days // 7 + 1
    return c.groupby('sem')['acum'].max().tolist()


def _eje_tiempo(ax, xmax, fin_semanas, arriba=True):
    ax.set_xlim(0, xmax)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(50))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(10))
    ax.grid(axis='x', which='major', color=REJILLA, linewidth=0.7)
    ax.grid(axis='x', which='minor', color=REJILLA, linewidth=0.3, alpha=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel('Tiempo (horas laborables desde el inicio del horizonte)')
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)
    if arriba:
        ax2 = ax.secondary_xaxis('top')
        lim = [0] + [h for h in fin_semanas if h <= xmax]
        centros = [(a + b) / 2 for a, b in zip(lim[:-1], lim[1:])]
        ax2.set_xticks(centros)
        ax2.set_xticklabels([f'S{k + 1}' for k in range(len(centros))], fontsize=7.5, color=TINTA2)
        ax2.tick_params(length=0)
        ax2.spines['top'].set_visible(False)
        ax2.set_xlabel('Semana', fontsize=8, color=TINTA2)
        for h in lim[1:]:
            ax.axvline(h, color='#aaaaaa', linewidth=0.6, linestyle=(0, (2, 3)), zorder=0)


def gantt_etapa(M, C, g, s, fin_semanas, ruta):
    color = {j: COLORES[i] for i, j in enumerate(M.TRABAJOS)}
    maqs = sorted({m for (_, _, m, _, _) in g[s]}, key=lambda m: int(m[1:]))
    pos = {m: k for k, m in enumerate(reversed(maqs))}
    alto = max(2.2, 0.36 * len(maqs) + 1.5)
    fig, ax = plt.subplots(figsize=(10, alto))
    for (j, b, m, ini, fin) in g[s]:
        ax.barh(pos[m], fin - ini, left=ini, height=0.74, color=color[j], edgecolor='white', linewidth=0.6)
        if fin - ini >= 3.1 * len(f'{j}-{b}'):
            ax.text((ini + fin) / 2, pos[m], f'{j}-{b}', ha='center', va='center', fontsize=6,
                    color=_texto_sobre(color[j]), fontweight='bold', clip_on=True)
    hay_al = False
    for (s_al, m_al, a, z) in g.get('alistamientos', []):
        if s_al == s and m_al in pos:
            hay_al = True      # dura 4,98 min: se marca con un triángulo sobre la barra
            ax.plot(a, pos[m_al] + 0.47, marker='v', markersize=4, color=TINTA, linestyle='none',
                    zorder=5, clip_on=False)
    fin_etapa = max(f for (*_, f) in g[s])
    ax.axvline(fin_etapa, color=TINTA, linewidth=1, linestyle='--')
    ax.text(fin_etapa + 3, len(maqs) - 0.5, f'fin de la etapa\n{_coma(fin_etapa)} h', fontsize=7.5,
            color=TINTA, va='top')
    ax.set_yticks(range(len(maqs)))
    ax.set_yticklabels(list(reversed(maqs)))
    ax.set_ylim(-0.6, len(maqs) - 0.4)
    ax.set_ylabel('Máquina')
    _eje_tiempo(ax, 620, fin_semanas)
    ley = [mpatches.Patch(color=color[j], label=f'{j} ({M.PRODUCTO[j]})') for j in M.TRABAJOS]
    if hay_al:
        ley.append(plt.Line2D([], [], marker='v', markersize=5, color=TINTA, linestyle='none',
                              label='Alistamiento (4,98 min)'))
    ax.legend(handles=ley, loc='upper center', bbox_to_anchor=(0.5, -0.30 if len(maqs) < 6 else -0.11),
              ncol=6, fontsize=7.5, frameon=False, handlelength=1.2, columnspacing=1.0)
    fig.savefig(ruta, dpi=200, bbox_inches='tight')
    plt.close(fig)


def ruta_orden(M, C, g, tam, j, ruta):
    ops = {(b, s): (m, i, f) for s in M.ETAPAS for (jj, b, m, i, f) in g[s] if jj == j}
    B = max(b for (b, _) in ops)
    r, d, cj = M.RELEASE[j], M.DUE_DATE[j], C[j]
    fig, ax = plt.subplots(figsize=(10, 0.42 * B + 1.8))
    for b in range(1, B + 1):
        y = B - b
        ax.plot([r, ops[(b, M.ETAPAS[-1])][2]], [y, y], color='#cccccc', linewidth=1, zorder=1)
        for k, s in enumerate(M.ETAPAS):
            m, i, f = ops[(b, s)]
            ax.barh(y, f - i, left=i, height=0.62, color=COLOR_ETAPA[k], edgecolor='white', linewidth=0.6, zorder=2)
            if f - i >= 8:
                ax.text((i + f) / 2, y, m, ha='center', va='center', fontsize=6.8,
                        color=_texto_sobre(COLOR_ETAPA[k]), fontweight='bold', zorder=3)
            else:            # segmento corto: la máquina se escribe encima
                ax.text((i + f) / 2, y + 0.36, m, ha='center', va='bottom', fontsize=6,
                        color=TINTA, zorder=3)
    for x, txt, est, ha in ((r, f'liberación r = {r:.0f} h', ':', 'left'),
                            (cj, f'terminación C = {_coma(cj)} h', '-', 'right'),
                            (d, f'entrega d = {d:.0f} h', '--', 'left')):
        ax.axvline(x, color=TINTA, linewidth=1, linestyle=est, zorder=4)
        ax.text(x + (1.5 if ha == 'left' else -1.5), B - 0.2, txt, fontsize=7.5, color=TINTA,
                va='bottom', ha=ha)
    ax.set_yticks(range(B))
    ax.set_yticklabels([f'S{b}  ({int(tam[j][b - 1])} doc.)' for b in range(B, 0, -1)])
    ax.set_ylim(-0.6, B + 0.6)
    ax.set_ylabel(f'Sublote de {j}')
    lo = 10 * int(r // 10) - 10
    hi = 10 * int(max(d, cj) // 10) + 30
    _eje_tiempo(ax, hi, [], arriba=False)
    ax.set_xlim(lo, hi)
    ley = [mpatches.Patch(color=COLOR_ETAPA[k], label=f'Etapa {k + 1}: {M.NOMBRE_ETAPA[s]}')
           for k, s in enumerate(M.ETAPAS)]
    ley.append(plt.Line2D([], [], color='#cccccc', linewidth=1, label='espera del sublote'))
    ax.legend(handles=ley, loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=5, fontsize=7.5,
              frameon=False, handlelength=1.4)
    fig.savefig(ruta, dpi=200, bbox_inches='tight')
    plt.close(fig)


def main():
    orden = sys.argv[1] if len(sys.argv) > 1 else 'J07'
    M, C, g, tam = cargar()
    fs = semanas()
    for k, s in enumerate(M.ETAPAS, start=1):
        gantt_etapa(M, C, g, s, fs, os.path.join(DIR, f'gantt_etapa{k}.png'))
    ruta_orden(M, C, g, tam, orden, os.path.join(DIR, f'ruta_{orden}.png'))
    print('Figuras guardadas en', DIR)


if __name__ == '__main__':
    main()
