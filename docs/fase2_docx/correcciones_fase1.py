# -*- coding: utf-8 -*-
"""
Actualiza las cifras de la Fase 1 del borrador con los datos vigentes de
BD_HFS.xlsx: Tabla 3 (cantidades, fechas de entrega y ventanas de cada orden),
Tabla 4 (carga y ocupación por etapa), horizonte de planeación, semanas de
entrega, orden de mayor tamaño y ritmo de producción requerido.

Los valores de carga se calculan con el mismo método de la Tabla 4 del borrador
(carga por máquina = Σ_j Q_j / R_p, con R_p la suma de los ritmos de las
máquinas de la etapa) a partir de BD_HFS.xlsx.
"""
import os

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
    inicio = pd.Timestamp(j['Fecha de liberación'].min()).normalize()
    semana = lambda f: (pd.Timestamp(f).normalize() - inicio).days // 7 + 1
    sem_min, sem_max = semana(j['Fechas de entrega'].min()), semana(j['Fechas de entrega'].max())
    mayor = j.loc[j['Cantidad (docenas)'].idxmax()]
    pct_mayor = 100.0 * mayor['Cantidad (docenas)'] / total
    hechos = []

    # Tabla 3 (órdenes) y Tabla 4 (carga por etapa)
    for t in documento.tables:
        cab = [cel.text.strip() for cel in t.rows[0].cells]
        if cab[:3] == ['Orden', 'Referencia', 'Cantidad de docenas']:
            for fila in t.rows[1:]:
                o = j[j['Orden de trabajo'] == fila.cells[0].text.strip()]
                if o.empty:
                    continue
                o = o.iloc[0]
                nuevos = {2: _n(o['Cantidad (docenas)'], 0), 3: _n(o['r_j Liberación'], 0),
                          4: _n(o['d_j horas'], 0), 5: _n(o['d_j horas'] - o['r_j Liberación'], 0)}
                for k, v in nuevos.items():
                    viejo = fila.cells[k].text.strip()
                    if viejo != v:
                        _reemplazar_en_parrafo(fila.cells[k].paragraphs[0], viejo, v)
            hechos.append('Tabla 3: cantidades, fechas de entrega y ventanas')
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
        ('entre la semana 11 y la semana 18', f'entre la semana {sem_min} y la semana {sem_max}'),
        ('es decir, 672 horas laborables, que equivalen a 17 semanas calendario',
         f'es decir, {_n(horizonte, 0)} horas laborables, que equivalen a {sem_max} semanas calendario'),
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


FIGURA1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase1_figuras',
                       'diagrama_proceso.png')


def insertar_figura(documento, texto_ancla, titulo, ruta_png, numero, ancho_cm=15.0):
    """Inserta una figura (rótulo e imagen) después del párrafo que contiene texto_ancla."""
    import lib_docx as L
    ancla = next((p for p in documento.paragraphs if texto_ancla in p.text), None)
    if ancla is None:
        raise ValueError(f'No se encontró el párrafo: «{texto_ancla[:50]}…»')
    cuerpo = documento.element.body
    antes = len(cuerpo)
    esc = L.Escritor(documento, {}, primer_figura=numero)
    esc.figura(titulo, os.path.abspath(ruta_png), ancho_cm)
    nuevos = [el for el in list(cuerpo)[antes - 1:] if not el.tag.endswith('sectPr')]
    pos = ancla._p
    for el in nuevos:
        pos.addnext(el)
        pos = el
    return ancla


def insertar_figura1(documento, ruta_png=FIGURA1):
    """Figura 1: diagrama de flujo del sistema, después del párrafo que la anuncia."""
    insertar_figura(documento, 'La figura 1 presenta el sistema estudiado',
                    'Diagrama de flujo del sistema productivo estudiado', ruta_png, 1, 15.0)
    return 'Figura 1: diagrama de flujo del sistema'


def insertar_figura_ocupacion(documento, ruta_png):
    """Figura 3: ocupación por etapa (la Figura 2, ventanas de tiempo, la anuncia el borrador)."""
    texto = 'las cuatro etapas tienen capacidad para procesar todas las ordenes dentro del horizonte de tiempo disponible'
    ancla = insertar_figura(documento, texto, 'Ocupación de las máquinas de cada etapa en el horizonte de '
                            'planeación', ruta_png, 3, 14.0)
    _reemplazar_en_parrafo(ancla, texto + '.', texto + ' (Figura 3).')
    return 'Figura 3: ocupación por etapa'


INTRO_METODOLOGIA = [
    ('p', 'Este capítulo presenta el desarrollo del trabajo, organizado en tres fases que corresponden a los '
          'tres objetivos específicos. Su propósito es dar respuesta a la pregunta de investigación, es decir, '
          'establecer cómo un algoritmo genético para la programación de la producción en un Flow Shop híbrido '
          'puede minimizar la tardanza total en la empresa. Para ello sigue una secuencia lógica: primero se '
          'comprende el sistema productivo, luego se construye y se pone a prueba un modelo para programarlo y, '
          'por último, se evalúa si ese modelo mejora la programación actual.'),
    ('p', 'El desarrollo se basa en la información de la empresa: los tiempos estándar de cada referencia en '
          'cada máquina, obtenidos mediante un estudio de tiempos; el calendario laboral, y un conjunto de diez '
          'órdenes de trabajo con sus cantidades, fechas de liberación y fechas de entrega. Los modelos se '
          'implementaron en Python: el modelo matemático se resolvió con el solver HiGHS y el algoritmo '
          'genético se programó a partir de esa misma formulación, de modo que los resultados pueden '
          'reproducirse con los datos y el código que acompañan el documento. El capítulo se organiza así:'),
    ('viñetas', [
        '**Caracterización del sistema Flow Shop híbrido (primer objetivo).** Describe las etapas del proceso, '
        'las máquinas y su clasificación, los tiempos de procesamiento, las órdenes de trabajo y la carga de '
        'cada etapa frente a su capacidad. Con esta información se establecen las restricciones y los '
        'supuestos del problema y se clasifica en la notación de tres campos.',
        '**Construcción del modelo matemático y del algoritmo genético (segundo objetivo).** Formula el modelo '
        'de programación lineal entera mixta, diseña el algoritmo genético (representación de la solución, '
        'decodificador y operadores), verifica y valida ambos con instancias reducidas, calibra los '
        'parámetros del algoritmo mediante diseño de experimentos y presenta la programación obtenida para el '
        'caso de estudio.',
        '**Evaluación del modelo propuesto frente al sistema actual (tercer objetivo).** Representa el sistema '
        'de programación actual y lo calibra con su desempeño histórico, define los indicadores de desempeño '
        'y compara ambos sistemas en el caso de estudio y en escenarios de mayor exigencia.']),
    ('p', 'Cada fase se apoya en los resultados de la anterior: la caracterización define los elementos que el '
          'modelo debe representar, y el modelo verificado, validado y calibrado es el que se compara con el '
          'sistema actual. La interpretación de conjunto de los resultados se presenta en el capítulo de '
          'análisis de resultados.'),
]


def insertar_intro_metodologia(documento):
    """Introducción del capítulo de desarrollo metodológico, debajo de su título."""
    import lib_docx as L
    ancla = next((p for p in documento.paragraphs
                  if p.text.strip().upper() == 'DESARROLLO METODOLÓGICO'
                  and p.style.name.startswith('Heading')), None)
    if ancla is None:
        raise ValueError('No se encontró el título DESARROLLO METODOLÓGICO.')
    cuerpo = documento.element.body
    antes = len(cuerpo)
    esc = L.Escritor(documento, {})
    L.escribir(esc, INTRO_METODOLOGIA)
    nuevos = [el for el in list(cuerpo)[antes - 1:] if not el.tag.endswith('sectPr')]
    pos = ancla._p
    for el in nuevos:
        pos.addnext(el)
        pos = el
    return 'Introducción del desarrollo metodológico'
