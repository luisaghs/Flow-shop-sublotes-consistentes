# -*- coding: utf-8 -*-
"""
Capítulos finales del trabajo de grado: análisis de resultados, conclusiones y
recomendaciones. Las cifras se calculan con el modelo, la base de datos y los
resultados guardados de las Fases 2 y 3, de modo que coinciden con las tablas de
esos capítulos.
"""
import json
import os

import pandas as pd

import fase3_doc as F3
from correcciones_fase1 import cargas

F = F3.F
n = F3.n
_lista = F3._lista
_NUM = {2: 'dos', 3: 'tres', 4: 'cuatro', 5: 'cinco', 6: 'seis', 7: 'siete', 8: 'ocho', 9: 'nueve'}


def _contexto(M, ruta_bd, indic, rep, D, val_info):
    det, ag, bb, act, regla, grupo, calib = F3.datos(M)
    a = act('base', bb)
    g10 = grupo('base', 10)
    gb = grupo('base', bb)
    edd10 = regla('base', 10, 'EDD')
    # Sistema actual, orden por orden
    ind_a = F.individuo_fifo_por_etapa(M, bb)
    Ca, ga = M.simular_hfs(ind_a)
    ra = M.calcular_indicadores(Ca)
    M.NUM_SUBLOTES = 10
    ini_a = {}
    for (j, b, m, i, f) in ga[M.ETAPAS[0]]:
        ini_a[j] = min(ini_a.get(j, 1e18), i)
    # Carga de troquelado frente al horizonte en cada escenario
    filas_c, total, horizonte, _ = cargas(ruta_bd)
    troq = filas_c[0]
    base = {'DUE_DATE': dict(M.DUE_DATE), 'DEMANDA': dict(M.DEMANDA)}
    carga_esc = {}
    for e in F.ESCENARIOS:
        F.aplicar_escenario(M, base, e)
        h = max(M.DUE_DATE.values())
        q = sum(M.DEMANDA.values())
        carga_esc[e] = 100.0 * troq[3] * q / total / h
    F.aplicar_escenario(M, base, 'base')
    # Calibración
    dec = json.load(open(os.path.join(F3.RAIZ, 'fase2', 'salida_calibracion', 'decisiones.json'),
                         encoding='utf-8'))
    return dict(det=det, ag=ag, bb=bb, a=a, g10=g10, gb=gb, edd10=edd10, ra=ra, ini_a=ini_a,
                troq=troq, carga_esc=carga_esc, dec=dec, indic=indic, rep=rep, D=D, val=val_info,
                ocup={f[0]: f[4] for f in filas_c}, n_maq={f[0]: f[1] for f in filas_c})


def capitulos(M, ruta_bd, indic, rep, D, val_info):
    c = _contexto(M, ruta_bd, indic, rep, D, val_info)
    a, g10, gb, bb, ra, ip = c['a'], c['g10'], c['gb'], c['bb'], c['ra'], indic
    J = list(M.TRABAJOS)
    n_ord = len(J)
    P = M.GA_PARAMS

    # --- Tabla por orden
    filas_ord = []
    for j in J:
        pa, pp = ra['por_trabajo'][j], ip['por_trabajo'][j]
        filas_ord.append([j, n(M.RELEASE[j], 0), n(M.DUE_DATE[j], 0), n(c['ini_a'][j]), n(pa['Ci']),
                          n(pa['Ti']), n(pp['Ci']), n(M.DUE_DATE[j] - pp['Ci'])])
    tard_a = [j for j in J if ra['por_trabajo'][j]['Ti'] > 1e-9]
    imposibles = [j for j in tard_a if c['ini_a'][j] >= M.DUE_DATE[j]]
    muy_temprano = max(J, key=lambda j: ra['por_trabajo'][j]['Ei'])
    holg = {j: M.DUE_DATE[j] - ip['por_trabajo'][j]['Ci'] for j in J}
    jmin = min(holg, key=holg.get)
    holg_ord = sorted(holg.values())
    pocas = [j for j in J if holg[j] < 25]

    # --- Validación y calibración
    v = c['val']
    con_opt = [i for i in v if i['opt']]
    hits = sum(i['hits'] for i in con_opt)
    reps_v = sum(i['reps'] for i in con_opt)
    sin_f1 = [i for i in v if i['f1_sin']]
    est = c['dec']['instancias']['real']
    sig_kw = [{'poblacion': 'el tamaño de la población', 'prob_cruce': 'la probabilidad de cruce',
               'prob_mutacion': 'la probabilidad de mutación'}[f]
              for f, p in est['p_kruskal'].items() if p < 0.05]
    reps_cero = int((c['rep']['suma_T'] <= 1e-6).sum())
    t_corr = c['rep']['segundos'].mean() / 60

    # --- Fase 3
    al_extra = g10.alistamientos.mean() - a.alistamientos
    exig = {e: c['carga_esc'][e] for e in F.ESCENARIOS if e != 'base'}
    mej_ex = []
    for e in F.ESCENARIOS:
        if e == 'base':
            continue
        x = c['det'][(c['det'].escenario == e) & (c['det'].B == bb)
                     & (c['det'].metodo == 'Actual (FIFO por etapa)')].iloc[0]
        g = c['ag'][(c['ag'].escenario == e) & (c['ag'].B == 10)]
        mej_ex.append(100.0 * (x.suma_T - g.suma_T.mean()) / x.suma_T)
    red_T = 100.0 * (a.suma_T - g10.suma_T.mean()) / a.suma_T
    red_C = 100.0 * (a.Cmax - g10.Cmax.mean()) / a.Cmax
    red_F = 100.0 * (a.flujo_medio - g10.flujo_medio.mean()) / a.flujo_medio
    acts = [c['det'][(c['det'].escenario == 'base') & (c['det'].B == B)
                     & (c['det'].metodo == 'Actual (FIFO por etapa)')].iloc[0].pct_tardias
            for B in F.B_ACTUAL_SENS]
    T_regla = c['D']['regla_T']
    maq = c['n_maq']

    analisis = [
        ('h1', 'ANÁLISIS DE RESULTADOS'),
        ('p', 'Este capítulo interpreta los resultados de las tres fases del desarrollo metodológico: '
              'valora el cumplimiento de cada objetivo, explica por qué la programación propuesta mejora '
              'el cumplimiento de las entregas, identifica lo que se cede a cambio, analiza los límites del '
              'modelo y contrasta los hallazgos con la literatura.'),

        ('h2', 'Cumplimiento de los objetivos'),
        ('p', f"**Caracterización del sistema.** La primera fase describió un Flow Shop híbrido de cuatro "
              f"etapas con {maq['Troquelado']}, {maq['Ensamble']}, {maq['Costura']} y {maq['Volteado']} "
              'máquinas, máquinas no relacionadas en ensamble y alistamientos dependientes de la secuencia en '
              f"troquelado. El análisis de carga identificó a troquelado como la etapa más exigida "
              f"({n(c['ocup']['Troquelado'], 0)} % de ocupación en el horizonte), con holgura en las demás. "
              'Esta caracterización definió los elementos del modelo: las liberaciones, las fechas de '
              'entrega, el alistamiento en troquelado y la división en sublotes consistentes.'),
        ('p', f"**Modelo y algoritmo.** El modelo matemático representó correctamente el sistema: sus "
              'soluciones cumplieron todas las restricciones y dos formulaciones independientes coincidieron '
              f"en el óptimo. El algoritmo genético alcanzó la tardanza óptima en las {_NUM.get(len(con_opt), len(con_opt))} "
              f"instancias reducidas con óptimo conocido ({hits} de {reps_v} réplicas), mientras que el "
              f"método exacto no encontró soluciones a partir de {min(i['sub'] for i in sin_f1)} sublotes. "
              'La calibración mostró que '
              + (_lista(sig_kw) if sig_kw else 'ningún parámetro')
              + f" {'influye' if len(sig_kw) == 1 else 'influyen'} de forma significativa en la calidad de las "
              f"soluciones. Con los parámetros calibrados, {reps_cero} de {len(c['rep'])} réplicas eliminaron "
              f"la tardanza del caso de estudio, frente a {n(T_regla)} h de la mejor regla de despacho."),
        ('p', f"**Comparación con el sistema actual.** La representación del sistema actual, calibrada con "
              f"el 45 % histórico de incumplimiento, produjo {n(a.pct_tardias, 0)} % de órdenes tardías; "
              f"el modelo propuesto lo redujo a {n(g10.pct_tardias.mean(), 1)} % en promedio, con una "
              f"reducción de la tardanza total de {n(red_T, 1)} %, y mejoró además el makespan y el tiempo "
              'de flujo. Los tres objetivos específicos se cumplieron y, con ellos, el objetivo general.'),

        ('h2', 'Por qué mejora la programación propuesta'),
        ('p', 'La Tabla {T:orden_comp} compara, orden por orden, el sistema actual con la programación '
              'propuesta. El sistema actual atiende las órdenes por orden de llegada, sin considerar su '
              f"fecha de entrega: {muy_temprano} termina a las {n(ra['por_trabajo'][muy_temprano]['Ci'])} h, "
              f"{n(ra['por_trabajo'][muy_temprano]['Ei'])} h antes de lo necesario, mientras que "
              + _lista([f"{j} (entrega a las {n(M.DUE_DATE[j], 0)} h) empieza troquelado a las "
                        f"{n(c['ini_a'][j])} h" for j in sorted(tard_a, key=lambda j: M.DUE_DATE[j])[:2]])
              + '. '
              + (f"En el caso de {_lista(imposibles)}, el troquelado comienza después de la fecha de entrega, "
                 'así que la orden ya no puede cumplirse. ' if imposibles else '')
              + 'El problema del sistema actual no es la falta de capacidad, sino la prioridad con que se '
              'usa.'),
        ('tabla', f'Inicio en troquelado, terminación y tardanza por orden: sistema actual (B = {bb}) frente '
                  'a la programación propuesta (horas)',
         ['Orden', 'r_j', 'd_j', 'Actual: inicio troquelado', 'Actual: C_j', 'Actual: T_j',
          'Propuesta: C_j', 'Propuesta: holgura d_j − C_j'], filas_ord,
         {'etiqueta': 'orden_comp', 'anchos': [800, 700, 700, 1350, 1100, 1100, 1250, 1838], 'tam': 9}),
        ('p', 'La Figura {F:comp} representa la misma comparación: para cada orden, el punto naranja es su '
              'terminación con el sistema actual, el azul su terminación con la programación propuesta y la '
              'línea negra su fecha de entrega. Con el sistema actual, '
              + _lista([f"{j}" for j in sorted(tard_a, key=lambda j: M.DUE_DATE[j])])
              + ' quedan a la derecha de su fecha de entrega; con la programación propuesta, '
              + ('todas las órdenes quedan a la izquierda.' if ip['suma_Ti'] <= 1e-6 else
                 'la mayoría quedan a la izquierda.')),
        ('figura', 'Terminación de cada orden con el sistema actual y con la programación propuesta, frente '
                   'a su fecha de entrega',
         os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figuras', 'comparacion_ordenes.png'),
         15.0, 'comp'),
        ('p', 'La programación propuesta, en cambio, adelanta las órdenes con entregas cercanas y retrasa '
              f"las que tienen holgura: todas terminan a tiempo, con márgenes entre {n(holg_ord[0])} h "
              f"({jmin}) y {n(holg_ord[-1])} h. A esto se suma el efecto de los sublotes: al dividir cada "
              'orden, sus partes avanzan a la etapa siguiente sin esperar a que termine la orden completa y '
              'se reparten entre las máquinas paralelas. La descomposición de la Fase 3 (Tabla {T:desc}) '
              'confirma que ninguno de los dos mecanismos basta por separado: dividir con una regla simple '
              f"deja {n(c['edd10'].suma_T)} h de tardanza y optimizar sin dividir más deja "
              f"{n(gb.suma_T.mean())} h; solo su combinación casi elimina la tardanza."),

        ('h2', 'Qué se cede a cambio'),
        ('p', 'La programación propuesta intercala más referencias en troquelado: los alistamientos '
              f"aumentan en {n(al_extra, 1)} en promedio (cerca de {n(al_extra * 4.98 / 60, 1)} h) y la "
              f"ocupación de la etapa pasa de {n(a.ocup_troquelado)} % a {n(g10.ocup_troquelado.mean())} %. "
              'Es un costo bajo frente a la reducción de la tardanza, pero recae en la etapa que la Fase 1 '
              'identificó como la más cargada. Además, al terminar las órdenes más cerca de su fecha, '
              + (f"algunas quedan con poco margen ({_lista([f'{j}, {n(holg[j])} h' for j in pocas])}), "
                 if pocas else 'el margen de cada orden se reduce, ')
              + 'lo que las hace más sensibles a fallas de máquinas o ausencias no previstas en el modelo.'),
        ('p', f"El caso del algoritmo con B = {bb} ilustra la prioridad del objetivo: con la misma división "
              'del sistema actual reduce la tardanza, pero alarga el makespan '
              f"({n(gb.Cmax.mean())} h frente a {n(a.Cmax)} h), porque retrasa órdenes con holgura para "
              'entregar a tiempo las urgentes. Con 10 sublotes por orden esta tensión desaparece y mejoran '
              'ambos indicadores.'),

        ('h2', 'Robustez y límites del modelo'),
        ('p', 'La ventaja del modelo propuesto no depende del número de partes asumido para el sistema '
              f"actual: con B = {_lista([str(B) for B in F.B_ACTUAL_SENS])}, el sistema actual tiene entre "
              f"{n(min(acts), 0)} % y {n(max(acts), 0)} % de órdenes tardías y el algoritmo se mantiene en "
              f"{n(g10.pct_tardias.mean(), 1)} %. En los escenarios de mayor exigencia el algoritmo ya no "
              f"evita toda la tardanza, aunque la reduce entre {n(min(mej_ex), 0)} % y {n(max(mej_ex), 0)} %. "
              'La tardanza residual se explica por la capacidad: con las fechas 20 % más ajustadas, el '
              f"troquelado necesitaría el {n(exig['fechas_-20'], 0)} % del horizonte, y con 20 % más de demanda "
              f"el {n(exig['demanda_+20'], 0)} %, sin contar los alistamientos. En esas condiciones el límite "
              'deja de ser la programación y pasa a ser la capacidad de troquelado.'),

        ('h2', 'Contraste con la literatura'),
        ('p', 'Los resultados son coherentes con Gürsoy Yılmaz y Yılmaz (2022), quienes encontraron que los '
              'sublotes consistentes superan a los sublotes iguales y que el número de sublotes influye de '
              'forma significativa en la calidad de las soluciones de un Flow Shop híbrido. En este trabajo, '
              'pasar de partes iguales a sublotes consistentes de tamaño optimizado redujo la tardanza total '
              f"en {n(red_T, 1)} % y el makespan en {n(red_C, 1)} %, y la tardanza bajó a medida que aumentó el "
              'número de sublotes (Tabla {T:bbar} y Tabla {T:sens}). A diferencia de ese estudio, centrado en '
              'el makespan, aquí el objetivo fue la tardanza total, en línea con el giro de la literatura hacia '
              'el cumplimiento de las fechas de entrega en entornos bajo pedido (Li et al., 2020). El buen '
              'desempeño del algoritmo genético en las instancias de validación respalda que sea el método de '
              'solución más usado en este tipo de problemas (Soon y Loong, 2019).'),

        ('h2', 'Validez y limitaciones'),
        ('viñetas', [
            '**Representación del sistema actual.** Se calibró con la tasa histórica de incumplimiento, no '
            'con una observación directa de cómo se dividen las órdenes; el análisis de sensibilidad '
            'muestra que la conclusión se mantiene en el rango plausible.',
            f"**Alcance de la instancia.** La evaluación usa un conjunto de {n_ord} órdenes; el 45 % "
            'histórico es una tasa de largo plazo, mientras que la instancia representa un periodo de '
            'planeación.',
            '**Supuestos del modelo.** Tiempos estándar deterministas, sin tiempos de transporte entre '
            'etapas, ausencias ni fallas de máquinas, y alistamiento solo en troquelado. El desempeño en '
            'planta puede diferir del calculado.',
            '**Límite de sublotes.** No se evaluaron más de 10 sublotes por orden por la complejidad '
            'logística y de control que implicarían en la planta.']),

        ('h2', 'Implicaciones para la empresa'),
        ('p', f"El algoritmo obtiene una programación en {n(t_corr, 0)} minutos en promedio en un computador "
              'personal, un tiempo compatible con una programación semanal o con la reprogramación cuando '
              'llega una orden nueva. Requiere datos que la empresa ya maneja: las órdenes con su cantidad, '
              'fecha de liberación y fecha de entrega, los tiempos estándar y el calendario laboral. Su uso '
              'cambiaría la forma de programar en dos aspectos: las órdenes se priorizarían según su fecha '
              'de entrega y no solo por su orden de llegada, y el tamaño de los paquetes que pasan entre '
              'etapas lo definiría el modelo, con un máximo de 10 por orden.'),
    ]

    conclusiones = [
        ('h1', 'CONCLUSIONES'),
        ('numerada', [
            f"El sistema productivo de la empresa es un Flow Shop híbrido de cuatro etapas con máquinas "
            f"paralelas, máquinas no relacionadas en ensamble y alistamientos en troquelado. Troquelado es la "
            f"etapa más exigida ({n(c['ocup']['Troquelado'], 0)} % de ocupación en el horizonte), por lo que "
            'concentra el efecto de las decisiones de programación.',
            'Se formuló un modelo de programación lineal entera mixta con sublotes consistentes, fechas de '
            'liberación, alistamientos y minimización de la tardanza total, y se diseñó un algoritmo genético '
            'con un cromosoma de dos niveles (tamaños de sublote y secuencias por etapa) y un decodificador '
            'que construye programaciones factibles.',
            f"El algoritmo genético alcanzó la tardanza óptima en todas las instancias reducidas con óptimo "
            f"conocido, mientras que el método exacto dejó de encontrar soluciones a partir de "
            f"{min(i['sub'] for i in sin_f1)} sublotes; el algoritmo es, por tanto, el método adecuado para "
            'el tamaño real del problema.',
            f"La calibración estadística fijó una población de {P['poblacion']}, una probabilidad de cruce de "
            f"{n(P['prob_cruce'], 1)}, una probabilidad de mutación de {n(P['prob_mutacion'], 1)} y un criterio "
            f"de parada de {P['sin_mejora']} generaciones sin mejora. Con esta configuración, el algoritmo "
            f"entrega a tiempo todas las órdenes del caso de estudio en {reps_cero} de {len(c['rep'])} "
            'réplicas.',
            f"Frente al sistema de programación actual, el modelo propuesto reduce las órdenes tardías de "
            f"{n(a.pct_tardias, 0)} % a {n(g10.pct_tardias.mean(), 1)} % en promedio y la tardanza total en "
            f"{n(red_T, 1)} %, y reduce además el makespan en {n(red_C, 1)} % y el tiempo de flujo medio en "
            f"{n(red_F, 1)} %, a cambio de un aumento moderado de los alistamientos en troquelado.",
            'La mejora proviene de combinar la priorización de las órdenes según su fecha de entrega con la '
            'división en sublotes consistentes de tamaño optimizado. Cambiar solo la regla de prioridad casi '
            'no reduce la tardanza, y con el límite de 10 sublotes ninguna regla de despacho alcanza el '
            'resultado del algoritmo.',
            f"La ventaja se mantiene para distintos supuestos sobre el sistema actual y en escenarios de mayor "
            f"exigencia, donde la tardanza se reduce entre {n(min(mej_ex), 0)} % y {n(max(mej_ex), 0)} %. "
            'Cuando la carga de troquelado se acerca a su capacidad, la tardanza residual depende más de la '
            'capacidad que de la programación.',
            'En respuesta a la pregunta de investigación, un algoritmo genético con sublotes consistentes, '
            'aplicado a la programación del Flow Shop híbrido de la empresa, permite minimizar la tardanza '
            'total y prácticamente eliminar el incumplimiento de las fechas de entrega en el caso de estudio.']),
    ]

    recomendaciones = [
        ('h1', 'RECOMENDACIONES'),
        ('h2', 'Para la empresa'),
        ('viñetas', [
            '**Prueba piloto.** Usar la programación propuesta durante un periodo de prueba y comparar las '
            'fechas reales de terminación con las programadas, para confirmar en planta los resultados.',
            '**Registro de datos.** Registrar en cuántas partes se divide cada orden y cuándo termina cada '
            'parte en cada etapa; estos datos permiten validar la representación del sistema actual y '
            'actualizar los tiempos estándar.',
            '**Tamaño de los sublotes.** Definir los paquetes que pasan entre etapas con el modelo, con un '
            'máximo de 10 por orden, y establecer cómo se identifican y controlan en la planta.',
            '**Troquelado.** Planear los cambios de referencia considerando el aumento de alistamientos y '
            'vigilar la carga de la etapa: si se acerca a su capacidad, evaluar horas extra, un turno '
            'adicional o la redistribución de la demanda antes de comprometer fechas de entrega.',
            '**Margen frente a imprevistos.** Cuando una orden quede con poca holgura, considerar un margen '
            'de seguridad o reprogramar con el modelo ante fallas o ausencias.',
            '**Uso periódico.** Ejecutar el modelo en cada ciclo de planeación y cada vez que ingrese una '
            'orden urgente, y capacitar a la persona responsable de la programación en su uso.']),
        ('h2', 'Para trabajos futuros'),
        ('viñetas', [
            'Incorporar tiempos de proceso variables, fallas de máquinas y ausencias mediante simulación o '
            'programación estocástica, y evaluar la robustez de la programación.',
            'Considerar la llegada dinámica de órdenes y la reprogramación en un horizonte rodante.',
            'Plantear un enfoque multiobjetivo que considere a la vez la tardanza, los alistamientos y el '
            'número de sublotes.',
            'Incluir tiempos de transporte entre etapas y alistamientos en otras etapas si la operación lo '
            'requiere.',
            'Comparar el algoritmo genético con otras metaheurísticas y evaluarlo con más órdenes y otros '
            'periodos de planeación.',
            'Desarrollar una herramienta de uso sencillo (por ejemplo, una interfaz en hoja de cálculo) que '
            'facilite su adopción en la empresa.']),
    ]
    return analisis + conclusiones + recomendaciones
