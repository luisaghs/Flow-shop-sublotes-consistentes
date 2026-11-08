# -*- coding: utf-8 -*-
"""
Arma salida_calibracion/anova_calibracion_excel.xlsx: el ANOVA del diseño factorial
de la calibración calculado SOLO con fórmulas de Excel, a partir de corridas_diseno.csv,
para revisar cada cifra paso a paso.

Uso: python anova_excel.py
"""
import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salida_calibracion')
FACT = [('poblacion', 'Población', 'A'), ('prob_cruce', 'Prob. cruce', 'B'),
        ('prob_mutacion', 'Prob. mutación', 'C')]
NEG = Font(bold=True)
CAB = PatternFill('solid', fgColor='DCE6F2')


def _coma(x, d):
    return f'{x:.{d}f}'.replace('.', ',')


def main():
    d = pd.read_csv(os.path.join(DIR, 'corridas_diseno.csv'))
    d = d.sort_values(['poblacion', 'prob_cruce', 'prob_mutacion', 'semilla']).reset_index(drop=True)
    a = pd.read_csv(os.path.join(DIR, 'anova.csv'))
    a = a.set_index(a.columns[0])
    n = len(d)
    ult = n + 1
    rng = lambda col: f'Corridas!${col}$2:${col}${ult}'
    Y = rng('E')

    wb = Workbook()
    ins = wb.active
    ins.title = 'Instrucciones'
    ins.column_dimensions['A'].width = 120
    p = a['valor p'] if 'valor p' in a.columns else a.iloc[:, -1]
    F = a['F'] if 'F' in a.columns else a.iloc[:, -2]
    nombres = {'Población': 'población', 'Prob. de cruce': 'cruce', 'Prob. de mutación': 'mutación'}
    tp = lambda v: 'p < 0,0001' if v < 1e-4 else f'p ≈ {_coma(v, 4)}'
    sig = [f"{nombres.get(k, k.lower())} (F ≈ {_coma(F[k], 2)}, {tp(p[k])})"
           for k in p.index if k not in ('Error', 'Total') and pd.notna(p[k]) and p[k] < 0.05]
    nosig = [nombres.get(k, k.lower()) for k in p.index
             if k not in ('Error', 'Total') and pd.notna(p[k]) and p[k] >= 0.05]
    textos = [
        ('ANOVA DE LA CALIBRACIÓN DEL ALGORITMO GENÉTICO, PASO A PASO', True), ('', False),
        (f'Hoja "Corridas": los {n} resultados del diseño factorial 3³ (5 réplicas por combinación).', False),
        ('Cada fila es una corrida del AG con su población, probabilidad de cruce, probabilidad de '
         'mutación y semilla.', False),
        ('La respuesta analizada es la tardanza total ΣTj (columna E).', False), ('', False),
        ('Hoja "ANOVA": todas las cifras se calculan con fórmulas a partir de "Corridas". Pueden '
         'revisar cada celda.', False),
        ('  1. Media general de ΣTj.', False),
        ('  2. Efectos principales: media de cada nivel; SC del factor = Σ n_nivel · (media_nivel − '
         'media general)².', False),
        ('  3. Interacciones dobles: SC = Σ n_celda · (media_celda − media_nivel_A − media_nivel_B + '
         'media general)².', False),
        ('  4. SC total = Σ (ΣTj − media general)²  (función DESVIA2 / DEVSQ).', False),
        ('  5. SC del error = SC total − suma de las SC de los efectos (incluye la interacción triple).', False),
        ('  6. CM = SC / gl;  F = CM / CM del error;  valor p = DISTR.F (cola derecha).', False), ('', False),
        ('Resultado esperado: significativos (p < 0,05): ' + '; '.join(sig) + '.', False),
        ('No significativos: ' + ', '.join(nosig) + '. Coincide con la tabla del ANOVA de la Fase 2.', False),
        ('', False),
        ('Ejercicio sugerido: cambien un valor de ΣTj en "Corridas" y observen cómo cambian las SC y '
         'el valor F.', False),
        ('Para comprobar que los datos son reproducibles, usen fase2/verificar_reproduccion.py.', False),
    ]
    for i, (t, b) in enumerate(textos, 1):
        ins.cell(i, 1, t).font = Font(bold=b, size=13 if i == 1 else 11)

    co = wb.create_sheet('Corridas')
    for j, t in enumerate(['Población', 'Prob. cruce', 'Prob. mutación', 'Semilla', 'ΣTj (h)', 'Cmax (h)'], 1):
        c = co.cell(1, j, t)
        c.font, c.fill = NEG, CAB
        co.column_dimensions['ABCDEF'[j - 1]].width = 15
    for i, r in d.iterrows():
        for j, v in enumerate([int(r.poblacion), float(r.prob_cruce), float(r.prob_mutacion),
                               int(r.semilla), float(r.suma_T), float(r.Cmax)], 1):
            co.cell(i + 2, j, v)
    co.freeze_panes = 'A2'

    an = wb.create_sheet('ANOVA')
    for col, w in zip('ABCDEF', [30, 14, 12, 16, 30, 12]):
        an.column_dimensions[col].width = w
    an['A1'] = 'ANOVA de la tardanza total (ΣTj)'
    an['A1'].font = Font(bold=True, size=13)
    an['A3'], an['B3'] = 'Media general', f'=AVERAGE({Y})'
    an['A4'], an['B4'] = 'Número de corridas', f'=COUNT({Y})'
    fila = 6
    media_nivel, sc = {}, {}
    for clave, nombre, col in FACT:
        an.cell(fila, 1, f'Efecto principal: {nombre}').font = NEG
        for j, t in enumerate(['Nivel', 'n', 'Media ΣTj', 'n·(media − media general)²'], 1):
            c = an.cell(fila + 1, j, t)
            c.font, c.fill = NEG, CAB
        niveles = sorted(d[clave].unique())
        for k, v in enumerate(niveles):
            f = fila + 2 + k
            an.cell(f, 1, int(v) if clave == 'poblacion' else float(v))
            an.cell(f, 2, f'=COUNTIF({rng(col)},A{f})')
            an.cell(f, 3, f'=AVERAGEIF({rng(col)},A{f},{Y})').number_format = '0.000'
            an.cell(f, 4, f'=B{f}*(C{f}-$B$3)^2').number_format = '0.000'
            media_nivel[(clave, v)] = f'$C${f}'
        f = fila + 2 + len(niveles)
        an.cell(f, 3, 'SC').font = NEG
        an.cell(f, 4, f'=SUM(D{fila + 2}:D{f - 1})').number_format = '0.000'
        sc[clave] = f'D{f}'
        fila = f + 2
    pares = [(0, 1), (0, 2), (1, 2)]
    for i1, i2 in pares:
        (k1, n1, c1), (k2, n2, c2) = FACT[i1], FACT[i2]
        an.cell(fila, 1, f'Interacción: {n1} × {n2}').font = NEG
        for j, t in enumerate([n1, n2, 'n', 'Media celda', 'n·(celda − A − B + general)²'], 1):
            c = an.cell(fila + 1, j, t)
            c.font, c.fill = NEG, CAB
        f = fila + 2
        for v1 in sorted(d[k1].unique()):
            for v2 in sorted(d[k2].unique()):
                an.cell(f, 1, int(v1) if k1 == 'poblacion' else float(v1))
                an.cell(f, 2, float(v2))
                an.cell(f, 3, f'=COUNTIFS({rng(c1)},A{f},{rng(c2)},B{f})')
                an.cell(f, 4, f'=AVERAGEIFS({Y},{rng(c1)},A{f},{rng(c2)},B{f})').number_format = '0.000'
                an.cell(f, 5, f'=C{f}*(D{f}-{media_nivel[(k1, v1)]}-{media_nivel[(k2, v2)]}+$B$3)^2'
                        ).number_format = '0.000'
                f += 1
        an.cell(f, 4, 'SC').font = NEG
        an.cell(f, 5, f'=SUM(E{fila + 2}:E{f - 1})').number_format = '0.000'
        sc[(k1, k2)] = f'E{f}'
        fila = f + 2

    an.cell(fila, 1, 'Tabla ANOVA').font = NEG
    for j, t in enumerate(['Fuente', 'SC', 'gl', 'CM', 'F', 'Valor p'], 1):
        c = an.cell(fila + 1, j, t)
        c.font, c.fill = NEG, CAB
    fuentes = [(n_, sc[k], 2) for k, n_, _ in FACT] + \
              [(f'{FACT[i1][1]} × {FACT[i2][1]}', sc[(FACT[i1][0], FACT[i2][0])], 4) for i1, i2 in pares]
    f0 = fila + 2
    f_err, f_tot = f0 + len(fuentes), f0 + len(fuentes) + 1
    for k, (nom, ref, gl) in enumerate(fuentes):
        f = f0 + k
        an.cell(f, 1, nom)
        an.cell(f, 2, f'={ref}').number_format = '#,##0.0'
        an.cell(f, 3, gl)
        an.cell(f, 4, f'=B{f}/C{f}').number_format = '#,##0.0'
        an.cell(f, 5, f'=D{f}/$D${f_err}').number_format = '0.00'
        an.cell(f, 6, f'=FDIST(E{f},C{f},$C${f_err})').number_format = '0.0000'
    an.cell(f_err, 1, 'Error')
    an.cell(f_err, 2, f'=B{f_tot}-SUM(B{f0}:B{f_err - 1})').number_format = '#,##0.0'
    an.cell(f_err, 3, f'=C{f_tot}-SUM(C{f0}:C{f_err - 1})')
    an.cell(f_err, 4, f'=B{f_err}/C{f_err}').number_format = '#,##0.0'
    an.cell(f_tot, 1, 'Total')
    an.cell(f_tot, 2, f'=DEVSQ({Y})').number_format = '#,##0.0'
    an.cell(f_tot, 3, '=B4-1')
    an.cell(f_tot + 2, 1, 'Un valor p menor que 0,05 indica que el factor tiene efecto significativo '
                          'sobre la tardanza total.')
    ruta = os.path.join(DIR, 'anova_calibracion_excel.xlsx')
    wb.save(ruta)
    print('Guardado en', ruta)


if __name__ == '__main__':
    main()
