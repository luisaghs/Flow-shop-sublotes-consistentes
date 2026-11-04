# -*- coding: utf-8 -*-
"""
Versión sintetizada de la Fase 2 (enfoque de ingeniería industrial, con el
pseudocódigo del algoritmo genético).

Uso:
  python generar_fase2_sintesis.py borrador.docx salida.docx ruta/modelo.py ruta/BD_HFS.xlsx
"""
import os
import sys

import docx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_docx as L                                                   # noqa: E402
import generar_fase2 as G                                              # noqa: E402
from generar_fase2 import n                                            # noqa: E402


def _de_modelo(tipo, clave):
    """Toma una tabla o ecuación de la versión extensa (mismo contenido técnico)."""
    for b in G.bloque_modelo():
        if b[0] == tipo and (b[1] == clave if tipo == 'tabla' else b[3] == clave):
            return b
    raise KeyError(clave)


def ec(numero):
    return _de_modelo('ecuacion', numero)


# ===========================================================================

def modelo():
    return [
        ('h2', 'Construcción del modelo matemático y del algoritmo genético'),
        ('p', 'Esta fase da cumplimiento al segundo objetivo específico. Se formula un modelo de '
              'programación lineal entera mixta (MILP) que representa el problema y se diseña un '
              'algoritmo genético (AG) para resolverlo a la escala de la empresa. El modelo se '
              'verifica y valida en instancias reducidas, los parámetros del algoritmo se calibran '
              'mediante diseño de experimentos y, al final, se presenta la programación obtenida '
              'para las órdenes del caso de estudio.'),
        ('h3', 'Modelo matemático'),
        ('p', 'El modelo se basa en la formulación con sublotes consistentes para Flow Shop híbrido '
              'de Gürsoy Yılmaz y Yılmaz (2022) e incorpora las condiciones de la empresa: fechas '
              'de liberación, alistamiento por cambio de referencia en troquelado, máquinas no '
              'relacionadas en ensamble y minimización de la tardanza total. Cada orden se divide '
              'en sublotes que avanzan de forma independiente por las etapas (*lot streaming*), de '
              'modo que un sublote puede iniciar ensamble mientras el resto de la orden sigue en '
              'troquelado. Los sublotes son consistentes: los de una misma orden pueden tener '
              'tamaños distintos, pero cada uno conserva su tamaño en las cuatro etapas.'),
        ('p', 'Además de las restricciones y supuestos de la fase de caracterización, se adoptan '
              'las siguientes condiciones:'),
        ('viñetas', [
            r'Cada orden $j$ se divide en $B_j$ sublotes de docenas enteras, con un mínimo de '
            r'$q^{\min}=1$ docena.',
            'En cada etapa, un sublote se procesa completo en una sola máquina y pasa a la '
            'siguiente etapa en cuanto termina, sin esperar a los demás sublotes de su orden.',
            'Los sublotes de distintas órdenes pueden intercalarse en una misma máquina.',
            'Cada máquina de troquelado requiere un alistamiento al iniciar y cada vez que cambia '
            'la referencia; puede realizarse mientras la máquina espera el sublote (Allahverdi et '
            'al., 2008).']),
        ('h4', 'Conjuntos, parámetros y variables'),
        _de_modelo('tabla', 'Conjuntos e índices del modelo'),
        _de_modelo('tabla', 'Parámetros del modelo'),
        _de_modelo('tabla', 'Variables de decisión del modelo'),
        ('h4', 'Función objetivo'),
        ('p', 'Se minimiza la tardanza total; entre soluciones con igual tardanza se prefiere la de '
              'menor makespan, que libera antes la capacidad (objetivo lexicográfico).'),
        ec(1),
        ('h4', 'Restricciones'),
        ('p', 'Los sublotes de cada orden suman su cantidad (2) y respetan el tamaño mínimo (3). En '
              'cada etapa, cada sublote se asigna a una sola máquina (4) y termina después de su '
              'tiempo de procesamiento en ella, que depende de la velocidad de la máquina (5).'),
        ec(2), ec(3), ec(4), ec(5),
        ('p', 'Ningún sublote inicia antes de la liberación de su orden (6), y cada sublote inicia '
              'una etapa cuando termina la anterior (7), sin esperar al resto de su orden.'),
        ec(6), ec(7),
        ('p', 'En cada máquina, cada sublote asignado tiene un antecesor inmediato, que puede ser el '
              'inicio ficticio 0 (8), a lo sumo un sucesor (9), y cada máquina tiene a lo sumo un '
              'primer sublote (10).'),
        ec(8), ec(9), ec(10),
        ('p', r'Si $i$ precede a $i^{\prime}$ en una máquina de troquelado, $i^{\prime}$ inicia '
              r'después de que termina $i$ más el alistamiento si cambia la referencia (11), y el '
              'primer sublote requiere el montaje inicial (12). En las demás etapas basta con que '
              r'$i^{\prime}$ inicie después de que termina $i$ (13).'),
        ec(11), ec(12), ec(13),
        ('p', 'La tardanza de cada orden es el exceso de la terminación de su último sublote sobre '
              'la fecha de entrega (14), y el makespan es la mayor terminación (15). La expresión '
              '(16) define el dominio de las variables.'),
        ec(14), ec(15), ec(16),
        ('h4', 'Tamaño del modelo y método de solución'),
        ('p', r'En el caso de estudio, las 10 órdenes divididas en $\overline{B}=10$ sublotes '
              'producen 100 sublotes que deben programarse en 36 máquinas. El modelo tendría unas '
              '363.600 variables binarias y cerca de 368.600 restricciones. Como la programación de '
              'un Flow Shop híbrido es NP-difícil incluso con dos etapas (Gupta, 1988), un problema '
              'de este tamaño no se resuelve de forma exacta en un tiempo razonable; la validación '
              'de la sección 4.2.3 lo confirma. Por ello se usa un algoritmo genético, el método más '
              'empleado en la literatura sobre Flow Shop híbrido (Ruiz y Vázquez-Rodríguez, 2010; '
              'López-Vargas y Arango-Marín, 2015), y el modelo matemático sirve para representar el '
              'problema y validar el algoritmo en instancias pequeñas.'),
    ]


def algoritmo(D):
    P = D['params']
    return [
        ('h3', 'Algoritmo genético'),
        ('p', 'El algoritmo adapta el esquema de Gürsoy Yılmaz y Yılmaz (2022) para sublotes '
              'consistentes. Cada cromosoma codifica los tamaños de los sublotes y el orden en que '
              'se procesan; un procedimiento de decodificación lo convierte en una programación '
              'factible y calcula su desempeño. La Figura {F:pseudo} presenta el pseudocódigo y las '
              'secciones siguientes describen sus componentes.'),
        ('codigo', 'Pseudocódigo del algoritmo genético propuesto', [
            '**Algoritmo genético para el HFS con sublotes consistentes**',
            'Entrada: órdenes (Q, p, r, d), tiempos a(j,m), máquinas de cada etapa',
            f"         Np = {P['poblacion']}, pc = {n(P['prob_cruce'], 1)}, pm = {n(P['prob_mutacion'], 1)}, "
            f"k = {P['tam_torneo']}, Gsm = {P['sin_mejora']}, Gmáx = {n(P['generaciones'], 0)}",
            'Salida:  mejor programación encontrada',
            ' 1  Evaluar FIFO, EDD, SPT, LPT, MST y CR con sublotes iguales',
            ' 2  P ← {cromosoma de la mejor regla} ∪ {Np − 1 cromosomas aleatorios}',
            ' 3  para cada c en P: Decodificar(c); f(c) ← (ΣT, Cmax)',
            ' 4  mejor ← c de P con menor f;  g ← 0;  gsm ← 0',
            ' 5  mientras g < Gmáx y gsm < Gsm hacer',
            ' 6     P′ ← {c de P con menor f}                      ▹ elitismo',
            ' 7     mientras |P′| < Np hacer',
            ' 8        p1 ← Torneo(P, k);  p2 ← Torneo(P, k)',
            ' 9        si aleatorio < pc entonces (h1, h2) ← Cruzar(p1, p2)',
            '10        si no (h1, h2) ← copias de (p1, p2)',
            '11        para h en {h1, h2}: si aleatorio < pm entonces Mutar(h)',
            '12        agregar h1 y h2 a P′',
            '13     P ← P′;  Decodificar(c) y calcular f(c) para cada c nuevo de P',
            '14     si f(menor de P) < f(mejor) entonces mejor ← menor de P; gsm ← 0',
            '15     si no gsm ← gsm + 1',
            '16     g ← g + 1',
            '17  devolver Decodificar(mejor)',
            '',
            '**Cruzar(p1, p2)**',
            '   para cada orden j:  λ ← U(0,1)',
            '      π(h1) ← λ·π(p1) + (1 − λ)·π(p2);   π(h2) ← (1 − λ)·π(p1) + λ·π(p2)',
            '   para cada etapa s:  O(h1) ← LOX(O(p1), O(p2));   O(h2) ← LOX(O(p2), O(p1))',
            '**Mutar(h)**',
            '   con prob. 0,30: elegir una etapa s e intercambiar dos sublotes de O(s)',
            '   para cada orden j, con prob. 0,40: sumar N(0; 0,15) a una proporción',
            '      de π(j) y normalizar',
            '**Decodificar(c)**: construye la programación del cromosoma (Figura {F:decod})'],
         'pseudo', 'mono'),
        ('h4', 'Representación de la solución'),
        ('p', r'El cromosoma tiene dos niveles. En el nivel 1, cada orden $j$ tiene un vector de '
              r'proporciones $\pi_j=(\pi_{j1},\dots,\pi_{jB_j})$ que suma uno y define el tamaño '
              r'relativo de sus sublotes. En el nivel 2, cada etapa $s$ tiene una secuencia $O_s$ de '
              'los 100 sublotes, que define el orden en que se programan. La máquina no se codifica: '
              'el decodificador asigna cada sublote a la máquina en la que termina primero (regla '
              'ECT), lo que reduce el espacio de búsqueda y evita, por ejemplo, enviar un sublote a '
              'una máquina lenta de ensamble cuando hay una rápida libre (Ruiz y Maroto, 2006). La '
              'Tabla {T:cromosoma} muestra un ejemplo con dos órdenes.'),
        ('tabla', 'Ejemplo de cromosoma con dos órdenes (J1: 25 docenas en 4 sublotes; '
                  'J2: 10 docenas en 2 sublotes)', ['Nivel', 'Gen', 'Valores'], [
            ['1', r'$\pi_{J1}$', '(0,10; 0,35; 0,30; 0,25)'],
            ['1', r'$\pi_{J2}$', '(0,50; 0,50)'],
            ['2', r'$O_1$ (troquelado)', 'J1-2, J2-1, J1-1, J1-3, J2-2, J1-4'],
            ['2', r'$O_2$ (ensamble)', 'J2-1, J1-2, J1-1, J2-2, J1-3, J1-4'],
            ['2', r'$O_3$ (costura)', 'J1-2, J2-1, J1-1, J2-2, J1-4, J1-3'],
            ['2', r'$O_4$ (volteado)', 'J2-1, J1-2, J2-2, J1-1, J1-3, J1-4']],
         {'etiqueta': 'cromosoma', 'anchos': [900, 2300, 5638], 'alineacion': ['c', 'l', 'l']}),
        ('p', r'Las proporciones se convierten en docenas enteras reservando el mínimo para cada '
              r'sublote y repartiendo las $L_j=Q_j-B_j\,q^{\min}$ docenas restantes según las '
              'proporciones; las unidades que quedan por el redondeo se asignan a los sublotes con '
              'mayor residuo:'),
        ('ecuacion', r'x_{jb}=q^{\min}+u_{jb},\qquad u_{jb}=\lfloor\pi_{jb}L_j\rfloor+\delta_{jb},'
                     r'\qquad \sum_{b}u_{jb}=L_j', r'$\forall j\in J,\; b=1,\dots,B_j$', 17),
        ('p', r'donde $\delta_{jb}\in\{0,1\}$. Así, todo cromosoma cumple las restricciones (2) y (3). '
              'En el ejemplo, J1 reparte 21 docenas: las partes enteras de (2,10; 7,35; 6,30; 5,25) '
              'suman 20 y la unidad restante va al sublote 2, de modo que los tamaños son (3, 9, 7, 6) '
              'docenas. La Figura {F:crom} representa este cromosoma: arriba, los tamaños de los sublotes '
              '(nivel 1), y abajo, su orden en cada etapa (nivel 2).'),
        ('figura', 'Representación del cromosoma del ejemplo con dos órdenes',
         os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figuras', 'cromosoma_ejemplo.png'),
         15.0, 'crom'),
        ('h4', 'Decodificación y aptitud'),
        ('p', r'El decodificador programa las etapas en orden. En cada etapa toma los sublotes en el '
              r'orden $O_s$ y, para cada uno, calcula en cada máquina el inicio posible a partir del '
              'momento en que el sublote está disponible (la liberación de la orden en troquelado o '
              'su terminación en la etapa anterior). En troquelado, el sublote se ubica después del '
              'último de la máquina y se suma el alistamiento si cambia la referencia; en las demás '
              'etapas ocupa el primer intervalo libre. El sublote se asigna a la máquina en la que '
              'termina primero. La programación resultante cumple por construcción todas las '
              'restricciones del modelo. La Figura {F:decod} presenta el procedimiento. La aptitud '
              'de un cromosoma es el par (ΣT_j, C_max) de su programación, comparado de forma '
              'lexicográfica.'),
        ('codigo', 'Pseudocódigo del procedimiento de decodificación', [
            '**Procedimiento Decodificar(c)**',
            'Entrada: cromosoma c = (π, O1, O2, O3, O4) y datos de la instancia',
            'Salida:  máquina, inicio y fin de cada sublote; ΣT y Cmax',
            ' 1  para cada orden j: x(j,·) ← docenas a partir de π(j)        ▹ ecuación (17)',
            ' 2  para cada sublote (j, b): listo(j, b) ← r(j)',
            ' 3  para cada máquina m: agenda(m) ← vacía; libre(m) ← 0; ref(m) ← ninguna',
            ' 4  para s = 1 hasta 4 hacer',
            ' 5     para cada sublote (j, b) en el orden O(s) hacer',
            ' 6        para cada máquina m de la etapa s hacer',
            ' 7           t ← a(j,m) · x(j,b)                         ▹ tiempo de proceso',
            ' 8           si s = 1 entonces                                ▹ troquelado',
            ' 9              α ← σ si ref(m) = ninguna o ref(m) ≠ p(j); si no α ← 0',
            '10              inicio(m) ← máx(libre(m) + α, listo(j, b))',
            '11           si no',
            '12              inicio(m) ← primer hueco de agenda(m) de duración t',
            '                             que empiece en o después de listo(j, b)',
            '13           fin(m) ← inicio(m) + t',
            '14        m′ ← máquina con menor fin(m); si hay empate, la de menor índice',
            '                                                             ▹ regla ECT',
            '15        registrar (j, b) en agenda(m′) entre inicio(m′) y fin(m′)',
            '16        si s = 1 entonces libre(m′) ← fin(m′); ref(m′) ← p(j)',
            '17        listo(j, b) ← fin(m′)               ▹ disponible para la etapa s + 1',
            '18  para cada orden j: C(j) ← máx_b listo(j, b); T(j) ← máx(0, C(j) − d(j))',
            '19  devolver la programación, ΣT = Σ_j T(j) y Cmax = máx_j C(j)'],
         'decod', 'mono'),
        ('h4', 'Población inicial'),
        ('p', f"La población tiene {P['poblacion']} cromosomas: {P['poblacion'] - 1} aleatorios y uno "
              'construido con la mejor de seis reglas de despacho aplicadas con sublotes iguales y la misma '
              r'secuencia de órdenes en todas las etapas (Tabla {T:reglas}), donde $P_j$ es el tiempo de la '
              'orden completa en la máquina más rápida de cada etapa. ' + D['texto_reglas'] +
              ' Sembrar la población con la mejor regla acelera la convergencia sin perder la diversidad '
              'que aportan los cromosomas aleatorios, y garantiza que la solución del algoritmo nunca sea '
              'peor que la de la regla.'),
        ('tabla', 'Reglas de despacho en la instancia del caso de estudio (10 sublotes iguales por orden)',
         ['Regla', 'Criterio de prioridad', 'ΣT_j (h)', 'T_max (h)', 'C_max (h)', 'Tardías'],
         D['filas_reglas'],
         {'etiqueta': 'reglas', 'anchos': [900, 2938, 1250, 1250, 1250, 1250],
          'alineacion': ['l', 'l', 'c', 'c', 'c', 'c']}),
        ('h4', 'Operadores genéticos y criterio de parada'),
        ('viñetas', [
            '**Selección por torneo:** se eligen tres cromosomas al azar y gana el de mejor aptitud '
            '(Goldberg y Deb, 1991).',
            r'**Cruce** (probabilidad $p_c$). En el nivel 1 se usa un cruce aritmético por orden, '
            r'con $\lambda\sim U(0,1)$ (18), que mantiene la suma de las proporciones en uno '
            '(Michalewicz, 1996). En el nivel 2 se usa el cruce de orden lineal (LOX) en cada etapa: '
            'el hijo conserva un tramo del primer padre en las mismas posiciones y completa el resto '
            'con los sublotes faltantes en el orden del segundo padre, lo que siempre produce una '
            'secuencia válida (Falkenauer y Bouffouix, 1991; Tabla {T:lox}).',]),
        ('ecuacion', r'\pi_j^{h_1}=\lambda\,\pi_j^{p_1}+(1-\lambda)\,\pi_j^{p_2},\qquad '
                     r'\pi_j^{h_2}=(1-\lambda)\,\pi_j^{p_1}+\lambda\,\pi_j^{p_2}', r'$\forall j\in J$', 18),
        ('tabla', 'Ejemplo del cruce LOX en una etapa (tramo conservado: posiciones 3 y 4)',
         ['Secuencia', 'Pos. 1', 'Pos. 2', 'Pos. 3', 'Pos. 4', 'Pos. 5', 'Pos. 6'], [
             ['Padre 1', 'J1-1', 'J1-2', '**J2-1**', '**J3-1**', 'J2-2', 'J3-2'],
             ['Padre 2', 'J3-1', 'J2-1', 'J1-1', 'J3-2', 'J1-2', 'J2-2'],
             ['Hijo', 'J1-1', 'J3-2', '**J2-1**', '**J3-1**', 'J1-2', 'J2-2']],
         {'etiqueta': 'lox', 'anchos': [1638, 1200, 1200, 1200, 1200, 1200, 1200]}),
        ('viñetas', [
            r'**Mutación** (probabilidad $p_m$ por hijo). Con probabilidad 0,30 se intercambian dos '
            'sublotes en la secuencia de una etapa; además, para cada orden, con probabilidad 0,40 se '
            r'perturba la proporción de un sublote con un valor $N(0;\,0{,}15)$ y se normaliza el '
            'vector.',
            '**Elitismo y parada:** el mejor cromosoma pasa a la generación siguiente. El algoritmo '
            f"se detiene tras {P['sin_mejora']} generaciones sin mejora o al llegar a "
            f"{n(P['generaciones'], 0)} generaciones."]),
        ('h4', 'Implementación'),
        ('p', 'El algoritmo se implementó en Python 3. Los datos se leen del libro de Excel '
              'BD_HFS.xlsx, con tres hojas: tiempos estándar por referencia y máquina, órdenes de '
              'trabajo (cantidad, liberación y fecha de entrega) y calendario laboral. Así, la empresa '
              'puede actualizar la información sin modificar el código. El programa entrega los '
              'tamaños de los sublotes, los indicadores por orden y globales, la programación por '
              'máquina y el diagrama de Gantt. Con los parámetros calibrados, una corrida en la '
              f"instancia real toma entre {D['t_min']} y {D['t_max']} minutos en un computador de 4 núcleos. "
              '[[El código se incluye en el Anexo X.]]'),
    ]


def _datos_validacion():
    """Tabla y cifras de la validación, leídas de resultados_validacion_todas.csv."""
    import pandas as pd
    v = pd.read_csv(os.path.join(G.SAL_VAL, 'resultados_validacion_todas.csv'))
    filas, info = [], []
    for _, r in v.iterrows():
        cand = [(r[f'{f} ΣTj'], r[f'{f} Cmax']) for f in ('F1', 'F2') if not pd.isna(r[f'{f} ΣTj'])]
        ref = min(cand, key=lambda c: (round(c[0], 6), round(c[1], 6)))
        ag = (r['AG mejor ΣTj'], r['AG mejor Cmax'])
        # mismo valor con distinta precisión numérica del solver → se muestra igual
        ref = tuple(g if abs(x - g) < 1e-4 else x for x, g in zip(ref, ag))
        opt = bool(r['ΣTj óptima demostrada'])
        txt_ref = f"{n(ref[0], 3)} / {n(ref[1], 3)}"
        sub = f"{int(r['Sublotes'])}" + (' (sin división)' if int(r['B̄']) == 1 else '')
        filas.append([r['Instancia'], sub, txt_ref if opt else f'No demostrado ({txt_ref})',
                      n(r['Regla ΣTj'], 3), f"{n(r['AG mejor ΣTj'], 3)} / {n(r['AG mejor Cmax'], 3)}",
                      n(r['AG prom ΣTj'], 3), r['AG ≤ MILP en ΣTj'], n(r['AG s prom'], 1)])
        info.append({'inst': r['Instancia'], 'opt': opt, 'ref': ref, 'B': int(r['B̄']),
                     'sub': int(r['Sublotes']), 'f1_sin': pd.isna(r['F1 ΣTj']),
                     'ag': (r['AG mejor ΣTj'], r['AG mejor Cmax']),
                     'hits': int(str(r['AG ≤ MILP en ΣTj']).split('/')[0]),
                     'reps': int(str(r['AG ≤ MILP en ΣTj']).split('/')[1]), 'seg': r['AG s prom']})
    return filas, info


def validacion():
    import pandas as pd
    sys.path.insert(0, os.path.join(G.RAIZ, 'fase2'))
    import validacion_milp as V
    v = pd.read_csv(os.path.join(G.SAL_VAL, 'resultados_validacion_todas.csv')).set_index('Instancia')
    _, info = _datos_validacion()
    inf = {i['inst']: i for i in info}

    # --- Tabla de instancias (definiciones de validacion_milp.py)
    etapas = ['Troquelado', 'Ensamble', 'Costura', 'Volteado']
    filas_inst = []
    for nombre, ordenes, b_max, maq in V.INSTANCIAS:
        conj = 'A' if maq == V.MAQ_A else 'B'
        filas_inst.append([nombre, f"{ordenes[0][0]}–{ordenes[-1][0]}", str(b_max),
                           str(int(v.loc[nombre, 'Sublotes'])),
                           '-'.join(str(len(maq[e])) for e in etapas) + f' ({conj})',
                           ', '.join(n(o[4], 0) for o in ordenes)])
    o_txt = _lista([f"{j} = {p} ({q} docenas, r = {n(r, 0)} h)" for j, p, q, r, _ in V.ORDENES_BASE])
    maqA = _lista([f"{_lista(V.MAQ_A[e])} ({e.lower()})" for e in etapas])
    extraB = _lista([f"{m} en {e.lower()}" for e in etapas for m in V.MAQ_B[e] if m not in V.MAQ_A[e]])

    # --- Tabla de resultados
    def est(e, s):
        e = str(e)
        t = 'óptimo' if e.startswith('Óptimo') else ('sin solución' if e.startswith('Sin') else 'límite')
        return f"{t} ({n(s, 0)})"

    def form(f, r):
        if pd.isna(r[f'{f} ΣTj']):
            return est(r[f'{f} estado'], r[f'{f} s'])
        r3 = lambda x: n(round(x, 4) + 1e-9, 3)          # misma cifra con distinta precisión del solver
        return f"{r3(r[f'{f} ΣTj'])} / {r3(r[f'{f} Cmax'])} · {est(r[f'{f} estado'], r[f'{f} s'])}"

    filas_res = []
    for nombre, r in v.iterrows():
        filas_res.append([nombre, str(int(r['Sublotes'])), form('F1', r), form('F2', r),
                          f"{n(r['Regla ΣTj'], 3)} ({r['Regla']})",
                          f"{n(round(r['AG mejor ΣTj'], 4) + 1e-9, 3)} / {n(round(r['AG mejor Cmax'], 4) + 1e-9, 3)}",
                          n(r['AG prom ΣTj'], 3),
                          r['AG ≤ MILP en ΣTj'], n(r['AG s prom'], 1)])

    # --- Cifras para las conclusiones
    opt = lambda e: str(e).startswith('Óptimo')
    ambos = [i for i, r in v.iterrows() if opt(r['F1 estado']) and opt(r['F2 estado'])
             and abs(r['F1 ΣTj'] - r['F2 ΣTj']) < 1e-3 and abs(r['F1 Cmax'] - r['F2 Cmax']) < 1e-3]
    solo_f2 = [i for i, r in v.iterrows() if opt(r['F2 estado']) and not opt(r['F1 estado'])
               and not pd.isna(r['F1 ΣTj']) and abs(r['F1 ΣTj'] - r['F2 ΣTj']) < 1e-3
               and abs(r['F1 Cmax'] - r['F2 Cmax']) < 1e-3]
    viol = int(v['F1 violaciones'].fillna(0).sum() + v['F2 violaciones'].fillna(0).sum())
    con_f1 = [i for i, r in v.iterrows() if not pd.isna(r['F1 ΣTj'])]
    igual_dec = [i for i in con_f1 if abs(v.loc[i, 'Decod. ΣTj'] - inf[i]['ref'][0]) < 1e-3
                 and abs(v.loc[i, 'Decod. Cmax'] - inf[i]['ref'][1]) < 1e-3]
    mayor_dec = [i for i in con_f1 if i not in igual_dec]
    ej = mayor_dec[0] if mayor_dec else None
    con_opt = [i['inst'] for i in info if i['opt']]
    hits = sum(inf[i]['hits'] for i in con_opt)
    reps = sum(inf[i]['reps'] for i in con_opt)
    brecha = {i: v.loc[i, 'AG prom ΣTj'] - inf[i]['ref'][0] for i in con_opt}
    i_br = max(brecha, key=brecha.get)
    dif_c = [i for i in con_opt if inf[i]['ag'][0] <= inf[i]['ref'][0] + 1e-3
             and inf[i]['ag'][1] > inf[i]['ref'][1] + 1e-3]
    f1_opt_max = max(int(v.loc[i, 'Sublotes']) for i, r in v.iterrows() if opt(r['F1 estado']))
    sin_f1 = [i for i, r in v.iterrows() if pd.isna(r['F1 ΣTj'])]
    t_ag = v['AG s prom'].max()
    i_big = sin_f1[-1] if sin_f1 else v.index[-1]
    rat = (v['F2 binarias'] / v['F1 binarias'])
    n_sub, n_maq = 100, 36
    bin_real = n_sub * n_maq + n_sub ** 2 * n_maq
    mejor_t = {i: min(inf[i]['ref'][0], inf[i]['ag'][0]) for i in inf}
    g5 = os.path.join(G.SAL_VAL, 'gantt_milp_vs_ag_I5.png')
    igual_i5 = (abs(inf['I5']['ag'][0] - inf['I5']['ref'][0]) < 1e-3
                and abs(inf['I5']['ag'][1] - inf['I5']['ref'][1]) < 1e-3)

    return [
        ('h3', 'Verificación y validación'),
        ('p', 'Antes de usar el modelo en el caso de estudio se comprobaron dos cosas: que las programaciones '
              'que produce cumplen todas las restricciones (verificación) y que sus resultados son correctos, '
              'es decir, que el algoritmo genético encuentra soluciones óptimas o muy cercanas al óptimo '
              '(validación).'),
        ('p', '**Verificación.** Un verificador independiente revisó, en las programaciones producidas '
              'por el decodificador, cada restricción del modelo: tamaños de sublote, asignación de '
              'máquinas, tiempos de proceso, liberaciones, precedencia entre etapas, no solapamiento y '
              'alistamientos. Se aplicó a 200 cromosomas aleatorios de la instancia real y a las seis '
              'reglas de despacho, sin encontrar violaciones.'),
        ('h4', 'Validación con instancias reducidas'),
        ('p', 'Para saber si el algoritmo encuentra buenas soluciones hay que compararlo con la mejor '
              'solución posible, el óptimo. El modelo matemático lo puede calcular de forma exacta, pero '
              'solo en problemas pequeños: a medida que aumentan los sublotes, el número de combinaciones '
              'crece tan rápido que el solver deja de encontrar respuesta en un tiempo razonable. Por eso '
              'la validación se hizo con instancias reducidas, en las que ambos métodos pueden compararse.'),
        ('p', 'Se construyeron nueve instancias con los tiempos estándar reales de la empresa, cantidades '
              'reducidas y un subconjunto de las máquinas de cada etapa (Tabla {T:inst}). En ensamble se '
              'incluyeron siempre máquinas de velocidades distintas (M5, lenta; M12, intermedia; M16, '
              'rápida), y dos órdenes de la misma referencia (C01), para comprobar que el alistamiento solo '
              'se aplica cuando cambia la referencia. Las instancias I1 e I2 tienen las mismas órdenes que '
              'I6 e I9, pero sin dividirlas en sublotes, lo que permite medir el efecto de la división.'),
        ('tabla', 'Instancias de validación', ['Instancia', 'Órdenes', 'B̄', 'Sublotes',
                                               'Máquinas (T-E-C-V)', 'd_j (h)'], filas_inst,
         {'etiqueta': 'inst', 'anchos': [1100, 1100, 700, 1100, 2100, 2738],
          'alineacion': ['c', 'c', 'c', 'c', 'c', 'c']}),
        ('p', f'Las órdenes son {o_txt}. El conjunto de máquinas A está formado por {maqA}; el conjunto '
              f'B agrega {extraB}. Con el conjunto B, que tiene más capacidad, se usaron fechas de entrega '
              'más ajustadas, para que la tardanza óptima fuera mayor que cero y las instancias '
              'permitieran diferenciar entre los métodos.'),
        ('p', '**Cómo se resolvieron.** Cada instancia se resolvió de forma exacta con el solver HiGHS, '
              'usando dos formulaciones del modelo. La primera (F1) es el modelo matemático presentado en esta fase, '
              'que decide qué sublote va inmediatamente antes de cada otro en cada máquina. La segunda (F2) '
              'es una formulación equivalente que solo decide, para cada par de sublotes que comparten '
              'máquina, cuál va primero (Naderi et al., 2014); necesita entre el '
              f'{n(100 * rat.min(), 0)} % y el {n(100 * rat.max(), 0)} % de las variables binarias de F1 '
              'y por eso resuelve más rápido. Si las dos formulaciones, construidas de manera distinta, '
              'llegan al mismo óptimo, es una evidencia fuerte de que el modelo está bien planteado.'),
        ('p', 'Como el objetivo es lexicográfico, cada instancia se resolvió en dos fases: primero se '
              'minimizó la tardanza total y luego el makespan, sin empeorar la tardanza óptima, con un '
              'límite de 10 minutos por fase. Sobre las mismas instancias se corrió el algoritmo genético, '
              'sin modificaciones y con los parámetros calibrados en la sección 4.2.4, 10 veces con '
              'semillas distintas. La Tabla {T:validacion} presenta los resultados.'),
        ('tabla', 'Resultados de la validación: modelo exacto frente al algoritmo genético',
         ['Inst.', 'Sub-lotes', 'F1: ΣT_j / C_max', 'F2: ΣT_j / C_max', 'Mejor regla ΣT_j',
          'AG mejor ΣT_j / C_max', 'AG prom. ΣT_j', 'AG ≤ MILP', 'AG (s)'], filas_res,
         {'etiqueta': 'validacion', 'anchos': [560, 640, 1700, 1700, 1000, 1150, 760, 680, 648],
          'alineacion': ['c'] * 9, 'tam': 8}),
        ('p', 'La tardanza total y el makespan se expresan en horas; entre paréntesis, el tiempo de cómputo '
              'del solver en segundos. «Óptimo» indica que el solver demostró la optimalidad de las dos '
              'fases; «límite», que se alcanzó el límite de tiempo con la mejor solución encontrada, y '
              '«sin solución», que no encontró ninguna solución factible. La columna «AG ≤ MILP» indica en '
              'cuántas de las 10 réplicas el algoritmo obtuvo una tardanza igual o menor que la mejor '
              'solución exacta.'),
        ('p', 'La Figura {F:gantt_val} compara, en la instancia I5, la programación óptima del modelo '
              'exacto con la mejor del algoritmo genético. '
              + ('Las dos programaciones son distintas, pues ordenan y asignan los sublotes de otra manera, '
                 'pero alcanzan exactamente el mismo valor óptimo: '
                 f"{n(inf['I5']['ref'][0], 3)} h de tardanza total y {n(inf['I5']['ref'][1], 3)} h de makespan. "
                 'Es decir, el problema puede tener varias soluciones óptimas, y el algoritmo encontró una '
                 'de ellas.' if igual_i5 else '')),
        ('figura', 'Programación óptima del modelo exacto (arriba) y mejor programación del algoritmo '
                   'genético (abajo) en la instancia I5', g5, 15.5, 'gantt_val'),
        ('p', 'Los resultados permiten las siguientes conclusiones:'),
        ('viñetas', [
            '**El modelo matemático está bien formulado.** '
            + (f'Ninguna de las soluciones del modelo exacto presentó violaciones de las restricciones. '
               if viol == 0 else '')
            + (f"En las instancias en que las dos formulaciones demostraron la optimalidad ({_lista(ambos)}), "
               'llegaron exactamente al mismo óptimo' if ambos else '')
            + (f"; en {_lista(solo_f2)}, F2 demostró el óptimo y F1 encontró esa misma solución, aunque no "
               'alcanzó a demostrar su optimalidad en el tiempo límite' if solo_f2 else '') + '.',
            '**El algoritmo y el modelo representan el mismo problema.** Al pasar los tamaños y secuencias '
            'de la solución exacta por el decodificador del algoritmo se obtuvieron exactamente los mismos '
            f"tiempos en {_lista(igual_dec)}. "
            + (f"En {_lista(mayor_dec)} el decodificador obtuvo un valor algo mayor con esas secuencias; en "
               f"{ej}, por ejemplo, {n(v.loc[ej, 'Decod. ΣTj'], 3)} h frente a {n(inf[ej]['ref'][0], 3)} h. "
               'La razón es la regla de asignación del decodificador: el modelo exacto puede enviar un '
               'sublote a una máquina lenta de ensamble para dejar libre la rápida, que otro sublote '
               'necesita poco después, mientras que el decodificador siempre elige la máquina en la que el '
               'sublote termina primero. Aun así, el algoritmo alcanzó el óptimo en esas instancias con '
               'otros cromosomas.' if mayor_dec else ''),
            '**El algoritmo encuentra soluciones óptimas o muy cercanas al óptimo.** En las '
            f"{NUM_TXT(len(con_opt))} instancias con tardanza óptima conocida, la mejor de las 10 réplicas "
            f"alcanzó la tardanza óptima en todos los casos, y {hits} de {reps} réplicas "
            f"({100 * hits / reps:.0f} %) la alcanzaron. La mayor diferencia promedio fue de "
            f"{n(brecha[i_br], 2)} h ({i_br})."
            + (f" El único caso en que no se alcanzó también el makespan óptimo fue {_lista(dif_c)}, con un "
               f"makespan {n(100 * (inf[dif_c[0]]['ag'][1] / inf[dif_c[0]]['ref'][1] - 1), 1)} % mayor y la "
               'misma tardanza.' if len(dif_c) == 1 else ''),
            '**El método exacto no escala; el algoritmo sí.** La formulación F1 solo demostró la '
            f"optimalidad hasta {f1_opt_max} sublotes"
            + (f" y no encontró ninguna solución factible con {_lista([str(int(v.loc[i, 'Sublotes'])) for i in sin_f1])} "
               'sublotes en 10 minutos' if sin_f1 else '')
            + '. En cambio, el algoritmo resolvió cada instancia en menos de '
            f"{int(t_ag) + 1} segundos y, en las más grandes, superó a la mejor solución del solver: en "
            f"{i_big}, obtuvo {n(inf[i_big]['ag'][0], 3)} h frente a {n(inf[i_big]['ref'][0], 3)} h. La "
            f"instancia real, con {n_sub} sublotes y {n_maq} máquinas, implicaría "
            f"{n(bin_real, 0)} variables binarias en F1, muy por encima de lo que el método exacto puede "
            'resolver; por eso se usa el algoritmo genético.',
            '**Dividir en sublotes reduce la tardanza.** Con las mismas cuatro órdenes, la mejor tardanza '
            f"encontrada es de {n(mejor_t['I1'], 2)} h sin dividirlas (I1), y baja a "
            f"{n(mejor_t['I6'], 2)} h con dos sublotes por orden (I6) y a {n(mejor_t['I8'], 2)} h con tres "
            f"(I8). Con cinco órdenes, baja de {n(mejor_t['I2'], 2)} h (I2) a {n(mejor_t['I9'], 2)} h (I9). "
            'Este resultado anticipa lo que se observa en el caso de estudio.']),
    ]


def NUM_TXT(k):
    return {1: 'una', 2: 'dos', 3: 'tres', 4: 'cuatro', 5: 'cinco', 6: 'seis', 7: 'siete', 8: 'ocho',
            9: 'nueve'}.get(k, str(k))


NUM = {2: 'dos', 3: 'tres', 4: 'cuatro'}
NOMBRE_F = {'poblacion': 'población', 'prob_cruce': 'probabilidad de cruce',
            'prob_mutacion': 'probabilidad de mutación'}


def _p(p):
    if p is None or p != p:
        return '—'
    return '< 0,001' if p < 0.001 else n(p, 3)


def _lista(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' y ' + xs[-1]


def calibracion(D):
    import json
    import pandas as pd
    C = G.SAL_CAL
    dec = json.load(open(os.path.join(C, 'decisiones.json'), encoding='utf-8'))
    est = dec['instancias']['real']
    y = est['respuesta']
    an = pd.read_csv(os.path.join(C, 'anova.csv'))
    rr = pd.read_csv(os.path.join(C, 'resumen_combinaciones.csv'))
    reps = int(rr['Corridas'].iloc[0])
    P = D['params']
    filas_anova = [[r.Fuente, n(r.SC, 1), str(int(r.gl)), n(r.CM, 1) if r.CM == r.CM else '',
                    n(r.F, 2) if r.F == r.F else '', _p(r._6) if r._6 == r._6 else '']
                   for r in an.itertuples()]
    sig = [NOMBRE_F[f] for f, p in est['p_anova'].items() if p < 0.05]
    nosig = [NOMBRE_F[f] for f, p in est['p_anova'].items() if p >= 0.05]
    kw = [NOMBRE_F[f] for f, p in est['p_kruskal'].items() if p < 0.05]
    supuestos_ok = est['p_shapiro'] >= 0.05 and all(p >= 0.05 for p in est['p_levene'].values())
    lev_mal = [NOMBRE_F[f] for f, p in est['p_levene'].items() if p < 0.05]
    fallas = []
    if est['p_shapiro'] < 0.05:
        fallas.append(f"los residuos no siguen una distribución normal (Shapiro-Wilk, p = {_p(est['p_shapiro'])})")
    if lev_mal:
        fallas.append(f'las varianzas no son homogéneas entre los niveles de {_lista(lev_mal)} (Levene, p < 0,05)')
    txt_supuestos = ('Los residuos siguen una distribución normal (Shapiro-Wilk, p = '
                     f"{_p(est['p_shapiro'])}), pero " + fallas[-1] + '; '
                     if est['p_shapiro'] >= 0.05 and fallas else
                     'No se cumplen todos los supuestos del ANOVA: ' + _lista(fallas) + '; ' if fallas else '')
    solo_anova = [f for f, p in est['p_anova'].items() if p < 0.05 and est['p_kruskal'].get(f, 0) >= 0.05]
    txt_difiere = ''.join(
        f"La {NOMBRE_F[f]} resulta significativa en el ANOVA (p = {_p(est['p_anova'][f])}), pero no en "
        f"Kruskal-Wallis (p = {_p(est['p_kruskal'][f])}), por lo que su efecto se considera débil. "
        for f in solo_anova)
    inter = [r for r in an.itertuples() if '×' in str(r.Fuente) and r._6 == r._6 and r._6 < 0.05]
    txt_inter = ''
    if inter:
        nom = lambda f: (str(f).replace('Prob. de ', 'probabilidad de ').replace('Población', 'población')
                         .replace(' × ', ' y '))
        txt_inter = ((f'También es significativa la interacción entre {nom(inter[0].Fuente)} '
                      f'(p = {_p(inter[0]._6)}): el efecto de un factor depende del nivel del otro. ')
                     if len(inter) == 1 else
                     'También son significativas las interacciones ' + _lista(
                         [f'{nom(r.Fuente)} (p = {_p(r._6)})' for r in inter]) + '. ')
    nresp = 'la tardanza total' if y == 'suma_T' else 'el makespan'
    de_resp = 'de la tardanza total' if y == 'suma_T' else 'del makespan'
    # Figura de la interacción población × mutación, si es significativa
    txt_fig_inter = []
    if any('Población' in str(r.Fuente) and 'mutación' in str(r.Fuente) for r in inter):
        cd = pd.read_csv(os.path.join(C, 'corridas_diseno.csv'))
        tt = cd.pivot_table(index='poblacion', columns='prob_mutacion', values='suma_T', aggfunc='mean')
        pmin, pmax, mmin, mmax = tt.index.min(), tt.index.max(), tt.columns.min(), tt.columns.max()
        txt_fig_inter = [
            ('p', 'La Figura {F:inter} muestra la interacción entre la población y la probabilidad de '
                  f'mutación: con una población de {pmin}, pasar de una mutación de {n(mmin, 1)} a '
                  f'{n(mmax, 1)} reduce la tardanza promedio de {n(tt.loc[pmin, mmin], 1)} h a '
                  f'{n(tt.loc[pmin, mmax], 1)} h, mientras que con una población de {pmax} la reduce de '
                  f'{n(tt.loc[pmax, mmin], 1)} h a {n(tt.loc[pmax, mmax], 1)} h. Una población pequeña depende '
                  'más de la mutación para explorar nuevas soluciones; una grande ya explora por sí sola.'),
            ('figura', 'Interacción entre el tamaño de la población y la probabilidad de mutación '
                       '(tardanza total promedio)',
             os.path.join(os.path.dirname(os.path.abspath(__file__)), 'figuras', 'interaccion_pob_mut.png'),
             12.0, 'inter')]
    top = rr.head(5)
    filas_top = [[int(r.poblacion), n(r.prob_cruce, 1), n(r.prob_mutacion, 1), n(r.T_prom, 1),
                  n(r.T_desv, 1), n(r.Tard, 1), n(r.C_prom, 1)] for r in top.itertuples()]
    mejor = dec['mejor_diseno']
    cfg = lambda c: (f"población {int(c['poblacion'])}, cruce {n(c['prob_cruce'], 1)} y mutación "
                     f"{n(c['prob_mutacion'], 1)}")
    a = dec.get('ampliacion')
    if a:
        borde = _lista([NOMBRE_F[f] for f in dec['en_borde']])
        if a['candidata'] is None:
            txt_amp = (f'Como la mejor combinación quedó en el borde del rango probado para {borde}, se '
                       'evaluaron niveles más allá con las mismas semillas; la combinación del diseño '
                       'siguió siendo la mejor.')
        else:
            pv = _p(a['p'].get('real'))
            txt_amp = (f'Como la mejor combinación quedó en el borde del rango probado para {borde}, se '
                       f"evaluaron niveles más allá con las mismas semillas. La mejor de ellas ({cfg(a['candidata'])}) "
                       + (f'mejoró de forma significativa (Wilcoxon, p = {pv}) y se adoptó.' if a['cambia'] else
                          f'no mejoró de forma significativa (Wilcoxon, p = {pv}), por lo que se conservó la '
                          'combinación del diseño por parsimonia.'))
    elif dec['en_borde']:
        txt_amp = (f"Esta combinación quedó en el borde del rango probado para "
                   f"{_lista([NOMBRE_F[f] for f in dec['en_borde']])}. El estudio se limitó a los niveles "
                   'del diseño, definidos a partir de los valores habituales en la literatura, por lo que '
                   'se adoptó la mejor combinación dentro de ese rango.')
    else:
        txt_amp = ('La mejor combinación no quedó en el borde del rango para ningún factor significativo, '
                   'así que no fue necesario ampliarlo.')
    par = dec.get('parada')
    filas_par, ps = [], ''
    niv_par = sorted(int(r['sin_mejora']) for r in par['tablas']['real']) if par else []
    tpar = sorted(par['tablas']['real'], key=lambda r: r['sin_mejora']) if par else []
    if par:
        for r in sorted(par['tablas']['real'], key=lambda r: r['sin_mejora']):
            filas_par.append([str(int(r['sin_mejora'])), n(r['T_prom'], 1), n(r['Tard'], 1),
                              n(r['C_prom'], 1), n(r['Gen'], 0), n(r['Seg'] / 60, 1)])
        ps = '; '.join(f"{k.split(':')[1].replace('->', ' → ')}: p = {_p(p)}" for k, p in par['p'].items())
    return [
        ('h3', 'Número de sublotes y calibración del algoritmo'),
        ('h4', 'Número de sublotes por orden'),
        ('p', r'El número de sublotes $\overline{B}$ define cuánto se divide cada orden. La Tabla '
              '{T:bbar} muestra su efecto en la instancia real con las reglas de despacho: sin '
              'división todas las órdenes resultan tardías, y la tardanza baja a medida que el '
              r'trabajo se reparte entre las máquinas paralelas. Se adopta $\overline{B}=10$ como número '
              f"máximo de sublotes por orden, con sublotes promedio entre {D['sub_min']} y {D['sub_max']}. "
              'Este límite coincide con el mayor número de sublotes por lote evaluado por Gürsoy Yılmaz y '
              'Yılmaz (2022) en un flow shop híbrido (2, 6 y 10 sublotes), quienes además recomiendan '
              'controlar y fijar de antemano el número de sublotes en sistemas de varias etapas, por su '
              'efecto significativo en la calidad de las soluciones. Aunque una división mayor puede '
              'reducir aún más la tardanza (Tabla {T:bbar}), en la planta cada sublote adicional implica '
              'más transferencias entre etapas, más registros y más seguimiento, lo que incrementa la '
              'complejidad logística y de control de la producción; por esa razón no se contemplan más '
              'de 10 sublotes por orden.'),
        ('tabla', 'Tardanza total (h) y órdenes tardías de las reglas de despacho según el número '
                  'de sublotes por orden', ['B̄', 'FIFO', 'EDD', 'CR', 'SPT'], D['filas_bbar'],
         {'etiqueta': 'bbar', 'anchos': [1238, 1900, 1900, 1900, 1900]}),
        ('h4', 'Calibración de los parámetros'),
        ('p', 'Los parámetros del algoritmo se calibraron con un diseño factorial completo 3³ sobre la '
              'instancia real (Montgomery, 2017; Ruiz, Maroto y Alcaraz, 2006): tamaño de población '
              r'(50, 100 y 150), probabilidad de cruce $p_c$ (0,7; 0,8 y 0,9) y probabilidad de '
              f'mutación $p_m$ (0,1; 0,3 y 0,5), con {reps} réplicas por combinación ({27 * reps} '
              'corridas). Todas las corridas tuvieron el mismo esfuerzo de cómputo (30.000 cromosomas '
              'generados), para que una población grande no tuviera ventaja solo por evaluar más '
              'soluciones, y cada réplica usó la misma semilla en todas las combinaciones. La variable '
              f'de respuesta fue {nresp}. La Tabla {{T:anova}} presenta el ANOVA.'),
        ('tabla', f"ANOVA {de_resp} en el diseño factorial", ['Fuente', 'SC', 'gl', 'CM', 'F', 'Valor p'],
         filas_anova, {'etiqueta': 'anova', 'anchos': [2838, 1300, 800, 1300, 1200, 1400]}),
        ('p', (f"{_lista(sig).capitalize()} {'tiene' if len(sig) == 1 else 'tienen'} efecto significativo "
               f"sobre {nresp} (p < 0,05)" if sig else f'Ningún factor tiene efecto significativo sobre {nresp}')
              + (f"; {_lista(nosig)} no lo {'tiene' if len(nosig) == 1 else 'tienen'}. " if nosig and sig else '. ')
              + txt_inter
              + ('Los supuestos de normalidad y homogeneidad de varianzas se cumplen. ' if supuestos_ok else
                 txt_supuestos
                 + 'por eso el resultado se confirmó con la prueba no paramétrica de Kruskal-Wallis, que '
                 f"identifica como significativos: {_lista(kw) if kw else 'ningún factor'}. " + txt_difiere)
              + 'La Figura {F:efectos} muestra los efectos principales y la Tabla {T:mejores} las mejores '
              'combinaciones.'),
        ('figura', f"Efectos principales sobre {nresp} (intervalos LSD al 95 %)",
         os.path.join(C, 'efectos_principales.png'), 15.5, 'efectos'),
    ] + (txt_fig_inter if txt_fig_inter else []) + [
        ('tabla', 'Mejores combinaciones del diseño factorial',
         ['Población', 'p_c', 'p_m', 'ΣT_j prom. (h)', 'ΣT_j desv. (h)', 'Tardías prom.', 'C_max prom. (h)'],
         filas_top, {'etiqueta': 'mejores', 'anchos': [1150, 700, 700, 1500, 1500, 1500, 1788],
                     'negrita_filas': (0,)}),
        ('p', f"La mejor combinación del diseño es {cfg(mejor)}. " + txt_amp +
              (f" Por último, con la configuración elegida se compararon {NUM.get(len(niv_par), len(niv_par))} criterios de "
               f"parada: {_lista([str(v) for v in niv_par])} generaciones sin mejora (Tabla {{T:parada}})."
               if par else '')),
    ] + ([
        ('tabla', 'Criterio de parada (10 réplicas por criterio)',
         ['Generaciones sin mejora', 'ΣT_j prom. (h)', 'Tardías prom.', 'C_max prom. (h)',
          'Generaciones prom.', 'Tiempo prom. (min)'], filas_par,
         {'etiqueta': 'parada', 'anchos': [1900, 1400, 1300, 1400, 1400, 1438]}),
        ('p', (f"Se adopta {par['elegido']} generaciones sin mejora: aumentar el criterio a "
               f"{niv_par[niv_par.index(par['elegido']) + 1]} no mejora de forma significativa la tardanza "
               f"(Wilcoxon; {ps}), así que se prefiere el menor tiempo de cómputo. "
               if par['elegido'] != niv_par[-1] else
               (f"Se adopta {par['elegido']} generaciones sin mejora. Con ambos criterios la tardanza es casi "
                f"nula ({_lista([n(r['T_prom'], 2) for r in tpar])} h en promedio), y con {par['elegido']} el makespan "
                f"promedio baja de {n(tpar[0]['C_prom'], 1)} a {n(tpar[-1]['C_prom'], 1)} h. La mejora es significativa "
                'según el objetivo del modelo, que compara primero la tardanza y luego el makespan (prueba de '
                f'Wilcoxon de una cola; {ps}). '
                if abs(tpar[0]['T_prom'] - tpar[-1]['T_prom']) < 1.0 else
                f"Se adopta {par['elegido']} generaciones sin mejora, porque reduce de forma significativa la "
                f"tardanza frente a {_lista([str(v) for v in niv_par[:-1]])} (prueba de Wilcoxon de una cola; {ps}). ")
               + 'La prueba es de una cola porque, con la misma semilla, la corrida con el criterio mayor '
               'continúa la de criterio menor y no puede terminar con una solución peor. Criterios más '
               'largos no se evaluaron. ')
              + 'La Tabla {T:final} resume la configuración final.'),
    ] if par else []) + [
        ('tabla', 'Configuración final del algoritmo genético', ['Parámetro', 'Valor'], [
            ['Tamaño de la población', str(P['poblacion'])],
            ['Probabilidad de cruce', n(P['prob_cruce'], 1)],
            ['Probabilidad de mutación', n(P['prob_mutacion'], 1)],
            ['Criterio de parada', f"{P['sin_mejora']} generaciones sin mejora (máximo {n(P['generaciones'], 0)})"],
            ['Tamaño del torneo', str(P['tam_torneo'])],
            ['Probabilidad de intercambio / de perturbación (desviación)',
             f"{n(P['prob_mut_pos'], 2)} / {n(P['prob_mut_prop'], 2)} ({n(P['desv_mut_prop'], 2)})"]],
         {'etiqueta': 'final', 'anchos': [5000, 3838], 'alineacion': ['l', 'c']}),
    ]


def solucion(M, rep, mejor, indic, tam, util, al, D):
    def fecha(x):
        f = M.horas_a_fecha(x)
        return f.strftime('%d/%m/%Y') if f is not None else '—'
    filas_tam = [[j] + [n(x, 0) for x in tam[j]] + [n(sum(tam[j]), 0)] for j in M.TRABAJOS]
    filas_ord = []
    for j in M.TRABAJOS:
        v = indic['por_trabajo'][j]
        filas_ord.append([j, M.PRODUCTO[j], n(M.DEMANDA[j], 0), n(v['di'], 0),
                          M.FECHA_ENTREGA[j].strftime('%d/%m/%Y'), n(v['Ci'], 1), fecha(v['Ci']),
                          n(v['Ti'], 1), n(v['Ei'], 1)])
    tard = int((rep['suma_T'] <= 1e-6).sum())
    hist = mejor['historial']
    gen_cero = next((g + 1 for g, h in enumerate(hist) if h[0] <= 1e-9), len(hist))
    mayor = max(util.values(), key=lambda u: u[3])
    tardias = [j for j in M.TRABAJOS if indic['por_trabajo'][j]['Ti'] > 1e-9]
    return [
        ('h3', 'Programación obtenida para el caso de estudio'),
        ('p', f'Con la configuración calibrada, el algoritmo se ejecutó {len(rep)} veces sobre la '
              f'instancia real (semillas {int(rep["semilla"].min())} a {int(rep["semilla"].max())}). '
              + ('Todas las réplicas eliminaron la tardanza; ' if tard == len(rep) else
                 (f'{tard} de {len(rep)} réplicas eliminaron la tardanza; ' if tard else
                  f'La tardanza total varió entre {n(rep["suma_T"].min(), 1)} y '
                  f'{n(rep["suma_T"].max(), 1)} h (promedio de {n(rep["suma_T"].mean(), 1)} h)'
                  + (f', con {int(rep["tardias"].iloc[0])} órdenes tardías en todas las réplicas; '
                     if rep['tardias'].nunique() == 1 else '; ')))
              + f'el makespan varió entre {n(rep["Cmax"].min(), 1)} y {n(rep["Cmax"].max(), 1)} h '
              f'(promedio de {n(rep["Cmax"].mean(), 1)} h) y cada corrida tomó en promedio '
              f'{n(rep["segundos"].mean() / 60, 1)} minutos. La mejor programación (semilla '
              f"{int(mejor['semilla'])}), que se propone para el conjunto de órdenes, partió de la regla "
              f"{D['regla_mejor']} ({n(D['regla_T'], 1)} h de tardanza y makespan de {n(D['regla_C'], 1)} h) y "
              + ((f"redujo la tardanza total a {n(indic['suma_Ti'], 1)} h, "
                  f"{n(100 * (1 - indic['suma_Ti'] / D['regla_T']), 1)} % menos que la regla, y el makespan "
                  f"a {n(indic['Cmax'], 1)} h" if indic['suma_Ti'] > 1e-6 else
                  f'eliminó la tardanza en la generación {gen_cero}') if D['regla_T'] > 1e-6 else
                 f"redujo el makespan a {n(indic['Cmax'], 1)} h, "
                 f"{n(100 * (D['regla_C'] - indic['Cmax']) / D['regla_C'], 1)} % menos que la regla, "
                 'manteniendo la tardanza en cero')
              + '. La Tabla {T:tamanos} presenta los tamaños de '
              'sublote, iguales en las cuatro etapas, y la Tabla {T:orden} los resultados por orden.'),
        ('tabla', 'Tamaños de los sublotes de la programación propuesta [docenas]',
         ['Orden'] + [f'S{b}' for b in range(1, 11)] + ['Total'], filas_tam,
         {'etiqueta': 'tamanos', 'anchos': [800] + [690] * 10 + [1138], 'tam': 9}),
        ('tabla', 'Resultados por orden de la programación propuesta',
         ['Orden', 'Ref.', 'Q_j (doc.)', 'd_j (h)', 'Entrega', 'C_j (h)', 'Terminación',
          'T_j (h)', 'E_j (h)'], filas_ord,
         {'etiqueta': 'orden', 'anchos': [780, 700, 900, 800, 1250, 950, 1300, 1000, 1158], 'tam': 9}),
        ('p', ('Ninguna orden termina después de su fecha de entrega. ' if indic['num_tardy'] == 0 else
               f"{_lista(tardias)} terminan después de su fecha de entrega, con "
               f"{_lista([n(indic['por_trabajo'][j]['Ti'], 1) for j in tardias])} h de retraso"
               f"{' respectivamente' if len(tardias) > 1 else ''}; las demás órdenes se entregan a tiempo. ")
              + 'La Tabla {T:indicadores} resume '
              'los indicadores globales; la ocupación de cada etapa es su tiempo de procesamiento '
              'dividido entre el número de máquinas por el makespan. '
              + (f'Troquelado, el cuello de botella identificado en la caracterización, tiene la mayor '
                 f'ocupación ({n(mayor[3], 1)} %).' if mayor[0].lower() == 'troquelado' else
                 f'La etapa con mayor ocupación es {mayor[0].lower()} ({n(mayor[3], 1)} %).')
              + ' La Figura {F:gantt} presenta el diagrama de Gantt.'),
        ('tabla', 'Indicadores globales de la programación propuesta', ['Indicador', 'Valor'], [
            ['Tardanza total (ΣT_j) / órdenes tardías',
             f'{n(indic["suma_Ti"], 2)} h / {indic["num_tardy"]} de {len(M.TRABAJOS)}'],
            ['Makespan (C_max)', f'{n(indic["Cmax"], 1)} h ({fecha(indic["Cmax"])})'],
            ['Adelanto total (ΣE_j)', f'{n(indic["suma_Ei"], 1)} h'],
            ['Tiempo de flujo medio', f'{n(indic["media_Fi"], 1)} h'],
            ['Alistamientos en troquelado', f'{len(al)} ({n(sum(f - i for (_, _, i, f) in al), 1)} h)']]
         + [[f'Ocupación de {u[0].lower()} ({u[1]} máquinas)', f'{n(u[3], 1)} %'] for u in util.values()],
         {'etiqueta': 'indicadores', 'anchos': [5000, 3838], 'alineacion': ['l', 'c']}),
        ('figura', 'Diagrama de Gantt de la programación propuesta (las líneas punteadas marcan las '
                   'fechas de entrega)', os.path.join(G.SAL_SOL, 'gantt_solucion.png'), 14.5, 'gantt'),
        ('p', 'En síntesis, la fase produjo un modelo matemático que representa el Flow Shop híbrido '
              'de la empresa con sublotes consistentes, y un algoritmo genético verificado, validado '
              'frente a soluciones óptimas y calibrado estadísticamente, que en el caso de estudio '
              + ('entrega una programación sin órdenes tardías' if indic['num_tardy'] == 0 else
                 f"reduce la tardanza total de {n(D['regla_T'], 1)} h, con la mejor regla de despacho, a "
                 f"{n(indic['suma_Ti'], 1)} h")
              + '. Su comparación con el sistema de '
              'programación actual se presenta en la Fase 3.'),
    ]


def datos_documento(M, rep):
    """Valores calculados desde la base de datos, el modelo y los resultados."""
    criterio = {'EDD': r'Menor $d_j$', 'FIFO': 'Orden de liberación', 'CR': r'Menor $d_j/P_j$',
                'SPT': r'Menor $P_j$', 'MST': r'Menor $d_j-P_j$', 'LPT': r'Mayor $P_j$'}
    b_orig = M.NUM_SUBLOTES
    M.NUM_SUBLOTES = 10
    reglas = sorted(M.evaluar_reglas(), key=lambda r: (r['suma_Ti'], r['Cmax']))
    filas_reglas = [[r['regla'], criterio[r['regla']], n(r['suma_Ti'], 2), n(r['Tmax'], 2),
                     n(r['Cmax'], 2), str(r['num_tardy'])] for r in reglas]
    mejor = reglas[0]
    if mejor['suma_Ti'] <= 1e-6:
        texto_reglas = (f"La regla {mejor['regla']} ya cumple todas las fechas de entrega con sublotes "
                        f"iguales (makespan de {n(mejor['Cmax'], 1)} h); el algoritmo parte de esa solución "
                        'y busca reducir el makespan sin generar tardanza.')
    else:
        texto_reglas = (f"La regla {mejor['regla']} obtiene la menor tardanza "
                        f"({n(mejor['suma_Ti'], 1)} h) y siembra la población.")
    filas_bbar = []
    for B in (1, 2, 5, 10, 20):
        M.NUM_SUBLOTES = B
        sec = M.secuencias_reglas()
        celdas = []
        for rg in ('FIFO', 'EDD', 'CR', 'SPT'):
            r = M.calcular_indicadores(M.simular_hfs(M.individuo_regla_ls(sec[rg]))[0])
            celdas.append(f"{n(r['suma_Ti'], 0)} ({r['num_tardy']})")
        filas_bbar.append([str(B)] + celdas)
    M.NUM_SUBLOTES = b_orig
    prom = {j: M.DEMANDA[j] / 10 for j in M.TRABAJOS}
    jmin, jmax = min(prom, key=prom.get), max(prom, key=prom.get)
    minutos = rep['segundos'] / 60
    return {
        'params': dict(M.GA_PARAMS), 'filas_reglas': filas_reglas, 'texto_reglas': texto_reglas,
        'regla_mejor': mejor['regla'], 'regla_T': mejor['suma_Ti'], 'regla_C': mejor['Cmax'],
        'filas_bbar': filas_bbar,
        'sub_min': f"{n(prom[jmin], 0)} docenas ({jmin})", 'sub_max': f"{n(prom[jmax], 0)} docenas ({jmax})",
        't_min': max(1, int(minutos.min())), 't_max': int(minutos.max()) + 1,
    }


def main():
    from correcciones_fase1 import corregir_fase1, insertar_figura1, insertar_figura_ocupacion
    import figuras_documento as FD
    borrador, salida, ruta_modelo, ruta_bd = sys.argv[1:5]
    M, rep, mejor, indic, tam, util, al = G.datos_solucion(ruta_modelo, ruta_bd)
    D = datos_documento(M, rep)
    import figuras_documento as FD
    from fase3_doc import F as _F3
    figs = FD.generar(M, indic, ruta_bd, _F3.B_ACTUAL_BASE)
    from fase3_doc import fase3
    from capitulos_finales import capitulos
    bloques = modelo() + algoritmo(D) + validacion() + calibracion(D) + \
        solucion(M, rep, mejor, indic, tam, util, al, D) + fase3(M) + \
        capitulos(M, ruta_bd, indic, rep, D, _datos_validacion()[1])
    bloques = L.resolver_referencias(bloques, tabla_ini=5, figura_ini=4)
    bloques = L.matematizar(bloques)
    d = docx.Document(borrador)
    for h in corregir_fase1(d, ruta_bd):
        print('Fase 1 corregida:', h)
    print('Fase 1:', insertar_figura1(d))
    print('Fase 1:', insertar_figura_ocupacion(d, figs['ocupacion']))
    L.quitar_desde(d, 'Construcción del modelo matemático')
    omml = L.latex_a_omml(L.recolectar_latex(bloques))
    esc = L.Escritor(d, omml, primer_figura=4, primer_tabla=5)
    L.escribir(esc, bloques)
    L.normalizar_orden(d)
    d.save(salida)
    print(f'Tablas: 5–{4 + esc.tabla_n} | Figuras: 4–{3 + esc.figura_n} | Guardado en {salida}')


if __name__ == '__main__':
    main()
