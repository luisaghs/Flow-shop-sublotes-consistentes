# -*- coding: utf-8 -*-
"""
Documento de anexos del trabajo de grado. Toma los estilos del documento
principal y arma los anexos A–K a partir de la base de datos, el modelo y los
resultados guardados del repositorio. Los anexos A, B y C (estudio de tiempos,
registros históricos y autorización de la empresa) quedan con una página guía
para que los autores incluyan los soportes.

Uso: python generar_anexos.py documento_base.docx salida.docx
"""
import os
import re
import sys
import json
import inspect
import importlib.util
import io
import contextlib
import platform

import docx
import pandas as pd
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_docx as L                                                   # noqa: E402
import generar_fase2 as G                                              # noqa: E402
import fase3_doc as F3                                                 # noqa: E402

RAIZ = G.RAIZ
BD = os.path.join(RAIZ, 'BD_HFS.xlsx')
MODELO = os.path.join(RAIZ, 'final_sc_hfsagls_S2_4.py')
FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figuras')
n = G.n
ETAPAS = ['Troquelado', 'Ensamble', 'Costura', 'Volteado']


def _clave_m(m):
    return int(''.join(c for c in m if c.isdigit()))


# ---------------------------------------------------------------------------
# Escritor con rótulos por anexo (Tabla D.1, Figura H.1, ...)
# ---------------------------------------------------------------------------

class EscritorAnexo(L.Escritor):
    def __init__(self, documento, omml):
        super().__init__(documento, omml)
        self.letra, self.cont = 'A', {}

    def _num_vineta(self):
        """numId de una lista con viñetas del documento base (nivel 0 con formato 'bullet')."""
        if getattr(self, '_nv', None):
            return self._nv
        nb = self._numeracion
        abst = set()
        for an in nb.findall(qn('w:abstractNum')):
            for lvl in an.findall(qn('w:lvl')):
                fmt = lvl.find(qn('w:numFmt'))
                if lvl.get(qn('w:ilvl')) == '0' and fmt is not None and fmt.get(qn('w:val')) == 'bullet':
                    abst.add(an.get(qn('w:abstractNumId')))
        for num in nb.findall(qn('w:num')):
            a = num.find(qn('w:abstractNumId'))
            if a is not None and a.get(qn('w:val')) in abst:
                self._nv = num.get(qn('w:numId'))
                return self._nv
        raise ValueError('El documento base no tiene una lista con viñetas.')

    def viñetas(self, items):
        self._lista(items, self._num_vineta())

    def nuevo_anexo(self, letra, titulo):
        self.letra, self.cont = letra, {}
        p = self.d.add_paragraph(f'Anexo {letra}. {titulo}', style='Titulo')
        p.paragraph_format.page_break_before = True

    def _rotulo(self, tipo, titulo, reiniciar=None):
        self.cont[tipo] = self.cont.get(tipo, 0) + 1
        p = self.d.add_paragraph(style='Caption')
        p.paragraph_format.keep_with_next = True
        r = p.add_run(f'{tipo} {self.letra}.{self.cont[tipo]}. {titulo}')
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0, 0, 0)
        return self.cont[tipo]

    def listado(self, lineas, tam=8):
        """Código en fuente monoespaciada, en párrafos (puede ocupar varias páginas)."""
        for ln in lineas:
            p = self.d.add_paragraph()
            pf = p.paragraph_format
            pf.space_after = Pt(0); pf.space_before = Pt(0); pf.line_spacing = 1.0
            pf.first_line_indent = Pt(0)
            r = p.add_run(ln.rstrip('\n') if ln.strip() else ' ')
            r.font.name = 'Consolas'; r.font.size = Pt(tam)
            r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
        self.d.add_paragraph()

    def nota(self, texto):
        """Recuadro de instrucciones para los autores (resaltado)."""
        p = self.d.add_paragraph()
        r = p.add_run(texto)
        r.italic = True
        r.font.highlight_color = 7                      # amarillo


# Hojas del libro Anexos_datos.xlsx (generar_anexos_excel.py) que respaldan cada anexo
RESPALDO_XLSX = {
    'D': ['D1_Ordenes', 'D2_Tiempos', 'D3_Calendario'],
    'E': ['E_Carga'],
    'F': ['F_Validacion'],
    'G': ['G1_Corridas', 'G2_Combinaciones', 'G3_ANOVA', 'G4_Supuestos', 'G5_Parada'],
    'H': ['H1_Replicas', 'H2_Programacion', 'H3_Por_orden'],
    'I': ['I_Sistema_actual'],
    'J': ['J1_Corridas_F3', 'J2_Deterministas', 'J3_Resumen'],
}


def _resolver(bloques, letra):
    """Reemplaza {T:x} y {F:x} por D.1, D.2... según el orden de aparición en el anexo."""
    nums, t, f = {}, 0, 0
    for b in bloques:
        if b[0] == 'tabla':
            t += 1
            kw = b[4] if len(b) > 4 else {}
            if kw.get('etiqueta'):
                nums['T:' + kw['etiqueta']] = f'{letra}.{t}'
        elif b[0] in ('figura', 'codigo'):
            f += 1
            lbl = b[4] if b[0] == 'figura' and len(b) > 4 else (b[3] if b[0] == 'codigo' and len(b) > 3 else None)
            if lbl:
                nums['F:' + lbl] = f'{letra}.{f}'

    def sub(x):
        if isinstance(x, str):
            return re.sub(r'\{([TF]:[a-z0-9_]+)\}', lambda m: nums[m.group(1)], x)
        if isinstance(x, list):
            return [sub(y) for y in x]
        if isinstance(x, tuple):
            return tuple(sub(y) for y in x)
        if isinstance(x, dict):
            return {k: sub(v) for k, v in x.items()}
        return x
    return [sub(b) for b in bloques]


def _cargar_modelo():
    spec = importlib.util.spec_from_file_location('modelo_ag', MODELO)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with contextlib.redirect_stdout(io.StringIO()):
        M.cargar_datos(BD)
    return M


# ---------------------------------------------------------------------------
# Anexos
# ---------------------------------------------------------------------------

def anexos_autores():
    return [
        ('A', 'Estudio de tiempos', [
            ('p', 'Este anexo respalda los tiempos estándar de la Tabla 2 y el tiempo de alistamiento en '
                  'troquelado. Debe incluir:'),
            ('viñetas', ['Los formatos de toma de tiempos de cada referencia en cada etapa, con las cinco '
                         'muestras tomadas, la fecha, la máquina y el operario observado.',
                         'El cálculo del tiempo observado (promedio de las muestras) y, si se aplicaron, la '
                         'valoración del ritmo y los suplementos con que se obtuvo el tiempo estándar.',
                         'Las mediciones del tiempo de alistamiento por cambio de referencia en troquelado '
                         '(4,98 minutos).',
                         'La relación entre las máquinas de ensamble y los tres grupos de velocidad.']),
            ('nota', '[Insertar aquí los formatos del estudio de tiempos.]')]),
        ('B', 'Registros históricos de cumplimiento', [
            ('p', 'Este anexo respalda las cifras del planteamiento del problema y la calibración del '
                  'sistema actual en la Fase 3. Debe incluir:'),
            ('viñetas', ['Los registros de las órdenes con su fecha de entrega pactada y su fecha real de '
                         'entrega, de los que se obtiene el 45 % de incumplimiento y el 10 % de adelantos, '
                         'indicando el periodo que cubren.',
                         'El soporte de la utilización de la capacidad mencionada en el planteamiento '
                         '(60 % en troquelado y 80 % en costura).',
                         'Si no existen registros formales, una constancia firmada por el responsable de '
                         'producción que certifique estas cifras y el periodo al que corresponden.']),
            ('nota', '[Insertar aquí los registros o la constancia de la empresa.]')]),
        ('C', 'Autorización de la empresa', [
            ('p', 'Este anexo respalda el uso de la información de la empresa en el trabajo. Debe incluir la '
                  'autorización del representante de la empresa para usar sus datos con fines académicos y, '
                  'si aplica, las condiciones de confidencialidad acordadas (por ejemplo, no publicar el '
                  'nombre de la empresa o de sus clientes).'),
            ('nota', '[Insertar aquí la autorización firmada.]')]),
    ]


def anexo_d():
    x = pd.ExcelFile(BD)
    j = x.parse('Trabajos')
    t = x.parse('Tiempo de procesamiento')
    t.columns = [c.strip() for c in t.columns]
    cal = x.parse('Disponibilidad')
    f = lambda v: pd.Timestamp(v).strftime('%d/%m/%Y')
    filas_ord = [[r['Orden de trabajo'], r['Codigo Producto'], n(r['Cantidad (docenas)'], 0), f(r['Fecha de liberación']),
                  n(r['r_j Liberación'], 0), f(r['Fechas de entrega']), n(r['d_j horas'], 0),
                  n(r['d_j horas'] - r['r_j Liberación'], 0)] for _, r in j.iterrows()]
    refs = sorted(t['Codigo producto'].astype(str).str.strip().unique())
    t['Maquina'] = t['Maquina'].astype(str).str.strip()
    piv = t.pivot_table(index=['Etapa', 'Maquina'], columns='Codigo producto', values='min x docena')
    filas_t = []
    for etapa in ETAPAS:
        maqs = sorted([m for (e, m) in piv.index if e.strip() == etapa], key=_clave_m)
        for m in maqs:
            fila = piv.loc[(next(e for (e, mm) in piv.index if mm == m), m)]
            filas_t.append([etapa if m == maqs[0] else '', m] + [n(fila[r], 2) for r in refs])
    # Calendario por semana hasta la última fecha de entrega
    cal = cal[cal['Fecha'].notna()].copy()
    cal['Fecha'] = pd.to_datetime(cal['Fecha'])
    fin = pd.Timestamp(j['Fechas de entrega'].max())
    cal = cal[cal['Fecha'] <= fin]
    ini = cal['Fecha'].min()
    cal['sem'] = (cal['Fecha'] - ini).dt.days // 7 + 1
    filas_c = []
    for s, g in cal.groupby('sem'):
        filas_c.append([str(s), f(g['Fecha'].min()), f(g['Fecha'].max()),
                        str(int((g['Horas disponibles'] > 0).sum())), n(g['Horas disponibles'].sum(), 0),
                        n(g['Horas acumuladas final día'].max(), 0)])
    fest = x.parse('Disponibilidad')['Festivos'].dropna()
    fest = [f(v) for v in fest if pd.Timestamp(v) <= fin]
    return [
        ('p', 'Este anexo presenta la información de la empresa con que se construyó el caso de estudio: '
              'las órdenes de trabajo, los tiempos estándar de cada referencia en cada máquina y el calendario '
              'laboral. Corresponde al archivo BD_HFS.xlsx del anexo digital y respalda las Tablas 1 a 3 del '
              'documento.'),
        ('tabla', 'Órdenes de trabajo del caso de estudio',
         ['Orden', 'Ref.', 'Cantidad (docenas)', 'Liberación', 'r_j (h)', 'Entrega', 'd_j (h)', 'd_j − r_j (h)'],
         filas_ord, {'etiqueta': 'ord', 'anchos': [800, 700, 1200, 1300, 900, 1300, 900, 1738], 'tam': 10,
                     'alineacion': ['c'] * 8}),
        ('p', 'Las horas $r_j$ y $d_j$ son horas laborables acumuladas desde el inicio del horizonte '
              f"({f(ini)}): la liberación corresponde al inicio de su día y la entrega al final de su día."),
        ('tabla', 'Tiempos estándar por máquina y referencia (minutos por docena)',
         ['Etapa', 'Máquina'] + refs, filas_t,
         {'etiqueta': 'tiempos', 'anchos': [1500, 1000] + [int(6338 / len(refs))] * len(refs), 'tam': 9,
          'alineacion': ['l', 'c'] + ['c'] * len(refs)}),
        ('tabla', 'Calendario laboral por semana hasta la última fecha de entrega',
         ['Semana', 'Desde', 'Hasta', 'Días laborables', 'Horas de la semana', 'Horas acumuladas'], filas_c,
         {'etiqueta': 'cal', 'anchos': [1000, 1600, 1600, 1500, 1500, 1638], 'tam': 10, 'alineacion': ['c'] * 6}),
        ('p', ('Días festivos dentro del horizonte (sin horas laborables): ' + ', '.join(fest) + '.')
              if fest else 'No hay días festivos dentro del horizonte.'),
    ]


def anexo_e():
    from correcciones_fase1 import cargas
    x = pd.ExcelFile(BD)
    t = x.parse('Tiempo de procesamiento'); t.columns = [c.strip() for c in t.columns]
    j = x.parse('Trabajos')
    refs = sorted(t['Codigo producto'].astype(str).str.strip().unique())
    R = {}
    for e in ETAPAS:
        te = t[t['Etapa'].str.strip() == e]
        for p in refs:
            R[(e, p)] = (60.0 / te[te['Codigo producto'].astype(str).str.strip() == p]['min x docena']).sum()
    filas_r = [[p] + [n(R[(e, p)], 2) for e in ETAPAS] for p in refs]
    filas_j, tot = [], {e: 0.0 for e in ETAPAS}
    for _, o in j.iterrows():
        p = str(o['Codigo Producto']).strip()
        hs = {e: o['Cantidad (docenas)'] / R[(e, p)] for e in ETAPAS}
        for e in ETAPAS:
            tot[e] += hs[e]
        filas_j.append([o['Orden de trabajo'], p, n(o['Cantidad (docenas)'], 0)] + [n(hs[e], 1) for e in ETAPAS])
    filas_j.append(['Total', '', n(j['Cantidad (docenas)'].sum(), 0)] + [n(tot[e], 1) for e in ETAPAS])
    filas, total, hor, _ = cargas(BD)
    filas_res = [[e, str(nm), n(ct, 1), n(pm, 1), n(hor, 0), n(oc, 1) + ' %'] for e, nm, ct, pm, oc in filas]
    return [
        ('p', 'Este anexo detalla el cálculo de la carga de trabajo frente a la capacidad (Tabla 4 del '
              'documento). Para cada etapa y referencia se calcula la capacidad agregada de la etapa, '
              r'$R_p=\sum_{m}60/t_{pm}$ docenas por hora, donde $t_{pm}$ es el tiempo estándar en minutos por '
              'docena de la referencia $p$ en la máquina $m$. La carga de cada orden en una etapa equivale a '
              r'$Q_j/R_p$ horas de trabajo de cada máquina, si la carga se reparte de forma equilibrada.'),
        ('tabla', 'Capacidad agregada de cada etapa por referencia (docenas por hora)',
         ['Referencia'] + ETAPAS, filas_r, {'etiqueta': 'rp', 'anchos': [1838] + [1750] * 4, 'tam': 10,
                                              'alineacion': ['c'] * 5}),
        ('tabla', 'Carga de cada orden por etapa (horas por máquina)',
         ['Orden', 'Ref.', 'Docenas'] + ETAPAS, filas_j,
         {'etiqueta': 'carga', 'anchos': [900, 800, 1138] + [1500] * 4, 'tam': 10, 'alineacion': ['c'] * 7,
          'negrita_filas': (len(filas_j) - 1,)}),
        ('tabla', 'Ocupación de cada etapa en el horizonte de planeación',
         ['Etapa', 'Máquinas', 'Carga total (h)', 'Carga por máquina (h)', 'Horizonte (h)', 'Ocupación'],
         filas_res, {'etiqueta': 'ocup', 'anchos': [1600, 1100, 1500, 1800, 1400, 1438], 'tam': 10,
                     'alineacion': ['l'] + ['c'] * 5}),
        ('p', 'La carga total de la etapa es la carga por máquina multiplicada por el número de máquinas, y la '
              'ocupación es la carga por máquina dividida entre el horizonte, que se extiende hasta la última '
              'fecha de entrega.'),
    ]


def anexo_f():
    import generar_fase2_sintesis as S
    bloques = S.validacion()
    bloques = [b for b in bloques if not (b[0] == 'h3')]
    reemplazos = [('los parámetros calibrados en la sección 4.2.4', 'los parámetros calibrados en la Fase 2')]

    def rep(x):
        if isinstance(x, str):
            for a, b in reemplazos:
                x = x.replace(a, b)
            return x
        if isinstance(x, list):
            return [rep(y) for y in x]
        if isinstance(x, tuple):
            return tuple(rep(y) for y in x)
        return x
    intro = [('p', 'Este anexo presenta la verificación del decodificador y la validación del modelo matemático '
                   'y del algoritmo genético con instancias reducidas. Respalda las afirmaciones del documento '
                   'sobre la correcta formulación del modelo y la capacidad del algoritmo para encontrar '
                   'soluciones óptimas.')]
    return intro + [rep(b) for b in bloques]


def _informe_supuestos():
    txt = open(os.path.join(G.SAL_CAL, 'informe_calibracion.md'), encoding='utf-8').read()
    filas = []
    NUM = r'(\d+(?:\.\d+)?(?:e-?\d+)?)'
    m = re.search(r'Shapiro-Wilk\): W = ' + NUM + ', p = ' + NUM, txt)
    if m:
        filas.append(['Normalidad de los residuos', 'Shapiro-Wilk', f"W = {n(float(m.group(1)), 3)}",
                      S_p(float(m.group(2)))])
    for fac, nom in (('Población', 'Población'), ('Prob. de cruce', 'Prob. de cruce'),
                     ('Prob. de mutación', 'Prob. de mutación')):
        m = re.search(re.escape(fac) + ': Levene p = ' + NUM + '; Kruskal-Wallis H = ' + NUM + ', p = ' + NUM, txt)
        if m:
            filas.append([f'Homogeneidad de varianzas ({nom.lower()})', 'Levene', '—', S_p(float(m.group(1)))])
            filas.append([f'Efecto de {nom.lower()} (no paramétrica)', 'Kruskal-Wallis',
                          f"H = {n(float(m.group(2)), 2)}", S_p(float(m.group(3)))])
    return filas


def S_p(p):
    return '< 0,0001' if p < 1e-4 else n(p, 4)


def anexo_g():
    rr = pd.read_csv(os.path.join(G.SAL_CAL, 'resumen_combinaciones.csv'))
    rr = rr.sort_values(['T_prom', 'C_prom']).reset_index(drop=True)
    filas = [[str(i + 1), str(int(r.poblacion)), n(r.prob_cruce, 1), n(r.prob_mutacion, 1), n(r.T_prom, 2),
              n(r.T_desv, 2), n(r.Tard, 1), n(r.C_prom, 1)] for i, r in rr.iterrows()]
    par = pd.read_csv(os.path.join(G.SAL_CAL, 'corridas_parada.csv'))
    piv = par.pivot_table(index='semilla', columns='sin_mejora', values=['suma_T', 'Cmax', 'generaciones'])
    niv = sorted(par['sin_mejora'].unique())
    filas_p = [[str(s)] + sum([[n(piv.loc[s, ('suma_T', k)], 2), n(piv.loc[s, ('Cmax', k)], 1),
                                 n(piv.loc[s, ('generaciones', k)], 0)] for k in niv], []) for s in piv.index]
    enc_p = ['Semilla'] + sum([[f'ΣT_j ({k})', f'C_max ({k})', f'Gen. ({k})'] for k in niv], [])
    d = pd.read_csv(os.path.join(G.SAL_CAL, 'corridas_diseno.csv'))
    return [
        ('p', f'Este anexo amplía la calibración de los parámetros del algoritmo genético (Tablas 7 a 10 del '
              f'documento). El diseño factorial completo 3³ tuvo {len(d)} corridas: 27 combinaciones de población, '
              'probabilidad de cruce y probabilidad de mutación, con 5 réplicas cada una (semillas 1001 a 1005, '
              'la misma semilla para la misma réplica en todas las combinaciones) y un esfuerzo de cómputo fijo '
              'de 30.000 cromosomas generados por corrida. La Tabla {T:combos} presenta las 27 combinaciones '
              'ordenadas de menor a mayor tardanza promedio; las 135 corridas individuales están en el archivo '
              'corridas_diseno.csv del anexo digital, y el ANOVA calculado con fórmulas de Excel, en '
              'anova_calibracion_excel.xlsx.'),
        ('tabla', 'Resultados de las 27 combinaciones del diseño factorial (promedio de 5 réplicas)',
         ['Pos.', 'Población', 'p_c', 'p_m', 'ΣT_j prom. (h)', 'ΣT_j desv. (h)', 'Tardías prom.', 'C_max prom. (h)'],
         filas, {'etiqueta': 'combos', 'anchos': [700, 1100, 800, 800, 1450, 1450, 1150, 1388], 'tam': 9,
                 'alineacion': ['c'] * 8, 'negrita_filas': (0,)}),
        ('p', 'La Tabla {T:supuestos} resume las pruebas de los supuestos del ANOVA y la prueba no paramétrica '
              'de Kruskal-Wallis con que se confirmó el resultado. Un valor p menor que 0,05 indica que no se '
              'cumple el supuesto (Shapiro-Wilk y Levene) o que el factor tiene efecto significativo '
              '(Kruskal-Wallis).'),
        ('tabla', 'Pruebas de supuestos y prueba de Kruskal-Wallis', ['Aspecto evaluado', 'Prueba', 'Estadístico',
                                                                      'Valor p'], _informe_supuestos(),
         {'etiqueta': 'supuestos', 'anchos': [3600, 1700, 1700, 1838], 'tam': 10,
          'alineacion': ['l', 'c', 'c', 'c']}),
        ('figura', 'Efectos principales de los parámetros sobre la tardanza total (intervalos LSD al 95 %)',
         os.path.join(G.SAL_CAL, 'efectos_principales.png'), 15.5, 'efectos'),
        ('figura', 'Interacción entre el tamaño de la población y la probabilidad de mutación',
         os.path.join(FIG, 'interaccion_pob_mut.png'), 12.0, 'inter'),
        ('p', 'Con la mejor combinación (población 150, cruce 0,9 y mutación 0,5) se compararon dos criterios '
              'de parada, 50 y 100 generaciones sin mejora, con 10 réplicas cada uno (semillas 1101 a 1110). '
              'La Tabla {T:parada} presenta cada réplica; con la misma semilla, la corrida de 100 generaciones '
              'continúa la de 50, por lo que nunca termina con una solución peor.'),
        ('tabla', 'Réplicas del experimento del criterio de parada (entre paréntesis, generaciones sin mejora)',
         enc_p, filas_p, {'etiqueta': 'parada', 'anchos': [1000] + [1306] * (len(enc_p) - 1), 'tam': 9,
                          'alineacion': ['c'] * len(enc_p)}),
    ]


def anexo_h(M):
    rep = pd.read_csv(os.path.join(G.SAL_SOL, 'replicas.csv'))
    mejor = json.load(open(os.path.join(G.SAL_SOL, 'mejor_solucion.json'), encoding='utf-8'))
    filas_r = [[str(int(r.semilla)), n(r.suma_T, 2), n(r.Cmax, 2), str(int(r.tardias)), str(int(r.generaciones)),
                n(r.segundos / 60, 1)] for r in rep.itertuples()]
    ind = mejor['individuo']
    ind = {'k': {j: int(v) for j, v in ind['k'].items()}, 'proporciones': ind['proporciones'],
           'posiciones': {int(s): [tuple(x) for x in v] for s, v in ind['posiciones'].items()}}
    C, g = M.simular_hfs(ind)
    tam = {j: M.props_a_docenas(j, ind['proporciones'][j]) for j in M.TRABAJOS}
    op = {}
    for s in M.ETAPAS:
        for (j, b, m, i, f) in g[s]:
            op[(j, b, s)] = (m, i, f)
    filas_p = []
    for j in M.TRABAJOS:
        for b in range(1, ind['k'][j] + 1):
            celdas = []
            for s in M.ETAPAS:
                m, i, f = op[(j, b, s)]
                celdas.append(f'{m}: {n(i, 1)}–{n(f, 1)}')
            filas_p.append([j if b == 1 else '', str(b), n(tam[j][b - 1], 0)] + celdas)
    al = g['alistamientos']
    return [
        ('p', f"Este anexo respalda la programación propuesta para el caso de estudio. La Tabla {{T:rep}} "
              f"presenta las {len(rep)} réplicas del algoritmo con los parámetros calibrados (semillas "
              f"{int(rep.semilla.min())} a {int(rep.semilla.max())}); la programación propuesta es la de la "
              f"semilla {int(mejor['semilla'])}, la de menor tardanza total y, en empate, menor makespan."),
        ('tabla', 'Réplicas finales del algoritmo genético',
         ['Semilla', 'ΣT_j (h)', 'C_max (h)', 'Órdenes tardías', 'Generaciones', 'Tiempo (min)'], filas_r,
         {'etiqueta': 'rep', 'anchos': [1300, 1400, 1500, 1600, 1500, 1538], 'tam': 10, 'alineacion': ['c'] * 6}),
        ('figura', f"Convergencia de la réplica con semilla {int(mejor['semilla'])}: tardanza total y makespan de "
                   'la mejor solución en cada generación', os.path.join(G.SAL_SOL, 'convergencia.png'), 14.5, 'conv'),
        ('p', 'La Tabla {T:prog} presenta la programación completa de la solución propuesta: para cada sublote, '
              'su tamaño y, en cada etapa, la máquina asignada y los instantes de inicio y fin, en horas laborables '
              f"desde el inicio del horizonte. La programación incluye {len(al)} alistamientos en troquelado, con "
              f"un total de {n(sum(f - i for (_, _, i, f) in al), 1)} h."),
        ('tabla', 'Programación detallada de la solución propuesta (máquina: inicio–fin, en horas)',
         ['Orden', 'Sub.', 'Doc.'] + ETAPAS, filas_p,
         {'etiqueta': 'prog', 'anchos': [700, 550, 650, 1735, 1735, 1735, 1733], 'tam': 8,
          'alineacion': ['c'] * 7}),
    ]


def anexo_i(M):
    det, ag, bb, act, regla, grupo, calib = F3.datos(M)
    filas_c = [[str(B), f"{r['tardias']} ({n(r['pct_tardias'], 0)} %)", n(r['suma_T'], 1), n(r['Cmax'], 1),
                n(r['flujo_medio'], 1)] for B, r in calib]
    b_orig = M.NUM_SUBLOTES
    res = {}
    for B in F3.F.B_ACTUAL_SENS:
        r = M.calcular_indicadores(M.simular_hfs(F3.F.individuo_fifo_por_etapa(M, B))[0])
        res[B] = r['por_trabajo']
    M.NUM_SUBLOTES = b_orig
    enc = ['Orden', 'd_j (h)'] + sum([[f'C_j B={B}', f'T_j B={B}'] for B in F3.F.B_ACTUAL_SENS], [])
    filas_o = [[j, n(M.DUE_DATE[j], 0)] + sum([[n(res[B][j]['Ci'], 1), n(res[B][j]['Ti'], 1)]
                                                 for B in F3.F.B_ACTUAL_SENS], []) for j in M.TRABAJOS]
    return [
        ('p', 'Este anexo respalda la representación del sistema de programación actual (Fase 3). El sistema '
              'actual se representa con la regla FIFO por etapa: en troquelado las órdenes se atienden por orden '
              'de liberación y, en cada etapa siguiente, los sublotes en el orden en que llegan; cada orden se '
              'divide en B partes iguales y cada parte se asigna a la máquina que la termina primero. La Tabla '
              '{T:calib} muestra su desempeño según B. Con diez órdenes, el porcentaje de órdenes tardías varía '
              f'de 10 en 10 puntos; se adoptó B = {bb}, el menor número de partes con el porcentaje más cercano '
              'al 45 % histórico.'),
        ('tabla', 'Desempeño del sistema actual según el número de partes por orden',
         ['B', 'Órdenes tardías', 'ΣT_j (h)', 'C_max (h)', 'Flujo medio (h)'], filas_c,
         {'etiqueta': 'calib', 'anchos': [1000, 2200, 1900, 1900, 1838], 'tam': 10, 'alineacion': ['c'] * 5,
          'negrita_filas': (bb - 2,)}),
        ('p', 'La Tabla {T:orden_act} presenta la terminación y la tardanza de cada orden con el sistema actual '
              f"para B = {F3._lista([str(B) for B in F3.F.B_ACTUAL_SENS])}, los valores usados en el análisis de "
              'sensibilidad.'),
        ('tabla', 'Terminación y tardanza por orden con el sistema actual (horas)', enc, filas_o,
         {'etiqueta': 'orden_act', 'anchos': [900, 1000] + [1156] * (len(enc) - 2), 'tam': 9,
          'alineacion': ['c'] * len(enc)}),
    ]


def anexo_j():
    ag = pd.read_csv(os.path.join(F3.DIR3, 'corridas_ag.csv'))
    det = pd.read_csv(os.path.join(F3.DIR3, 'deterministas.csv'))
    bb = F3.F.B_ACTUAL_BASE
    b10 = ag[(ag.escenario == 'base') & (ag.B == 10)].set_index('semilla').sort_index()
    bB = ag[(ag.escenario == 'base') & (ag.B == bb)].set_index('semilla')
    filas_b = [[str(s), str(int(r.tardias)), n(r.suma_T, 2), n(r.Cmax, 1), str(int(bB.loc[s, 'tardias'])),
                n(bB.loc[s, 'suma_T'], 2), n(bB.loc[s, 'Cmax'], 1)] for s, r in b10.iterrows()]
    sens = [B for B in F3.F.B_ACTUAL_SENS if B != bb]
    gs = {B: ag[(ag.escenario == 'base') & (ag.B == B)].set_index('semilla') for B in sens}
    sem_s = sorted(gs[sens[0]].index)
    filas_s = [[str(s)] + sum([[str(int(gs[B].loc[s, 'tardias'])), n(gs[B].loc[s, 'suma_T'], 2)] for B in sens], [])
               for s in sem_s]
    esc = [e for e in F3.F.ESCENARIOS if e != 'base']
    ge = {e: ag[(ag.escenario == e) & (ag.B == 10)].set_index('semilla') for e in esc}
    filas_e = [[str(s)] + [f"{n(ge[e].loc[s, 'suma_T'], 1)} ({int(ge[e].loc[s, 'tardias'])})" for e in esc]
               for s in sorted(ge[esc[0]].index)]
    nom_e = {'fechas_-10': 'Fechas −10 %', 'fechas_-20': 'Fechas −20 %', 'demanda_+10': 'Demanda +10 %',
             'demanda_+20': 'Demanda +20 %'}
    base = det[det.escenario == 'base']
    Bs = sorted(base.B.unique())
    metodos = list(dict.fromkeys(base.metodo))
    filas_d = []
    for mtd in metodos:
        fila = [mtd.replace('Actual (FIFO por etapa)', 'Sistema actual (FIFO por etapa)')]
        for B in Bs:
            r = base[(base.metodo == mtd) & (base.B == B)]
            fila.append(f"{n(r.pct_tardias.iloc[0], 0)} % / {n(r.suma_T.iloc[0], 1)}" if len(r) else '—')
        filas_d.append(fila)
    return [
        ('p', 'Este anexo presenta los resultados individuales de los experimentos de la Fase 3, que respaldan '
              f'las Tablas 14 a 17 del documento. En el escenario base, el algoritmo se ejecutó {len(b10)} veces con '
              f'B̄ = 10 y otras {len(bB)} con B = {bb} (semillas {b10.index.min()} a {b10.index.max()}); la Tabla '
              '{T:base} presenta cada réplica.'),
        ('tabla', f'Réplicas del escenario base: algoritmo genético con B̄ = 10 y con B = {bb}',
         ['Semilla', 'Tardías (B̄=10)', 'ΣT_j (B̄=10)', 'C_max (B̄=10)', f'Tardías (B={bb})', f'ΣT_j (B={bb})',
          f'C_max (B={bb})'], filas_b,
         {'etiqueta': 'base', 'anchos': [1000, 1300, 1300, 1300, 1300, 1300, 1338], 'tam': 9,
          'alineacion': ['c'] * 7}),
        ('tabla', f"Réplicas de la sensibilidad: algoritmo genético con B = {F3._lista([str(B) for B in sens])}",
         ['Semilla'] + sum([[f'Tardías (B={B})', f'ΣT_j (B={B})'] for B in sens], []), filas_s,
         {'etiqueta': 'sens', 'anchos': [1300] + [int(7538 / (2 * len(sens)))] * (2 * len(sens)), 'tam': 9,
          'alineacion': ['c'] * (1 + 2 * len(sens))}),
        ('tabla', 'Réplicas de los escenarios de exigencia, algoritmo genético con B̄ = 10: tardanza total en '
                  'horas (órdenes tardías)',
         ['Semilla'] + [nom_e.get(e, e) for e in esc], filas_e,
         {'etiqueta': 'exig', 'anchos': [1300] + [int(7538 / len(esc))] * len(esc), 'tam': 9,
          'alineacion': ['c'] * (1 + len(esc))}),
        ('p', 'La Tabla {T:reglas} presenta, como referencia, el desempeño determinista del sistema actual y de '
              'las seis reglas de despacho con distinto número de partes por orden.'),
        ('tabla', 'Sistema actual y reglas de despacho en el caso de estudio: órdenes tardías / tardanza total (h)',
         ['Método'] + [f'B = {B}' for B in Bs], filas_d,
         {'etiqueta': 'reglas', 'anchos': [2838] + [int(6000 / len(Bs))] * len(Bs), 'tam': 9,
          'alineacion': ['l'] + ['c'] * len(Bs)}),
        ('figura', 'Distribución de la tardanza total y del porcentaje de órdenes tardías en las réplicas del '
                   'escenario base, frente al sistema actual (línea punteada)',
         os.path.join(F3.DIR3, 'comparacion_base.png'), 15.0, 'cajas'),
    ]


def anexo_k(M):
    import importlib.metadata as md
    vers = []
    for p, nom in (('pulp', 'PuLP (modelado del MILP)'), ('highspy', 'HiGHS (solver del MILP)'),
                   ('pandas', 'pandas (datos)'), ('numpy', 'NumPy'), ('scipy', 'SciPy (pruebas estadísticas)'),
                   ('matplotlib', 'Matplotlib (gráficas)'), ('openpyxl', 'openpyxl (lectura de Excel)')):
        try:
            vers.append([nom, md.version(p)])
        except md.PackageNotFoundError:
            pass
    vers.insert(0, ['Python', platform.python_version()])
    semillas = [
        ['Verificación del decodificador', '1', '200 cromosomas aleatorios'],
        ['Validación con instancias reducidas', '1 a 10', '10 réplicas por instancia'],
        ['Calibración: diseño factorial', '1001 a 1005', 'La réplica r usa 1000 + r en las 27 combinaciones'],
        ['Calibración: criterio de parada', '1101 a 1110', '10 réplicas por criterio'],
        ['Réplicas finales', '1201 a 1210', f"La programación propuesta es la de la semilla {M.GA_PARAMS['semilla']}"],
        ['Fase 3: escenario base', '3001 a 3030', '30 réplicas por configuración'],
        ['Fase 3: sensibilidad y exigencia', '3001 a 3010', '10 réplicas por caso']]
    comandos = [
        ['Ejecutar el modelo (programación propuesta)', 'python final_sc_hfsagls_S2_4.py BD_HFS.xlsx'],
        ['Verificar el decodificador', 'python fase2/verificar_factibilidad.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx'],
        ['Validación con instancias reducidas', 'python fase2/validacion_milp.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx'],
        ['Calibración: diseño factorial', 'python fase2/calibracion_ag.py diseno final_sc_hfsagls_S2_4.py BD_HFS.xlsx --instancia real'],
        ['Calibración: criterio de parada', 'python fase2/calibracion_ag.py parada final_sc_hfsagls_S2_4.py BD_HFS.xlsx --instancia real'],
        ['Réplicas finales', 'python fase2/solucion_final.py final_sc_hfsagls_S2_4.py BD_HFS.xlsx 10'],
        ['Experimentos de la Fase 3', 'python fase3/experimentos_fase3.py correr final_sc_hfsagls_S2_4.py BD_HFS.xlsx'],
        ['Libro de Excel de los anexos', 'python docs/fase2_docx/generar_anexos_excel.py Anexos_datos.xlsx']]
    funciones = [('simular_hfs', 'Decodificador: convierte el cromosoma en una programación'),
                 ('cruce', 'Operador de cruce (aritmético en el nivel 1, LOX en el nivel 2)'),
                 ('mutar', 'Operador de mutación (perturbación en el nivel 1, intercambio en el nivel 2)'),
                 ('algoritmo_genetico', 'Ciclo principal del algoritmo genético')]
    bloques = [
        ('p', 'Este anexo describe cómo reproducir los resultados del trabajo. El modelo se implementó en Python, '
              'en el archivo final_sc_hfsagls_S2_4.py, y los experimentos en los programas de las carpetas fase2 '
              'y fase3 del anexo digital. Todos los programas leen los datos de BD_HFS.xlsx. Como el algoritmo '
              'genético es aleatorio, cada corrida usa una semilla fija: con la misma semilla, el mismo código y '
              'los mismos datos se obtiene exactamente el mismo resultado; solo cambia el tiempo de cómputo según '
              'el computador.'),
        ('tabla', 'Software utilizado', ['Componente', 'Versión'], vers,
         {'etiqueta': 'soft', 'anchos': [5838, 3000], 'tam': 10, 'alineacion': ['l', 'c']}),
        ('p', f"Los tiempos de cómputo reportados corresponden a un equipo Linux con procesador "
              f"{_cpu()} y 4 núcleos, con hasta cuatro corridas en paralelo."),
        ('tabla', 'Semillas de los experimentos', ['Experimento', 'Semillas', 'Observación'], semillas,
         {'etiqueta': 'sem', 'anchos': [3400, 1500, 3938], 'tam': 10, 'alineacion': ['l', 'c', 'l']}),
        ('tabla', 'Programas y comandos para reproducir los resultados', ['Resultado', 'Comando'], comandos,
         {'etiqueta': 'cmd', 'anchos': [3000, 5838], 'tam': 9, 'alineacion': ['l', 'l']}),
        ('p', 'A continuación se presentan las funciones principales del modelo. El código completo, con la '
              'lectura de datos, las reglas de despacho y los reportes, está en el anexo digital.'),
    ]
    for fn, desc in funciones:
        src = inspect.getsource(getattr(M, fn)).splitlines()
        bloques.append(('h4', f'{desc} ({fn})'))
        bloques.append(('listado', src))
    return bloques


def _cpu():
    try:
        for ln in open('/proc/cpuinfo', encoding='utf-8'):
            if ln.startswith('model name'):
                return ln.split(':', 1)[1].strip().replace('(R)', '')
    except OSError:
        pass
    return platform.processor() or 'no identificado'


# ---------------------------------------------------------------------------

def main():
    base, salida = sys.argv[1:3]
    M = _cargar_modelo()
    d = docx.Document(base)
    cuerpo = d.element.body
    for el in list(cuerpo):
        if not el.tag.endswith('sectPr'):
            cuerpo.remove(el)

    anexos = [(l, t, b) for l, t, b in anexos_autores()] + [
        ('D', 'Base de datos del caso de estudio', anexo_d()),
        ('E', 'Cálculo de la carga frente a la capacidad', anexo_e()),
        ('F', 'Verificación y validación del modelo', anexo_f()),
        ('G', 'Detalle de la calibración del algoritmo genético', anexo_g()),
        ('H', 'Réplicas finales y programación detallada', anexo_h(M)),
        ('I', 'Representación del sistema actual', anexo_i(M)),
        ('J', 'Resultados de los experimentos de la Fase 3', anexo_j()),
        ('K', 'Reproducción de los resultados y código del modelo', anexo_k(M)),
    ]
    anexos.sort(key=lambda a: a[0])
    bloques_todos = []
    for letra, titulo, bloques in anexos:
        bloques = L.matematizar(_resolver(bloques, letra))
        bloques_todos.append((letra, titulo, bloques))
    todos = [b for _, _, bl in bloques_todos for b in bl]
    omml = L.latex_a_omml(L.recolectar_latex([b for b in todos if b[0] != 'listado']))
    esc = EscritorAnexo(d, omml)

    p = d.add_paragraph('ANEXOS', style='Titulo')
    esc.p('Los anexos respaldan la información presentada en el documento. Los anexos A, B y C contienen los '
          'soportes aportados por la empresa; los anexos D a K se generaron a partir de la base de datos, el '
          'modelo y los resultados de los experimentos, que se entregan además en formato digital. Los anexos D a J '
          'se acompañan del libro de Excel Anexos_datos.xlsx, cuya hoja Indice indica qué hoja respalda cada '
          'anexo y cada tabla del documento.')
    esc.viñetas([f'**Anexo {l}.** {t}' for l, t, _ in bloques_todos])
    for letra, titulo, bloques in bloques_todos:
        esc.nuevo_anexo(letra, titulo)
        if letra in RESPALDO_XLSX:
            hojas = RESPALDO_XLSX[letra]
            lista = ', '.join(f'**{h}**' for h in hojas[:-1]) + (' y ' if len(hojas) > 1 else '') + f'**{hojas[-1]}**'
            esc.p(f'*Respaldo digital:* hoja{"s" if len(hojas) > 1 else ""} {lista} del libro **Anexos_datos.xlsx**, '
                  'donde los datos se presentan completos y los cálculos se reproducen con fórmulas.')
        for b in bloques:
            if b[0] == 'listado':
                esc.listado(b[1])
            elif b[0] == 'nota':
                esc.nota(b[1])
            else:
                L.escribir(esc, [b])
    L.normalizar_orden(d)
    d.save(salida)
    print('Guardado en', salida)


if __name__ == '__main__':
    main()
