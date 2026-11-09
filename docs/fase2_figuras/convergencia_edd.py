# -*- coding: utf-8 -*-
"""
Figura de convergencia del algoritmo genético frente a la solución inicial EDD
(datos de fase2/salida_revision, experimentos A y C):
  convergencia_edd.png : mejor tardanza total y mejor makespan por generación en las
                         10 réplicas sembradas con EDD y las 10 con población aleatoria.

Uso (desde la raíz del repositorio): python docs/fase2_figuras/convergencia_edd.py
"""
import os
import json

os.environ.setdefault('MPLBACKEND', 'Agg')
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DIR = os.path.dirname(os.path.abspath(__file__))
REV = os.path.join(RAIZ, 'fase2', 'salida_revision')
AZUL, NARANJA, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#222222', '#555555', '#d9d9d9'


def main():
    conv = json.load(open(os.path.join(REV, 'convergencia.json'), encoding='utf-8'))
    d = pd.read_csv(os.path.join(REV, 'corridas.csv'))
    edd = d[d.config == 'A'].iloc[0]
    with plt.rc_context({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': TINTA2,
                         'xtick.color': TINTA2, 'ytick.color': TINTA2}):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
        for conf, color, etiqueta in (('C', NARANJA, 'Población aleatoria'), ('A', AZUL, 'Sembrada con EDD')):
            primero = True
            for clave, hist in conv.items():
                if not clave.startswith(conf + '_'):
                    continue
                g = range(1, len(hist) + 1)
                kw = dict(color=color, linewidth=0.9, alpha=0.75, label=etiqueta if primero else None)
                a1.plot(g, [h[0] for h in hist], **kw)
                a2.plot(g, [h[1] for h in hist], **kw)
                primero = False
        for ax, y, txt in ((a1, edd.regla_suma_T, f"EDD: {edd.regla_suma_T:.1f} h".replace('.', ',')),
                           (a2, edd.regla_Cmax, f"EDD: {edd.regla_Cmax:.1f} h".replace('.', ','))):
            ax.axhline(y, color=TINTA, linewidth=0.9, linestyle='--')
            ax.text(1.1, y, txt, fontsize=7.5, color=TINTA, va='bottom')
            ax.set_xscale('log')
            ax.set_xlim(1, 1000)
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f'{v:g}'))
            ax.grid(color=REJILLA, linewidth=0.6)
            ax.set_axisbelow(True)
            ax.set_xlabel('Generación (escala logarítmica)')
            for lado in ('top', 'right'):
                ax.spines[lado].set_visible(False)
        a1.set_ylabel('Mejor tardanza total ΣTj (h)')
        a2.set_ylabel('Mejor makespan Cmax (h)')
        a1.set_title('Tardanza total', loc='left', fontsize=9.5, fontweight='bold', color=TINTA)
        a2.set_title('Makespan', loc='left', fontsize=9.5, fontweight='bold', color=TINTA)
        a1.legend(frameon=False, fontsize=8, loc='upper right')
        fig.tight_layout()
        fig.savefig(os.path.join(DIR, 'convergencia_edd.png'), dpi=200, bbox_inches='tight')
    print('Figura guardada en', os.path.join(DIR, 'convergencia_edd.png'))


if __name__ == '__main__':
    main()
