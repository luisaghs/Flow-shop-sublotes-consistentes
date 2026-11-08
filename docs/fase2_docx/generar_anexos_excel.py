# -*- coding: utf-8 -*-
"""
Libro de Excel de respaldo de los anexos (Anexos_datos.xlsx): datos de entrada,
resultados completos de los experimentos y cálculos con fórmulas (carga frente a
capacidad, ANOVA, resúmenes y tardanza por orden a partir de la programación).

Convención: texto azul = dato de entrada o resultado de una corrida (valor fijo);
texto negro = fórmula. Las pruebas no paramétricas (Shapiro-Wilk, Levene,
Kruskal-Wallis, Wilcoxon) se calcularon en Python y se registran como valores.

Uso: python generar_anexos_excel.py salida.xlsx
"""
import os
import sys
import json
import io
import contextlib
import importlib.util

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BD = os.path.join(RAIZ, 'BD_HFS.xlsx')
MODELO = os.path.join(RAIZ, 'final_sc_hfsagls_S2_4.py')
CAL = os.path.join(RAIZ, 'fase2', 'salida_calibracion')
SOL = os.path.join(RAIZ, 'fase2', 'salida_solucion')
VAL = os.path.join(RAIZ, 'fase2', 'salida_validacion')
F3D = os.path.join(RAIZ, 'fase3', 'salida_fase3')
ETAPAS = ['Troquelado', 'Ensamble', 'Costura', 'Volteado']

FUENTE = 'Arial'
AZUL = Font(name=FUENTE, size=10, color='0000FF')
NEGRO = Font(name=FUENTE, size=10, color='000000')
NEG = Font(name=FUENTE, size=10, bold=True)
TIT = Font(name=FUENTE, size=12, bold=True)
NOTA = Font(name=FUENTE, size=9, italic=True, color='555555')
CAB = PatternFill('solid', fgColor='DCE6F2')


def _modelo():
    spec = importlib.util.spec_from_file_location('modelo_ag', MODELO)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with contextlib.redirect_stdout(io.StringIO()):
        M.cargar_datos(BD)
    return M


def _hoja(wb, nombre, titulo, nota=None):
    ws = wb.create_sheet(nombre)
    ws['A1'] = titulo
    ws['A1'].font = TIT
    if nota:
        ws['A2'] = nota
        ws['A2'].font = NOTA
    return ws


def _tabla(ws, fila, encabezado, filas, formatos=None, anchos=None):
    """Escribe una tabla desde la fila indicada. Los str que empiezan con '=' son fórmulas (negro);
    el resto son valores (azul). Devuelve (fila del encabezado, primera fila de datos, última)."""
    for k, t in enumerate(encabezado, start=1):
        c = ws.cell(fila, k, t)
        c.font, c.fill = NEG, CAB
        c.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
    for i, f in enumerate(filas, start=fila + 1):
        for k, v in enumerate(f, start=1):
            c = ws.cell(i, k, v)
            c.font = NEGRO if (isinstance(v, str) and v.startswith('=')) else AZUL
            if formatos and formatos[k - 1]:
                c.number_format = formatos[k - 1]
    if anchos:
        for k, w in enumerate(anchos, start=1):
            ws.column_dimensions[get_column_letter(k)].width = w
    ws.freeze_panes = ws.cell(fila + 1, 1)
    return fila, fila + 1, fila + len(filas)


def indice(wb, hojas):
    ws = wb.active
    ws.title = 'Indice'
    ws['A1'] = 'ANEXOS DEL TRABAJO DE GRADO: DATOS Y CÁLCULOS DE RESPALDO'
    ws['A1'].font = TIT
    ws['A3'] = ('Este libro respalda los anexos del documento. Cada hoja indica el anexo y la información '
                'del documento que respalda.')
    ws['A4'] = 'Convención de colores:'
    ws['A4'].font = NEG
    ws['A5'] = 'Texto azul: dato de entrada o resultado registrado de una corrida (valor fijo).'
    ws['A5'].font = AZUL
    ws['A6'] = 'Texto negro: fórmula, se recalcula si cambian los datos.'
    ws['A6'].font = NEGRO
    ws['A7'] = ('Las pruebas Shapiro-Wilk, Levene, Kruskal-Wallis y Wilcoxon se calcularon en Python '
                '(SciPy) y se registran como valores.')
    ws['A7'].font = NOTA
    _tabla(ws, 9, ['Hoja', 'Anexo', 'Contenido', 'Respalda en el documento'], hojas,
           anchos=[24, 9, 70, 45])
    for r in ws.iter_rows(min_row=10):
        for c in r:
            c.font = NEGRO
            c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.freeze_panes = None


def hojas_d(wb):
    x = pd.ExcelFile(BD)
    j = x.parse('Trabajos')
    ws = _hoja(wb, 'D1_Ordenes', 'Anexo D. Órdenes de trabajo del caso de estudio',
               'r_j y d_j en horas laborables acumuladas desde el inicio del horizonte.')
    filas = []
    for i, r in j.iterrows():
        f = 5 + i
        filas.append([r['Orden de trabajo'], r['Codigo Producto'], int(r['Cantidad (docenas)']),
                      pd.Timestamp(r['Fecha de liberación']).to_pydatetime(), int(r['r_j Liberación']),
                      pd.Timestamp(r['Fechas de entrega']).to_pydatetime(), int(r['d_j horas']), f'=G{f}-E{f}'])
    _, a, b = _tabla(ws, 4, ['Orden', 'Referencia', 'Cantidad (docenas)', 'Fecha de liberación', 'r_j (h)',
                             'Fecha de entrega', 'd_j (h)', 'Ventana d_j − r_j (h)'], filas,
                     [None, None, '#,##0', 'dd/mm/yyyy', '0', 'dd/mm/yyyy', '0', '0'],
                     [10, 12, 14, 16, 10, 16, 10, 16])
    ws.cell(b + 1, 1, 'Total').font = NEG
    ws.cell(b + 1, 3, f'=SUM(C{a}:C{b})').number_format = '#,##0'
    ws.cell(b + 2, 1, 'Horizonte (h)').font = NEG
    ws.cell(b + 2, 7, f'=MAX(G{a}:G{b})')

    t = x.parse('Tiempo de procesamiento')
    t.columns = [c.strip() for c in t.columns]
    t['Maquina'] = t['Maquina'].astype(str).str.strip()
    t['Etapa'] = t['Etapa'].astype(str).str.strip()
    t['Codigo producto'] = t['Codigo producto'].astype(str).str.strip()
    t['_e'] = t['Etapa'].map({e: k for k, e in enumerate(ETAPAS)})
    t['_m'] = t['Maquina'].str.extract(r'(\d+)').astype(int)
    t = t.sort_values(['_e', '_m', 'Codigo producto'])
    ws = _hoja(wb, 'D2_Tiempos', 'Anexo D. Tiempos estándar por máquina y referencia',
               'Ritmo = 60 / tiempo estándar (docenas por hora).')
    filas = []
    for i, (_, r) in enumerate(t.iterrows()):
        f = 5 + i
        filas.append([r['Etapa'], r['Maquina'], r['Codigo producto'], float(r['min x docena']), f'=60/D{f}'])
    _tabla(ws, 4, ['Etapa', 'Máquina', 'Referencia', 'Tiempo estándar (min/docena)', 'Ritmo (docenas/h)'], filas,
           [None, None, None, '0.00', '0.000'], [14, 10, 12, 18, 16])

    cal = x.parse('Disponibilidad')
    cal = cal[cal['Fecha'].notna()]
    fin = pd.Timestamp(j['Fechas de entrega'].max())
    cal = cal[pd.to_datetime(cal['Fecha']) <= fin]
    ws = _hoja(wb, 'D3_Calendario', 'Anexo D. Calendario laboral hasta la última fecha de entrega',
               'Horas acumuladas al final del día = acumulado anterior + horas disponibles del día.')
    filas = []
    for i, (_, r) in enumerate(cal.iterrows()):
        f = 5 + i
        acum = f'=D{f}' if i == 0 else f'=E{f - 1}+D{f}'
        filas.append([pd.Timestamp(r['Fecha']).to_pydatetime(), r['Dia semana'], None, float(r['Horas disponibles']), acum])
        filas[-1][2] = ['', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'][int(r['Dia semana'])]
    _tabla(ws, 4, ['Fecha', 'Día de la semana (n.º)', 'Día', 'Horas disponibles', 'Horas acumuladas final del día'],
           filas, ['dd/mm/yyyy', '0', None, '0', '0'], [14, 12, 12, 14, 18])


def hoja_e(wb, n_ord):
    ws = _hoja(wb, 'E_Carga', 'Anexo E. Carga de trabajo frente a capacidad',
               'R_p = suma de ritmos de las máquinas de la etapa para la referencia; carga = docenas / R_p '
               '(horas por máquina con la carga repartida de forma equilibrada).')
    refs = sorted(pd.read_excel(BD, 'Tiempo de procesamiento')['Codigo producto'].astype(str).str.strip().unique())
    T = "D2_Tiempos!"
    rng = lambda c: f"{T}${c}$5:${c}$260"
    # Capacidad R_p
    filas = [[p] + [f'=SUMIFS({rng("E")},{rng("A")},"{e}",{rng("C")},$A{6 + i})' for e in ETAPAS]
             for i, p in enumerate(refs)]
    ws.cell(4, 1, 'Capacidad agregada R_p (docenas por hora)').font = NEG
    _, a, b = _tabla(ws, 5, ['Referencia'] + ETAPAS, filas, [None] + ['0.00'] * 4, [16, 14, 14, 14, 14])
    # Carga por orden
    f0 = b + 3
    ws.cell(f0 - 1, 1, 'Carga de cada orden (horas por máquina)').font = NEG
    filas = []
    for i in range(n_ord):
        f = f0 + 1 + i
        filas.append([f'=D1_Ordenes!A{5 + i}', f'=D1_Ordenes!B{5 + i}', f'=D1_Ordenes!C{5 + i}']
                     + [f'=C{f}/INDEX(${col}${a}:${col}${b},MATCH(B{f},$A${a}:$A${b},0))'
                        for col in 'BCDE'])
    _, a2, b2 = _tabla(ws, f0, ['Orden', 'Referencia', 'Docenas'] + ETAPAS, filas,
                       [None, None, '#,##0'] + ['0.0'] * 4)
    ws.cell(b2 + 1, 1, 'Total por máquina (h)').font = NEG
    for k, col in enumerate('DEFG'):
        ws[f'{col}{b2 + 1}'] = f'=SUM({col}{a2}:{col}{b2})'
        ws[f'{col}{b2 + 1}'].number_format = '0.0'
    # Resumen de ocupación
    f1 = b2 + 4
    ws.cell(f1 - 1, 1, 'Ocupación de cada etapa en el horizonte').font = NEG
    filas = []
    for k, e in enumerate(ETAPAS):
        f = f1 + 1 + k
        col = 'DEFG'[k]
        filas.append([e, f'=COUNTIFS({rng("A")},A{f},{rng("C")},"{refs[0]}")', f'=D{f}*B{f}', f'={col}{b2 + 1}',
                      '=MAX(D1_Ordenes!$G$5:$G$14)', f'=D{f}/E{f}'])
    _tabla(ws, f1, ['Etapa', 'Máquinas', 'Carga total (h)', 'Carga por máquina (h)', 'Horizonte (h)', 'Ocupación'],
           filas, [None, '0', '#,##0.0', '0.0', '0', '0.0%'])
    ws.freeze_panes = None


def hojas_f(wb):
    v = pd.read_csv(os.path.join(VAL, 'resultados_validacion_todas.csv'))
    ws = _hoja(wb, 'F_Validacion', 'Anexo F. Validación con instancias reducidas: resultados completos',
               'F1: formulación del documento; F2: formulación de precedencia general. Estados y tiempos del '
               'solver HiGHS; el AG se corrió 10 veces por instancia (semillas 1 a 10).')
    cols = ['Instancia', 'Órdenes', 'B̄', 'Sublotes', 'Máquinas', 'F1 binarias', 'F1 ΣTj', 'F1 Cmax', 'F1 estado',
            'F1 s', 'F2 binarias', 'F2 ΣTj', 'F2 Cmax', 'F2 estado', 'F2 s', 'Regla', 'Regla ΣTj', 'AG mejor ΣTj',
            'AG mejor Cmax', 'AG prom ΣTj', 'AG ≤ MILP en ΣTj', 'AG s prom']
    filas = [[(None if pd.isna(r[c]) else (r[c].item() if hasattr(r[c], 'item') else r[c])) for c in cols]
             for _, r in v.iterrows()]
    hdr = cols + ['Mejor exacta ΣTj', 'Diferencia AG prom − exacta (h)']
    for i, f in enumerate(filas):
        k = 5 + i
        f += [f'=IF(AND(G{k}="",L{k}=""),"",MIN(IF(G{k}="",L{k},G{k}),IF(L{k}="",G{k},L{k})))',
              f'=IF(W{k}="","",T{k}-W{k})']
    _tabla(ws, 4, hdr, filas, [None] * 6 + ['0.000', '0.000', None, '0.0', None, '0.000', '0.000', None, '0.0', None,
                                            '0.000', '0.000', '0.000', '0.000', None, '0.0', '0.000', '0.000'],
           [9, 8, 5, 8, 9, 9, 9, 9, 28, 7, 9, 9, 9, 28, 7, 7, 9, 10, 10, 10, 10, 8, 11, 12])


def hojas_g(wb):
    d = pd.read_csv(os.path.join(CAL, 'corridas_diseno.csv'))
    d = d.sort_values(['poblacion', 'prob_cruce', 'prob_mutacion', 'semilla']).reset_index(drop=True)
    ws = _hoja(wb, 'G1_Corridas', 'Anexo G. Las 135 corridas del diseño factorial 3³',
               'Esfuerzo fijo de 30.000 cromosomas por corrida; la réplica r usa la semilla 1000 + r.')
    filas = [[int(r.poblacion), float(r.prob_cruce), float(r.prob_mutacion), int(r.semilla), float(r.suma_T),
              float(r.Cmax), int(r.tardias), int(r.generaciones), round(float(r.segundos), 1)] for r in d.itertuples()]
    # La hoja ANOVA copiada usa las filas 2 a 136, por eso los datos empiezan en la fila 2
    ws.delete_rows(1, 2)
    _tabla(ws, 1, ['Población', 'Prob. cruce', 'Prob. mutación', 'Semilla', 'ΣTj (h)', 'Cmax (h)', 'Tardías',
                   'Generaciones', 'Tiempo (s)'], filas, ['0', '0.0', '0.0', '0', '0.000', '0.000', '0', '0', '0.0'],
           [11, 11, 13, 9, 11, 11, 9, 12, 10])
    n = len(d)
    # Resumen por combinación con fórmulas
    ws2 = _hoja(wb, 'G2_Combinaciones', 'Anexo G. Promedio de las 5 réplicas de cada combinación',
                'Fórmulas sobre la hoja G1_Corridas; ordenar por ΣTj promedio para ver las mejores combinaciones.')
    combos = d[['poblacion', 'prob_cruce', 'prob_mutacion']].drop_duplicates().values.tolist()
    R = lambda c: f'G1_Corridas!${c}$2:${c}${n + 1}'
    cond = lambda f: f'{R("A")},A{f},{R("B")},B{f},{R("C")},C{f}'
    filas = []
    for i, (p, c, m) in enumerate(combos):
        f = 5 + i
        filas.append([int(p), float(c), float(m), f'=COUNTIFS({cond(f)})', f'=AVERAGEIFS({R("E")},{cond(f)})',
                      f'=SQRT(SUMPRODUCT(({R("A")}=A{f})*({R("B")}=B{f})*({R("C")}=C{f})*({R("E")}-E{f})^2)/(D{f}-1))',
                      f'=AVERAGEIFS({R("G")},{cond(f)})', f'=AVERAGEIFS({R("F")},{cond(f)})'])
    _tabla(ws2, 4, ['Población', 'Prob. cruce', 'Prob. mutación', 'Corridas', 'ΣTj prom. (h)', 'ΣTj desv. (h)',
                    'Tardías prom.', 'Cmax prom. (h)'], filas, ['0', '0.0', '0.0', '0', '0.00', '0.00', '0.0', '0.0'],
           [11, 11, 13, 9, 13, 13, 12, 13])
    # ANOVA con fórmulas (copiado del libro anova_calibracion_excel.xlsx, apuntando a G1_Corridas)
    src = load_workbook(os.path.join(CAL, 'anova_calibracion_excel.xlsx'))['ANOVA']
    ws3 = wb.create_sheet('G3_ANOVA')
    for row in src.iter_rows():
        for c in row:
            if c.value is None:
                continue
            val = c.value
            if isinstance(val, str):
                val = val.replace('Corridas!', 'G1_Corridas!')
            nc = ws3.cell(c.row, c.column, val)
            nc.font = NEG if (c.font and c.font.b) else (NEGRO if isinstance(val, str) and val.startswith('=')
                                                           else AZUL)
            nc.number_format = c.number_format
            if c.fill and c.fill.fgColor and c.fill.fgColor.rgb not in (None, '00000000'):
                nc.fill = CAB
    # formatos numéricos: el libro de origen los deja en General
    fila_tabla = next(c.row for c in ws3['A'] if c.value == 'Fuente')
    for row in ws3.iter_rows():
        for c in row:
            if not (isinstance(c.value, str) and c.value.startswith('=')):
                continue
            if c.row > fila_tabla and c.column == 3:
                c.number_format = '0'                              # grados de libertad
            elif c.row > fila_tabla and c.column == 6:
                c.number_format = '[<0.0001]"<0.0001";0.0000'      # valor p
            elif c.value.upper().startswith('=COUNT'):
                c.number_format = '0'
            else:
                c.number_format = '0.00'
    for col, w in zip('ABCDEF', [30, 14, 12, 16, 30, 12]):
        ws3.column_dimensions[col].width = w
    ws3['H1'] = 'Todas las cifras se calculan con fórmulas a partir de la hoja G1_Corridas.'
    ws3['H1'].font = NOTA
    # Supuestos y Kruskal-Wallis (valores calculados en Python)
    import re
    txt = open(os.path.join(CAL, 'informe_calibracion.md'), encoding='utf-8').read()
    NUM = r'(\d+(?:\.\d+)?(?:e-?\d+)?)'
    filas = []
    m = re.search(r'Shapiro-Wilk\): W = ' + NUM + ', p = ' + NUM, txt)
    if m:
        filas.append(['Normalidad de los residuos', 'Shapiro-Wilk', float(m.group(1)), float(m.group(2))])
    for fac in ('Población', 'Prob. de cruce', 'Prob. de mutación'):
        m = re.search(re.escape(fac) + ': Levene p = ' + NUM + '; Kruskal-Wallis H = ' + NUM + ', p = ' + NUM, txt)
        if m:
            filas.append([f'Homogeneidad de varianzas ({fac.lower()})', 'Levene', None, float(m.group(1))])
            filas.append([f'Efecto de {fac.lower()}', 'Kruskal-Wallis (H)', float(m.group(2)), float(m.group(3))])
    ws4 = _hoja(wb, 'G4_Supuestos', 'Anexo G. Pruebas de supuestos del ANOVA y prueba de Kruskal-Wallis',
                'Calculadas en Python (SciPy) sobre las 135 corridas. Valor p < 0,05: no se cumple el supuesto '
                '(Shapiro-Wilk, Levene) o el factor tiene efecto significativo (Kruskal-Wallis).')
    _tabla(ws4, 4, ['Aspecto evaluado', 'Prueba', 'Estadístico', 'Valor p'], filas, [None, None, '0.000', '0.0000'],
           [44, 22, 12, 12])
    # Criterio de parada
    par = pd.read_csv(os.path.join(CAL, 'corridas_parada.csv')).sort_values(['sin_mejora', 'semilla'])
    ws5 = _hoja(wb, 'G5_Parada', 'Anexo G. Experimento del criterio de parada',
                'Configuración: población 150, cruce 0,9, mutación 0,5; semillas 1101 a 1110.')
    filas = [[int(r.sin_mejora), int(r.semilla), float(r.suma_T), float(r.Cmax), int(r.tardias), int(r.generaciones),
              round(float(r.segundos), 1)] for r in par.itertuples()]
    _, a, b = _tabla(ws5, 4, ['Generaciones sin mejora', 'Semilla', 'ΣTj (h)', 'Cmax (h)', 'Tardías', 'Generaciones',
                              'Tiempo (s)'], filas, ['0', '0', '0.000', '0.000', '0', '0', '0.0'],
                     [14, 9, 11, 11, 9, 12, 10])
    f0 = b + 3
    ws5.cell(f0, 1, 'Resumen por criterio').font = NEG
    filas = []
    for i, nv in enumerate(sorted(par.sin_mejora.unique())):
        f = f0 + 2 + i
        filas.append([int(nv), f'=COUNTIF($A${a}:$A${b},A{f})',
                      f'=AVERAGEIF($A${a}:$A${b},A{f},$C${a}:$C${b})', f'=AVERAGEIF($A${a}:$A${b},A{f},$D${a}:$D${b})',
                      f'=AVERAGEIF($A${a}:$A${b},A{f},$F${a}:$F${b})', f'=AVERAGEIF($A${a}:$A${b},A{f},$G${a}:$G${b})/60'])
    _tabla(ws5, f0 + 1, ['Generaciones sin mejora', 'Réplicas', 'ΣTj prom. (h)', 'Cmax prom. (h)', 'Generaciones prom.',
                         'Tiempo prom. (min)'], filas, ['0', '0', '0.00', '0.0', '0', '0.0'])
    ws5.freeze_panes = 'A5'


def hojas_h(wb, M):
    rep = pd.read_csv(os.path.join(SOL, 'replicas.csv'))
    ws = _hoja(wb, 'H1_Replicas', 'Anexo H. Réplicas finales del algoritmo genético (semillas 1201 a 1210)')
    filas = [[int(r.semilla), float(r.suma_T), float(r.Cmax), int(r.tardias), int(r.generaciones),
              round(float(r.segundos), 1)] for r in rep.itertuples()]
    _, a, b = _tabla(ws, 4, ['Semilla', 'ΣTj (h)', 'Cmax (h)', 'Órdenes tardías', 'Generaciones', 'Tiempo (s)'], filas,
                     ['0', '0.000', '0.000', '0', '0', '0.0'], [10, 11, 11, 14, 13, 11])
    resumen = [('Réplicas sin tardanza', f'=COUNTIF(B{a}:B{b},0)', '0'),
               ('ΣTj promedio (h)', f'=AVERAGE(B{a}:B{b})', '0.00'),
               ('Cmax mínimo (h)', f'=MIN(C{a}:C{b})', '0.00'), ('Cmax máximo (h)', f'=MAX(C{a}:C{b})', '0.00'),
               ('Tiempo promedio (min)', f'=AVERAGE(F{a}:F{b})/60', '0.0')]
    for k, (t, fml, fmt) in enumerate(resumen):
        ws.cell(b + 2 + k, 1, t).font = NEG
        c = ws.cell(b + 2 + k, 2, fml); c.font = NEGRO; c.number_format = fmt
    # Programación detallada
    mejor = json.load(open(os.path.join(SOL, 'mejor_solucion.json'), encoding='utf-8'))
    ind = mejor['individuo']
    ind = {'k': {j: int(v) for j, v in ind['k'].items()}, 'proporciones': ind['proporciones'],
           'posiciones': {int(s): [tuple(x) for x in v] for s, v in ind['posiciones'].items()}}
    C, g = M.simular_hfs(ind)
    tam = {j: M.props_a_docenas(j, ind['proporciones'][j]) for j in M.TRABAJOS}
    ops = sorted([(j, b, s, m, i, f) for s in M.ETAPAS for (j, b, m, i, f) in g[s]],
                 key=lambda o: (o[0], o[1], o[2]))
    ws2 = _hoja(wb, 'H2_Programacion', f"Anexo H. Programación detallada de la solución propuesta (semilla "
                                       f"{int(mejor['semilla'])})",
                'Inicio y fin en horas laborables desde el inicio del horizonte.')
    filas = []
    for i, (j, b, s, m, ini, fin) in enumerate(ops):
        f = 5 + i
        filas.append([j, b, int(tam[j][b - 1]), s, ETAPAS[s - 1], m, round(ini, 4), round(fin, 4), f'=H{f}-G{f}'])
    _, a, b = _tabla(ws2, 4, ['Orden', 'Sublote', 'Docenas', 'Etapa (n.º)', 'Etapa', 'Máquina', 'Inicio (h)', 'Fin (h)',
                              'Duración (h)'], filas, [None, '0', '0', '0', None, None, '0.000', '0.000', '0.000'],
                     [8, 8, 9, 9, 12, 9, 10, 10, 11])
    # Indicadores por orden calculados desde la programación
    ws3 = _hoja(wb, 'H3_Por_orden', 'Anexo H. Terminación y tardanza por orden, calculadas desde la programación',
                'C_j = mayor fin de los sublotes de la orden en la última etapa; T_j = máx(0, C_j − d_j).')
    P = lambda c: f'H2_Programacion!${c}${a}:${c}${b}'
    filas = []
    for i, jj in enumerate(M.TRABAJOS):
        f = 5 + i
        filas.append([jj, f'=INDEX(D1_Ordenes!$G$5:$G$14,MATCH(A{f},D1_Ordenes!$A$5:$A$14,0))',
                      f'=_xlfn.MAXIFS({P("H")},{P("A")},A{f},{P("D")},4)', f'=MAX(0,C{f}-B{f})', f'=MAX(0,B{f}-C{f})',
                      f'=IF(D{f}>0.000001,1,0)'])
    _, a3, b3 = _tabla(ws3, 4, ['Orden', 'd_j (h)', 'C_j (h)', 'Tardanza T_j (h)', 'Adelanto E_j (h)', 'Tardía (1/0)'],
                       filas, [None, '0', '0.00', '0.00', '0.00', '0'], [9, 10, 10, 15, 15, 12])
    tot = [('Tardanza total ΣTj (h)', f'=SUM(D{a3}:D{b3})', '0.00'), ('Órdenes tardías', f'=SUM(F{a3}:F{b3})', '0'),
           ('Makespan Cmax (h)', f'=MAX(C{a3}:C{b3})', '0.00'), ('Adelanto total (h)', f'=SUM(E{a3}:E{b3})', '0.0')]
    for k, (t, fml, fmt) in enumerate(tot):
        ws3.cell(b3 + 2 + k, 1, t).font = NEG
        c = ws3.cell(b3 + 2 + k, 4, fml); c.font = NEGRO; c.number_format = fmt


def hojas_i(wb, M):
    sys.path.insert(0, os.path.join(RAIZ, 'fase3'))
    import experimentos_fase3 as F
    ws = _hoja(wb, 'I_Sistema_actual', 'Anexo I. Representación del sistema actual (FIFO por etapa, B partes iguales)',
               'Desempeño según el número de partes por orden; el porcentaje de tardías se calcula con fórmula.')
    filas = []
    b_orig = M.NUM_SUBLOTES
    for i, B in enumerate(range(2, 11)):
        r = F.indicadores(M, F.individuo_fifo_por_etapa(M, B))
        f = 5 + i
        filas.append([B, int(r['tardias']), f'=B{f}/10', round(r['suma_T'], 3), round(r['Cmax'], 3),
                      round(r['flujo_medio'], 3)])
    _tabla(ws, 4, ['B', 'Órdenes tardías', '% tardías', 'ΣTj (h)', 'Cmax (h)', 'Flujo medio (h)'], filas,
           ['0', '0', '0%', '0.0', '0.0', '0.0'], [8, 14, 11, 11, 11, 14])
    ws.cell(15, 1, 'Referencia histórica: 45 %% de órdenes tardías. Se adopta B = %d.' % F.B_ACTUAL_BASE).font = NOTA
    f0 = 18
    ws.cell(f0 - 1, 1, 'Terminación por orden con el sistema actual').font = NEG
    res = {}
    for B in F.B_ACTUAL_SENS:
        res[B] = M.calcular_indicadores(M.simular_hfs(F.individuo_fifo_por_etapa(M, B))[0])['por_trabajo']
    M.NUM_SUBLOTES = b_orig
    filas = []
    for i, j in enumerate(M.TRABAJOS):
        f = f0 + 1 + i
        fila = [j, f'=INDEX(D1_Ordenes!$G$5:$G$14,MATCH(A{f},D1_Ordenes!$A$5:$A$14,0))']
        for k, B in enumerate(F.B_ACTUAL_SENS):
            cc = get_column_letter(3 + 2 * k)
            fila += [round(res[B][j]['Ci'], 3), f'=MAX(0,{cc}{f}-B{f})']
        filas.append(fila)
    hdr = ['Orden', 'd_j (h)'] + sum([[f'C_j B={B}', f'T_j B={B}'] for B in F.B_ACTUAL_SENS], [])
    _, a, b = _tabla(ws, f0, hdr, filas, [None, '0'] + ['0.0', '0.0'] * len(F.B_ACTUAL_SENS))
    ws.cell(b + 1, 1, 'Total').font = NEG
    for k in range(len(F.B_ACTUAL_SENS)):
        cc = get_column_letter(4 + 2 * k)
        ws[f'{cc}{b + 1}'] = f'=SUM({cc}{a}:{cc}{b})'
        ws[f'{cc}{b + 1}'].number_format = '0.0'
    ws.freeze_panes = None


def hojas_j(wb):
    ag = pd.read_csv(os.path.join(F3D, 'corridas_ag.csv'))
    ag = ag.sort_values(['escenario', 'B', 'semilla'])
    cols = ['grupo', 'escenario', 'B', 'semilla', 'tardias', 'pct_tardias', 'suma_T', 'T_max', 'suma_E', 'Cmax',
            'flujo_medio', 'ocup_troquelado', 'alistamientos', 'generaciones', 'segundos']
    nombres = ['Grupo', 'Escenario', 'B', 'Semilla', 'Tardías', '% tardías', 'ΣTj (h)', 'Tmax (h)', 'ΣEj (h)', 'Cmax (h)',
               'Flujo medio (h)', 'Ocupación troquelado (%)', 'Alistamientos', 'Generaciones', 'Tiempo (s)']
    ws = _hoja(wb, 'J1_Corridas_F3', 'Anexo J. Las corridas del algoritmo genético en la Fase 3',
               'Escenario base: semillas 3001 a 3030; sensibilidad y escenarios de exigencia: 3001 a 3010.')
    filas = [[(r[c].item() if hasattr(r[c], 'item') else r[c]) for c in cols] for _, r in ag.iterrows()]
    _, a, b = _tabla(ws, 4, nombres, filas, [None, None, '0', '0', '0', '0.0', '0.000', '0.000', '0.0', '0.000', '0.0',
                                             '0.0', '0', '0', '0.0'], [12, 13, 5, 9, 9, 10, 10, 10, 10, 10, 12, 13, 12, 12, 10])
    det = pd.read_csv(os.path.join(F3D, 'deterministas.csv'))
    ws2 = _hoja(wb, 'J2_Deterministas', 'Anexo J. Sistema actual y reglas de despacho (resultados deterministas)')
    dc = ['escenario', 'metodo', 'B', 'tardias', 'pct_tardias', 'suma_T', 'T_max', 'suma_E', 'Cmax', 'flujo_medio',
          'ocup_troquelado', 'alistamientos']
    filas = [[(r[c].item() if hasattr(r[c], 'item') else r[c]) for c in dc] for _, r in det.iterrows()]
    _, da, db = _tabla(ws2, 4, ['Escenario', 'Método', 'B', 'Tardías', '% tardías', 'ΣTj (h)', 'Tmax (h)', 'ΣEj (h)',
                                'Cmax (h)', 'Flujo medio (h)', 'Ocupación troquelado (%)', 'Alistamientos'], filas,
                       [None, None, '0', '0', '0.0', '0.000', '0.000', '0.0', '0.000', '0.0', '0.0', '0'],
                       [13, 26, 5, 9, 10, 10, 10, 10, 10, 12, 13, 12])
    # Resumen con fórmulas: media, desviación e IC del 95 % por configuración
    ws3 = _hoja(wb, 'J3_Resumen', 'Anexo J. Resumen de las réplicas del algoritmo por escenario y número de sublotes',
                'Media, desviación estándar e intervalo de confianza del 95 % (t de Student) calculados con fórmulas '
                'sobre J1_Corridas_F3; reducción frente al sistema actual con B = 6 (hoja J2_Deterministas).')
    R = lambda c: f'J1_Corridas_F3!${c}${a}:${c}${b}'
    D = lambda c: f'J2_Deterministas!${c}${da}:${c}${db}'
    confs = ag[['escenario', 'B']].drop_duplicates().values.tolist()
    filas = []
    for i, (e, B) in enumerate(confs):
        f = 5 + i
        cnd = f'{R("B")},A{f},{R("C")},B{f}'
        filas.append([e, int(B), f'=COUNTIFS({cnd})', f'=AVERAGEIFS({R("F")},{cnd})/100',
                      f'=AVERAGEIFS({R("G")},{cnd})',
                      f'=SQRT(SUMPRODUCT(({R("B")}=A{f})*({R("C")}=B{f})*({R("G")}-E{f})^2)/(C{f}-1))',
                      f'=TINV(0.05,C{f}-1)*F{f}/SQRT(C{f})', f'=AVERAGEIFS({R("J")},{cnd})',
                      f'=SUMIFS({D("F")},{D("A")},A{f},{D("B")},"Actual (FIFO por etapa)",{D("C")},6)',
                      f'=IF(I{f}=0,"",1-E{f}/I{f})'])
    _tabla(ws3, 4, ['Escenario', 'B del AG', 'Réplicas', '% tardías prom.', 'ΣTj prom. (h)', 'ΣTj desv. (h)',
                    'IC 95 % ± (h)', 'Cmax prom. (h)', 'ΣTj sistema actual B=6 (h)', 'Reducción de ΣTj'], filas,
           [None, '0', '0', '0.0%', '0.00', '0.00', '0.00', '0.0', '0.0', '0.0%'],
           [13, 9, 9, 13, 12, 12, 12, 12, 16, 13])


def main():
    salida = sys.argv[1]
    M = _modelo()
    wb = Workbook()
    hojas = [
        ['D1_Ordenes', 'D', 'Órdenes de trabajo: cantidad, liberación y entrega (fechas y horas)', 'Tabla 3'],
        ['D2_Tiempos', 'D', 'Tiempo estándar de cada referencia en cada máquina y su ritmo', 'Tabla 2'],
        ['D3_Calendario', 'D', 'Calendario laboral día a día y horas acumuladas', 'Horizonte de 611 h; r_j y d_j'],
        ['E_Carga', 'E', 'Capacidad por etapa y referencia, carga de cada orden y ocupación (fórmulas)',
         'Tabla 4 y 76 % de ocupación de troquelado'],
        ['F_Validacion', 'F', 'Resultados completos de las seis instancias reducidas (solver y AG)',
         'Validación del modelo (Anexo F)'],
        ['G1_Corridas', 'G', 'Las 135 corridas del diseño factorial', 'Tablas 7 a 9'],
        ['G2_Combinaciones', 'G', 'Promedio y desviación de cada combinación (fórmulas)', 'Tabla 9'],
        ['G3_ANOVA', 'G', 'ANOVA calculado paso a paso con fórmulas', 'Tabla 8'],
        ['G4_Supuestos', 'G', 'Shapiro-Wilk, Levene y Kruskal-Wallis', 'Supuestos del ANOVA'],
        ['G5_Parada', 'G', 'Las 20 corridas del criterio de parada y su resumen', 'Tabla 10'],
        ['H1_Replicas', 'H', 'Las 10 réplicas finales y su resumen', '"8 de 10 réplicas eliminaron la tardanza"'],
        ['H2_Programacion', 'H', 'Programación detallada: 400 operaciones (máquina, inicio y fin)', 'Figura 2'],
        ['H3_Por_orden', 'H', 'C_j, T_j y E_j de cada orden calculados con fórmulas desde la programación',
         'Tabla 12'],
        ['I_Sistema_actual', 'I', 'Sistema actual con B de 2 a 10 y terminación por orden con B = 5, 6 y 7',
         'Elección de B = 6 y Tabla 18'],
        ['J1_Corridas_F3', 'J', 'Las 120 corridas del algoritmo en la Fase 3', 'Tablas 14 a 17'],
        ['J2_Deterministas', 'J', 'Sistema actual y reglas de despacho en cada escenario', 'Tablas 15 a 17'],
        ['J3_Resumen', 'J', 'Media, desviación, IC 95 % y reducción frente al sistema actual (fórmulas)',
         'Tablas 14 y 17'],
    ]
    indice(wb, hojas)
    hojas_d(wb)
    hoja_e(wb, len(M.TRABAJOS))
    hojas_f(wb)
    hojas_g(wb)
    hojas_h(wb, M)
    hojas_i(wb, M)
    hojas_j(wb)
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = True
    # fuente uniforme: toda celda con contenido queda en Arial
    from copy import copy
    for hoja in wb:
        for fila in hoja.iter_rows():
            for c in fila:
                if c.value is not None and c.font.name != 'Arial':
                    f = copy(c.font)
                    f.name = 'Arial'
                    f.size = f.size or 10
                    c.font = f
    wb.save(salida)
    print('Guardado en', salida)


if __name__ == '__main__':
    main()
