# Diagrama de flujo del algoritmo genético (figura del documento)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

fig, ax = plt.subplots(figsize=(7.2, 9.6))
ax.set_xlim(0, 10); ax.set_ylim(2.7, 24.8); ax.axis('off')
X, W, H = 4.6, 6.4, 1.15
AZUL, GRIS, VERDE = '#DCE6F2', '#F2F2F2', '#E2EFDA'

def caja(y, texto, color=AZUL, w=W, redonda=False):
    est = 'round,pad=0.02,rounding_size=0.55' if redonda else 'square,pad=0.02'
    ax.add_patch(FancyBboxPatch((X - w / 2, y - H / 2), w, H, boxstyle=est,
                                fc=color, ec='#333333', lw=1))
    ax.text(X, y, texto, ha='center', va='center', fontsize=8.6, family='serif')

def rombo(y, texto, w=6.6, h=1.9):
    ax.add_patch(Polygon([(X, y + h / 2), (X + w / 2, y), (X, y - h / 2), (X - w / 2, y)],
                         closed=True, fc='#FFF2CC', ec='#333333', lw=1))
    ax.text(X, y, texto, ha='center', va='center', fontsize=8.4, family='serif')

def flecha(x1, y1, x2, y2, txt=None, txt_pos=None):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='-|>', color='#333333', lw=1))
    if txt:
        ax.text(*(txt_pos or ((x1 + x2) / 2 + 0.15, (y1 + y2) / 2)), txt, fontsize=8, family='serif')

ys = [24.0, 22.3, 20.6, 18.9, 17.2, 15.5, 13.8, 12.1, 10.1, 8.0, 5.9, 3.6]
caja(ys[0], 'Inicio: lectura de datos (BD_HFS.xlsx)', GRIS, redonda=True)
caja(ys[1], 'Evaluar las reglas de despacho con sublotes iguales\n(FIFO, EDD, SPT, LPT, MST, CR)')
caja(ys[2], 'Población inicial: 149 cromosomas aleatorios\n+ cromosoma de la mejor regla')
caja(ys[3], 'Decodificar cada cromosoma y calcular su aptitud\n(ΣTj, Cmax)')
caja(ys[4], 'Elitismo: copiar el mejor individuo\na la nueva población')
caja(ys[5], 'Selección de dos padres por torneo (k = 3)')
caja(ys[6], 'Cruce (pc = 0,9): aritmético en el nivel 1,\nLOX en el nivel 2')
caja(ys[7], 'Mutación (pm = 0,5): perturbación en el nivel 1,\nintercambio en el nivel 2')
rombo(ys[8], '¿Nueva población\ncompleta (150)?')
caja(ys[9], 'Decodificar y evaluar la nueva población;\nactualizar la mejor solución')
rombo(ys[10], '¿100 generaciones sin mejora\no 1.000 generaciones?')
caja(ys[11], 'Fin: mejor programación\n(tamaños de sublote, secuencias, Gantt, indicadores)', VERDE, redonda=True)

for a, b in zip(ys[:8], ys[1:9]):
    off = 1.9 / 2 if b == ys[8] else H / 2
    flecha(X, a - H / 2, X, b + off)
flecha(X, ys[8] - 0.95, X, ys[9] + H / 2, 'Sí')
flecha(X, ys[9] - H / 2, X, ys[10] + 0.95)
flecha(X, ys[10] - 0.95, X, ys[11] + H / 2, 'Sí')
# Retornos
xr1 = X + 3.3 + 0.6
ax.plot([X + 3.3, xr1, xr1], [ys[8], ys[8], ys[5]], color='#333333', lw=1)
flecha(xr1, ys[5], X + W / 2, ys[5])
ax.text(X + 3.4, ys[8] + 0.15, 'No', fontsize=8, family='serif')
xr2 = X + 3.3 + 1.2
ax.plot([X + 3.3, xr2, xr2], [ys[10], ys[10], ys[4]], color='#333333', lw=1)
flecha(xr2, ys[4], X + W / 2, ys[4])
ax.text(X + 3.4, ys[10] + 0.15, 'No', fontsize=8, family='serif')
fig.savefig('diagrama_ag.png', dpi=200, bbox_inches='tight')
