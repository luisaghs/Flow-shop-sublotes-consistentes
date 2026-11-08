# -*- coding: utf-8 -*-
"""
Libros de Excel de respaldo de los anexos D a J, uno por anexo: datos de entrada,
resultados completos de los experimentos y cálculos con fórmulas (carga frente a
capacidad, ANOVA, resúmenes, tardanza por orden y uso de máquinas a partir de la
programación). Cada libro es independiente: incluye los datos que sus fórmulas usan.

Convención: texto azul = dato de entrada o resultado de una corrida (valor fijo);
texto negro = fórmula. Las pruebas no paramétricas (Shapiro-Wilk, Levene,
Kruskal-Wallis, Wilcoxon) se calcularon en Python y se registran como valores.

Uso: python generar_anexos_excel.py carpeta_salida
     (luego recalcular cada libro, p. ej. con LibreOffice, para guardar los resultados de las fórmulas)
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


def leeme(wb, letra, titulo, descripcion, hojas):
    """Primera hoja de cada libro: qué anexo respalda, convención de colores y contenido de cada hoja."""
    ws = wb.active
    ws.title = 'Leeme'
    ws['A1'] = f'ANEXO {letra}. {titulo.upper()}'
    ws['A1'].font = TIT
    ws['A3'] = descripcion
    ws['A3'].alignment = Alignment(wrap_text=True, vertical='top')
    ws.merge_cells('A3:D3')
    ws.row_dimensions[3].height = 15 * (1 + len(descripcion) // 120)
    ws['A5'] = 'Convención de colores:'
    ws['A5'].font = NEG
    ws['A6'] = 'Texto azul: dato de entrada o resultado registrado de una corrida (valor fijo).'
    ws['A6'].font = AZUL
    ws['A7'] = 'Texto negro: fórmula; se recalcula si cambian los datos.'
    ws['A7'].font = NEGRO
    _tabla(ws, 9, ['Hoja', 'Contenido', 'Respalda en el documento'], [h[:3] for h in hojas], anchos=[22, 75, 45])
    for r in ws.iter_rows(min_row=10):
        for c in r:
            c.font = NEGRO
            c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.freeze_panes = None


def _calendario_bd():
    x = pd.ExcelFile(BD)
    j = x.parse('Trabajos')
    cal = x.parse('Disponibilidad')
    cal = cal[cal['Fecha'].notna()]
    cal = cal[pd.to_datetime(cal['Fecha']) <= pd.Timestamp(j['Fechas de entrega'].max())]
    return j, cal


def hoja_ordenes(wb, calculo=False):
    """Órdenes (D1_Ordenes). Con calculo=True, r_j y d_j se recalculan desde el calendario (D3_Calendario)."""
    j, cal = _calendario_bd()
    ws = _hoja(wb, 'D1_Ordenes', 'Órdenes de trabajo del caso de estudio',
               'r_j y d_j en horas laborables acumuladas desde el inicio del horizonte (04/05/2026).')
    nc = len(cal)
    C = lambda c: f'D3_Calendario!${c}$5:${c}${4 + nc}'
    filas = []
    for i, r in j.iterrows():
        f = 5 + i
        fila = [r['Orden de trabajo'], r['Codigo Producto'], int(r['Cantidad (docenas)']),
                pd.Timestamp(r['Fecha de liberación']).to_pydatetime(), int(r['r_j Liberación']),
                pd.Timestamp(r['Fechas de entrega']).to_pydatetime(), int(r['d_j horas']), f'=G{f}-E{f}']
        if calculo:
            fila += [f'=SUMIFS({C("D")},{C("A")},"<"&D{f})', f'=SUMIFS({C("D")},{C("A")},"<="&F{f})',
                     f'=IF(AND(I{f}=E{f},J{f}=G{f}),"Sí","No")']
        filas.append(fila)
    hdr = ['Orden', 'Referencia', 'Cantidad (docenas)', 'Fecha de liberación', 'r_j (h)', 'Fecha de entrega',
           'd_j (h)', 'Ventana d_j − r_j (h)']
    fmt = [None, None, '#,##0', 'dd/mm/yyyy', '0', 'dd/mm/yyyy', '0', '0']
    anchos = [10, 12, 14, 16, 10, 16, 10, 16]
    if calculo:
        hdr += ['r_j calculado (h)', 'd_j calculado (h)', '¿Coincide con la base?']
        fmt += ['0', '0', None]
        anchos += [14, 14, 14]
    _, a, b = _tabla(ws, 4, hdr, filas, fmt, anchos)
    ws.cell(b + 1, 1, 'Total').font = NEG
    ws.cell(b + 1, 3, f'=SUM(C{a}:C{b})').number_format = '#,##0'
    ws.cell(b + 2, 1, 'Horizonte (h)').font = NEG
    ws.cell(b + 2, 7, f'=MAX(G{a}:G{b})')
    if calculo:
        ws.cell(b + 4, 1, 'r_j calculado = horas disponibles de los días anteriores a la liberación (la orden se '
                          'libera al inicio de su día); d_j calculado = horas disponibles hasta el final del día de '
                          'entrega, inclusive (hoja Calendario).').font = NOTA


def hoja_tiempos(wb):
    t = pd.read_excel(BD, 'Tiempo de procesamiento')
    t.columns = [c.strip() for c in t.columns]
    for c in ('Maquina', 'Etapa', 'Codigo producto'):
        t[c] = t[c].astype(str).str.strip()
    t['_e'] = t['Etapa'].map({e: k for k, e in enumerate(ETAPAS)})
    t['_m'] = t['Maquina'].str.extract(r'(\d+)').astype(int)
    t = t.sort_values(['_e', '_m', 'Codigo producto'])
    ws = _hoja(wb, 'D2_Tiempos', 'Tiempos estándar por máquina y referencia',
               'Ritmo = 60 / tiempo estándar (docenas por hora).')
    filas = []
    for i, (_, r) in enumerate(t.iterrows()):
        f = 5 + i
        filas.append([r['Etapa'], r['Maquina'], r['Codigo producto'], float(r['min x docena']), f'=60/D{f}'])
    _tabla(ws, 4, ['Etapa', 'Máquina', 'Referencia', 'Tiempo estándar (min/docena)', 'Ritmo (docenas/h)'], filas,
           [None, None, None, '0.00', '0.000'], [14, 10, 12, 18, 16])
    return t


def hoja_matriz(wb, t):
    """Tabla de tiempos en forma de matriz (máquina × referencia), armada con fórmulas desde D2_Tiempos."""
    refs = sorted(t['Codigo producto'].unique())
    maqs = t[['Etapa', 'Maquina', '_e', '_m']].drop_duplicates().sort_values(['_e', '_m'])
    n = len(t)
    T = lambda c: f'D2_Tiempos!${c}$5:${c}${4 + n}'
    ws = _hoja(wb, 'D4_Matriz', 'Tiempos estándar por máquina y referencia (min/docena), en forma de matriz',
               'Cada celda toma el valor de la hoja Tiempos con SUMIFS; al final, el promedio de cada etapa.')
    filas = []
    for i, (_, r) in enumerate(maqs.iterrows()):
        f = 5 + i
        filas.append([r['Etapa'], r['Maquina']] + [f'=SUMIFS({T("D")},{T("B")},$B{f},{T("C")},{get_column_letter(3 + k)}$4)'
                                                   for k in range(len(refs))])
    _, a, b = _tabla(ws, 4, ['Etapa', 'Máquina'] + refs, filas, [None, None] + ['0.00'] * len(refs),
                     [13, 10] + [9] * len(refs))
    ws.cell(b + 2, 1, 'Promedio por etapa (min/docena)').font = NEG
    for k, e in enumerate(ETAPAS):
        f = b + 3 + k
        ws.cell(f, 1, e).font = NEGRO
        for q in range(len(refs)):
            col = get_column_letter(3 + q)
            c = ws.cell(f, 3 + q, f'=AVERAGEIF($A${a}:$A${b},$A{f},{col}${a}:{col}${b})')
            c.font, c.number_format = NEGRO, '0.00'


def hoja_calendario(wb):
    _, cal = _calendario_bd()
    ws = _hoja(wb, 'D3_Calendario', 'Calendario laboral hasta la última fecha de entrega',
               'Horas acumuladas al final del día = acumulado anterior + horas disponibles del día.')
    filas = []
    dias = ['', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    for i, (_, r) in enumerate(cal.iterrows()):
        f = 5 + i
        filas.append([pd.Timestamp(r['Fecha']).to_pydatetime(), int(r['Dia semana']), dias[int(r['Dia semana'])],
                      float(r['Horas disponibles']), f'=D{f}' if i == 0 else f'=E{f - 1}+D{f}'])
    _, a, b = _tabla(ws, 4, ['Fecha', 'Día de la semana (n.º)', 'Día', 'Horas disponibles',
                             'Horas acumuladas final del día'], filas, ['dd/mm/yyyy', '0', None, '0', '0'],
                     [14, 12, 12, 14, 18])
    ws.cell(4, 7, 'Resumen').font = NEG
    res = [('Días del calendario', f'=COUNT(A{a}:A{b})'), ('Días laborables', f'=COUNTIF(D{a}:D{b},">0")'),
           ('Horas disponibles (horizonte)', f'=SUM(D{a}:D{b})')]
    for k, (t, fml) in enumerate(res):
        ws.cell(5 + k, 7, t).font = NEGRO
        ws.cell(5 + k, 8, fml).font = NEGRO
    ws.column_dimensions['G'].width = 28


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


def _validacion():
    spec = importlib.util.spec_from_file_location('validacion_milp', os.path.join(RAIZ, 'fase2', 'validacion_milp.py'))
    V = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(V)
    return V


def hojas_f(wb):
    V = _validacion()
    # Órdenes de prueba
    ws = _hoja(wb, 'F1_Ordenes_prueba', 'Anexo F. Órdenes de las instancias de prueba',
               'Tiempos reales de la empresa; cantidades y fechas reducidas para que el problema se pueda resolver '
               'de forma exacta.')
    filas = [[o, ref, q, r, d, f'=E{5 + i}-D{5 + i}'] for i, (o, ref, q, r, d) in enumerate(V.ORDENES)]
    _tabla(ws, 4, ['Orden', 'Referencia', 'Cantidad (docenas)', 'r_j (h)', 'd_j (h)', 'Ventana d_j − r_j (h)'],
           filas, [None, None, '0', '0.0', '0.0', '0.0'], [9, 11, 14, 9, 9, 16])
    # Máquinas y tiempos de procesamiento de cada orden
    t = pd.read_excel(BD, 'Tiempo de procesamiento')
    t.columns = [c.strip() for c in t.columns]
    for c in ('Maquina', 'Etapa', 'Codigo producto'):
        t[c] = t[c].astype(str).str.strip()
    tiempo = {(r['Maquina'], r['Codigo producto']): float(r['min x docena']) for _, r in t.iterrows()}
    ws2 = _hoja(wb, 'F2_Tiempos_prueba', 'Anexo F. Máquinas del conjunto de prueba y tiempo de procesamiento '
                                         'de cada orden completa',
                'Tiempo de la orden (h) = cantidad × tiempo estándar / 60. Las órdenes se toman de la hoja '
                'Ordenes_prueba; los tiempos estándar, de la base de datos.')
    refs = sorted({ref for _, ref, *_ in V.ORDENES})
    maqs = [(e, m) for e in ETAPAS for m in V.MAQUINAS[e]]
    no = len(V.ORDENES)
    ws2.cell(4, 1, 'Tiempo estándar (min/docena)').font = NEG
    filas = [[e, m] + [tiempo[(m, r)] for r in refs] for e, m in maqs]
    _, a, b = _tabla(ws2, 5, ['Etapa', 'Máquina'] + refs, filas, [None, None] + ['0.00'] * len(refs),
                     [13, 10] + [11] * max(len(refs), no))
    f0 = b + 3
    ws2.cell(f0, 1, 'Tiempo de procesamiento de cada orden completa (h)').font = NEG
    ordenes = [o for o, *_ in V.ORDENES]
    filas = []
    for i, (e, m) in enumerate(maqs):
        f = f0 + 2 + i
        fila = [e, m]
        for k in range(no):
            ro = 5 + k
            fila.append(f'=F1_Ordenes_prueba!$C${ro}*INDEX($C{a + i}:${get_column_letter(2 + len(refs))}{a + i},'
                        f'MATCH(F1_Ordenes_prueba!$B${ro},$C$5:${get_column_letter(2 + len(refs))}$5,0))/60')
        filas.append(fila)
    _tabla(ws2, f0 + 1, ['Etapa', 'Máquina'] + ordenes, filas, [None, None] + ['0.00'] * no)
    ws2.freeze_panes = None
    # Diseño de las instancias
    ws3 = _hoja(wb, 'F3_Instancias', 'Anexo F. Diseño de las seis instancias de prueba',
                'Sublotes = órdenes × B̄ (máximo de sublotes por orden).')
    filas = []
    for i, (nom, ords, bb, mq) in enumerate(V.INSTANCIAS):
        f = 5 + i
        filas.append([nom, ', '.join(o[0] for o in ords), len(ords), bb, f'=C{f}*D{f}',
                      '-'.join(str(len(mq[e])) for e in ETAPAS), sum(len(mq[e]) for e in ETAPAS)])
    _tabla(ws3, 4, ['Instancia', 'Órdenes incluidas', 'N.º de órdenes', 'B̄', 'Sublotes', 'Máquinas por etapa',
                    'Máquinas en total'], filas, [None, None, '0', '0', '0', None, '0'], [10, 20, 12, 6, 10, 16, 14])
    # Resultados
    v = pd.read_csv(os.path.join(VAL, 'resultados_validacion_todas.csv'))
    ws = _hoja(wb, 'F4_Resultados', 'Anexo F. Validación con instancias reducidas: resultados completos',
               'F1: formulación del documento; F2: formulación de precedencia general. Estados y tiempos del '
               'solver HiGHS; el AG se corrió 10 veces por instancia (semillas 1 a 10).')
    cols = ['Instancia', 'Órdenes', 'B̄', 'Sublotes', 'Máquinas', 'F1 binarias', 'F1 ΣTj', 'F1 Cmax', 'F1 estado',
            'F1 s', 'F2 binarias', 'F2 ΣTj', 'F2 Cmax', 'F2 estado', 'F2 s', 'Regla', 'Regla ΣTj', 'AG mejor ΣTj',
            'AG mejor Cmax', 'AG prom ΣTj', 'AG ≤ MILP en ΣTj', 'AG s prom']
    filas = [[(None if pd.isna(r[c]) else (r[c].item() if hasattr(r[c], 'item') else r[c])) for c in cols]
             for _, r in v.iterrows()]
    hdr = cols + ['Mejor exacta ΣTj', 'Diferencia AG prom − exacta (h)', 'Reducción de binarias F2 vs F1',
                  'Mejora del AG (promedio) frente a la regla']
    for i, f in enumerate(filas):
        k = 5 + i
        f += [f'=IF(AND(G{k}="",L{k}=""),"",MIN(IF(G{k}="",L{k},G{k}),IF(L{k}="",G{k},L{k})))',
              f'=IF(W{k}="","",T{k}-W{k})', f'=1-K{k}/F{k}', f'=IF(Q{k}=0,"",1-T{k}/Q{k})']
    _, a, b = _tabla(ws, 4, hdr, filas, [None] * 6 + ['0.000', '0.000', None, '0.0', None, '0.000', '0.000', None, '0.0',
                                                      None, '0.000', '0.000', '0.000', '0.000', None, '0.0', '0.000',
                                                      '0.000', '0.0%', '0.0%'],
                     [9, 8, 5, 8, 9, 9, 9, 9, 28, 7, 9, 9, 9, 28, 7, 7, 9, 10, 10, 10, 10, 8, 11, 12, 12, 12])
    res = [('Instancias con óptimo demostrado (F1 o F2)', f'=COUNTIF(I{a}:I{b},"Óptimo")+COUNTIFS(I{a}:I{b},"<>Óptimo",'
                                                          f'N{a}:N{b},"Óptimo")', '0'),
           ('Reducción promedio de binarias con F2', f'=AVERAGE(Y{a}:Y{b})', '0.0%'),
           ('Mejora promedio del AG (promedio de réplicas) frente a la regla', f'=AVERAGE(Z{a}:Z{b})', '0.0%')]
    for k, (txt, fml, fmt) in enumerate(res):
        ws.cell(b + 2 + k, 1, txt).font = NEG
        c = ws.cell(b + 2 + k, 7, fml); c.font = NEGRO; c.number_format = fmt


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
    txt = txt_inf = open(os.path.join(CAL, 'informe_calibracion.md'), encoding='utf-8').read()
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
    _, _, b2 = _tabla(ws5, f0 + 1, ['Generaciones sin mejora', 'Réplicas', 'ΣTj prom. (h)', 'Cmax prom. (h)',
                                    'Generaciones prom.', 'Tiempo prom. (min)'], filas,
                      ['0', '0', '0.00', '0.0', '0', '0.0'])
    # Comparación pareada por semilla (misma semilla con ambos criterios)
    f1 = b2 + 3
    ws5.cell(f1, 1, 'Comparación pareada por semilla').font = NEG
    niveles = sorted(par.sin_mejora.unique())
    lo, hi = int(niveles[0]), int(niveles[-1])
    filas = []
    for i, sem in enumerate(sorted(par.semilla.unique())):
        f = f1 + 2 + i
        S = lambda col, nv: f'SUMIFS(${col}${a}:${col}${b},$A${a}:$A${b},{nv},$B${a}:$B${b},A{f})'
        filas.append([int(sem), f'={S("C", lo)}', f'={S("C", hi)}', f'=B{f}-C{f}', f'={S("D", lo)}',
                      f'={S("D", hi)}', f'=E{f}-F{f}'])
    _, a3, b3 = _tabla(ws5, f1 + 1, ['Semilla', f'ΣTj con {lo} (h)', f'ΣTj con {hi} (h)', 'Diferencia ΣTj (h)',
                                     f'Cmax con {lo} (h)', f'Cmax con {hi} (h)', 'Diferencia Cmax (h)'], filas,
                       ['0', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000'])
    res = [(f'Semillas en que {hi} mejora el resultado (ΣTj o Cmax)',
            f'=SUMPRODUCT(((D{a3}:D{b3}>0.000001)+((ABS(D{a3}:D{b3})<=0.000001)*(G{a3}:G{b3}>0.000001)))>0)', '0'),
           ('Mejora promedio de Cmax (h)', f'=AVERAGE(G{a3}:G{b3})', '0.00')]
    for k, (txt, fml, fmt) in enumerate(res):
        ws5.cell(b3 + 2 + k, 1, txt).font = NEG
        c = ws5.cell(b3 + 2 + k, 4, fml); c.font = NEGRO; c.number_format = fmt
    m = re.search(r'Wilcoxon de una cola p = ' + NUM, txt_inf)
    if m:
        ws5.cell(b3 + 5, 1, 'Prueba de Wilcoxon de una cola (calculada en Python sobre el resultado lexicográfico '
                            'pareado): valor p').font = NEG
        c = ws5.cell(b3 + 5, 4, float(m.group(1))); c.font = AZUL; c.number_format = '0.0000'
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
    # Comprobaciones de la división en sublotes (columnas a la derecha)
    hdr = ['Cantidad (docenas)', 'Sublotes', 'Docenas programadas en troquelado', '¿Se programa toda la orden?',
           'Inicio en troquelado (h)', 'r_j (h)', '¿Respeta la liberación?']
    for k, h in enumerate(hdr):
        c = ws3.cell(4, 8 + k, h)
        c.font, c.fill = NEG, CAB
        c.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        ws3.column_dimensions[get_column_letter(8 + k)].width = 14
    for i in range(len(M.TRABAJOS)):
        f = a3 + i
        fmls = [f'=INDEX(D1_Ordenes!$C$5:$C$14,MATCH(A{f},D1_Ordenes!$A$5:$A$14,0))',
                f'=COUNTIFS({P("A")},A{f},{P("D")},1)', f'=SUMIFS({P("C")},{P("A")},A{f},{P("D")},1)',
                f'=IF(J{f}=H{f},"Sí","No")', f'=_xlfn.MINIFS({P("G")},{P("A")},A{f},{P("D")},1)',
                f'=INDEX(D1_Ordenes!$E$5:$E$14,MATCH(A{f},D1_Ordenes!$A$5:$A$14,0))',
                f'=IF(L{f}>=M{f}-0.000001,"Sí","No")']
        for k, (fml, fmt) in enumerate(zip(fmls, ['#,##0', '0', '#,##0', None, '0.00', '0', None])):
            c = ws3.cell(f, 8 + k, fml); c.font = NEGRO
            if fmt:
                c.number_format = fmt
    ws3.cell(b3 + 2, 8, 'Sublotes en total').font = NEG
    c = ws3.cell(b3 + 2, 9, f'=SUM(I{a3}:I{b3})'); c.font = NEGRO
    # Uso de cada máquina
    maqs = sorted({(o[2], o[3]) for o in ops}, key=lambda x: (x[0], int(x[1][1:])))
    ws4 = _hoja(wb, 'H4_Por_maquina', 'Anexo H. Uso de cada máquina en la programación propuesta',
                'Horas ocupadas = suma de las duraciones de sus operaciones (hoja Programacion); '
                'utilización = horas ocupadas / makespan (hoja Por_orden).')
    cmax = f'H3_Por_orden!$D${b3 + 4}'
    filas = []
    for i, (st, m) in enumerate(maqs):
        f = 5 + i
        filas.append([ETAPAS[st - 1], m, f'=COUNTIF({P("F")},B{f})', f'=SUMIFS({P("I")},{P("F")},B{f})',
                      f'=_xlfn.MINIFS({P("G")},{P("F")},B{f})', f'=_xlfn.MAXIFS({P("H")},{P("F")},B{f})',
                      f'=D{f}/{cmax}'])
    _, a4, b4 = _tabla(ws4, 4, ['Etapa', 'Máquina', 'Operaciones', 'Horas ocupadas', 'Primer inicio (h)',
                                'Último fin (h)', 'Utilización'], filas,
                       [None, None, '0', '0.0', '0.0', '0.0', '0.0%'], [13, 10, 12, 14, 14, 14, 12])
    f0 = b4 + 3
    ws4.cell(f0, 1, 'Resumen por etapa').font = NEG
    filas = []
    for k, e in enumerate(ETAPAS):
        f = f0 + 2 + k
        filas.append([e, f'=COUNTIF($A${a4}:$A${b4},A{f})', f'=SUMIF($A${a4}:$A${b4},A{f},$C${a4}:$C${b4})',
                      f'=SUMIF($A${a4}:$A${b4},A{f},$D${a4}:$D${b4})',
                      f'=AVERAGEIF($A${a4}:$A${b4},A{f},$G${a4}:$G${b4})'])
    _tabla(ws4, f0 + 1, ['Etapa', 'Máquinas usadas', 'Operaciones', 'Horas ocupadas', 'Utilización promedio'], filas,
           [None, '0', '0', '0.0', '0.0%'])
    ws4.freeze_panes = 'A5'


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
    Bb = F.B_ACTUAL_BASE
    ind_b = F.individuo_fifo_por_etapa(M, Bb)
    tam_b = {j: M.props_a_docenas(j, ind_b['proporciones'][j]) for j in M.TRABAJOS}
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
    # Comparación con el registro histórico
    ws.cell(4, 8, 'Comparación con el registro histórico').font = NEG
    cmp_ = [('Órdenes tardías históricas', 0.45, '0%'), (f'Órdenes tardías con B = {Bb}', f'=INDEX(C5:C13,MATCH({Bb},A5:A13,0))', '0%'),
            ('Diferencia (puntos porcentuales)', '=(I6-I5)*100', '0.0')]
    for k, (t, v, fmt) in enumerate(cmp_):
        ws.cell(5 + k, 8, t).font = NEGRO
        c = ws.cell(5 + k, 9, v); c.number_format = fmt
        c.font = AZUL if not isinstance(v, str) else NEGRO
    ws.column_dimensions['H'].width = 30
    # Tamaño de las partes iguales con B = Bb
    f1 = b + 4
    ws.cell(f1, 1, f'Tamaño de las {Bb} partes de cada orden (docenas) con el sistema actual').font = NEG
    ws.cell(f1 + 1, 1, 'Partes iguales ajustadas a múltiplos enteros de docena; la suma debe ser igual a la cantidad de '
                       'la orden.').font = NOTA
    filas = []
    for i, j in enumerate(M.TRABAJOS):
        f = f1 + 3 + i
        ult, cs, cq = get_column_letter(1 + Bb), get_column_letter(2 + Bb), get_column_letter(3 + Bb)
        filas.append([j] + [int(x) for x in tam_b[j]] + [f'=SUM(B{f}:{ult}{f})',
                     f'=INDEX(D1_Ordenes!$C$5:$C$14,MATCH(A{f},D1_Ordenes!$A$5:$A$14,0))',
                     f'=IF({cs}{f}={cq}{f},"Sí","No")', f'={cq}{f}/{Bb}'])
    _tabla(ws, f1 + 2, ['Orden'] + [f'Parte {k + 1}' for k in range(Bb)] + ['Suma', 'Cantidad de la orden',
                                                                          '¿Coincide?', 'Cantidad / B'],
           filas, [None] + ['0'] * Bb + ['#,##0', '#,##0', None, '0.0'])
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
    _, _, b3 = _tabla(ws3, 4, ['Escenario', 'B del AG', 'Réplicas', '% tardías prom.', 'ΣTj prom. (h)',
                               'ΣTj desv. (h)', 'IC 95 % ± (h)', 'Cmax prom. (h)', 'ΣTj sistema actual B=6 (h)',
                               'Reducción de ΣTj'], filas,
                      [None, '0', '0', '0.0%', '0.00', '0.00', '0.00', '0.0', '0.0', '0.0%'],
                      [13, 9, 9, 13, 12, 12, 12, 12, 16, 13])
    # Comparación de los tres métodos en cada escenario
    f0 = b3 + 3
    ws3.cell(f0, 1, 'Comparación por escenario: sistema actual, mejor regla de despacho y algoritmo genético '
                    '(B = 6 para el sistema actual y las reglas; B̄ = 10 para el algoritmo)').font = NEG
    escen = list(dict.fromkeys(ag['escenario']))
    filas = []
    for i, e in enumerate(escen):
        f = f0 + 2 + i
        filas.append([e, f'=SUMIFS({D("F")},{D("A")},A{f},{D("B")},"Actual (FIFO por etapa)",{D("C")},6)',
                      f'=_xlfn.MINIFS({D("F")},{D("A")},A{f},{D("B")},"<>Actual (FIFO por etapa)",{D("C")},6)',
                      f'=INDEX({D("B")},MATCH(1,INDEX(({D("A")}=A{f})*({D("C")}=6)*({D("F")}=C{f}),0),0))',
                      f'=AVERAGEIFS({R("G")},{R("B")},A{f},{R("C")},10)',
                      f'=IF(B{f}=0,"",1-E{f}/B{f})', f'=IF(C{f}=0,"",1-E{f}/C{f})'])
    _tabla(ws3, f0 + 1, ['Escenario', 'ΣTj sistema actual (h)', 'ΣTj mejor regla (h)', 'Mejor regla',
                         'ΣTj AG prom. (h)', 'Reducción frente al sistema actual', 'Reducción frente a la mejor regla'],
           filas, [None, '0.0', '0.0', None, '0.0', '0.0%', '0.0%'])
    ws3.freeze_panes = 'A5'


# Libros por anexo: (letra, archivo, título, descripción, constructor, hojas)
# hojas: [nombre interno, nombre en el libro, contenido, respalda en el documento]
def _d(wb, M):
    hoja_ordenes(wb, calculo=True)
    t = hoja_tiempos(wb)
    hoja_calendario(wb)
    hoja_matriz(wb, t)


def _e(wb, M):
    hoja_e(wb, len(M.TRABAJOS))
    hoja_ordenes(wb)
    hoja_tiempos(wb)


def _h(wb, M):
    hojas_h(wb, M)
    hoja_ordenes(wb)


def _i(wb, M):
    hojas_i(wb, M)
    hoja_ordenes(wb)


LIBROS = [
    ('D', 'Anexo_D_Base_de_datos.xlsx', 'Base de datos del caso de estudio',
     'Datos de entrada del modelo: órdenes, tiempos estándar y calendario laboral. Las horas de liberación y '
     'entrega (r_j, d_j) se recalculan desde el calendario para comprobar que coinciden con la base de datos.', _d,
     [['D1_Ordenes', 'Ordenes', 'Órdenes: cantidad, liberación y entrega; r_j y d_j recalculados desde el calendario',
       'Tabla 3'],
      ['D4_Matriz', 'Matriz_tiempos', 'Tiempos estándar en forma de matriz máquina × referencia, con promedio por etapa',
       'Tabla 2'],
      ['D2_Tiempos', 'Tiempos', 'Tiempo estándar de cada referencia en cada máquina (252 filas) y su ritmo', 'Tabla 2'],
      ['D3_Calendario', 'Calendario', 'Calendario laboral día a día y horas acumuladas', 'Horizonte de 611 h']]),
    ('E', 'Anexo_E_Carga_y_capacidad.xlsx', 'Cálculo de la carga frente a la capacidad',
     'Capacidad de cada etapa por referencia, carga de cada orden en horas por máquina y ocupación de cada etapa '
     'en el horizonte. Todo se calcula con fórmulas desde las hojas de datos Ordenes y Tiempos.', _e,
     [['E_Carga', 'Carga', 'Capacidad R_p, carga de cada orden y ocupación de cada etapa (fórmulas)',
       'Tabla 4 y 76 % de ocupación de troquelado'],
      ['D1_Ordenes', 'Ordenes', 'Datos: órdenes de trabajo', 'Anexo D'],
      ['D2_Tiempos', 'Tiempos', 'Datos: tiempos estándar y ritmos', 'Anexo D']]),
    ('F', 'Anexo_F_Validacion.xlsx', 'Verificación y validación del modelo',
     'Instancias reducidas con las que se comparó el algoritmo genético con la solución exacta del modelo '
     'matemático: órdenes, máquinas, tiempos, diseño de las instancias y resultados completos.', lambda wb, M: hojas_f(wb),
     [['F4_Resultados', 'Resultados', 'Resultados del solver y del algoritmo en las seis instancias, con diferencias '
                                     'y reducciones calculadas', 'Validación del modelo'],
      ['F1_Ordenes_prueba', 'Ordenes_prueba', 'Las cinco órdenes de prueba', 'Validación del modelo'],
      ['F2_Tiempos_prueba', 'Tiempos_prueba', 'Máquinas del conjunto de prueba y tiempo de cada orden (fórmulas)',
       'Validación del modelo'],
      ['F3_Instancias', 'Instancias', 'Diseño de las instancias I1 a I6', 'Validación del modelo']]),
    ('G', 'Anexo_G_Calibracion.xlsx', 'Calibración del algoritmo genético',
     'Diseño factorial 3³ con 5 réplicas (135 corridas), ANOVA calculado con fórmulas, pruebas de supuestos y '
     'experimento del criterio de parada.', lambda wb, M: hojas_g(wb),
     [['G1_Corridas', 'Corridas', 'Las 135 corridas del diseño factorial', 'Tablas 7 a 9'],
      ['G2_Combinaciones', 'Combinaciones', 'Promedio y desviación de cada combinación (fórmulas)', 'Tabla 9'],
      ['G3_ANOVA', 'ANOVA', 'ANOVA paso a paso con fórmulas', 'Tabla 8'],
      ['G4_Supuestos', 'Supuestos', 'Shapiro-Wilk, Levene y Kruskal-Wallis', 'Supuestos del ANOVA'],
      ['G5_Parada', 'Parada', 'Criterio de parada: 20 corridas, resumen y comparación pareada', 'Tabla 10']]),
    ('H', 'Anexo_H_Solucion_propuesta.xlsx', 'Réplicas finales y programación detallada',
     'Réplicas finales del algoritmo calibrado y programación completa de la mejor solución. La terminación, la '
     'tardanza de cada orden y el uso de cada máquina se calculan con fórmulas desde la programación.', _h,
     [['H1_Replicas', 'Replicas', 'Las 10 réplicas finales y su resumen', '"8 de 10 réplicas eliminaron la tardanza"'],
      ['H2_Programacion', 'Programacion', 'Programación detallada: operaciones con máquina, inicio y fin', 'Figura 2'],
      ['H3_Por_orden', 'Por_orden', 'C_j, T_j y E_j de cada orden y comprobación de sublotes y liberaciones',
       'Tabla 12'],
      ['H4_Por_maquina', 'Por_maquina', 'Horas ocupadas y utilización de cada máquina y de cada etapa',
       'Análisis de la programación'],
      ['D1_Ordenes', 'Ordenes', 'Datos: órdenes de trabajo (d_j, r_j y cantidad)', 'Anexo D']]),
    ('I', 'Anexo_I_Sistema_actual.xlsx', 'Representación del sistema actual',
     'Desempeño del sistema actual (FIFO por etapa, órdenes divididas en B partes iguales) para B de 2 a 10, '
     'comparación con el 45 % histórico, terminación por orden y tamaño de las partes.', _i,
     [['I_Sistema_actual', 'Sistema_actual', 'Sistema actual con B de 2 a 10, terminación por orden con B = 5, 6 y 7 '
                                           'y tamaño de las partes', 'Elección de B = 6 y Tabla 18'],
      ['D1_Ordenes', 'Ordenes', 'Datos: órdenes de trabajo', 'Anexo D']]),
    ('J', 'Anexo_J_Fase3.xlsx', 'Resultados de los experimentos de la Fase 3',
     'Corridas del algoritmo genético y resultados del sistema actual y de las reglas de despacho en el escenario '
     'base y en los escenarios de exigencia, con los resúmenes y las reducciones calculadas con fórmulas.', lambda wb, M: hojas_j(wb),
     [['J3_Resumen', 'Resumen', 'Media, desviación, IC 95 % y reducciones frente al sistema actual y a la mejor regla',
       'Tablas 14 y 17'],
      ['J1_Corridas_F3', 'Corridas', 'Las 120 corridas del algoritmo en la Fase 3', 'Tablas 14 a 17'],
      ['J2_Deterministas', 'Deterministas', 'Sistema actual y reglas de despacho en cada escenario',
       'Tablas 15 a 17']]),
]


def _renombrar(wb, hojas):
    """Renombra las hojas y actualiza las referencias en fórmulas y textos."""
    mapa = sorted(((h[0], h[1]) for h in hojas), key=lambda x: -len(x[0]))
    for ws in wb.worksheets:
        for fila in ws.iter_rows():
            for c in fila:
                if isinstance(c.value, str):
                    v = c.value
                    for a, n in mapa:
                        v = v.replace(a, n)
                    if v != c.value:
                        c.value = v
    for a, n in mapa:
        wb[a].title = n


def libro(M, letra, archivo, titulo, descripcion, constructor, hojas, carpeta):
    from copy import copy
    wb = Workbook()
    leeme(wb, letra, titulo, descripcion, [h[1:] for h in hojas])
    constructor(wb, M)
    _renombrar(wb, hojas)
    orden = ['Leeme'] + [h[1] for h in hojas]
    wb._sheets = [wb[n] for n in orden]
    for hoja in wb:
        hoja.sheet_view.showGridLines = True
        for fila in hoja.iter_rows():
            for c in fila:
                if c.value is not None and c.font.name != 'Arial':
                    f = copy(c.font)
                    f.name, f.size = 'Arial', f.size or 10
                    c.font = f
    ruta = os.path.join(carpeta, archivo)
    wb.save(ruta)
    print('Guardado en', ruta)


def main():
    carpeta = sys.argv[1]
    os.makedirs(carpeta, exist_ok=True)
    M = _modelo()
    for L in LIBROS:
        libro(M, *L, carpeta)


if __name__ == '__main__':
    main()
