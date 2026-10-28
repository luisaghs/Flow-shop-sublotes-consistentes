# -*- coding: utf-8 -*-
"""
Genera la Fase 2 del trabajo de grado dentro de una copia del borrador.

Uso:
  python generar_fase2.py borrador.docx salida.docx ruta/modelo.py ruta/BD_HFS.xlsx

Reemplaza desde el encabezado "Construcción del modelo matemático" hasta el
final del borrador por la Fase 2 completa (el resto del documento no cambia).
"""
import io
import json
import os
import sys
import contextlib
import importlib.util

import docx
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_docx as L                                                   # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FIG = os.path.join(RAIZ, 'docs', 'fase2_figuras')
SAL_VAL = os.path.join(RAIZ, 'fase2', 'salida_validacion')
SAL_CAL = os.path.join(RAIZ, 'fase2', 'salida_calibracion')
SAL_SOL = os.path.join(RAIZ, 'fase2', 'salida_solucion')


def n(x, dec=2):
    """Número con coma decimal y punto de miles."""
    s = f"{x:,.{dec}f}"
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


# ===========================================================================
# 1. Introducción y modelo matemático
# ===========================================================================

def bloque_modelo():
    B = []
    B += [('h2', 'Construcción del modelo matemático y del algoritmo genético'),
          ('p', 'Esta fase da cumplimiento al segundo objetivo específico: construir un modelo '
                'matemático y definir los operadores adecuados para representar y resolver el '
                'problema de programación del Flow Shop híbrido caracterizado en la fase anterior. '
                'El desarrollo tiene dos componentes complementarios. El primero es un modelo de '
                'programación lineal entera mixta (MILP) que representa de forma rigurosa el '
                'problema: la división de las órdenes en sublotes, la asignación de máquinas, la '
                'secuenciación, las restricciones del sistema y el criterio de desempeño. El segundo '
                'es un algoritmo genético (AG) que resuelve el problema a la escala real de la '
                'empresa, donde el modelo exacto no es tratable en un tiempo razonable.'),
          ('p', 'La fase se organiza en siete partes: (i) la formulación del modelo matemático; '
                '(ii) el análisis de su tamaño y la selección del método de solución; (iii) el '
                'diseño del algoritmo genético y de sus operadores; (iv) la implementación '
                'computacional; (v) la verificación y validación del modelo, mediante la '
                'comparación con soluciones óptimas en instancias reducidas; (vi) la calibración '
                'de los parámetros del algoritmo, y (vii) la programación obtenida para el '
                'conjunto de órdenes del caso de estudio.')]

    B += [('h3', 'Modelo matemático'),
          ('p', 'El modelo toma como base la formulación con sublotes consistentes para el Flow '
                'Shop híbrido de Gürsoy Yılmaz y Yılmaz (2022) e incorpora los elementos propios '
                'del sistema estudiado: las fechas de liberación de las órdenes, el alistamiento '
                'dependiente de la secuencia en troquelado, las máquinas no relacionadas de '
                'ensamble y la minimización de la tardanza total.'),
          ('p', 'El modelo permite dividir cada orden en sublotes que avanzan por las etapas de '
                'manera independiente, técnica conocida como *lot streaming*; así, un sublote '
                'puede iniciar en ensamble mientras el resto de la orden continúa en troquelado. '
                'Se adopta el esquema de sublotes consistentes, en el que los sublotes de una '
                'orden pueden tener tamaños distintos entre sí, pero cada sublote conserva su '
                'tamaño en todas las etapas. Este esquema ofrece más flexibilidad que los sublotes '
                'iguales y es más sencillo de implementar en planta que los sublotes variables, '
                'cuyo tamaño cambia de una etapa a otra (Gürsoy Yılmaz y Yılmaz, 2022).'),
          ('h4', 'Supuestos de la división en sublotes'),
          ('p', 'Además de las restricciones y supuestos del sistema establecidos en la fase de '
                'caracterización, la división en sublotes se rige por las siguientes condiciones:'),
          ('viñetas', [
              r'Cada orden $j$ se divide en un número fijo de sublotes $B_j$.',
              'Los tamaños de los sublotes de una orden pueden ser distintos entre sí, pero cada '
              'sublote conserva su tamaño en las cuatro etapas.',
              r'Los tamaños se expresan en docenas enteras, con un mínimo de $q^{\min}=1$ docena.',
              'En cada etapa, un sublote se procesa completo en una sola máquina y sin interrupción.',
              'Un sublote pasa a la etapa siguiente en cuanto termina la etapa actual, sin esperar '
              'a los demás sublotes de su orden.',
              'Los sublotes de distintas órdenes pueden intercalarse en una misma máquina.',
              'Cada máquina de troquelado requiere un alistamiento inicial antes de su primer '
              'sublote y un alistamiento cada vez que cambia la referencia; dos sublotes '
              'consecutivos de la misma referencia no lo requieren.',
              'El alistamiento puede realizarse mientras la máquina espera la llegada del sublote '
              '(alistamiento anticipatorio; Allahverdi et al., 2008).',
              'El modelo decide el tamaño de cada sublote, la máquina que lo procesa en cada etapa '
              'y el orden de los sublotes en cada máquina.']),
          ('h4', 'Conjuntos e índices'),
          ('tabla', 'Conjuntos e índices del modelo', ['Símbolo', 'Descripción'], [
              [r'$j, j^{\prime} \in J$', r'Órdenes de trabajo ($|J|=10$).'],
              [r'$s \in S=\{1,\dots,|S|\}$', 'Etapas de la ruta: 1 troquelado, 2 ensamble, '
                                              '3 costura y 4 volteado.'],
              [r'$m \in M_s$', r'Máquinas de la etapa $s$ ($|M_1|=4$, $|M_2|=15$, $|M_3|=9$, '
                               r'$|M_4|=8$).'],
              [r'$b \in \{1,\dots,B_j\}$', r'Sublotes de la orden $j$.'],
              [r'$i, i^{\prime} \in N$', r'Conjunto de todos los sublotes; $i=(j,b)$, '
                                         r'$i^{\prime}=(j^{\prime},b^{\prime})$.'],
              ['0', 'Sublote ficticio que representa el inicio de la secuencia de cada máquina.']],
           {'anchos': [2600, 6238], 'alineacion': ['l', 'l']}),
          ('h4', 'Parámetros'),
          ('tabla', 'Parámetros del modelo', ['Símbolo', 'Descripción'], [
              [r'$Q_j$', r'Cantidad de la orden $j$ [docenas].'],
              [r'$p_j$', r'Referencia (código de producto) de la orden $j$.'],
              [r'$r_j$', r'Liberación de la orden $j$: horas laborables acumuladas al inicio del '
                         r'día de liberación [h].'],
              [r'$d_j$', r'Fecha de entrega de la orden $j$: horas laborables acumuladas al final '
                         r'del día de entrega [h].'],
              [r'$a_{jm}$', r'Tiempo estándar de procesamiento por docena de la referencia de la '
                            r'orden $j$ en la máquina $m$ [h/docena].'],
              [r'$q^{\min}$', 'Tamaño mínimo de sublote [docenas] (1 docena).'],
              [r'$\overline{B}$', r'Número máximo de sublotes por orden ($\overline{B}=10$).'],
              [r'$B_j$', r'Número de sublotes de la orden $j$: '
                         r'$B_j=\max\{1,\min\{\overline{B},\lfloor Q_j/q^{\min}\rfloor\}\}$.'],
              [r'$\sigma$', 'Tiempo de alistamiento en troquelado: 4,98 min (0,083 h).'],
              [r'$\sigma_{ii^{\prime}}$', r'Alistamiento cuando $i$ precede inmediatamente a '
                                          r'$i^{\prime}$ en una máquina de troquelado: $\sigma$ si '
                                          r'$p_j\neq p_{j^{\prime}}$ y 0 si $p_j=p_{j^{\prime}}$; '
                                          r'$\sigma_{0i^{\prime}}=\sigma$ (montaje inicial).'],
              [r'$H$', 'Constante suficientemente grande: cota superior del horizonte de '
                       'programación [h].']],
           {'anchos': [1500, 7338], 'alineacion': ['l', 'l']}),
          ('h4', 'Variables de decisión'),
          ('tabla', 'Variables de decisión del modelo', ['Variable', 'Descripción'], [
              [r'$x_{jb}\in\{0,1,2,\dots\}$', r'Tamaño del sublote $b$ de la orden $j$ [docenas].'],
              [r'$y_{ism}\in\{0,1\}$', r'1 si el sublote $i$ se procesa en la máquina $m$ de la '
                                       r'etapa $s$; 0 en caso contrario.'],
              [r'$z_{ii^{\prime}sm}\in\{0,1\}$', r'1 si el sublote $i$ precede inmediatamente a '
                                                 r'$i^{\prime}$ en la máquina $m$ de la etapa $s$ '
                                                 r'($i=0$ indica que $i^{\prime}$ es el primero).'],
              [r'$S_{is},\,C_{is}\ge 0$', r'Inicio y terminación del sublote $i$ en la etapa $s$ '
                                          r'[h].'],
              [r'$T_j\ge 0$', r'Tardanza de la orden $j$ [h].'],
              [r'$C_{\max}\ge 0$', 'Makespan: terminación del último sublote en la última '
                                   'etapa [h].']],
           {'anchos': [2600, 6238], 'alineacion': ['l', 'l']})]

    B += [('h4', 'Función objetivo'),
          ('p', 'El criterio de desempeño es la tardanza total. Como pueden existir varias '
                'programaciones con la misma tardanza total, se usa un objetivo lexicográfico: '
                'primero se minimiza la tardanza total y, entre las soluciones con igual tardanza, '
                'se prefiere la de menor makespan, lo que libera antes la capacidad del sistema '
                'para nuevas órdenes.'),
          ('ecuacion', r'\operatorname{lex\,min}\left(\sum_{j\in J}T_j,\; C_{\max}\right)', '', 1),
          ('h4', 'Restricciones'),
          ('p', '**Tamaño de los sublotes.** Los sublotes de cada orden suman su cantidad (2) y '
                'respetan el tamaño mínimo (3).'),
          ('ecuacion', r'\sum_{b=1}^{B_j}x_{jb}=Q_j', r'$\forall j\in J$', 2),
          ('ecuacion', r'x_{jb}\ge q^{\min}', r'$\forall j\in J,\; b=1,\dots,B_j$', 3),
          ('p', '**Asignación de máquinas.** En cada etapa, cada sublote se procesa en exactamente '
                'una máquina.'),
          ('ecuacion', r'\sum_{m\in M_s}y_{ism}=1', r'$\forall i\in N,\; s\in S$', 4),
          ('p', r'**Tiempo de procesamiento.** Si el sublote $i=(j,b)$ se asigna a la máquina $m$, '
                'termina después de su tiempo de procesamiento en esa máquina, que es proporcional '
                'a su tamaño; para las demás máquinas la restricción queda desactivada por la '
                r'constante $H$. Así se representa la diferencia de velocidad de las máquinas no '
                'relacionadas de ensamble.'),
          ('ecuacion', r'C_{is}\ge S_{is}+a_{jm}\,x_{jb}-H\,(1-y_{ism})',
           r'$\forall i=(j,b)\in N$;; $s\in S,\; m\in M_s$', 5),
          ('p', '**Liberación y precedencia entre etapas.** Ningún sublote inicia antes de la '
                'liberación de su orden (6), y cada sublote inicia una etapa solo cuando terminó la '
                'anterior (7). La restricción (7) se aplica a cada sublote por separado: el sublote '
                'pasa a la etapa siguiente sin esperar a los demás sublotes de su orden, que es la '
                'esencia del *lot streaming*.'),
          ('ecuacion', r'S_{i1}\ge r_j', r'$\forall i=(j,b)\in N$', 6),
          ('ecuacion', r'S_{i,s+1}\ge C_{is}', r'$\forall i\in N,\; s=1,\dots,|S|-1$', 7),
          ('p', '**Secuencia en cada máquina.** Cada sublote asignado a una máquina tiene '
                'exactamente un antecesor inmediato, que puede ser el inicio ficticio 0 (8); cada '
                'sublote tiene a lo sumo un sucesor en la máquina (9), y cada máquina tiene a lo '
                'sumo un primer sublote (10).'),
          ('ecuacion', r'\sum_{i\in N\cup\{0\},\; i\neq i^{\prime}}z_{ii^{\prime}sm}=y_{i^{\prime}sm}',
           r'$\forall s\in S,\; m\in M_s$;; $i^{\prime}\in N$', 8),
          ('ecuacion', r'\sum_{i^{\prime}\in N,\; i^{\prime}\neq i}z_{ii^{\prime}sm}\le y_{ism}',
           r'$\forall s\in S,\; m\in M_s$;; $i\in N$', 9),
          ('ecuacion', r'\sum_{i^{\prime}\in N}z_{0i^{\prime}sm}\le 1', r'$\forall s\in S,\; m\in M_s$', 10),
          ('p', r'**No solapamiento y alistamientos.** Si $i$ precede inmediatamente a $i^{\prime}$ '
                r'en una máquina de troquelado, $i^{\prime}$ inicia después de que termina $i$ más '
                'el alistamiento por cambio de referencia (11); el primer sublote de cada máquina de '
                'troquelado requiere el montaje inicial (12). En las etapas 2 a 4 no hay alistamiento '
                r'y basta con que $i^{\prime}$ inicie después de que termina $i$ (13). El alistamiento '
                'se cuenta desde que la máquina queda libre, de modo que puede superponerse con la '
                'espera del sublote.'),
          ('ecuacion', r'S_{i^{\prime}1}\ge C_{i1}+\sigma_{ii^{\prime}}-H\,(1-z_{ii^{\prime}1m})',
           r'$\forall m\in M_1$;; $i,i^{\prime}\in N,\; i\neq i^{\prime}$', 11),
          ('ecuacion', r'S_{i^{\prime}1}\ge \sigma\, z_{0i^{\prime}1m}', r'$\forall m\in M_1,\; i^{\prime}\in N$', 12),
          ('ecuacion', r'S_{i^{\prime}s}\ge C_{is}-H\,(1-z_{ii^{\prime}sm})',
           r'$\forall s\ge 2,\; m\in M_s$;; $i,i^{\prime}\in N,\; i\neq i^{\prime}$', 13),
          ('p', r'**Tardanza y makespan.** La orden $j$ termina cuando su último sublote sale de la '
                'última etapa; su tardanza es el exceso de esa terminación sobre la fecha de entrega '
                '(14), y el makespan es la mayor terminación de todos los sublotes (15).'),
          ('ecuacion', r'T_j\ge C_{(j,b),|S|}-d_j', r'$\forall j\in J,\; b=1,\dots,B_j$', 14),
          ('ecuacion', r'C_{\max}\ge C_{i,|S|}', r'$\forall i\in N$', 15),
          ('p', '**Dominio de las variables.**'),
          ('ecuacion', r'x_{jb}\in\{0,1,2,\dots\};\quad y_{ism},\,z_{ii^{\prime}sm}\in\{0,1\};\quad '
                       r'S_{is},\,C_{is},\,T_j,\,C_{\max}\ge 0', '', 16),
          ('p', 'Como el modelo admite tardanza, el horizonte de 672 horas laborables no se impone '
                r'como una restricción dura: define el calendario en el que se miden $r_j$ y $d_j$, '
                r'mientras que $H$ es solo una cota superior que activa o desactiva las '
                'restricciones disyuntivas (5), (11) y (13).')]

    B += [('h3', 'Tamaño del modelo y selección del método de solución'),
          ('p', r'En la instancia del caso de estudio, las 10 órdenes se dividen en $\overline{B}=10$ '
                'sublotes cada una, lo que produce 100 sublotes que deben asignarse y secuenciarse '
                'en 36 máquinas. La Tabla {T:tamano} resume el tamaño del modelo para esa instancia.'),
          ('tabla', 'Tamaño del modelo matemático para la instancia del caso de estudio',
           ['Elemento', 'Expresión', 'Cantidad'], [
               [r'Variables $y_{ism}$ (binarias)', r'$|N|\cdot\sum_s|M_s|$', '3.600'],
               [r'Variables $z_{ii^{\prime}sm}$ (binarias)', r'$\sum_s|M_s|\cdot|N|^2$', '360.000'],
               [r'Variables $x_{jb}$ (enteras)', r'$|N|$', '100'],
               ['Variables continuas', r'$2|N||S|+|J|+1$', '811'],
               ['Restricciones disyuntivas (11) y (13)', r'$\sum_s|M_s|\cdot|N|(|N|-1)$', '356.400'],
               ['Restricciones totales', '', '≈ 368.600']],
           {'etiqueta': 'tamano', 'anchos': [3900, 3138, 1800], 'alineacion': ['l', 'c', 'r']}),
          ('p', 'El problema de programación en un Flow Shop híbrido es NP-difícil incluso con '
                'dos etapas (Gupta, 1988), y la formulación con restricciones disyuntivas de '
                'constante grande tiene relajaciones lineales débiles. Con más de 363.000 '
                'variables binarias, la instancia real no puede resolverse de forma exacta en un '
                'tiempo razonable. La validación de la sección 4.2.5 lo confirma: con el solver '
                'HiGHS, el modelo dejó de encontrar soluciones factibles en 10 minutos a partir de '
                '12 sublotes. Por esta razón se selecciona un algoritmo genético como método de '
                'solución, en concordancia con la literatura sobre Flow Shop híbrido (Ruiz y '
                'Vázquez-Rodríguez, 2010; López-Vargas y Arango-Marín, 2015). El modelo matemático '
                'cumple dos funciones: representar el problema de forma rigurosa y servir de '
                'referencia para validar el algoritmo en instancias reducidas.')]
    return B


# ===========================================================================
# 2. Algoritmo genético
# ===========================================================================

def bloque_ag():
    B = [('h3', 'Diseño del algoritmo genético'),
         ('p', 'El algoritmo genético propuesto adapta el esquema de Gürsoy Yılmaz y Yılmaz (2022) '
               'para sublotes consistentes al sistema estudiado y a la minimización de la tardanza '
               'total. Cada individuo (cromosoma) codifica los tamaños de los sublotes y el orden en '
               'que se procesan en cada etapa; un procedimiento de decodificación convierte el '
               'cromosoma en una programación factible y calcula su aptitud. La Figura {F:flujo} presenta '
               'el diagrama de flujo del algoritmo, y las secciones siguientes describen cada uno '
               'de sus componentes.'),
         ('figura', 'Diagrama de flujo del algoritmo genético',
          os.path.join(FIG, 'diagrama_ag.png'), 11.5, 'flujo'),
         ('h4', 'Representación de la solución'),
         ('p', 'El cromosoma tiene dos niveles:'),
         ('viñetas', [
             r'**Nivel 1, tamaños de sublote.** Para cada orden $j$, un vector de proporciones '
             r'$\pi_j=(\pi_{j1},\dots,\pi_{jB_j})$, con $\pi_{jb}\ge 0$ y $\sum_b\pi_{jb}=1$, que '
             'define el tamaño relativo de cada sublote. Como los sublotes son consistentes, el '
             'mismo tamaño se usa en las cuatro etapas.',
             r'**Nivel 2, secuencias.** Para cada etapa $s$, una permutación $O_s$ de los 100 '
             'sublotes que define el orden en que se programan en esa etapa. Las secuencias de '
             'las etapas son independientes, de modo que un sublote puede adelantar a otro entre '
             'etapas.']),
         ('p', 'La máquina de cada sublote no forma parte del cromosoma: la elige el decodificador '
               'con la regla del menor tiempo de terminación (ECT, por sus siglas en inglés). Esta '
               'es la principal diferencia con el cromosoma de tres niveles de Gürsoy Yılmaz y '
               'Yılmaz (2022), que codifica también la máquina. La asignación por ECT reduce el '
               'espacio de búsqueda y evita asignaciones dominadas, como enviar un sublote a una '
               'máquina lenta de ensamble cuando una rápida está libre; Ruiz y Maroto (2006) '
               'emplean el mismo principio en Flow Shop híbrido. La Tabla {T:cromosoma} muestra un cromosoma '
               'de ejemplo con dos órdenes: J1, de 25 docenas en 4 sublotes, y J2, de 10 docenas '
               'en 2 sublotes.'),
         ('tabla', 'Ejemplo de cromosoma con dos órdenes', ['Nivel', 'Gen', 'Valores'], [
             ['1', r'$\pi_{J1}$', '(0,10; 0,35; 0,30; 0,25)'],
             ['1', r'$\pi_{J2}$', '(0,50; 0,50)'],
             ['2', r'$O_1$ (troquelado)', 'J1-2, J2-1, J1-1, J1-3, J2-2, J1-4'],
             ['2', r'$O_2$ (ensamble)', 'J2-1, J1-2, J1-1, J2-2, J1-3, J1-4'],
             ['2', r'$O_3$ (costura)', 'J1-2, J2-1, J1-1, J2-2, J1-4, J1-3'],
             ['2', r'$O_4$ (volteado)', 'J2-1, J1-2, J2-2, J1-1, J1-3, J1-4']],
          {'etiqueta': 'cromosoma', 'anchos': [900, 2300, 5638], 'alineacion': ['c', 'l', 'l']}),
         ('h4', 'Conversión de proporciones en tamaños de sublote'),
         ('p', r'Las proporciones del nivel 1 se convierten en docenas enteras. Primero se reserva '
               r'el tamaño mínimo para cada sublote, y las $L_j=Q_j-B_j\,q^{\min}$ docenas restantes '
               r'se reparten según las proporciones: cada sublote recibe la parte entera de '
               r'$\pi_{jb}L_j$, y las unidades que faltan se asignan a los sublotes con mayor '
               'residuo (método del mayor residuo).'),
         ('ecuacion', r'x_{jb}=q^{\min}+u_{jb},\qquad u_{jb}=\lfloor\pi_{jb}L_j\rfloor+\delta_{jb},'
                      r'\qquad \sum_{b}u_{jb}=L_j', r'$\forall j\in J,\; b=1,\dots,B_j$', 17),
         ('p', r'donde $\delta_{jb}\in\{0,1\}$ vale 1 para los sublotes con los mayores residuos '
               r'$\pi_{jb}L_j-\lfloor\pi_{jb}L_j\rfloor$, hasta completar $L_j$. La conversión '
               'garantiza tamaños enteros, mayores o iguales al mínimo, cuya suma es exactamente la '
               'cantidad de la orden; por lo tanto, todo cromosoma cumple las restricciones (2) y '
               r'(3). En el ejemplo de la Tabla {T:cromosoma}, para J1: $L=25-4=21$ y '
               r'$\pi L=(2{,}10;\,7{,}35;\,6{,}30;\,5{,}25)$. Las partes enteras (2, 7, 6, 5) suman '
               '20; la unidad faltante se asigna al sublote 2, que tiene el mayor residuo (0,35). '
               'Los tamaños resultantes son (3, 9, 7, 6) docenas, que suman 25.'),
         ('h4', 'Decodificación: construcción de la programación'),
         ('p', 'El decodificador construye la programación etapa por etapa, siguiendo en cada '
               r'etapa el orden $O_s$ del cromosoma. Para cada sublote $i=(j,b)$:'),
         ('numerada', [
             r'Calcula el instante en que el sublote está disponible: la liberación $r_j$ en '
             'troquelado o su terminación en la etapa anterior en las demás etapas.',
             r'Para cada máquina $m$ de la etapa, calcula el tiempo de procesamiento '
             r'$a_{jm}x_{jb}$ y el inicio posible. En troquelado, el sublote se ubica después del '
             'último sublote de la máquina y se suma el alistamiento si la máquina está vacía o si '
             'cambia la referencia; como el alistamiento es anticipatorio, el inicio es el máximo '
             'entre la liberación de la máquina más el alistamiento y la disponibilidad del '
             'sublote. En ensamble, costura y volteado, el sublote ocupa el primer intervalo libre '
             'de la máquina con duración suficiente desde su disponibilidad.',
             'Asigna el sublote a la máquina en la que termina primero (regla ECT); en caso de '
             'empate, a la de menor índice.',
             'Actualiza la agenda de la máquina y registra la terminación del sublote, que queda '
             'disponible para la etapa siguiente.']),
         ('p', r'Al terminar la última etapa, la terminación de cada orden es $C_j=\max_b C_{(j,b),4}$ '
               r'y se calculan $T_j=\max\{0,\,C_j-d_j\}$, la tardanza total y el makespan. Por '
               'construcción, la programación cumple todas las restricciones del modelo matemático, '
               'lo que se verificó de forma independiente en la sección 4.2.5. La Figura {F:pseudo} resume '
               'el procedimiento.'),
         ('codigo', 'Pseudocódigo del decodificador', [
             'Entrada: cromosoma (π, O_1, …, O_4) y datos de la instancia',
             'calcular los tamaños x_jb a partir de π (método del mayor residuo)',
             'listo(j, b) ← r_j para todos los sublotes',
             'para s = 1 hasta 4 hacer',
             '  para cada sublote (j, b) en el orden O_s hacer',
             '    para cada máquina m de la etapa s hacer',
             '      p ← a_jm · x_jb',
             '      si s = 1 entonces',
             '        α ← σ si m está vacía o su última referencia ≠ p_j; en otro caso α ← 0',
             '        inicio(m) ← máx(libre(m) + α, listo(j, b))',
             '      si no',
             '        inicio(m) ← primer hueco de m con duración p desde listo(j, b)',
             '      fin(m) ← inicio(m) + p',
             '    m* ← máquina con menor fin(m)          (regla ECT)',
             '    asignar (j, b) a m* y actualizar la agenda de m*',
             '    listo(j, b) ← fin(m*)',
             'C_j ← máx_b listo(j, b);  T_j ← máx(0, C_j − d_j)',
             'Salida: programación, ΣT_j y C_max'], 'pseudo'),
         ('h4', 'Función de aptitud'),
         ('p', 'La aptitud de un individuo es el par (ΣT_j, C_max) de su programación, comparado de '
               'forma lexicográfica: un individuo es mejor que otro si tiene menor tardanza total '
               'o, con la misma tardanza, menor makespan. Los valores se redondean a 10⁻⁶ h para '
               'evitar diferencias numéricas irrelevantes, y la aptitud de cada individuo se '
               'guarda para no recalcularla.'),
         ('h4', 'Población inicial'),
         ('p', 'La población inicial tiene 150 individuos. De ellos, 149 se generan al azar: las '
               'proporciones del nivel 1 se obtienen normalizando variables exponenciales (una '
               'distribución de Dirichlet uniforme) y las secuencias del nivel 2 son permutaciones '
               'aleatorias independientes por etapa. El individuo restante se construye con la '
               'mejor de seis reglas de despacho clásicas, aplicadas con sublotes iguales y con la '
               'misma secuencia de órdenes en las cuatro etapas. La Tabla {T:reglas} define las reglas y '
               'muestra su desempeño en la instancia del caso de estudio.'),
         ('tabla', 'Reglas de despacho usadas para sembrar la población inicial '
                   '(10 sublotes iguales por orden)',
          ['Regla', 'Criterio de prioridad', 'ΣT_j (h)', 'T_max (h)', 'C_max (h)', 'Tardías'], [
              ['EDD', r'Menor $d_j$', '145,00', '145,00', '817,00', '1'],
              ['FIFO', 'Orden de liberación', '242,48', '135,27', '620,64', '2'],
              ['CR', r'Menor razón crítica $d_j/P_j$', '244,18', '164,33', '591,33', '2'],
              ['SPT', r'Menor $P_j$', '253,61', '162,69', '834,69', '3'],
              ['MST', r'Menor holgura $d_j-P_j$', '311,70', '159,86', '587,27', '2'],
              ['LPT', r'Mayor $P_j$', '341,32', '179,24', '589,08', '2']],
          {'etiqueta': 'reglas', 'anchos': [900, 3138, 1200, 1200, 1200, 1200], 'alineacion': ['l', 'l', 'c', 'c', 'c', 'c']}),
         ('p', r'En la tabla, $P_j=\sum_s\min_m a_{jm}Q_j$ es el tiempo de procesamiento de la orden '
               'completa en la máquina más rápida de cada etapa. La regla EDD obtiene la menor '
               'tardanza total (145 h, con una orden tardía) y siembra la población. La semilla '
               'acelera la convergencia, mientras que los individuos aleatorios mantienen la '
               'diversidad de la población.'),
         ('h4', 'Selección'),
         ('p', 'Los padres se eligen por torneo (Goldberg y Deb, 1991): se toman tres individuos '
               'al azar de la población y se selecciona el de mejor aptitud. El procedimiento se '
               'repite para cada padre. El torneo solo compara individuos, por lo que se aplica '
               'directamente a la aptitud lexicográfica sin necesidad de escalarla.'),
         ('h4', 'Cruce'),
         ('p', r'Con probabilidad $p_c$, dos padres producen dos hijos; en otro caso, los hijos son '
               'copias de los padres. Cada nivel se cruza con un operador adecuado a su tipo de '
               'dato.'),
         ('p', r'**Nivel 1: cruce aritmético.** Para cada orden se sortea $\lambda\sim U(0,1)$ y '
               'los hijos reciben combinaciones convexas de las proporciones de los padres:'),
         ('ecuacion', r'\pi_j^{h_1}=\lambda\,\pi_j^{p_1}+(1-\lambda)\,\pi_j^{p_2},\qquad '
                      r'\pi_j^{h_2}=(1-\lambda)\,\pi_j^{p_1}+\lambda\,\pi_j^{p_2}', r'$\forall j\in J$', 18),
         ('p', 'La combinación convexa conserva la propiedad de que las proporciones suman uno '
               r'(Michalewicz, 1996). Por ejemplo, con $\pi^{p_1}=(0{,}10;\,0{,}35;\,0{,}30;\,0{,}25)$, '
               r'$\pi^{p_2}=(0{,}25;\,0{,}25;\,0{,}25;\,0{,}25)$ y $\lambda=0{,}6$, se obtienen '
               r'$\pi^{h_1}=(0{,}16;\,0{,}31;\,0{,}28;\,0{,}25)$ y '
               r'$\pi^{h_2}=(0{,}19;\,0{,}29;\,0{,}27;\,0{,}25)$.'),
         ('p', '**Nivel 2: cruce de orden lineal (LOX).** En cada etapa se eligen dos puntos de '
               'corte. El hijo conserva el tramo del primer padre entre los cortes, en las mismas '
               'posiciones, y completa las posiciones restantes, de izquierda a derecha, con los '
               'sublotes que faltan en el orden en que aparecen en el segundo padre; el segundo '
               'hijo se obtiene intercambiando los papeles de los padres (Falkenauer y Bouffouix, '
               '1991). LOX siempre produce una permutación válida, sin sublotes repetidos ni '
               'faltantes, y conserva el orden relativo de los padres. La Tabla {T:lox} muestra un '
               'ejemplo con seis sublotes y cortes en las posiciones 3 y 4.'),
         ('tabla', 'Ejemplo del cruce de orden lineal (LOX) en una etapa',
          ['Secuencia', 'Pos. 1', 'Pos. 2', 'Pos. 3', 'Pos. 4', 'Pos. 5', 'Pos. 6'], [
              ['Padre 1', 'J1-1', 'J1-2', '**J2-1**', '**J3-1**', 'J2-2', 'J3-2'],
              ['Padre 2', 'J3-1', 'J2-1', 'J1-1', 'J3-2', 'J1-2', 'J2-2'],
              ['Hijo', 'J1-1', 'J3-2', '**J2-1**', '**J3-1**', 'J1-2', 'J2-2']],
          {'etiqueta': 'lox', 'anchos': [1638, 1200, 1200, 1200, 1200, 1200, 1200]}),
         ('p', 'El hijo conserva el tramo (J2-1, J3-1) del padre 1. Los sublotes restantes, en el '
               'orden del padre 2, son J1-1, J3-2, J1-2 y J2-2, y ocupan las posiciones libres de '
               'izquierda a derecha.'),
         ('h4', 'Mutación'),
         ('p', r'Cada hijo se muta con probabilidad $p_m$. La mutación actúa sobre los dos niveles:'),
         ('viñetas', [
             '**Nivel 2, intercambio:** con probabilidad 0,30 se elige una etapa al azar y se '
             'intercambian dos sublotes de su secuencia.',
             '**Nivel 1, perturbación:** para cada orden, con probabilidad 0,40, se suma a la '
             r'proporción de un sublote al azar un valor $\varepsilon\sim N(0;\,0{,}15)$; la '
             'proporción se acota en un valor positivo mínimo y el vector se normaliza para que '
             'sume uno.']),
         ('p', 'El intercambio modifica el orden de procesamiento; la perturbación cambia los '
               'tamaños de los sublotes sin alterar la cantidad de la orden, ya que la conversión '
               'de la ecuación (17) siempre reparte exactamente las docenas de la orden.'),
         ('h4', 'Elitismo, reemplazo y criterio de parada'),
         ('p', 'Cada generación se construye con reemplazo generacional: la nueva población se '
               'forma con los hijos producidos por selección, cruce y mutación, y conserva al mejor '
               'individuo de la generación anterior (elitismo de un individuo), de modo que la mejor '
               'solución nunca empeora. El algoritmo se detiene cuando transcurren 100 generaciones '
               'sin mejora de la mejor solución o al alcanzar 1.000 generaciones. Los valores de '
               'los parámetros se definieron mediante la calibración de la sección 4.2.6. La '
               'Tabla {T:componentes} resume los componentes del algoritmo.'),
         ('tabla', 'Componentes y parámetros del algoritmo genético',
          ['Componente', 'Elección', 'Parámetro'], [
              ['Representación', 'Proporciones (nivel 1) y secuencias por etapa (nivel 2)', '—'],
              ['Asignación de máquinas', 'Regla del menor tiempo de terminación (ECT)', '—'],
              ['Aptitud', 'Lexicográfica (ΣT_j, C_max)', '—'],
              ['Población inicial', '149 aleatorios y la mejor regla de despacho', 'Tamaño 150'],
              ['Selección', 'Torneo', 'k = 3'],
              ['Cruce', 'Aritmético (nivel 1) y LOX (nivel 2)', r'$p_c=0{,}9$'],
              ['Mutación', 'Perturbación normal (nivel 1) e intercambio (nivel 2)',
               r'$p_m=0{,}5$ (0,40; 0,30; σ = 0,15)'],
              ['Reemplazo', 'Generacional con elitismo', '1 individuo'],
              ['Parada', 'Generaciones sin mejora o máximo de generaciones', '100 / 1.000']],
          {'etiqueta': 'componentes', 'anchos': [2200, 4138, 2500], 'alineacion': ['l', 'l', 'l']})]
    return B


# ===========================================================================
# 3. Implementación, verificación y validación
# ===========================================================================

def bloque_implementacion():
    return [
        ('h3', 'Implementación computacional'),
        ('p', 'El modelo se implementó en Python 3. La lectura de datos usa las librerías pandas y '
              'openpyxl; los diagramas de Gantt y las figuras, matplotlib; el modelo matemático de '
              'validación se programó con PuLP y se resolvió con el solver de código abierto HiGHS '
              '(Mitchell et al., 2011; Huangfu y Hall, 2018), y el análisis estadístico de la '
              'calibración usa SciPy y statsmodels. Los datos de entrada se leen del libro de Excel '
              'BD_HFS.xlsx, cuya estructura se presenta en la Tabla {T:libro}; así, la empresa puede '
              'actualizar las órdenes, los tiempos o el calendario sin modificar el código.'),
        ('tabla', 'Estructura del libro de datos de entrada', ['Hoja', 'Contenido'], [
            ['Tiempo de procesamiento', 'Código de producto, máquina, etapa y tiempo estándar '
                                        '[min/docena] para cada combinación de referencia y máquina.'],
            ['Trabajos', r'Orden de trabajo, código de producto, cantidad [docenas], liberación '
                         r'$r_j$ [h], fecha de entrega y $d_j$ [h].'],
            ['Disponibilidad', 'Calendario laboral: fecha, horas disponibles y horas acumuladas al '
                               'inicio y al final de cada día; permite convertir las horas '
                               'laborables en fechas.']],
         {'etiqueta': 'libro', 'anchos': [2600, 6238], 'alineacion': ['l', 'l']}),
        ('p', 'El programa se organiza en cuatro módulos: (i) lectura y validación de los datos; '
              '(ii) evaluación de las reglas de despacho; (iii) algoritmo genético, con el '
              'decodificador y los operadores descritos, y (iv) reportes: tamaños de los '
              'sublotes, indicadores por orden y globales, programación por etapa y máquina, y '
              'diagrama de Gantt. En un computador con un procesador de 4 núcleos, cada evaluación '
              'de un cromosoma de la instancia real toma en promedio 2,4 ms, y una corrida completa '
              'del algoritmo con los parámetros calibrados toma entre 2 y 8 minutos. '
              '[[El código fuente se incluye en el Anexo X.]]')]


def bloque_validacion():
    B = [('h3', 'Verificación y validación del modelo'),
         ('p', 'Antes de usar el modelo para programar la producción, se verificó que el algoritmo '
               'genera programaciones factibles y se validó el modelo matemático frente a '
               'soluciones óptimas en instancias reducidas. Estas pruebas responden tres preguntas: '
               '¿el modelo matemático está bien formulado?, ¿el algoritmo genético representa el '
               'mismo problema? y ¿qué tan buenas son las soluciones del algoritmo?'),
         ('h4', 'Verificación del decodificador'),
         ('p', 'Se programó un verificador independiente que recorre la programación producida por '
               'el decodificador y comprueba cada restricción del modelo matemático: suma de los '
               'sublotes igual a la cantidad de la orden y tamaño mínimo (2)–(3), una máquina por '
               'sublote y etapa (4), duración igual al tiempo estándar por el tamaño (5), inicio '
               'posterior a la liberación (6), precedencia entre etapas (7), no solapamiento en '
               'cada máquina y alistamiento en troquelado cuando cambia la referencia (11)–(13). '
               'El verificador se aplicó a 200 cromosomas aleatorios de la instancia real y a las '
               'programaciones de las seis reglas de despacho, sin encontrar ninguna violación. '
               'Para confirmar que el verificador detecta errores, se introdujeron fallas '
               'deliberadas (una operación adelantada y la omisión de los alistamientos), que '
               'fueron detectadas en todos los casos.'),
         ('h4', 'Validación del modelo matemático con instancias reducidas'),
         ('p', 'Se construyeron nueve instancias con los tiempos estándar reales de la empresa, '
               'cantidades reducidas y un subconjunto de las máquinas de cada etapa (Tabla {T:instancias}). En '
               'ensamble se incluyeron siempre máquinas de grupos con velocidades distintas (M5, '
               'lenta; M12, intermedia; M16, rápida), y dos órdenes de la misma referencia (C01) '
               'para comprobar que el alistamiento solo se aplica cuando cambia la referencia. Las '
               'instancias I1 e I2 corresponden a las mismas órdenes de I6 e I9, pero sin dividirlas '
               r'en sublotes ($\overline{B}=1$).'),
         ('tabla', 'Instancias de validación',
          ['Instancia', 'Órdenes', 'B̄', 'Sublotes', 'Máquinas (T-E-C-V)', 'd_j (h)'], [
              ['I1', 'J1–J4', '1', '4', '2-3-2-1 (B)', '9, 7, 8, 12'],
              ['I2', 'J1–J5', '1', '5', '2-3-2-1 (B)', '9, 7, 8, 12, 14'],
              ['I3', 'J1–J3', '2', '6', '2-2-1-1 (A)', '15, 12, 14'],
              ['I4', 'J1–J3', '2', '6', '2-3-2-1 (B)', '9, 7, 8'],
              ['I5', 'J1–J4', '2', '8', '2-2-1-1 (A)', '15, 12, 14, 20'],
              ['I6', 'J1–J4', '2', '8', '2-3-2-1 (B)', '9, 7, 8, 12'],
              ['I7', 'J1–J3', '3', '9', '2-2-1-1 (A)', '15, 12, 14'],
              ['I8', 'J1–J4', '3', '12', '2-3-2-1 (B)', '9, 7, 8, 12'],
              ['I9', 'J1–J5', '3', '15', '2-3-2-1 (B)', '9, 7, 8, 12, 14']],
          {'etiqueta': 'instancias', 'anchos': [1100, 1200, 700, 1200, 2338, 2300]}),
         ('p', 'Las órdenes son J1 = C01 (8 docenas, r = 0 h), J2 = V03 (6 docenas, r = 0 h), '
               'J3 = C04 (5 docenas, r = 2 h), J4 = C01 (7 docenas, r = 3 h) y J5 = V02 (6 docenas, '
               'r = 5 h). El conjunto de máquinas A está formado por M1 y M2 (troquelado), M5 y M16 '
               '(ensamble), M20 (costura) y M29 (volteado); el conjunto B agrega M12 en ensamble y '
               'M21 en costura. Con el conjunto B se usaron fechas de entrega más ajustadas, para '
               'que la tardanza óptima fuera positiva y las instancias discriminaran entre métodos.'),
         ('p', 'Cada instancia se resolvió con el solver HiGHS mediante dos formulaciones. La '
               'primera (F1) es el modelo de la sección 4.2.1. La segunda (F2) es una formulación '
               r'equivalente que reemplaza las variables $z_{ii^{\prime}sm}$ y las restricciones '
               r'(8)–(13) por variables de precedencia general $u_{ii^{\prime}s}$, que valen 1 si '
               r'$i$ se procesa antes que $i^{\prime}$ cuando comparten máquina (Naderi et al., '
               '2014):'),
         ('ecuacion', r"S_{i's}\ge C_{is}+\sigma^{s}_{ii'}-H\,(3-u_{ii's}-y_{ism}-y_{i'sm})",
          r"$\forall i<i^{\prime},\; s\in S$;; $m\in M_s$", 19),
         ('ecuacion', r"S_{is}\ge C_{i's}+\sigma^{s}_{i'i}-H\,(2+u_{ii's}-y_{ism}-y_{i'sm})",
          r"$\forall i<i^{\prime},\; s\in S$;; $m\in M_s$", 20),
         ('ecuacion', r'S_{i1}\ge\sigma', r'$\forall i\in N$', 21),
         ('p', r'donde $\sigma^{s}_{ii^{\prime}}=\sigma_{ii^{\prime}}$ en troquelado y 0 en las demás '
               'etapas. F2 es exacta porque el alistamiento cumple la desigualdad triangular: si '
               r'$i$ precede a $i^{\prime}$ en la misma máquina, aunque no sea inmediatamente, y sus '
               'referencias son distintas, entre ambos hay al menos un cambio de referencia; la '
               'restricción (21) basta para el montaje inicial, porque los sublotes que no son '
               'primeros inician aún más tarde. F2 usa entre la tercera y la cuarta parte de las '
               'variables binarias de F1 y sirve para obtener óptimos de referencia; que las dos '
               'formulaciones coincidan es, además, evidencia de que el modelo está bien planteado.'),
         ('p', 'El objetivo lexicográfico se resolvió en dos fases: primero se minimizó la tardanza '
               r'total y luego el makespan, sujeto a no empeorar la tardanza óptima, con un límite '
               'de 600 s por fase. Para acelerar el solver se agregaron refuerzos que no cambian el '
               'óptimo: una cota del horizonte obtenida de la mejor regla de despacho, la ruptura '
               r'de simetría $x_{jb}\ge x_{j,b+1}$ entre los sublotes de una orden y la desigualdad '
               r'válida $C_{is}\ge S_{is}+\min_m a_{jm}x_{jb}$. Sobre las mismas instancias se '
               'corrió el algoritmo genético, con los parámetros calibrados en la sección 4.2.6, con '
               '10 semillas distintas. La '
               'Tabla {T:validacion} presenta los resultados.'),
         ('tabla', 'Resultados de la validación: modelo exacto frente al algoritmo genético',
          ['Inst.', 'Sub-lotes', 'F1: ΣT_j / C_max (s)', 'F2: ΣT_j / C_max (s)', 'EDD ΣT_j',
           'AG mejor ΣT_j / C_max', 'AG prom. ΣT_j', 'AG ≤ MILP', 'AG (s)'], [
              ['I1', '4', '28,190 / 19,836 · óptimo (1)', '28,190 / 19,836 · óptimo (2)', '30,439',
               '28,190 / 19,836', '28,306', '7/10', '3,4'],
              ['I2', '5', '34,374 / 21,794 · óptimo (21)', '34,374 / 21,794 · óptimo (4)', '37,635',
               '34,374 / 21,794', '34,428', '9/10', '3,7'],
              ['I3', '6', '0,955 / 15,955 · óptimo (121)', '0,955 / 15,955 · óptimo (4)', '2,067',
               '0,955 / 15,955', '1,169', '4/10', '4,5'],
              ['I4', '6', '3,861 / 12,082 · óptimo (168)', '3,861 / 12,082 · óptimo (60)', '4,149',
               '3,861 / 12,082', '3,861', '10/10', '4,3'],
              ['I5', '8', '1,113 / 20,158 · límite (1.144)', '1,113 / 20,158 · óptimo (34)', '3,325',
               '1,113 / 20,158', '1,247', '7/10', '6,9'],
              ['I6', '8', '6,379 / 13,983 · límite (1.200)', '5,928 / 13,942 · límite (807)', '6,682',
               '5,928 / 13,942', '6,020', '8/10', '6,6'],
              ['I7', '9', '0,000 / 14,747 · límite (723)', '0,000 / 14,399 · óptimo (587)', '0,404',
               '0,000 / 14,496', '0,000', '10/10', '7,9'],
              ['I8', '12', 'sin solución (600)', '3,142 / 12,780 · límite (1.200)', '2,341',
               '1,214 / 12,114', '1,336', '10/10', '9,9'],
              ['I9', '15', 'sin solución (600)', '8,077 / 15,847 · límite (1.200)', '2,666',
               '1,214 / 13,857', '1,457', '10/10', '11,3']],
          {'etiqueta': 'validacion', 'anchos': [560, 640, 1760, 1760, 720, 1340, 740, 700, 618],
           'alineacion': ['l'] + ['c'] * 8, 'tam': 8}),
         ('p', 'ΣT_j y C_max se expresan en horas; entre paréntesis, el tiempo de cómputo en '
               'segundos. "Óptimo" indica que el solver demostró la optimalidad de las dos fases '
               'dentro del límite; "límite", que se alcanzó el límite de tiempo, y "sin solución", '
               'que no se encontró ninguna solución factible. La columna "AG ≤ MILP" indica en '
               'cuántas de las 10 réplicas el algoritmo genético obtuvo una tardanza total igual o '
               'menor que la mejor solución del modelo exacto. La Figura {F:gantt_i5} compara la programación '
               'óptima del modelo exacto con la mejor del algoritmo genético en la instancia I5.'),
         ('figura', 'Programación óptima del modelo exacto (arriba) y mejor programación del '
                    'algoritmo genético (abajo) en la instancia I5',
          os.path.join(SAL_VAL, 'gantt_milp_vs_ag_I5.png'), 15.5, 'gantt_i5'),
         ('p', 'Los resultados permiten las siguientes conclusiones:'),
         ('numerada', [
             '**El modelo matemático está bien formulado.** Las soluciones del modelo exacto en '
             'las nueve instancias pasaron el verificador sin ninguna violación. En las cuatro '
             'instancias en que F1 demostró la optimalidad (I1 a I4), F2 llegó exactamente al mismo '
             'óptimo; en I5, F2 demostró el óptimo y F1 encontró esa misma solución, aunque no '
             'alcanzó a demostrar su optimalidad.',
             '**El algoritmo genético y el modelo representan el mismo problema.** Al pasar los '
             'tamaños y secuencias óptimos del modelo exacto por el decodificador del algoritmo se '
             'obtuvieron exactamente los mismos tiempos en I1, I2, I6 e I7. En I3, I4 e I5 el '
             'decodificador produjo un valor algo mayor con esas secuencias; por ejemplo, en I3 '
             'obtuvo 1,279 h frente a 0,955 h. La causa es la regla ECT: en el óptimo de I3, el '
             'modelo envía un sublote a la máquina lenta de ensamble para dejar libre la rápida, '
             'que otro sublote necesita poco después, mientras que el decodificador siempre asigna '
             'la máquina que termina primero. Aun así, el algoritmo alcanzó el valor óptimo en esas '
             'instancias mediante otros cromosomas.',
             '**El algoritmo genético encuentra soluciones óptimas o cercanas al óptimo.** En las '
             'seis instancias con tardanza óptima conocida (I1 a I5 e I7), la mejor de las 10 '
             'réplicas alcanzó la tardanza óptima en todos los casos; en total, 47 de 60 réplicas '
             '(78 %) llegaron al óptimo, y la mayor diferencia promedio fue de 0,21 h (I3). El único '
             'caso en que no se alcanzó el óptimo lexicográfico fue el makespan de I7, 0,7 % mayor '
             'con la tardanza en cero.',
             '**El método exacto no escala, mientras que el algoritmo genético sí.** F1 demostró la '
             'optimalidad solo hasta 6 sublotes y no encontró soluciones factibles con 12 y 15 '
             'sublotes en 10 minutos. En las instancias medianas, el algoritmo igualó o superó en '
             'menos de 12 segundos la mejor solución que el solver obtuvo en 20 minutos; en I9, por '
             'ejemplo, obtuvo 1,214 h frente a 8,077 h. La instancia real, con 100 sublotes y más '
             'de 363.000 variables binarias, está muy por encima de lo que el método exacto puede '
             'resolver.',
             '**La división en sublotes reduce la tardanza de forma notable.** Con las mismas cuatro '
             'órdenes, la tardanza total óptima es de 28,19 h sin dividirlas (I1), y baja a '
             '5,93 h con dos sublotes por orden (I6) y a 1,21 h con tres (I8). Con cinco órdenes, '
             'baja de 34,37 h (I2) a 1,21 h (I9).'])]
    return B


# ===========================================================================
# 4. Número de sublotes y calibración
# ===========================================================================

def bloque_sublotes():
    return [
        ('h4', 'Número de sublotes por orden'),
        ('p', r'El número máximo de sublotes por orden $\overline{B}$ es un parámetro del modelo, no del '
              'algoritmo: define cuánto se divide cada orden. La Tabla {T:bbar} muestra su efecto sobre la '
              'tardanza total de las reglas de despacho en la instancia del caso de estudio.'),
        ('tabla', 'Tardanza total (h) y número de órdenes tardías de las reglas de despacho según '
                  'el número de sublotes por orden',
         ['B̄', 'FIFO', 'EDD', 'CR', 'SPT'], [
             ['1', '8.490 (10)', '8.316 (10)', '8.741 (10)', '8.353 (10)'],
             ['2', '3.051 (10)', '3.203 (9)', '3.743 (10)', '2.939 (8)'],
             ['5', '704 (6)', '495 (3)', '798 (7)', '809 (4)'],
             ['10', '242 (2)', '145 (1)', '244 (2)', '254 (3)'],
             ['20', '141 (2)', '17 (1)', '131 (2)', '66 (2)'],
             ['40', '89 (2)', '0 (0)', '99 (1)', '0 (0)']],
         {'etiqueta': 'bbar', 'anchos': [1238, 1900, 1900, 1900, 1900]}),
        ('p', 'Sin división en sublotes, todas las órdenes resultan tardías, porque cada orden ocupa '
              'una sola máquina por etapa durante cientos de horas. A medida que aumenta el número '
              'de sublotes, el trabajo se reparte entre las máquinas paralelas y las etapas se '
              r'superponen, y la tardanza disminuye. Se adopta $\overline{B}=10$, con el que los '
              'sublotes tienen en promedio entre 21 docenas (J09) y 117 docenas (J01). '
              '[[Confirmar con la práctica de la planta: tamaño habitual de los paquetes que se '
              'transfieren entre puestos y número de sublotes que es viable controlar por orden.]] '
              r'Un valor mayor de $\overline{B}$ reduciría aún más la tardanza, pero aumentaría la '
              'manipulación de material y el control de la producción; el efecto de este parámetro '
              'sobre los indicadores se analiza en la Fase 3.')]


def bloque_calibracion():
    return [
        ('h4', 'Calibración de los parámetros del algoritmo genético'),
        ('p', 'El desempeño de un algoritmo genético depende de sus parámetros. Para elegirlos con '
              'un criterio objetivo, se realizó una calibración mediante diseño de experimentos '
              'sobre la instancia real (Ruiz, Maroto y Alcaraz, 2006; Montgomery, 2017), en tres '
              'experimentos.'),
        ('h4', 'Diseño de los experimentos'),
        ('p', '**Experimento 1: diseño factorial completo.** Se evaluaron tres factores con tres '
              'niveles cada uno (Tabla {T:factores}), con 5 réplicas por combinación, para un total de 135 '
              'corridas. Los demás parámetros se mantuvieron fijos: torneo de tamaño 3, '
              'probabilidades internas de mutación de 0,30 (intercambio) y 0,40 (perturbación), '
              'desviación de la perturbación de 0,15 y elitismo de un individuo.'),
        ('tabla', 'Factores y niveles del diseño factorial', ['Factor', 'Niveles'], [
            ['Tamaño de la población', '50; 100; 150'],
            [r'Probabilidad de cruce ($p_c$)', '0,7; 0,8; 0,9'],
            [r'Probabilidad de mutación ($p_m$)', '0,1; 0,3; 0,5']],
         {'etiqueta': 'factores', 'anchos': [4419, 4419], 'alineacion': ['l', 'c']}),
        ('p', 'Para que la comparación fuera justa, todas las corridas tuvieron el mismo '
              'presupuesto de cómputo: 30.000 individuos generados, es decir, 600 generaciones con '
              'población 50, 300 con 100 y 200 con 150. Si se usara el criterio de generaciones sin '
              'mejora, una población grande consumiría más evaluaciones y obtendría ventaja solo '
              'por eso. Además, se usaron números aleatorios comunes: la réplica r empleó la misma '
              'semilla en las 27 combinaciones, de modo que las diferencias entre combinaciones se '
              'deben a los parámetros y no al azar.'),
        ('p', '**Variable de respuesta.** La respuesta principal es la tardanza total de la mejor '
              'solución de cada corrida; la secundaria es la desviación porcentual relativa del '
              r'makespan, $RPD=100\,(C_{\max}-C_{\max}^{*})/C_{\max}^{*}$, donde $C_{\max}^{*}$ es '
              'el menor makespan entre las corridas con la mejor tardanza. Las pruebas de rangos '
              r'(Kruskal-Wallis y Wilcoxon) se aplicaron sobre $Z=1000\cdot\sum T_j+C_{\max}$: como '
              r'solo usan el orden de los datos, ordenar por $Z$ equivale a ordenar según el '
              'objetivo lexicográfico.'),
        ('p', '**Análisis.** Se aplicó un ANOVA multifactorial con efectos principales e '
              'interacciones dobles, se construyeron gráficos de medias con intervalos LSD al 95 % '
              'y se verificaron los supuestos de normalidad (Shapiro-Wilk) y homogeneidad de '
              'varianzas (Levene). Como confirmación no paramétrica se usó la prueba de '
              'Kruskal-Wallis (Kruskal y Wallis, 1952), y las comparaciones entre pares de '
              'configuraciones se hicieron con la prueba de Wilcoxon pareada por semilla '
              '(Wilcoxon, 1945).'),
        ('p', '**Experimento 1b: ampliación del rango.** Si la mejor combinación queda en el borde '
              'del rango probado, el óptimo podría estar fuera de él. Por eso se previó probar, con '
              'las mismas semillas y el mismo presupuesto, poblaciones de 150, 200 y 250 con '
              'probabilidades de mutación de 0,5 y 0,7, y cambiar la configuración solo si la mejora '
              'resultaba significativa.'),
        ('p', '**Experimento 2: criterio de parada.** Con la configuración seleccionada se compararon '
              'tres criterios de parada, 50, 100 y 200 generaciones sin mejora (máximo de 1.000 '
              'generaciones), con 10 réplicas cada uno, en términos de calidad y tiempo de cómputo.'),
        ('h4', 'Resultados del diseño factorial'),
        ('p', 'La Tabla {T:factorial} presenta las mejores y las peores combinaciones del diseño; la '
              '[[tabla completa de las 27 combinaciones se incluye en el Anexo Y]].'),
        ('tabla', 'Resultados del diseño factorial (mejores y peores combinaciones)',
         ['Población', 'p_c', 'p_m', 'ΣT_j prom. (h)', 'ΣT_j desv. (h)', '% réplicas ΣT_j = 0',
          'C_max prom. (h)', 'RPD C_max (%)', 'Tiempo (s)'], [
             ['150', '0,9', '0,5', '0,00', '0,00', '100', '652,3', '3,7', '95'],
             ['150', '0,8', '0,5', '0,37', '0,84', '80', '656,1', '4,3', '98'],
             ['100', '0,9', '0,3', '1,82', '4,07', '80', '651,6', '3,6', '89'],
             ['150', '0,9', '0,3', '5,04', '11,28', '80', '671,3', '6,8', '92'],
             ['150', '0,8', '0,3', '5,56', '7,32', '40', '664,4', '5,6', '88'],
             ['…', '…', '…', '…', '…', '…', '…', '…', '…'],
             ['50', '0,9', '0,3', '59,57', '20,36', '0', '731,6', '16,3', '90'],
             ['50', '0,7', '0,1', '61,83', '37,51', '0', '733,8', '16,7', '71'],
             ['50', '0,8', '0,1', '73,48', '22,35', '0', '745,5', '18,5', '79']],
         {'etiqueta': 'factorial', 'anchos': [1150, 600, 600, 1100, 1100, 1200, 1150, 1000, 938], 'tam': 10,
          'negrita_filas': (0,)}),
        ('p', 'La combinación de población 150, probabilidad de cruce 0,9 y probabilidad de '
              'mutación 0,5 fue la única que eliminó la tardanza en las cinco réplicas. La Tabla {T:anova} '
              'presenta el ANOVA sobre la tardanza total.'),
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
        ('p', 'El tamaño de la población y la probabilidad de mutación tienen efectos significativos '
              'sobre la tardanza total (p < 0,001), mientras que la probabilidad de cruce no es '
              'significativa en el rango 0,7–0,9 (p = 0,127), y ninguna interacción lo es. Los '
              'residuos cumplen el supuesto de normalidad (Shapiro-Wilk, W = 0,990; p = 0,459), pero '
              'las varianzas no son homogéneas entre los niveles de población (Levene, p < 0,001) '
              'ni de mutación (p = 0,029). Por eso las conclusiones se confirmaron con la prueba de '
              'Kruskal-Wallis, que coincide con el ANOVA: población, H = 30,2 (p < 0,001); mutación, '
              'H = 14,5 (p < 0,001), y cruce, H = 4,5 (p = 0,106). La Figura {F:efectos} muestra los efectos '
              'principales: aumentar la población de 50 a 150 y la probabilidad de mutación de 0,1 '
              'a 0,5 reduce la tardanza de forma significativa, ya que los intervalos LSD de sus '
              'niveles no se traslapan. Como no hay interacciones significativas, cada parámetro '
              'puede elegirse por separado.'),
        ('figura', 'Efectos principales sobre la tardanza total, con intervalos LSD al 95 %',
         os.path.join(SAL_CAL, 'efectos_principales.png'), 15.5, 'efectos'),
        ('h4', 'Ampliación del rango'),
        ('p', 'La mejor combinación quedó en el borde del rango probado, con la población y la '
              'mutación en sus valores máximos, por lo que se realizó el experimento 1b (Tabla {T:ampliacion}).'),
        ('tabla', 'Ampliación del rango de población y mutación (probabilidad de cruce 0,9)',
         ['Población', 'p_m', 'ΣT_j prom. (h)', '% réplicas ΣT_j = 0', 'C_max prom. (h)',
          'Wilcoxon frente a la actual (p)'], [
             ['150', '0,5', '0,00', '100', '652,3', '—'],
             ['200', '0,5', '0,00', '100', '656,6', '0,813'],
             ['150', '0,7', '0,16', '80', '664,0', '0,125'],
             ['250', '0,5', '2,00', '80', '665,1', '0,438'],
             ['200', '0,7', '2,99', '20', '672,1', '0,063'],
             ['250', '0,7', '8,67', '0', '680,7', '0,063']],
         {'etiqueta': 'ampliacion', 'anchos': [1200, 900, 1500, 1700, 1600, 1938], 'negrita_filas': (0,)}),
        ('p', 'Fuera del rango original, el desempeño se mantiene (población 200) o empeora '
              '(población 250 o mutación 0,7); la prueba de Kruskal-Wallis entre las seis '
              'configuraciones es significativa (H = 17,1; p = 0,004). Con un presupuesto fijo, una '
              'población mayor dispone de menos generaciones para evolucionar, y una mutación más '
              'alta destruye buenas soluciones. El óptimo se encuentra, por lo tanto, dentro del '
              'rango probado. Como la población 200 no es significativamente distinta de la 150, '
              'se conserva la población 150 por parsimonia: igual resultado con menos individuos.'),
        ('h4', 'Criterio de parada'),
        ('p', 'La Tabla {T:parada} presenta los resultados del experimento 2 con la configuración '
              'seleccionada.'),
        ('tabla', 'Comparación de criterios de parada (población 150, cruce 0,9, mutación 0,5)',
         ['Generaciones sin mejora', 'ΣT_j prom. (h)', '% réplicas ΣT_j = 0', 'C_max prom. (h)',
          'RPD C_max (%)', 'Generaciones (prom.)', 'Tiempo prom. (min)'], [
             ['50', '0,00', '100', '650,8', '4,47', '388', '3,1'],
             ['100', '0,00', '100', '644,5', '3,45', '633', '5,0'],
             ['200', '0,00', '100', '642,7', '3,18', '855', '6,6']],
         {'etiqueta': 'parada', 'anchos': [1500, 1100, 1250, 1200, 1150, 1400, 1238], 'negrita_filas': (1,)}),
        ('p', 'Con la configuración calibrada, las 30 corridas eliminaron la tardanza, por lo que '
              'la diferencia entre los criterios está en el makespan y en el tiempo de cómputo. '
              'Pasar de 50 a 100 generaciones sin mejora reduce el makespan de forma significativa '
              '(Wilcoxon pareado, p = 0,016, significativo también con la corrección de Bonferroni '
              'para dos comparaciones, α = 0,025). Pasar de 100 a 200 no produce una mejora '
              'significativa (p = 0,063) y aumenta el tiempo de cómputo en 33 %. Se adopta, por lo '
              'tanto, el criterio de 100 generaciones sin mejora. La prueba global de '
              'Kruskal-Wallis no detecta diferencias (p = 0,21) porque no aprovecha el '
              'emparejamiento por semilla.'),
        ('h4', 'Configuración final'),
        ('tabla', 'Configuración final del algoritmo genético', ['Parámetro', 'Valor', 'Origen'], [
            ['Tamaño de la población', '150', 'Experimentos 1 y 1b'],
            ['Probabilidad de cruce', '0,9', 'Experimento 1 (sin efecto significativo; menor ΣT_j)'],
            ['Probabilidad de mutación', '0,5', 'Experimentos 1 y 1b'],
            ['Criterio de parada', '100 generaciones sin mejora (máx. 1.000)', 'Experimento 2'],
            ['Tamaño del torneo', '3', 'Fijo'],
            ['Probabilidades de intercambio y perturbación', '0,30 y 0,40', 'Fijo'],
            ['Desviación de la perturbación', '0,15', 'Fijo']],
         {'etiqueta': 'final', 'anchos': [3300, 2700, 2838], 'alineacion': ['l', 'c', 'l']}),
        ('p', 'La calibración se realizó sobre la instancia del caso de estudio. Si cambian de forma '
              'importante las condiciones del problema, por ejemplo el número de sublotes o el '
              'volumen de órdenes, conviene repetir al menos el experimento del criterio de parada.')]


# ===========================================================================
# 5. Solución obtenida
# ===========================================================================

def datos_solucion(ruta_modelo, ruta_bd):
    spec = importlib.util.spec_from_file_location('modelo_ag', ruta_modelo)
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    with contextlib.redirect_stdout(io.StringIO()):
        M.cargar_datos(ruta_bd)
    rep = pd.read_csv(os.path.join(SAL_SOL, 'replicas.csv'))
    with open(os.path.join(SAL_SOL, 'mejor_solucion.json'), encoding='utf-8') as fh:
        mejor = json.load(fh)
    ind = mejor['individuo']
    ind = {'k': ind['k'], 'proporciones': ind['proporciones'],
           'posiciones': {int(s): [tuple(x) for x in v] for s, v in ind['posiciones'].items()}}
    C, gantt = M.simular_hfs(ind)
    indic = M.calcular_indicadores(C)
    tam = {j: M.props_a_docenas(j, ind['proporciones'][j]) for j in M.TRABAJOS}
    cmax = indic['Cmax']
    util = {}
    for s in M.ETAPAS:
        ocupado = sum(f - i for (_, _, _, i, f) in gantt[s])
        util[s] = (M.NOMBRE_ETAPA[s], len(M.MAQUINAS_POR_ETAPA[s]), ocupado,
                   100.0 * ocupado / (len(M.MAQUINAS_POR_ETAPA[s]) * cmax))
    al = gantt['alistamientos']
    # Figuras
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    gantt_documento(M, gantt, indic, os.path.join(SAL_SOL, 'gantt_solucion.png'))
    hist = mejor['historial']
    fig, ax1 = plt.subplots(figsize=(8, 3.6))
    g = list(range(1, len(hist) + 1))
    ax1.plot(g, [h[0] for h in hist], color='#4E79A7', lw=1.6, label='ΣTj (h)')
    ax1.set_xlabel('Generación'); ax1.set_ylabel('Tardanza total de la mejor solución (h)', color='#4E79A7')
    ax2 = ax1.twinx()
    ax2.plot(g, [h[1] for h in hist], color='#E15759', lw=1.2, ls='--', label='Cmax (h)')
    ax2.set_ylabel('Makespan de la mejor solución (h)', color='#E15759')
    ax1.grid(alpha=0.3, ls=':')
    l1, n1 = ax1.get_legend_handles_labels(); l2, n2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, n1 + n2, loc='upper right', fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(SAL_SOL, 'convergencia.png'), dpi=200)
    plt.close(fig)
    return M, rep, mejor, indic, tam, util, al


def gantt_documento(M, gantt, indic, ruta):
    """Gantt compacto en vertical para el documento: una fila por máquina."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    colores = ['#4E79A7', '#F28E2B', '#59A14F', '#E15759', '#B07AA1',
               '#76B7B2', '#EDC948', '#FF9DA7', '#9C755F', '#BAB0AC']
    color = {j: colores[k % 10] for k, j in enumerate(M.TRABAJOS)}
    maquinas = [(s, m) for s in M.ETAPAS for m in M.MAQUINAS_POR_ETAPA[s]]
    y = {m: len(maquinas) - 1 - k for k, (_, m) in enumerate(maquinas)}
    fig, ax = plt.subplots(figsize=(7.5, 9.6))
    for s in M.ETAPAS:
        for (j, b, m, ini, fin) in gantt[s]:
            ax.barh(y[m], fin - ini, left=ini, height=0.8, color=color[j], edgecolor='white',
                    linewidth=0.2)
    for (s, m, ini, fin) in gantt['alistamientos']:
        ax.barh(y[m], fin - ini, left=ini, height=0.8, color='black')
    limites = []
    acum = 0
    for s in M.ETAPAS:
        nmaq = len(M.MAQUINAS_POR_ETAPA[s])
        top = len(maquinas) - acum - 0.5
        acum += nmaq
        bottom = len(maquinas) - acum - 0.5
        ax.axhline(bottom, color='#555555', lw=0.8)
        ax.text(-0.075, 1 - (len(maquinas) - (top + bottom) / 2 - 0.5) / len(maquinas),
                M.NOMBRE_ETAPA[s], rotation=90, ha='center', va='center', fontsize=8,
                fontweight='bold', transform=ax.transAxes)
    for j in M.TRABAJOS:
        ax.axvline(M.DUE_DATE[j], color=color[j], lw=0.6, ls=':', alpha=0.9)
    ax.set_yticks(list(y.values()))
    ax.set_yticklabels(list(y.keys()), fontsize=5.5)
    ax.set_ylim(-0.6, len(maquinas) - 0.4)
    ax.set_xlim(0, max(indic['Cmax'], max(M.DUE_DATE.values())) * 1.02)
    ax.set_xlabel('Tiempo (horas laborables)', fontsize=8)
    ax.tick_params(axis='x', labelsize=7)
    ax.grid(axis='x', ls=':', alpha=0.4)
    leyenda = [mpatches.Patch(color=color[j], label=f"{j} ({M.PRODUCTO[j]})") for j in M.TRABAJOS]
    leyenda.append(mpatches.Patch(color='black', label='Alistamiento'))
    ax.legend(handles=leyenda, loc='upper center', bbox_to_anchor=(0.5, -0.06), ncol=4,
              fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(ruta, dpi=220, bbox_inches='tight')
    plt.close(fig)


def bloque_solucion(M, rep, mejor, indic, tam, util, al):
    def fecha(x):
        f = M.horas_a_fecha(x)
        return f.strftime('%d/%m/%Y') if f is not None else '—'

    filas_tam = []
    for j in M.TRABAJOS:
        filas_tam.append([j] + [n(x, 0) for x in tam[j]] + [n(sum(tam[j]), 0)])
    filas_ord = []
    for j in M.TRABAJOS:
        v = indic['por_trabajo'][j]
        filas_ord.append([j, M.PRODUCTO[j], n(M.DEMANDA[j], 0), n(v['ri'], 0), n(v['di'], 0),
                          M.FECHA_ENTREGA[j].strftime('%d/%m/%Y') if M.FECHA_ENTREGA[j] is not None else '—',
                          n(v['Ci'], 2), fecha(v['Ci']), n(v['Ti'], 2), n(v['Ei'], 2)])
    tard = (rep['suma_T'] <= 1e-6).sum()
    hist = mejor['historial']
    gen_cero = next((g + 1 for g, h in enumerate(hist) if h[0] <= 1e-9), len(hist))
    cmax_cero = hist[gen_cero - 1][1]
    gen_ultima = max((g + 1 for g in range(1, len(hist)) if hist[g] != hist[g - 1]), default=1)
    mayor = max(util.values(), key=lambda u: u[3])
    if mayor[0].lower() == 'troquelado':
        frase_ocupacion = ('Troquelado, el cuello de botella identificado en la caracterización, '
                           f'es la etapa con mayor ocupación ({n(mayor[3], 1)} %).')
    else:
        frase_ocupacion = (f'La etapa con mayor ocupación es {mayor[0].lower()} '
                           f'({n(mayor[3], 1)} %).')
    mejor_i = indic
    B = [('h3', 'Programación obtenida para el caso de estudio'),
         ('p', f'Con los parámetros calibrados se ejecutó el algoritmo genético {len(rep)} veces '
               'sobre la instancia del caso de estudio, con semillas distintas. '
               + (f'Todas las réplicas eliminaron la tardanza (ΣT_j = 0 h); '
                  if tard == len(rep) else
                  f'En {tard} de las {len(rep)} réplicas se eliminó la tardanza; la tardanza total '
                  f'promedio fue de {n(rep["suma_T"].mean(), 2)} h (máximo '
                  f'{n(rep["suma_T"].max(), 2)} h); ') +
               f'el makespan promedio fue de {n(rep["Cmax"].mean(), 1)} h (entre {n(rep["Cmax"].min(), 1)} y '
               f'{n(rep["Cmax"].max(), 1)} h) y el tiempo promedio por corrida de '
               f'{n(rep["segundos"].mean() / 60, 1)} minutos. Se presenta a continuación la mejor '
               'programación obtenida, que corresponde a la propuesta del modelo para el conjunto '
               'de órdenes. La Tabla {T:tamanos} muestra los tamaños de los sublotes, que se mantienen en '
               'las cuatro etapas.'),
         ('tabla', 'Tamaños de los sublotes de la programación propuesta [docenas]',
          ['Orden'] + [f'S{b}' for b in range(1, 11)] + ['Total'], filas_tam,
          {'etiqueta': 'tamanos', 'anchos': [800] + [690] * 10 + [1138], 'tam': 9}),
         ('p', 'Los tamaños de los sublotes de una misma orden son distintos entre sí, lo que '
               'muestra el aprovechamiento de los sublotes consistentes: el algoritmo combina '
               'sublotes pequeños, que adelantan el inicio de las etapas siguientes, con sublotes '
               'mayores que completan la orden. La Tabla {T:orden} presenta los resultados por orden.'),
         ('tabla', 'Resultados por orden de la programación propuesta',
          ['Orden', 'Ref.', 'Q_j (doc.)', 'r_j (h)', 'd_j (h)', 'Entrega', 'C_j (h)',
           'Terminación', 'T_j (h)', 'E_j (h)'], filas_ord,
          {'etiqueta': 'orden', 'anchos': [780, 650, 800, 680, 680, 1100, 900, 1300, 950, 998], 'tam': 9}),
         ('p', 'La Tabla {T:indicadores} resume los indicadores globales de la programación.'),
         ('tabla', 'Indicadores globales de la programación propuesta', ['Indicador', 'Valor'], [
             ['Tardanza total (ΣT_j)', f'{n(mejor_i["suma_Ti"], 2)} h'],
             ['Órdenes tardías', f'{mejor_i["num_tardy"]} de {len(M.TRABAJOS)}'],
             ['Tardanza máxima (T_max)', f'{n(mejor_i["Tmax"], 2)} h'],
             ['Makespan (C_max)', f'{n(mejor_i["Cmax"], 2)} h ({fecha(mejor_i["Cmax"])})'],
             ['Adelanto total (ΣE_j)', f'{n(mejor_i["suma_Ei"], 2)} h'],
             ['Tiempo de flujo medio', f'{n(mejor_i["media_Fi"], 2)} h'],
             ['Alistamientos en troquelado', f'{len(al)} ({n(sum(f - i for (_, _, i, f) in al), 2)} h)']]
          + [[f'Ocupación de {u[0].lower()} ({u[1]} máquinas)', f'{n(u[3], 1)} %']
             for u in util.values()],
          {'etiqueta': 'indicadores', 'anchos': [5000, 3838], 'alineacion': ['l', 'c']}),
         ('p', 'La ocupación se calcula como el tiempo de procesamiento de la etapa dividido entre '
               'el número de máquinas por el makespan. ' + frase_ocupacion + ' La Figura {F:gantt} '
               'presenta el diagrama de Gantt de la programación y la Figura {F:conv} la evolución '
               'de la mejor solución durante la búsqueda.'),
         ('figura', 'Diagrama de Gantt de la programación propuesta (las líneas punteadas '
                    'marcan las fechas de entrega)',
          os.path.join(SAL_SOL, 'gantt_solucion.png'), 14.5, 'gantt'),
         ('figura', 'Convergencia del algoritmo genético en la mejor réplica',
          os.path.join(SAL_SOL, 'convergencia.png'), 14.5, 'conv'),
         ('p', f'La búsqueda parte de la solución de la regla EDD (ΣT_j = 145 h, C_max = 817 h) y '
               f'elimina la tardanza en la generación {gen_cero}, con un makespan de '
               f'{n(cmax_cero, 1)} h. A partir de ese punto, el algoritmo continúa reduciendo el '
               f'makespan hasta {n(mejor_i["Cmax"], 1)} h, con la última mejora en la generación '
               f'{gen_ultima}, y se detiene en la generación {mejor["generaciones"]} '
               + ('tras 100 generaciones sin mejora. ' if mejor['generaciones'] < 1000 else
                  'al alcanzar el máximo de generaciones. ') +
               'La comparación detallada de esta programación con el sistema de programación '
               'actual de la empresa, mediante los indicadores de desempeño, se presenta en la '
               'Fase 3.'),
         ('h4', 'Síntesis de la fase'),
         ('p', 'En esta fase se construyó un modelo de programación lineal entera mixta que '
               'representa el Flow Shop híbrido de la empresa con sublotes consistentes, '
               'liberaciones, alistamiento dependiente de la secuencia en troquelado y máquinas no '
               'relacionadas en ensamble, con el objetivo de minimizar la tardanza total. Como el '
               'modelo no es tratable de forma exacta a la escala real, se diseñó un algoritmo '
               'genético con un cromosoma de dos niveles, un decodificador que garantiza la '
               'factibilidad, cruce aritmético y LOX, mutación por perturbación e intercambio, y una '
               'población inicial sembrada con reglas de despacho. La validación con nueve '
               'instancias reducidas confirmó que el modelo está bien formulado y que el algoritmo '
               'alcanza el óptimo en las instancias donde este se conoce, y la calibración '
               'estadística permitió fijar sus parámetros. El resultado es un método de '
               'programación verificado, validado y calibrado, que se evalúa frente al sistema '
               'actual en la siguiente fase.')]
    return B


# ===========================================================================

def main():
    borrador, salida, ruta_modelo, ruta_bd = sys.argv[1:5]
    M, rep, mejor, indic, tam, util, al = datos_solucion(ruta_modelo, ruta_bd)
    bloques = (bloque_modelo() + bloque_ag() + bloque_implementacion() + bloque_validacion()
               + [('h3', 'Número de sublotes y calibración de parámetros')]
               + bloque_sublotes() + bloque_calibracion()
               + bloque_solucion(M, rep, mejor, indic, tam, util, al))
    bloques = L.resolver_referencias(bloques, tabla_ini=5, figura_ini=3)
    bloques = L.matematizar(bloques)
    import re as _re
    for b in bloques:                      # aviso: símbolos con "_" que quedaron como texto
        if b[0] in ('codigo', 'figura', 'ecuacion'):
            continue
        for x in _re.findall(r'[^$]+(?=\$|$)', json.dumps(b, ensure_ascii=False)):
            pass
        texto = json.dumps(b[1:], ensure_ascii=False)
        fuera = _re.sub(r'\$[^$]*\$', '', texto)
        for m in _re.findall(r'[A-Za-zΣ]+_[A-Za-z]+', fuera):
            if m not in ('BD_HFS',):
                print('Aviso: símbolo como texto:', m)
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
