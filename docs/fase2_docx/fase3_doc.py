# -*- coding: utf-8 -*-
"""
Redacción de la Fase 3 (evaluación del modelo propuesto frente al sistema actual)
para el documento del trabajo de grado. Lee los resultados de fase3/salida_fase3/
(corridas_ag.csv y deterministas.csv) y usa las mismas funciones de
fase3/experimentos_fase3.py, así que las cifras coinciden con informe_fase3.md.
"""
import os
import sys

import pandas as pd

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(RAIZ, 'fase3'))
import experimentos_fase3 as F                                         # noqa: E402

DIR3 = os.path.join(RAIZ, 'fase3', 'salida_fase3')


def n(x, d=1):
    return F._f(x, d)


def _p(p):
    if p is None or p != p:
        return '—'
    return '< 0,0001' if p < 1e-4 else f'{p:.4f}'.replace('.', ',')


def _lista(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' y ' + xs[-1]


def datos(M):
    det = pd.read_csv(os.path.join(DIR3, 'deterministas.csv'))
    ag = pd.read_csv(os.path.join(DIR3, 'corridas_ag.csv'))
    bb = F.B_ACTUAL_BASE
    act = lambda e, B: det[(det.escenario == e) & (det.B == B)
                           & (det.metodo == 'Actual (FIFO por etapa)')].iloc[0]
    regla = lambda e, B, r: det[(det.escenario == e) & (det.B == B) & (det.metodo == f'Regla {r}')].iloc[0]
    grupo = lambda e, B: ag[(ag.escenario == e) & (ag.B == B)]
    # Calibración del número de partes: FIFO por etapa con B = 2..10 (determinista)
    b_orig = M.NUM_SUBLOTES
    calib = []
    for B in range(2, 11):
        r = F.indicadores(M, F.individuo_fifo_por_etapa(M, B))
        calib.append((B, r))
    M.NUM_SUBLOTES = b_orig
    return det, ag, bb, act, regla, grupo, calib


def fase3(M):
    det, ag, bb, act, regla, grupo, calib = datos(M)
    n_ord = len(M.TRABAJOS)
    a = act('base', bb)
    g10, gb = grupo('base', 10), grupo('base', bb)
    edd_b, edd10 = regla('base', bb, 'EDD'), regla('base', 10, 'EDD')
    sens = [B for B in F.B_ACTUAL_SENS if B != bb]

    # --- Calibración de B
    filas_cal = [[str(B), f"{r['tardias']} ({n(r['pct_tardias'], 0)} %)", n(r['suma_T']), n(r['Cmax'])]
                 for B, r in calib]
    pct = {B: r['pct_tardias'] for B, r in calib}

    def _bs(v):
        bs = [B for B in pct if pct[B] == v]
        return f'B = {bs[0]}' if len(bs) == 1 else (f'B = {bs[0]} o {bs[1]}' if len(bs) == 2 else
                                                     f'B = {bs[0]} a {bs[-1]}')
    arriba = min(v for v in pct.values() if v > 45)
    abajo = max(v for v in pct.values() if v < 45)
    txt_rango = f'{n(arriba, 0)} % ({_bs(arriba)}) y {n(abajo, 0)} % ({_bs(abajo)})'

    # --- Indicadores (escenario base)
    IND = [('pct_tardias', '% de órdenes tardías', 1), ('suma_T', 'Tardanza total ΣT_j (h)', 1),
           ('T_max', 'Tardanza máxima T_max (h)', 1), ('suma_E', 'Adelanto total ΣE_j (h)', 1),
           ('Cmax', 'Makespan C_max (h)', 1), ('flujo_medio', 'Tiempo de flujo medio (h)', 1),
           ('ocup_troquelado', 'Ocupación de troquelado (%)', 1),
           ('alistamientos', 'Alistamientos en troquelado', 1)]

    def tabla_comp(g):
        filas, res = [], {}
        for col, nom, d in IND:
            media, desv, ic, mn, mx, p, mej = F._comparar(g, a[col], col)
            cambio = 100.0 * (media - a[col]) / a[col] if a[col] else float('nan')
            res[col] = dict(media=media, ic=ic, mn=mn, mx=mx, p=p, cambio=cambio)
            filas.append([nom, n(a[col], d), f'{n(media, d)} ± {n(ic, d)}', f'{n(mn, d)} – {n(mx, d)}',
                          ('+' if cambio > 0 else '') + n(cambio, 1) + ' %', _p(p)])
        return filas, res

    filas10, r10 = tabla_comp(g10)
    sin_tard = int((g10.suma_T <= 1e-6).sum())
    extra_al = r10['alistamientos']['media'] - a['alistamientos']
    t_al = extra_al * 4.98 / 60

    # --- Descomposición
    pasos = [
        ('Sistema actual: FIFO por etapa', f'B = {bb}', a['pct_tardias'], a['suma_T'], a['Cmax']),
        ('Cambiar solo la regla de prioridad (EDD)', f'B = {bb}', edd_b['pct_tardias'], edd_b['suma_T'], edd_b['Cmax']),
        ('Dividir más con una regla simple (EDD)', 'B̄ = 10', edd10['pct_tardias'], edd10['suma_T'], edd10['Cmax']),
        ('Optimizar con la misma división (AG, media)', f'B = {bb}', gb.pct_tardias.mean(), gb.suma_T.mean(), gb.Cmax.mean()),
        ('Dividir más y optimizar (AG, media)', 'B̄ = 10', g10.pct_tardias.mean(), g10.suma_T.mean(), g10.Cmax.mean()),
    ]
    filas_desc = [[p, b, n(t, 1) + ' %', n(s, 1), n(c, 1)] for p, b, t, s, c in pasos]

    # --- Sensibilidad al número de partes del sistema actual
    filas_sens = []
    for B in F.B_ACTUAL_SENS:
        x = act('base', B)
        gB = grupo('base', B)
        filas_sens.append([f'B = {B}', f"{n(x.pct_tardias, 0)} % / {n(x.suma_T)}",
                           f"{n(gB.pct_tardias.mean(), 0)} % / {n(gB.suma_T.mean())}" if not gB.empty else '—',
                           f"{n(g10.pct_tardias.mean(), 0)} % / {n(g10.suma_T.mean())}"])
    act_rng = [act('base', B).pct_tardias for B in F.B_ACTUAL_SENS]

    # --- Escenarios de exigencia
    filas_ex, mej_ex, ps_ex = [], [], []
    for e in F.ESCENARIOS:
        x, g = act(e, bb), grupo(e, 10)
        if g.empty:
            continue
        media, desv, ic, mn, mx, p, mej = F._comparar(g, x['suma_T'], 'suma_T')
        filas_ex.append([F.DESCRIPCION[e], f"{n(x.pct_tardias, 0)} % / {n(x.suma_T)}",
                         f"{n(g.pct_tardias.mean(), 0)} % / {n(media)}", n(mej, 1) + ' %', _p(p)])
        if e != 'base':
            mej_ex.append(mej)
            ps_ex.append(p)

    nrep_b, nrep_s = len(g10), len(grupo(list(F.ESCENARIOS)[1], 10))
    sem_b = f"{min(F.SEM_BASE)} a {max(F.SEM_BASE)}"
    sem_s = f"{min(F.SEM_SENS)} a {max(F.SEM_SENS)}"

    return [
        ('h2', 'Evaluación del modelo propuesto frente al sistema actual'),
        ('p', 'Esta fase da cumplimiento al tercer objetivo específico: evaluar la calidad de las '
              'soluciones del modelo propuesto mediante indicadores de desempeño, comparándolas con el '
              'sistema de programación actual de la empresa. Para ello se representa el sistema actual, '
              'se calibra con su desempeño histórico y se compara con el algoritmo genético en el caso '
              'de estudio y en escenarios de mayor exigencia.'),

        ('h3', 'Representación del sistema actual'),
        ('p', 'De la programación actual se conoce la regla de prioridad, pues las órdenes se atienden '
              'en el orden en que llegan, y su desempeño: según los registros históricos, cerca del 45 % '
              'de las órdenes se entrega después de la fecha pactada. No se conoce, en cambio, en '
              'cuántas partes se divide cada orden para pasar de una etapa a otra. Ante esta situación '
              'se aplica un procedimiento usual en simulación: construir un modelo del sistema con lo que '
              'se sabe y calibrar lo que no se sabe con el dato histórico, comprobando después que la '
              'conclusión no dependa del valor elegido (Sargent, 2013; Law, 2015).'),
        ('p', 'El sistema actual se representa con la regla FIFO por etapa: en troquelado las órdenes se '
              'atienden por orden de liberación y, en cada etapa siguiente, los sublotes se atienden en '
              'el orden en que llegan de la etapa anterior. Cada orden se divide en B partes iguales y '
              'cada parte se asigna a la máquina que la termina más temprano. Se usan el mismo '
              'decodificador, los mismos tiempos estándar y los mismos alistamientos que en el modelo '
              'propuesto, de modo que la comparación solo refleja la forma de programar.'),
        ('p', 'La Tabla {T:calib} muestra el desempeño de esta representación según el número de '
              f'partes B. Con {n_ord} órdenes, el porcentaje de órdenes tardías solo varía de 10 en 10 '
              f'puntos, y el 45 % histórico queda entre {txt_rango}. Se adopta B = {bb}, el menor número de partes con '
              'el porcentaje más cercano al histórico; elegir el menor es la opción conservadora, pues no le '
              'atribuye al sistema actual más división de la necesaria. Como el valor es una '
              f"representación calibrada y no una observación directa, la comparación se repite con B = "
              f"{_lista([str(B) for B in sens])}."),
        ('tabla', 'Calibración de la representación del sistema actual: FIFO por etapa con B partes '
                  'iguales por orden', ['B', 'Órdenes tardías', 'ΣT_j (h)', 'C_max (h)'], filas_cal,
         {'etiqueta': 'calib', 'anchos': [1200, 2600, 2400, 2600], 'negrita_filas': (bb - 2,)}),

        ('h3', 'Indicadores de desempeño'),
        ('p', 'La comparación usa los indicadores de la Tabla {T:ind}. El porcentaje de órdenes tardías '
              'se compara directamente con el 45 % histórico, y la tardanza total es el objetivo del '
              'modelo; los demás indicadores permiten ver qué se gana y qué se cede con la programación '
              'propuesta.'),
        ('tabla', 'Indicadores de desempeño', ['Indicador', 'Definición', 'Unidad'], [
            ['Órdenes tardías', r'$100\cdot\frac{1}{n}\sum_j \delta_j$, con $\delta_j=1$ si $T_j>0$', '%'],
            ['Tardanza total', r'$\sum_j T_j = \sum_j \max(0,\,C_j-d_j)$', 'h'],
            ['Tardanza máxima', r'$T_{\max}=\max_j T_j$', 'h'],
            ['Adelanto total', r'$\sum_j E_j = \sum_j \max(0,\,d_j-C_j)$', 'h'],
            ['Makespan', r'$C_{\max}=\max_j C_j$', 'h'],
            ['Tiempo de flujo medio', r'$\frac{1}{n}\sum_j (C_j-r_j)$', 'h'],
            ['Ocupación de troquelado', 'Tiempo de proceso de la etapa / (máquinas × makespan)', '%'],
            ['Alistamientos en troquelado', 'Número de cambios de referencia en las máquinas de troquelado', '—']],
         {'etiqueta': 'ind', 'anchos': [2400, 5338, 1100], 'alineacion': ['l', 'l', 'c']}),

        ('h3', 'Diseño de la comparación'),
        ('p', f'El sistema actual es determinista: con los mismos datos siempre produce la misma '
              f'programación. El algoritmo genético, con los parámetros calibrados en la Fase 2, es '
              f'aleatorio, por lo que en el caso de estudio se ejecutó {nrep_b} veces (semillas {sem_b}) '
              f'con B̄ = 10 y otras {len(gb)} con B = {bb}, la misma división del sistema actual, para '
              'separar el efecto de optimizar del efecto de dividir más. Para cada indicador se reportan '
              'la media, el intervalo de confianza del 95 %, el mínimo y el máximo de las réplicas, y el '
              'cambio porcentual frente al sistema actual. La diferencia se evaluó con la prueba de '
              'rangos con signo de Wilcoxon de una muestra (Wilcoxon, 1945), que compara la mediana de '
              'las réplicas con el valor del sistema actual sin suponer normalidad.'),
        ('p', f'La sensibilidad se analizó en dos frentes, con {nrep_s} réplicas por caso (semillas {sem_s}): '
              f'el número de partes del sistema actual (B = {_lista([str(B) for B in F.B_ACTUAL_SENS])}) y '
              'cuatro escenarios de mayor exigencia: fechas de entrega 10 % y 20 % más ajustadas (se reduce '
              r'la ventana $d_j-r_j$) y demanda 10 % y 20 % mayor. Las semillas son distintas de las usadas '
              'en la Fase 2.'),

        ('h3', 'Resultados en el escenario base'),
        ('p', f'La Tabla {{T:base}} compara el sistema actual (B = {bb}) con el algoritmo genético '
              f'(B̄ = 10). En {sin_tard} de las {nrep_b} réplicas el algoritmo entregó todas las órdenes a '
              f"tiempo; en promedio, el porcentaje de órdenes tardías bajó de {n(a.pct_tardias, 0)} % a "
              f"{n(r10['pct_tardias']['media'], 1)} % y la tardanza total de {n(a.suma_T)} h a "
              f"{n(r10['suma_T']['media'])} h ({n(-r10['suma_T']['cambio'], 1)} % menos). También mejoraron "
              f"el makespan ({n(-r10['Cmax']['cambio'], 1)} % menos) y el tiempo de flujo medio "
              f"({n(-r10['flujo_medio']['cambio'], 1)} % menos), y el adelanto total se redujo en "
              f"{n(-r10['suma_E']['cambio'], 1)} %, lo que indica que las órdenes se terminan más cerca de "
              'su fecha de entrega. Todas las diferencias son significativas (Wilcoxon, p < 0,05).'),
        ('tabla', f'Sistema actual (B = {bb}) frente al algoritmo genético con B̄ = 10 en el caso de estudio '
                  f'({nrep_b} réplicas)',
         ['Indicador', 'Sistema actual', 'AG: media ± IC 95 %', 'AG: mín. – máx.', 'Cambio', 'Valor p'],
         filas10, {'etiqueta': 'base', 'anchos': [2500, 1150, 1750, 1500, 1000, 938], 'tam': 9,
                   'alineacion': ['l'] + ['c'] * 5}),
        ('p', 'La mejora tiene un costo en troquelado: el algoritmo intercala más referencias en las '
              f"máquinas, lo que eleva los alistamientos de {n(a.alistamientos, 0)} a "
              f"{n(r10['alistamientos']['media'], 1)} en promedio y la ocupación de la etapa de "
              f"{n(a.ocup_troquelado)} % a {n(r10['ocup_troquelado']['media'])} %. Como cada alistamiento "
              f'toma 4,98 minutos, los alistamientos adicionales suman cerca de {n(t_al, 1)} horas, poco '
              'frente a la reducción de la tardanza. La Figura {F:cajas} muestra la distribución de las '
              'réplicas frente al sistema actual.'),
        ('figura', f'Tardanza total y porcentaje de órdenes tardías de las réplicas del algoritmo genético '
                   f'frente al sistema actual (línea punteada)', os.path.join(DIR3, 'comparacion_base.png'),
         15.5, 'cajas'),

        ('h4', 'Descomposición de la mejora'),
        ('p', 'La comparación anterior mezcla tres cambios: la regla de prioridad, el número de sublotes y '
              'la optimización. La Tabla {T:desc} los separa aplicándolos uno a uno.'),
        ('tabla', 'Descomposición de la mejora en el caso de estudio',
         ['Paso', 'Sublotes', 'Órdenes tardías', 'ΣT_j (h)', 'C_max (h)'], filas_desc,
         {'etiqueta': 'desc', 'anchos': [3900, 1100, 1300, 1200, 1338], 'tam': 9,
          'alineacion': ['l', 'c', 'c', 'c', 'c']}),
        ('viñetas', [
            f"**Cambiar solo la regla no basta:** con la regla EDD y la misma división, la tardanza total "
            f"casi no cambia ({n(edd_b.suma_T)} h frente a {n(a.suma_T)} h) y las órdenes tardías pasan de "
            f"{n(a.pct_tardias, 0)} % a {n(edd_b.pct_tardias, 0)} %.",
            f"**Dividir más y optimizar aportan por separado:** dividir en 10 sublotes con la regla EDD "
            f"lleva la tardanza a {n(edd10.suma_T)} h, y optimizar con el algoritmo sin cambiar la división "
            f"la lleva a {n(gb.suma_T.mean())} h en promedio.",
            f"**La combinación es la que casi elimina la tardanza:** el algoritmo con B̄ = 10 la reduce a "
            f"{n(g10.suma_T.mean())} h en promedio. Con el límite de 10 sublotes por orden, la mejor regla "
            f"de despacho deja {n(edd10.suma_T)} h de tardanza y {n(edd10.tardias, 0)} órdenes tardías, por lo "
            'que el algoritmo genético sí es necesario para alcanzar ese resultado.']),

        ('h3', 'Análisis de sensibilidad'),
        ('p', f'La Tabla {{T:sens}} repite la comparación con B = {_lista([str(B) for B in F.B_ACTUAL_SENS])} '
              f'partes en el sistema actual. Su porcentaje de órdenes tardías varía entre '
              f'{n(min(act_rng), 0)} % y {n(max(act_rng), 0)} %, mientras que el algoritmo con B̄ = 10 '
              f'se mantiene en {n(g10.pct_tardias.mean(), 1)} %. La ventaja del modelo propuesto, por tanto, '
              'no depende del número de partes elegido para representar el sistema actual. Con la misma '
              'división del sistema actual, el algoritmo también reduce la tardanza en todos los casos.'),
        ('tabla', 'Sensibilidad al número de partes del sistema actual (órdenes tardías / tardanza total en horas)',
         ['Sistema actual', 'Actual', 'AG con la misma B (media)', 'AG con B̄ = 10 (media)'], filas_sens,
         {'etiqueta': 'sens', 'anchos': [1900, 2200, 2400, 2338]}),
        ('p', 'La Tabla {T:exig} presenta los escenarios de mayor exigencia. Con fechas más ajustadas o más '
              'demanda, el algoritmo ya no logra evitar toda la tardanza, pero la reduce entre '
              f'{n(min(mej_ex), 0)} % y {n(max(mej_ex), 0)} % frente al sistema actual, con diferencias '
              f"significativas (Wilcoxon, p ≤ {_p(max(ps_ex))}). El valor p de 0,002 es el menor posible "
              f'con {nrep_s} réplicas.'),
        ('tabla', f'Escenarios de exigencia: sistema actual (B = {bb}) frente al algoritmo genético '
                  f'(B̄ = 10; órdenes tardías / tardanza total en horas)',
         ['Escenario', 'Sistema actual', 'AG (media)', 'Reducción de la tardanza', 'Valor p'], filas_ex,
         {'etiqueta': 'exig', 'anchos': [3100, 1700, 1700, 1300, 1038], 'tam': 9,
          'alineacion': ['l', 'c', 'c', 'c', 'c']}),

        ('h3', 'Discusión'),
        ('p', 'Los resultados indican que la programación propuesta mejora de forma clara el cumplimiento '
              f"de las entregas: en el caso de estudio pasa de {n(a.pct_tardias, 0)} % de órdenes tardías "
              f"con el sistema actual a {n(g10.pct_tardias.mean(), 1)} % en promedio, sin empeorar el "
              'makespan ni el tiempo de flujo. La mejora se explica por la combinación de dividir las '
              'órdenes en sublotes consistentes de tamaño variable y decidir con el algoritmo el tamaño de '
              'esos sublotes y su secuencia en cada etapa; ninguno de los dos cambios por separado alcanza '
              'el mismo resultado.'),
        ('p', '**Limitaciones.** El sistema actual se representa con un modelo calibrado con la tasa '
              'histórica de incumplimiento, no con una observación directa de cómo se dividen las órdenes; '
              'el análisis de sensibilidad muestra que la conclusión se mantiene en el rango plausible. '
              f'La evaluación usa un conjunto de {n_ord} órdenes, tiempos estándar deterministas y no '
              'considera tiempos de transporte entre etapas, ausencias ni fallas de máquinas, por lo que '
              'el desempeño en planta puede diferir del calculado. Además, el algoritmo aumenta el número '
              'de alistamientos en troquelado, aspecto que la empresa debe considerar al programar.'),
        ('p', '**Recomendaciones para la empresa.** (i) Probar la programación propuesta en un periodo '
              'piloto, comparando las fechas reales de terminación con las programadas; (ii) registrar en '
              'cuántas partes se divide cada orden y cuándo termina cada parte, para validar la '
              'representación del sistema actual; (iii) mantener el límite de 10 sublotes por orden y '
              'definir el tamaño de los sublotes con el modelo; y (iv) programar los cambios de referencia '
              'en troquelado considerando el aumento de alistamientos.'),
        ('p', 'En síntesis, frente al sistema de programación actual, el modelo propuesto reduce la tardanza '
              f"total en {n(-r10['suma_T']['cambio'], 1)} % en el caso de estudio y entre "
              f'{n(min(mej_ex), 0)} % y {n(max(mej_ex), 0)} % en los escenarios de mayor exigencia, lo que '
              'cumple el tercer objetivo específico.'),
    ]
