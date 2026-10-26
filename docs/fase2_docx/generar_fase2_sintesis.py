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


def algoritmo():
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
            '         Np = 150, pc = 0,9, pm = 0,5, k = 3, Gsm = 100, Gmáx = 1.000',
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
            '**Decodificar(c)**',
            '   convertir π en docenas enteras (método del mayor residuo)',
            '   para s = 1 hasta 4, para cada sublote (j, b) en el orden O(s):',
            '      listo ← r(j) si s = 1; si no, terminación de (j, b) en la etapa s − 1',
            '      para cada máquina m de la etapa s:',
            '         troquelado: inicio ← máx(libre(m) + alistamiento, listo)',
            '         otras etapas: inicio ← primer hueco libre de m desde listo',
            '         fin(m) ← inicio + a(j,m)·x(j,b)',
            '      asignar (j, b) a la máquina con menor fin(m)       ▹ regla ECT',
            '   C(j) ← máx_b fin(j, b);  T(j) ← máx(0, C(j) − d(j));  calcular ΣT y Cmax'],
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
              'docenas.'),
        ('h4', 'Decodificación y aptitud'),
        ('p', r'El decodificador programa las etapas en orden. En cada etapa toma los sublotes en el '
              r'orden $O_s$ y, para cada uno, calcula en cada máquina el inicio posible a partir del '
              'momento en que el sublote está disponible (la liberación de la orden en troquelado o '
              'su terminación en la etapa anterior). En troquelado, el sublote se ubica después del '
              'último de la máquina y se suma el alistamiento si cambia la referencia; en las demás '
              'etapas ocupa el primer intervalo libre. El sublote se asigna a la máquina en la que '
              'termina primero. La programación resultante cumple por construcción todas las '
              'restricciones del modelo. La aptitud de un cromosoma es el par (ΣT_j, C_max) de su '
              'programación, comparado de forma lexicográfica.'),
        ('h4', 'Población inicial'),
        ('p', 'La población tiene 150 cromosomas: 149 aleatorios y uno construido con la mejor de seis '
              'reglas de despacho aplicadas con sublotes iguales y la misma secuencia de órdenes en '
              r'todas las etapas (Tabla {T:reglas}), donde $P_j$ es el tiempo de la orden completa en '
              'la máquina más rápida de cada etapa. La regla EDD obtiene la menor tardanza y siembra la '
              'población, lo que acelera la convergencia sin perder la diversidad que aportan los '
              'cromosomas aleatorios.'),
        ('tabla', 'Reglas de despacho en la instancia del caso de estudio (10 sublotes iguales por orden)',
         ['Regla', 'Criterio de prioridad', 'ΣT_j (h)', 'T_max (h)', 'C_max (h)', 'Tardías'], [
             ['EDD', r'Menor $d_j$', '145,00', '145,00', '817,00', '1'],
             ['FIFO', 'Orden de liberación', '242,48', '135,27', '620,64', '2'],
             ['CR', r'Menor $d_j/P_j$', '244,18', '164,33', '591,33', '2'],
             ['SPT', r'Menor $P_j$', '253,61', '162,69', '834,69', '3'],
             ['MST', r'Menor $d_j-P_j$', '311,70', '159,86', '587,27', '2'],
             ['LPT', r'Mayor $P_j$', '341,32', '179,24', '589,08', '2']],
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
            'se detiene tras 100 generaciones sin mejora o al llegar a 1.000 generaciones.']),
        ('h4', 'Implementación'),
        ('p', 'El algoritmo se implementó en Python 3. Los datos se leen del libro de Excel '
              'BD_HFS.xlsx, con tres hojas: tiempos estándar por referencia y máquina, órdenes de '
              'trabajo (cantidad, liberación y fecha de entrega) y calendario laboral. Así, la empresa '
              'puede actualizar la información sin modificar el código. El programa entrega los '
              'tamaños de los sublotes, los indicadores por orden y globales, la programación por '
              'máquina y el diagrama de Gantt. Con los parámetros calibrados, una corrida en la '
              'instancia real toma entre 2 y 8 minutos en un computador de 4 núcleos. '
              '[[El código se incluye en el Anexo X.]]'),
    ]


def validacion():
    return [
        ('h3', 'Verificación y validación'),
        ('p', '**Verificación.** Un verificador independiente revisó, en las programaciones producidas '
              'por el decodificador, cada restricción del modelo: tamaños de sublote, asignación de '
              'máquinas, tiempos de proceso, liberaciones, precedencia entre etapas, no solapamiento y '
              'alistamientos. Se aplicó a 200 cromosomas aleatorios de la instancia real y a las seis '
              'reglas de despacho, sin encontrar violaciones.'),
        ('p', '**Validación con instancias reducidas.** Se construyeron nueve instancias con los '
              'tiempos estándar reales, de 3 a 5 órdenes (5 a 8 docenas cada una), de 4 a 15 '
              'sublotes y un subconjunto de máquinas por etapa que incluye máquinas de ensamble de '
              'distinta velocidad. El modelo matemático se resolvió con el solver HiGHS (límite de '
              '10 minutos por objetivo) y, para confirmar los óptimos, con una formulación '
              'equivalente de precedencia general (Naderi et al., 2014). El algoritmo genético se '
              'corrió 10 veces en cada instancia. La Tabla {T:validacion} resume los resultados.'),
        ('tabla', 'Validación: modelo exacto frente al algoritmo genético',
         ['Inst.', 'Sublotes', 'Óptimo exacto ΣT_j / C_max (h)', 'Mejor regla ΣT_j (h)',
          'AG mejor ΣT_j / C_max (h)', 'AG prom. ΣT_j (h)', 'Réplicas AG ≤ referencia',
          'Tiempo AG (s)'], [
             ['I1', '4 (sin división)', '28,190 / 19,836', '30,439', '28,190 / 19,836', '28,306', '7/10', '0,9'],
             ['I2', '5 (sin división)', '34,374 / 21,794', '37,635', '34,374 / 21,794', '34,428', '9/10', '1,1'],
             ['I3', '6', '0,955 / 15,955', '2,067', '0,955 / 15,955', '1,169', '4/10', '1,4'],
             ['I4', '6', '3,861 / 12,082', '4,149', '3,861 / 12,082', '3,861', '10/10', '1,3'],
             ['I5', '8', '1,113 / 20,158', '3,325', '1,113 / 20,158', '1,247', '7/10', '2,3'],
             ['I6', '8', 'No demostrado (5,928 / 13,942)', '6,682', '5,928 / 13,942', '6,080', '7/10', '2,1'],
             ['I7', '9', '0,000 / 14,399', '0,404', '0,000 / 14,496', '0,000', '10/10', '2,9'],
             ['I8', '12', 'No demostrado (3,142 / 12,780)', '2,341', '1,214 / 12,114', '1,336', '10/10', '3,8'],
             ['I9', '15', 'No demostrado (8,077 / 15,847)', '2,666', '1,214 / 13,857', '1,468', '10/10', '4,0']],
         {'etiqueta': 'validacion', 'anchos': [620, 1000, 1880, 900, 1480, 900, 1200, 858],
          'alineacion': ['l'] + ['c'] * 7, 'tam': 9}),
        ('p', 'La referencia es el óptimo exacto o, si no se demostró en el tiempo límite, la mejor '
              'solución exacta encontrada (entre paréntesis). Los resultados permiten concluir que:'),
        ('viñetas', [
            '**El modelo está bien formulado:** todas sus soluciones cumplieron las restricciones, y '
            'las dos formulaciones coincidieron en el óptimo.',
            '**El algoritmo alcanza el óptimo:** en las seis instancias con óptimo conocido, la mejor '
            'réplica obtuvo la tardanza óptima, y 47 de 60 réplicas (78 %) la alcanzaron. La única '
            'diferencia fue el makespan de I7, 0,7 % mayor con la tardanza en cero.',
            '**El método exacto no escala:** con 12 y 15 sublotes, la formulación propuesta no '
            'encontró ninguna solución factible en 10 minutos, mientras que el algoritmo obtuvo en '
            'menos de 4 segundos soluciones mejores que las del solver. La instancia real, con 100 '
            'sublotes, solo es abordable con el algoritmo.',
            '**Dividir en sublotes reduce la tardanza:** con las mismas cuatro órdenes, la tardanza '
            'óptima baja de 28,19 h sin división (I1) a 5,93 h con dos sublotes (I6) y a 1,21 h con '
            'tres (I8).']),
    ]


def calibracion():
    return [
        ('h3', 'Número de sublotes y calibración del algoritmo'),
        ('h4', 'Número de sublotes por orden'),
        ('p', r'El número de sublotes $\overline{B}$ define cuánto se divide cada orden. La Tabla '
              '{T:bbar} muestra su efecto en la instancia real con las reglas de despacho: sin '
              'división todas las órdenes resultan tardías, y la tardanza baja a medida que el '
              r'trabajo se reparte entre las máquinas paralelas. Se adopta $\overline{B}=10$, con '
              'sublotes promedio entre 21 docenas (J09) y 117 docenas (J01). [[Confirmar con la '
              'práctica de la planta el tamaño habitual de los paquetes que pasan entre puestos.]] '
              'El efecto de este parámetro se analiza en la Fase 3.'),
        ('tabla', 'Tardanza total (h) y órdenes tardías de las reglas de despacho según el número '
                  'de sublotes por orden',
         ['B̄', 'FIFO', 'EDD', 'CR', 'SPT'], [
             ['1', '8.490 (10)', '8.316 (10)', '8.741 (10)', '8.353 (10)'],
             ['2', '3.051 (10)', '3.203 (9)', '3.743 (10)', '2.939 (8)'],
             ['5', '704 (6)', '495 (3)', '798 (7)', '809 (4)'],
             ['10', '242 (2)', '145 (1)', '244 (2)', '254 (3)'],
             ['20', '141 (2)', '17 (1)', '131 (2)', '66 (2)']],
         {'etiqueta': 'bbar', 'anchos': [1238, 1900, 1900, 1900, 1900]}),
        ('h4', 'Calibración de los parámetros'),
        ('p', 'Los parámetros del algoritmo se calibraron con un diseño factorial completo 3³ sobre '
              'la instancia real (Montgomery, 2017; Ruiz, Maroto y Alcaraz, 2006): tamaño de '
              r'población (50, 100 y 150), probabilidad de cruce $p_c$ (0,7; 0,8 y 0,9) y '
              r'probabilidad de mutación $p_m$ (0,1; 0,3 y 0,5), con 5 réplicas por combinación '
              '(135 corridas). Todas las corridas tuvieron el mismo esfuerzo de cómputo (30.000 '
              'cromosomas generados) para que una población grande no tuviera ventaja solo por '
              'evaluar más soluciones, y cada réplica usó la misma semilla en todas las '
              'combinaciones. La variable de respuesta fue la tardanza total. La Tabla {T:anova} '
              'presenta el ANOVA.'),
        ('tabla', 'ANOVA de la tardanza total en el diseño factorial',
         ['Fuente', 'SC', 'gl', 'CM', 'F', 'Valor p'], [
             ['Población', '26.514,5', '2', '13.257,3', '20,65', '< 0,001'],
             ['Probabilidad de cruce', '2.702,8', '2', '1.351,4', '2,10', '0,127'],
             ['Probabilidad de mutación', '11.110,5', '2', '5.555,2', '8,65', '< 0,001'],
             ['Población × cruce', '4.076,3', '4', '1.019,1', '1,59', '0,182'],
             ['Población × mutación', '2.254,8', '4', '563,7', '0,88', '0,480'],
             ['Cruce × mutación', '688,1', '4', '172,0', '0,27', '0,898'],
             ['Error', '74.484,3', '116', '642,1', '', ''],
             ['Total', '121.831,3', '134', '', '', '']],
         {'etiqueta': 'anova', 'anchos': [2838, 1300, 800, 1300, 1200, 1400]}),
        ('p', 'La población y la probabilidad de mutación tienen efecto significativo sobre la '
              'tardanza (p < 0,001); la probabilidad de cruce y las interacciones no lo tienen. Los '
              'residuos son normales (Shapiro-Wilk, p = 0,459), pero las varianzas no son homogéneas '
              'entre niveles, por lo que el resultado se confirmó con la prueba no paramétrica de '
              'Kruskal-Wallis, que coincide con el ANOVA. Como muestra la Figura {F:efectos}, la '
              'tardanza disminuye al aumentar la población y la mutación. La combinación de población '
              '150, cruce 0,9 y mutación 0,5 fue la única que eliminó la tardanza en las cinco '
              'réplicas (makespan promedio de 652,3 h).'),
        ('figura', 'Efectos principales sobre la tardanza total (intervalos LSD al 95 %)',
         os.path.join(G.SAL_CAL, 'efectos_principales.png'), 15.5, 'efectos'),
        ('p', 'Como la mejor combinación quedó en el límite superior del rango probado, se evaluaron '
              'además poblaciones de 200 y 250 y una mutación de 0,7. Ninguna mejoró de forma '
              'significativa (prueba de Wilcoxon, p ≥ 0,06) y las más altas empeoraron, de modo que '
              'se conservó la población de 150. Por último, con esta configuración se compararon tres '
              'criterios de parada (Tabla {T:parada}).'),
        ('tabla', 'Criterio de parada (10 réplicas por criterio)',
         ['Generaciones sin mejora', 'Réplicas con ΣT_j = 0', 'C_max prom. (h)',
          'Generaciones prom.', 'Tiempo prom. (min)'], [
             ['50', '10/10', '650,8', '388', '3,1'],
             ['100', '10/10', '644,5', '633', '5,0'],
             ['200', '10/10', '642,7', '855', '6,6']],
         {'etiqueta': 'parada', 'anchos': [2000, 1700, 1700, 1700, 1738], 'negrita_filas': (1,)}),
        ('p', 'Todas las corridas eliminaron la tardanza. Pasar de 50 a 100 generaciones sin mejora '
              'redujo el makespan de forma significativa (Wilcoxon, p = 0,016), mientras que pasar a '
              '200 no lo hizo (p = 0,063) y aumentó el tiempo en 33 %. La Tabla {T:final} resume la '
              'configuración final.'),
        ('tabla', 'Configuración final del algoritmo genético', ['Parámetro', 'Valor'], [
            ['Tamaño de la población', '150'],
            ['Probabilidad de cruce', '0,9'],
            ['Probabilidad de mutación', '0,5'],
            ['Criterio de parada', '100 generaciones sin mejora (máximo 1.000)'],
            ['Tamaño del torneo', '3'],
            ['Probabilidad de intercambio / de perturbación (desviación)', '0,30 / 0,40 (0,15)']],
         {'etiqueta': 'final', 'anchos': [5000, 3838], 'alineacion': ['l', 'c']}),
    ]


def solucion(M, rep, mejor, indic, tam, util, al):
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
    return [
        ('h3', 'Programación obtenida para el caso de estudio'),
        ('p', f'Con la configuración calibrada, el algoritmo se ejecutó {len(rep)} veces sobre la '
              'instancia real. '
              + ('Todas las réplicas eliminaron la tardanza; '
                 if tard == len(rep) else f'{tard} de {len(rep)} réplicas eliminaron la tardanza; ')
              + f'el makespan varió entre {n(rep["Cmax"].min(), 1)} y {n(rep["Cmax"].max(), 1)} h '
              f'(promedio de {n(rep["Cmax"].mean(), 1)} h) y cada corrida tomó en promedio '
              f'{n(rep["segundos"].mean() / 60, 1)} minutos. La mejor programación, que se propone '
              f'para el conjunto de órdenes, partió de la regla EDD (145 h de tardanza) y eliminó la '
              f'tardanza en la generación {gen_cero}. La Tabla {{T:tamanos}} presenta los tamaños de '
              'sublote, iguales en las cuatro etapas, y la Tabla {T:orden} los resultados por orden.'),
        ('tabla', 'Tamaños de los sublotes de la programación propuesta [docenas]',
         ['Orden'] + [f'S{b}' for b in range(1, 11)] + ['Total'], filas_tam,
         {'etiqueta': 'tamanos', 'anchos': [800] + [690] * 10 + [1138], 'tam': 9}),
        ('tabla', 'Resultados por orden de la programación propuesta',
         ['Orden', 'Ref.', 'Q_j (doc.)', 'd_j (h)', 'Entrega', 'C_j (h)', 'Terminación',
          'T_j (h)', 'E_j (h)'], filas_ord,
         {'etiqueta': 'orden', 'anchos': [780, 700, 900, 800, 1250, 950, 1300, 1000, 1158], 'tam': 9}),
        ('p', 'Ninguna orden termina después de su fecha de entrega. La Tabla {T:indicadores} resume '
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
              'entrega una programación sin órdenes tardías. Su comparación con el sistema de '
              'programación actual se presenta en la Fase 3.'),
    ]


def main():
    borrador, salida, ruta_modelo, ruta_bd = sys.argv[1:5]
    M, rep, mejor, indic, tam, util, al = G.datos_solucion(ruta_modelo, ruta_bd)
    bloques = modelo() + algoritmo() + validacion() + calibracion() + \
        solucion(M, rep, mejor, indic, tam, util, al)
    bloques = L.resolver_referencias(bloques, tabla_ini=5, figura_ini=3)
    bloques = L.matematizar(bloques)
    d = docx.Document(borrador)
    L.quitar_desde(d, 'Construcción del modelo matemático')
    omml = L.latex_a_omml(L.recolectar_latex(bloques))
    esc = L.Escritor(d, omml, primer_figura=3)
    L.escribir(esc, bloques)
    L.normalizar_orden(d)
    d.save(salida)
    print(f'Tablas: 5–{4 + esc.tabla_n} | Figuras: 3–{2 + esc.figura_n} | Guardado en {salida}')


if __name__ == '__main__':
    main()
