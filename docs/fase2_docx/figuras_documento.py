# -*- coding: utf-8 -*-
"""
Figuras adicionales del documento, generadas a partir de los datos y resultados:

  ocupacion_etapas.png      Fase 1: ocupación de cada etapa en el horizonte (Tabla 4)
  cromosoma_ejemplo.png     Fase 2: esquema del cromosoma del ejemplo de la tabla
  interaccion_pob_mut.png   Fase 2: interacción población × mutación (calibración)
  comparacion_ordenes.png   Cap. 5: terminación por orden, sistema actual frente a la propuesta

Se guardan en docs/fase2_docx/figuras/. Las llama generar_fase2_sintesis.py.
"""
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import pandas as pd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figuras')

# Paleta categórica validada (orden fijo) y tintas de texto
AZUL, NARANJA, AGUA = '#2a78d6', '#eb6834', '#1baf7a'
TINTA, TINTA2, REJILLA = '#0b0b0b', '#52514e', '#d9d9d6'

plt.rcParams.update({'font.size': 9, 'axes.edgecolor': TINTA2, 'axes.labelcolor': TINTA,
                     'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.titlesize': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})


def _coma(x, d=1):
    return f'{x:,.{d}f}'.replace(',', '§').replace('.', ',').replace('§', '.')


def _guardar(fig, nombre):
    os.makedirs(DIR, exist_ok=True)
    ruta = os.path.join(DIR, nombre)
    fig.savefig(ruta, dpi=220, bbox_inches='tight')
    plt.close(fig)
    return ruta


# ---------------------------------------------------------------------------

def ocupacion_etapas(ruta_bd):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from correcciones_fase1 import cargas
    filas, _, horizonte, _ = cargas(ruta_bd)
    etapas = [f[0] for f in filas][::-1]
    ocup = [f[4] for f in filas][::-1]
    maq = [f[1] for f in filas][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 2.5))
    ax.barh(range(len(etapas)), ocup, height=0.55, color=AZUL)
    for i, v in enumerate(ocup):
        ax.text(v + 1.2, i, f'{_coma(v, 0)} %', va='center', fontsize=9, color=TINTA)
    ax.axvline(100, color=TINTA2, lw=1, ls='--')
    ax.text(101.5, len(etapas) - 0.5, 'Horas\ndisponibles\n(100 %)', ha='left', va='top', fontsize=8,
            color=TINTA2)
    ax.set_yticks(range(len(etapas)))
    ax.set_yticklabels([f'{e} ({m} máq.)' for e, m in zip(etapas, maq)])
    ax.set_xlim(0, 118)
    ax.set_xlabel(f'Ocupación de cada máquina en el horizonte de {_coma(horizonte, 0)} h (%)')
    ax.grid(axis='x', color=REJILLA, lw=0.6)
    ax.set_axisbelow(True)
    return _guardar(fig, 'ocupacion_etapas.png')


def cromosoma_ejemplo():
    """Mismo ejemplo de la tabla del documento: J1 (25 docenas, 4 sublotes) y J2 (10, 2)."""
    ej = {'J1': ([0.10, 0.35, 0.30, 0.25], [3, 9, 7, 6]), 'J2': ([0.50, 0.50], [5, 5])}
    secuencias = [
        ('$O_1$ Troquelado', ['J1-2', 'J2-1', 'J1-1', 'J1-3', 'J2-2', 'J1-4']),
        ('$O_2$ Ensamble', ['J2-1', 'J1-2', 'J1-1', 'J2-2', 'J1-3', 'J1-4']),
        ('$O_3$ Costura', ['J1-2', 'J2-1', 'J1-1', 'J2-2', 'J1-4', 'J1-3']),
        ('$O_4$ Volteado', ['J2-1', 'J1-2', 'J2-2', 'J1-1', 'J1-3', 'J1-4'])]
    color = {'J1': AZUL, 'J2': NARANJA}
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.set_xlim(0, 30)
    ax.set_ylim(-0.6, 19)
    ax.axis('off')
    F = 'serif'

    def chip(x, y, w, h, txt, c, fs=8.5):
        ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h, boxstyle='round,pad=0,rounding_size=0.2',
                                    fc=c, ec='white', lw=1.5))
        ax.text(x + w / 2, y, txt, ha='center', va='center', fontsize=fs, color='white',
                fontweight='bold', family=F)

    # Nivel 1
    ax.text(0, 18.3, 'Nivel 1: tamaño de los sublotes (proporciones $\\pi_j$ → docenas)',
            fontsize=9.5, fontweight='bold', family=F, color=TINTA)
    escala = 0.85                                   # unidades de dibujo por docena
    for fila, (j, (props, tam)) in enumerate(ej.items()):
        y = 16.4 - fila * 2.5
        ax.text(0, y, f'{j}\n({sum(tam)} doc.)', va='center', fontsize=8.5, family=F, color=TINTA)
        x = 3.2
        for b, (p, q) in enumerate(zip(props, tam), start=1):
            w = q * escala
            chip(x, y, w, 1.3, f'{q}', color[j])
            ax.text(x + w / 2, y + 0.95, f'{_coma(p, 2)}', ha='center', va='bottom', fontsize=7.5,
                    family=F, color=TINTA2)
            x += w
        if fila == 0:
            ax.text(x + 0.4, y, '← docenas por sublote', va='center', fontsize=7.8, family=F,
                    color=TINTA2)
    ax.text(3.2, 12.75, 'Arriba de cada sublote: su proporción $\\pi_{jb}$; adentro: su tamaño en docenas '
                       '(igual en las cuatro etapas).', fontsize=7.8, family=F, color=TINTA2)

    # Nivel 2
    ax.text(0, 11.3, 'Nivel 2: orden de los sublotes en cada etapa (secuencias $O_s$)',
            fontsize=9.5, fontweight='bold', family=F, color=TINTA)
    for fila, (nombre, seq) in enumerate(secuencias):
        y = 9.8 - fila * 1.7
        ax.text(0, y, nombre, va='center', fontsize=8.5, family=F, color=TINTA)
        for k, s in enumerate(seq):
            chip(7.6 + k * 3.25, y, 3.0, 1.25, s, color[s.split('-')[0]], fs=8)
    ax.annotate('', xy=(27.5, 3.75), xytext=(7.6, 3.75),
                arrowprops=dict(arrowstyle='-|>', color=TINTA2, lw=1))
    ax.text(17.5, 3.4, 'se programa primero  →  se programa después', ha='center', va='top',
            fontsize=7.8, family=F, color=TINTA2)

    # Decodificador
    ax.add_patch(FancyBboxPatch((2.5, -0.5), 25, 2.2, boxstyle='round,pad=0,rounding_size=0.35',
                                fc='#F2F2F2', ec=TINTA2, lw=1))
    ax.text(15, 0.6, 'Decodificador: recorre cada secuencia y asigna cada sublote a la máquina\n'
                     'donde termina primero (regla ECT) → programación, $\\sum T_j$ y $C_{\\max}$',
            ha='center', va='center', fontsize=8.5, family=F, color=TINTA)
    return _guardar(fig, 'cromosoma_ejemplo.png')


def interaccion_pob_mut():
    d = pd.read_csv(os.path.join(RAIZ, 'fase2', 'salida_calibracion', 'corridas_diseno.csv'))
    t = d.pivot_table(index='poblacion', columns='prob_mutacion', values='suma_T', aggfunc='mean')
    fig, ax = plt.subplots(figsize=(5.6, 3.3))
    finales = []
    for c, m in zip((AZUL, NARANJA, AGUA), t.columns):
        ax.plot(t.index, t[m], color=c, lw=2, marker='o', ms=7, mec='white', mew=1.5,
                label=f'$p_m$ = {_coma(m, 1)}')
        finales.append([t[m].iloc[-1], m])
    # etiquetas directas al final de cada línea, separadas para que no se encimen
    finales.sort()
    sep = (t.values.max() - t.values.min()) * 0.07
    for k in range(1, len(finales)):
        finales[k][0] = max(finales[k][0], finales[k - 1][0] + sep)
    for y, m in finales:
        ax.text(t.index[-1] + 5, y, f'$p_m$ = {_coma(m, 1)}', va='center', fontsize=8.5, color=TINTA)
    ax.set_xticks(list(t.index))
    ax.set_xlim(t.index[0] - 8, t.index[-1] + 28)
    ax.set_xlabel('Tamaño de la población')
    ax.set_ylabel('Tardanza total promedio (h)')
    ax.grid(axis='y', color=REJILLA, lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(title='Probabilidad de mutación', fontsize=8, title_fontsize=8, frameon=False,
              loc='upper right', bbox_to_anchor=(0.86, 1.0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: _coma(v, 0)))
    return _guardar(fig, 'interaccion_pob_mut.png')


def comparacion_ordenes(M, indic, B_actual):
    sys.path.insert(0, os.path.join(RAIZ, 'fase3'))
    import experimentos_fase3 as F3
    b_orig = M.NUM_SUBLOTES
    ra = M.calcular_indicadores(M.simular_hfs(F3.individuo_fifo_por_etapa(M, B_actual))[0])
    M.NUM_SUBLOTES = b_orig
    J = sorted(M.TRABAJOS, key=lambda j: M.DUE_DATE[j], reverse=True)
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    for i, j in enumerate(J):
        ca, cp, d = ra['por_trabajo'][j]['Ci'], indic['por_trabajo'][j]['Ci'], M.DUE_DATE[j]
        ax.plot([min(ca, cp), max(ca, cp)], [i, i], color=REJILLA, lw=2, zorder=1)
        ax.plot([d, d], [i - 0.32, i + 0.32], color=TINTA, lw=2, zorder=2)
        ax.scatter([ca], [i], s=55, color=NARANJA, edgecolor='white', lw=1.5, zorder=3)
        ax.scatter([cp], [i], s=55, color=AZUL, edgecolor='white', lw=1.5, zorder=3)
        if ca > d + 1e-6:
            ax.text(ca + 8, i, f'+{_coma(ca - d, 0)} h', va='center', fontsize=8, color=TINTA2)
    ax.set_yticks(range(len(J)))
    ax.set_yticklabels([f'{j}  ($d_j$ = {_coma(M.DUE_DATE[j], 0)} h)' for j in J])
    ax.set_xlabel('Terminación de la orden $C_j$ (horas laborables)')
    ax.grid(axis='x', color=REJILLA, lw=0.6)
    ax.set_axisbelow(True)
    xmax = max(max(ra['por_trabajo'][j]['Ci'] for j in J), max(M.DUE_DATE.values())) + 60
    ax.set_xlim(150, xmax)
    from matplotlib.lines import Line2D
    ley = [Line2D([], [], marker='o', ls='', color=NARANJA, ms=7, label=f'Sistema actual (B = {B_actual})'),
           Line2D([], [], marker='o', ls='', color=AZUL, ms=7, label='Programación propuesta'),
           Line2D([], [], marker='|', ls='', color=TINTA, ms=12, mew=2, label='Fecha de entrega $d_j$')]
    ax.legend(handles=ley, loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False,
              fontsize=8.5)
    return _guardar(fig, 'comparacion_ordenes.png')


def generar(M, indic, ruta_bd, B_actual):
    return {'ocupacion': ocupacion_etapas(ruta_bd), 'cromosoma': cromosoma_ejemplo(),
            'interaccion': interaccion_pob_mut(), 'comparacion': comparacion_ordenes(M, indic, B_actual)}

