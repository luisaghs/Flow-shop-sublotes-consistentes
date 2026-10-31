# -*- coding: utf-8 -*-
"""
Correcciones de la Fase 1 por el cambio de datos de la orden J01
(cantidad: 1.172 → 580 docenas; fecha de entrega: 01/09/2026 → 25/08/2026,
d_j: 672 → 630 h). Con el cambio, la última entrega es la de J10 (657 h).

Los valores de carga se calculan con el mismo método de la Tabla 4 del borrador
(carga por máquina = Σ_j Q_j / R_p, con R_p la suma de los ritmos de las
máquinas de la etapa) a partir de BD_HFS.xlsx.
"""
import pandas as pd

ETAPAS = ['Troquelado', 'Ensamble', 'Costura', 'Volteado']


def _n(x, d=1):
    return f"{x:,.{d}f}".replace(',', '§').replace('.', ',').replace('§', '.')


def cargas(ruta_bd):
    x = pd.ExcelFile(ruta_bd)
    t = x.parse('Tiempo de procesamiento')
    t.columns = [c.strip() for c in t.columns]
    j = x.parse('Trabajos')
    horizonte = float(j['d_j horas'].max())
    filas = []
    for etapa in ETAPAS:
        te = t[t['Etapa'].str.strip() == etapa]
        nm = te['Maquina'].nunique()
        por_maquina = 0.0
        for _, o in j.iterrows():
            tp = te[te['Codigo producto'] == o['Codigo Producto']]['min x docena']
            por_maquina += o['Cantidad (docenas)'] / (60.0 / tp).sum()
        filas.append((etapa, nm, por_maquina * nm, por_maquina, 100.0 * por_maquina / horizonte))
    return filas, int(j['Cantidad (docenas)'].sum()), horizonte, j


def _reemplazar_en_parrafo(p, viejo, nuevo):
    for r in p.runs:
        if viejo in r.text:
            r.text = r.text.replace(viejo, nuevo)
            return True
    if viejo in p.text:                      # el texto cruza varios fragmentos
        completo = p.text.replace(viejo, nuevo)
        for k, r in enumerate(p.runs):
            r.text = completo if k == 0 else ''
        return True
    return False


def corregir_fase1(documento, ruta_bd):
    filas, total, horizonte, j = cargas(ruta_bd)
    c = {f[0]: f for f in filas}
    tro, ens, cos, vol = (c[e] for e in ETAPAS)
    j01 = j[j['Orden de trabajo'] == 'J01'].iloc[0]
    mayor = j.loc[j['Cantidad (docenas)'].idxmax()]
    pct_mayor = 100.0 * mayor['Cantidad (docenas)'] / total
    hechos = []

    # Tabla 3 (órdenes) y Tabla 4 (carga por etapa)
    for t in documento.tables:
        cab = [cel.text.strip() for cel in t.rows[0].cells]
        if cab[:3] == ['Orden', 'Referencia', 'Cantidad de docenas']:
            for fila in t.rows[1:]:
                if fila.cells[0].text.strip() == 'J01':
                    nuevos = {2: _n(j01['Cantidad (docenas)'], 0), 4: _n(j01['d_j horas'], 0),
                              5: _n(j01['d_j horas'] - j01['r_j Liberación'], 0)}
                    for k, v in nuevos.items():
                        _reemplazar_en_parrafo(fila.cells[k].paragraphs[0],
                                               fila.cells[k].text.strip(), v)
                    hechos.append('Tabla 3: fila J01')
        if cab[:3] == ['Etapa', 'Cantidad Maquinas', 'Carga total (h)']:
            for fila in t.rows[1:]:
                nombre = fila.cells[0].text.split('.')[-1].strip()
                if nombre in c:
                    _, _, tot, pm, oc = c[nombre]
                    for k, v in {2: _n(tot), 3: _n(pm), 4: _n(oc) + '%'}.items():
                        _reemplazar_en_parrafo(fila.cells[k].paragraphs[0],
                                               fila.cells[k].text.strip(), v)
            hechos.append('Tabla 4: cargas y ocupación')

    textos = [
        ('entre la semana 11 y la semana 18', 'entre la semana 11 y la semana 17'),
        ('es decir, 672 horas laborables', f'es decir, {_n(horizonte, 0)} horas laborables'),
        ('Es posible notar que J01 concentra al menos el 20% del volumen, con 1.172 docenas, '
         'mientras que J09 solo tiene 210 docenas.',
         f"Es posible notar que {mayor['Orden de trabajo']} es la orden de mayor tamaño, con "
         f"{_n(mayor['Cantidad (docenas)'], 0)} docenas (cerca del {pct_mayor:.0f}% del volumen), "
         f"mientras que J09 solo tiene 210 docenas."),
        ('acumula 515 horas de trabajo, el 77% de la disponibilidad',
         f'acumula {tro[3]:.0f} horas de trabajo, el {tro[4]:.0f}% de la disponibilidad'),
        ('ensamble con el 50% de ocupación y volteado 27%',
         f'ensamble con el {ens[4]:.0f}% de ocupación y volteado {vol[4]:.0f}%'),
        ('terminar las 5.834 docenas en 672 horas exige procesar en promedio 8,7 docenas por hora',
         f'terminar las {_n(total, 0)} docenas en {_n(horizonte, 0)} horas exige procesar en '
         f'promedio {_n(total / horizonte, 1)} docenas por hora'),
    ]
    pendientes = dict(textos)
    for p in documento.paragraphs:
        for viejo, nuevo in textos:
            if viejo in pendientes and viejo in p.text and _reemplazar_en_parrafo(p, viejo, nuevo):
                pendientes.pop(viejo)
                hechos.append(f'Texto: «{viejo[:45]}…»')
    if pendientes:
        raise ValueError('No se encontraron estos textos de la Fase 1: ' + ' | '.join(pendientes))
    return hechos
