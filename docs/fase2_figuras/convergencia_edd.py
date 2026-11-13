# -*- coding: utf-8 -*-
"""
Figura de convergencia del algoritmo genético frente a la solución inicial EDD
(datos de fase2/salida_revision, experimentos A y C):
  convergencia_edd.png : mejor tardanza total por generación en las 10 réplicas sembradas
                         con EDD y las 10 con población aleatoria (escala completa y detalle).

Uso (desde la carpeta principal del proyecto): python docs/fase2_figuras/convergencia_edd.py
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
        for conf, color, etiqueta in (('C', NARANJA, 'Población inicial aleatoria'),
                                      ('A', AZUL, 'Población sembrada con EDD')):
            primero = True
            for clave, hist in conv.items():
                if not clave.startswith(conf + '_'):
                    continue
                g = range(1, len(hist) + 1)
                for ax in (a1, a2):
                    ax.plot(g, [h[0] for h in hist], color=color, linewidth=0.9, alpha=0.75,
                            label=etiqueta if primero and ax is a1 else None)
                primero = False
        txt = f"EDD: {edd.regla_suma_T:.1f} h".replace('.', ',')
        for ax in (a1, a2):
            ax.axhline(edd.regla_suma_T, color=TINTA, linewidth=0.9, linestyle='--')
            ax.set_xscale('log')
            ax.set_xlim(1, 1000)
            ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f'{v:g}'))
            ax.grid(color=REJILLA, linewidth=0.6)
            ax.set_axisbelow(True)
            ax.set_xlabel('Generación (escala logarítmica)')
            ax.set_ylabel('Mejor tardanza total ΣTj (h)')
            for lado in ('top', 'right'):
                ax.spines[lado].set_visible(False)
        a1.text(1.1, edd.regla_suma_T + 15, txt, fontsize=7.5, color=TINTA, va='bottom')
        a2.text(1.1, edd.regla_suma_T + 1.5, txt, fontsize=7.5, color=TINTA, va='bottom')
        a2.set_ylim(-3, 110)
        a1.set_title('Escala completa', loc='left', fontsize=9.5, fontweight='bold', color=TINTA)
        a2.set_title('Detalle entre 0 y 110 h', loc='left', fontsize=9.5, fontweight='bold', color=TINTA)
        a1.legend(frameon=False, fontsize=8, loc='upper right')
        fig.tight_layout()
        fig.savefig(os.path.join(DIR, 'convergencia_edd.png'), dpi=200, bbox_inches='tight')
    print('Figura guardada en', os.path.join(DIR, 'convergencia_edd.png'))


if __name__ == '__main__':
    main()
