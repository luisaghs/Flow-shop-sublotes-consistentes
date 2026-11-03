# -*- coding: utf-8 -*-
"""
Figura 1 del documento: diagrama de flujo del sistema estudiado (Fase 1).
Flow Shop híbrido de cuatro etapas con máquinas en paralelo; los elementos
excluidos del modelo (recepción del cuero y empaque/despacho) quedan fuera del
recuadro del sistema. Formato vertical para que el texto sea legible a 16 cm de ancho.

Uso: python diagrama_proceso.py   → genera diagrama_proceso.png en esta carpeta
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

AZUL, AZUL_OSC, GRIS = '#DCE6F2', '#B4C7E7', '#F2F2F2'
F = 'serif'

fig, ax = plt.subplots(figsize=(7.0, 8.6))
ax.set_xlim(0, 14)
ax.set_ylim(0, 21)
ax.axis('off')


def caja(x, y, w, h, texto, color=AZUL, fs=8.5, redonda=False, negrita=False, ls='-'):
    est = 'round,pad=0.02,rounding_size=0.3' if redonda else 'square,pad=0.02'
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=est, fc=color, ec='#333333',
                                lw=1, ls=ls))
    ax.text(x, y, texto, ha='center', va='center', fontsize=fs, family=F,
            fontweight='bold' if negrita else 'normal')


def flecha(x, y1, y2, txt=None):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1.1))
    if txt:
        ax.text(x + 0.25, (y1 + y2) / 2, txt, ha='left', va='center', fontsize=8, family=F)


X_TIT, W_TIT, H = 2.05, 2.9, 1.7          # columna de títulos de etapa
X0, X1 = 4.0, 13.4                        # franja de las máquinas

# --- Entrada (fuera del sistema)
caja(X_TIT + 1.9, 20.2, 6.9, 1.1, 'Bodega: recepción y selección del cuero\n(fuera del sistema)',
     GRIS, redonda=True, ls='--', fs=8.3)
flecha(X_TIT, 19.62, 16.25 + 0.02, None)
ax.text(X_TIT + 0.25, 18.9, 'Liberación de la orden ($r_j$)', ha='left', va='center', fontsize=8,
        family=F)

# --- Recuadro del sistema modelado
ax.add_patch(Rectangle((0.25, 2.55), 13.5, 15.6, fill=False, ec='#1F4E79', lw=1.3, ls='--'))
ax.text(8.45, 17.3, 'Sistema modelado:\nFlow Shop híbrido FH4 (P4, R15, P9, P8)', ha='center',
        va='center', fontsize=9.3, family=F, fontweight='bold', color='#1F4E79')

# --- Etapas: (y, título, máquinas, ancho de cada máquina, nota)
etapas = [
    (15.4, 'Etapa 1\nTrazado y\ntroquelado', ['M1', 'M2', 'M3', 'M4'], 1.75,
     '4 máquinas idénticas\nalistamiento de 4,98 min por cambio de referencia'),
    (11.8, 'Etapa 2\nEnsamble', ['M5 – M11\n(7, más lentas)', 'M12 – M15\n(4, intermedias)',
                                 'M16 – M19\n(4, más rápidas)'], 2.65,
     '15 máquinas no relacionadas\n(el tiempo depende de la referencia y de la máquina)'),
    (8.2, 'Etapa 3\nCostura', ['M20', 'M21', '…', 'M28'], 1.75, '9 máquinas idénticas'),
    (4.6, 'Etapa 4\nVolteado', ['M29', 'M30', '…', 'M36'], 1.75, '8 máquinas idénticas'),
]
for y, titulo, maqs, w, nota in etapas:
    caja(X_TIT, y, W_TIT, H, titulo, AZUL_OSC, fs=8.8, negrita=True)
    n = len(maqs)
    hueco = (X1 - X0 - n * w) / (n + 1)
    for i, t in enumerate(maqs):
        x = X0 + hueco * (i + 1) + w * (i + 0.5)
        if t == '…':
            ax.text(x, y + 0.15, '· · ·', ha='center', va='center', fontsize=12, family=F)
        else:
            caja(x, y + 0.15, w, 1.05 if '\n' in t else 0.8, t, fs=8.2)
    # corchete que agrupa las máquinas en paralelo y lo une a su etapa
    ax.plot([X0 - 0.05, X0 - 0.2, X0 - 0.2, X0 - 0.05], [y + 0.85, y + 0.85, y - 0.55, y - 0.55],
            color='#555555', lw=0.8)
    ax.plot([X_TIT + W_TIT / 2, X0 - 0.2], [y, y], color='#555555', lw=0.8)
    ax.text((X0 + X1) / 2, y - 0.95 - 0.22 * nota.count('\n'), nota, ha='center', va='center', fontsize=7.8, family=F,
            style='italic')

for (y1, *_), (y2, *_) in zip(etapas[:-1], etapas[1:]):
    flecha(X_TIT, y1 - H / 2, y2 + H / 2, 'sublotes')

# --- Salida (fuera del sistema)
flecha(X_TIT, etapas[-1][0] - H / 2, 1.55)
ax.text(X_TIT + 0.25, 2.2, 'Terminación ($C_j$)', ha='left', va='center', fontsize=8, family=F)
caja(X_TIT + 1.9, 1.0, 6.9, 1.05, 'Empaque, etiquetado y despacho\n(fuera del sistema)', GRIS,
     redonda=True, ls='--', fs=8.3)

ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagrama_proceso.png')
fig.savefig(ruta, dpi=220, bbox_inches='tight')
print('Guardado en', ruta)
