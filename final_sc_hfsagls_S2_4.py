# -*- coding: utf-8 -*-
"""
=============================================================================
PROGRAMACIÓN DE UN FLOW SHOP HÍBRIDO CON SUBLOTES CONSISTENTES
MEDIANTE UN ALGORITMO GENÉTICO — PRODUCCIÓN DE GUANTES INDUSTRIALES
=============================================================================

Objetivo: minimizar la tardanza total (ΣTj) de las órdenes de trabajo.

Sistema: cuatro etapas en serie (troquelado, ensamble, costura y volteado)
con máquinas paralelas; en troquelado, cada cambio de referencia en una
máquina exige un alistamiento.

Lot streaming: cada orden se divide en un número fijo de sublotes de tamaño
variable (en docenas enteras), que conservan su tamaño en todas las etapas
(sublotes consistentes,
escenario 2 de Gürsoy Yılmaz y Yılmaz, 2022). Cada sublote pasa a la etapa
siguiente en cuanto termina la actual.

Cromosoma de dos niveles:
  Nivel 1 → proporciones de los tamaños de los sublotes de cada orden
  Nivel 2 → secuencia de los sublotes en cada etapa
La máquina de cada sublote la elige el decodificador con la regla del menor
tiempo de terminación (ECT).

Datos de entrada: libro de Excel BD_HFS.xlsx con las hojas
  "Tiempo de procesamiento": Codigo producto | Maquina | Etapa | min x docena
  "Trabajos"               : Orden de trabajo | Codigo Producto | Cantidad
                             (docenas) | r_j | Fechas de entrega | d_j horas
  "Disponibilidad"         : calendario laboral (horas acumuladas por día)

Uso:  python final_sc_hfsagls_S2_4.py [ruta/BD_HFS.xlsx]
"""

import random
import copy
import os
import sys
import math
import bisect
import unicodedata
from typing import List, Dict, Tuple, Optional

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker

# ---------------------------------------------------------------------------
# 1. DATOS DEL PROBLEMA (se llenan con cargar_datos)
# ---------------------------------------------------------------------------

RUTA_EXCEL = "BD_HFS.xlsx"

TRABAJOS: List[str] = []                        # ['J01', 'J02', ...]
PRODUCTO: Dict[str, str] = {}                   # orden → referencia
DEMANDA: Dict[str, float] = {}                  # orden → cantidad [docenas]
RELEASE: Dict[str, float] = {}                  # orden → liberación r_j [h]
DUE_DATE: Dict[str, float] = {}                 # orden → entrega d_j [h]
FECHA_ENTREGA: Dict[str, object] = {}           # orden → fecha calendario

ETAPAS: List[int] = []                          # [1, 2, 3, 4]
NOMBRE_ETAPA: Dict[int, str] = {}               # 1 → 'Troquelado', ...
MAQUINAS_POR_ETAPA: Dict[int, List[str]] = {}   # 1 → ['M1', ..., 'M4']
ETAPA_DE_MAQUINA: Dict[str, int] = {}           # 'M1' → 1

# Tiempo estándar [min/docena] por (referencia, máquina)
TIEMPO_MIN_DOCENA: Dict[Tuple[str, str], float] = {}

# Máquinas que procesan cada referencia en cada etapa: (referencia, etapa) → [máquinas]
ELEGIBLES: Dict[Tuple[str, int], List[str]] = {}

# Calendario laboral: (fecha, horas hábiles acumuladas al final del día)
CALENDARIO: List[Tuple[object, float]] = []

# ---------------------------------------------------------------------------
# 2. PARÁMETROS DEL MODELO
# ---------------------------------------------------------------------------

NUM_SUBLOTES = 10               # sublotes por orden (se reduce solo si la orden
                                # no alcanza para 10 sublotes del tamaño mínimo)
GRANULARIDAD_DOCENAS = 1.0      # los tamaños son docenas enteras
MIN_DOCENAS_POR_SUBLOTE = 1.0   # tamaño mínimo de sublote [docenas]

# Alistamiento por cambio de referencia [min]. Se aplica también al primer
# sublote de cada máquina (montaje inicial) y puede ejecutarse mientras la
# máquina espera la llegada del sublote.
ALISTAMIENTO_MIN_POR_ETAPA = {'Troquelado': 4.98}

# ---------------------------------------------------------------------------
# 3. PARÁMETROS DEL ALGORITMO GENÉTICO
#    Calibrados en la Fase 2 (sección 4.2.4): diseño factorial 3³ de población,
#    cruce y mutación, ampliación del rango y comparación del criterio de parada
#    (ver fase2/calibracion_ag.py y fase2/salida_calibracion/).
# ---------------------------------------------------------------------------

GA_PARAMS = {
    'poblacion'    : 150,   # tamaño de la población
    'generaciones' : 1000,  # máximo de generaciones
    'sin_mejora'   : 100,   # parada tras 100 generaciones sin mejora (calibrado)
    'prob_cruce'   : 0.90,  # probabilidad de cruce
    'prob_mutacion': 0.50,  # probabilidad de mutar cada hijo
    'prob_mut_pos' : 0.30,  # probabilidad de intercambio de posiciones (nivel 2)
    'prob_mut_prop': 0.40,  # probabilidad de perturbar los tamaños de una orden (nivel 1)
    'desv_mut_prop': 0.15,  # desviación de la perturbación de tamaños
    'tam_torneo'   : 3,     # tamaño del torneo
    'semilla'      : 42,    # semilla aleatoria (None = distinta en cada corrida)
}

# ---------------------------------------------------------------------------
# 4. LECTURA DEL LIBRO DE EXCEL
# ---------------------------------------------------------------------------

def _norm(texto) -> str:
    """Texto en minúsculas, sin tildes y sin espacios repetidos."""
    t = unicodedata.normalize('NFKD', str(texto))
    t = t.encode('ascii', 'ignore').decode('ascii').lower()
    return ' '.join(t.split())


def _buscar_hoja(hojas: List[str], *claves: str) -> Optional[str]:
    """Primera hoja cuyo nombre contiene alguna de las claves."""
    for h in hojas:
        if any(c in _norm(h) for c in claves):
            return h
    return None


def _buscar_col(df: pd.DataFrame, condicion, descripcion: str,
                obligatoria: bool = True) -> Optional[str]:
    """Primera columna cuyo nombre normalizado cumple la condición."""
    for col in df.columns:
        if condicion(_norm(col)):
            return col
    if obligatoria:
        raise ValueError(f"No se encontró la columna '{descripcion}'. "
                         f"Columnas disponibles: {list(df.columns)}")
    return None


def _clave_maquina(m: str):
    """Orden natural de máquinas: M2 antes que M10."""
    digitos = ''.join(c for c in str(m) if c.isdigit())
    return (int(digitos) if digitos else 0, str(m))


def _resolver_ruta(ruta: str) -> str:
    """Busca el libro en la ruta dada, en el directorio actual y junto al script."""
    base = os.path.basename(ruta)
    candidatas = [ruta, os.path.join(os.getcwd(), base)]
    try:
        candidatas.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), base))
    except NameError:       # ejecución dentro de un notebook
        pass
    for c in candidatas:
        if os.path.isfile(c):
            return c
    raise FileNotFoundError(f"No se encontró el libro de Excel '{ruta}'.")


def _horas_acumuladas_hasta(fecha, incluir_dia: bool) -> Optional[float]:
    """Horas hábiles acumuladas al final del día 'fecha' (o del día anterior)."""
    if not CALENDARIO:
        return None
    fecha = pd.Timestamp(fecha).normalize()
    acumuladas = 0.0
    for f, h in CALENDARIO:
        if f < fecha or (incluir_dia and f == fecha):
            acumuladas = h
        else:
            break
    return acumuladas


def horas_a_fecha(horas: float):
    """Fecha del calendario en que se alcanzan las horas hábiles dadas."""
    for f, h in CALENDARIO:
        if h >= horas - 1e-9 and h > 0:
            return f
    return None


def cargar_datos(ruta: str = RUTA_EXCEL) -> None:
    """Lee el libro de Excel y llena las estructuras del problema."""
    ruta = _resolver_ruta(ruta)
    xls = pd.ExcelFile(ruta)

    hoja_tiempos = _buscar_hoja(xls.sheet_names, 'tiempo')
    hoja_trab    = _buscar_hoja(xls.sheet_names, 'trabajo')
    hoja_disp    = _buscar_hoja(xls.sheet_names, 'disponib', 'calendario')
    if hoja_tiempos is None or hoja_trab is None:
        raise ValueError(f"El libro debe tener las hojas de tiempos y de trabajos. "
                         f"Hojas: {xls.sheet_names}")

    for estructura in (TRABAJOS, CALENDARIO, ETAPAS):
        estructura.clear()
    for estructura in (PRODUCTO, DEMANDA, DUE_DATE, RELEASE, FECHA_ENTREGA,
                       NOMBRE_ETAPA, MAQUINAS_POR_ETAPA, ETAPA_DE_MAQUINA,
                       TIEMPO_MIN_DOCENA, ELEGIBLES):
        estructura.clear()

    # ── Calendario laboral ──
    if hoja_disp is not None:
        dfc = xls.parse(hoja_disp)
        c_fecha = _buscar_col(dfc, lambda n: n == 'fecha', 'Fecha', False)
        c_acum  = (_buscar_col(dfc, lambda n: 'acumulad' in n and 'final' in n,
                               'Horas acumuladas final día', False)
                   or _buscar_col(dfc, lambda n: 'acumulad' in n and 'inicio' not in n,
                                  'Horas acumuladas', False))
        c_hdisp = _buscar_col(dfc, lambda n: 'horas disponibles' in n,
                              'Horas disponibles', False)
        if c_fecha is not None and (c_acum is not None or c_hdisp is not None):
            dfc = dfc[dfc[c_fecha].notna()].copy()
            dfc[c_fecha] = pd.to_datetime(dfc[c_fecha]).dt.normalize()
            dfc = dfc.sort_values(c_fecha)
            acum = (dfc[c_acum].astype(float).tolist() if c_acum is not None
                    else dfc[c_hdisp].astype(float).cumsum().tolist())
            CALENDARIO.extend(zip(dfc[c_fecha].tolist(), acum))

    # ── Tiempos de procesamiento ──
    dft = xls.parse(hoja_tiempos)
    c_prod  = _buscar_col(dft, lambda n: 'codigo' in n or 'producto' in n, 'Codigo producto')
    c_maq   = _buscar_col(dft, lambda n: 'maquina' in n, 'Maquina')
    c_etapa = _buscar_col(dft, lambda n: 'etapa' in n, 'Etapa')
    c_min   = _buscar_col(dft, lambda n: n.startswith('min'), 'min x docena', False)
    c_hora  = _buscar_col(dft, lambda n: n.startswith('h') and 'docena' in n,
                          'h x docena', False)
    if c_min is None and c_hora is None:
        raise ValueError("La hoja de tiempos debe tener 'min x docena' o 'h x docena'.")

    dft = dft[dft[c_prod].notna() & dft[c_maq].notna() & dft[c_etapa].notna()]

    # Las etapas se numeran en el orden en que aparecen en la hoja
    nombres_en_orden: List[str] = []
    for nombre in dft[c_etapa].astype(str).str.strip():
        if nombre not in nombres_en_orden:
            nombres_en_orden.append(nombre)
    id_etapa = {nombre: i + 1 for i, nombre in enumerate(nombres_en_orden)}
    ETAPAS.extend(id_etapa.values())
    NOMBRE_ETAPA.update({i: n for n, i in id_etapa.items()})
    for s in ETAPAS:
        MAQUINAS_POR_ETAPA[s] = []

    for _, fila in dft.iterrows():
        prod = str(fila[c_prod]).strip()
        maq  = str(fila[c_maq]).strip()
        s    = id_etapa[str(fila[c_etapa]).strip()]
        if c_min is not None and pd.notna(fila[c_min]):
            t_min = float(fila[c_min])
        elif c_hora is not None and pd.notna(fila[c_hora]):
            t_min = float(fila[c_hora]) * 60.0
        else:
            continue
        if maq in ETAPA_DE_MAQUINA and ETAPA_DE_MAQUINA[maq] != s:
            raise ValueError(f"La máquina {maq} aparece en dos etapas distintas.")
        ETAPA_DE_MAQUINA[maq] = s
        if maq not in MAQUINAS_POR_ETAPA[s]:
            MAQUINAS_POR_ETAPA[s].append(maq)
        TIEMPO_MIN_DOCENA[(prod, maq)] = t_min
        ELEGIBLES.setdefault((prod, s), [])
        if maq not in ELEGIBLES[(prod, s)]:
            ELEGIBLES[(prod, s)].append(maq)

    for s in ETAPAS:
        MAQUINAS_POR_ETAPA[s].sort(key=_clave_maquina)
    for clave in ELEGIBLES:
        ELEGIBLES[clave].sort(key=_clave_maquina)

    # ── Órdenes de trabajo ──
    dfj = xls.parse(hoja_trab)
    c_orden = _buscar_col(dfj, lambda n: 'orden' in n or n.startswith('trabajo'),
                          'Orden de trabajo')
    c_prodj = _buscar_col(dfj, lambda n: 'codigo' in n or 'producto' in n,
                          'Codigo Producto')
    c_pares = _buscar_col(dfj, lambda n: 'pares' in n, 'Cantidad (pares)', False)
    c_doc   = _buscar_col(dfj, lambda n: 'docena' in n, 'Cantidad (docenas)', False)
    c_rj    = _buscar_col(dfj, lambda n: n.startswith('r_j') or n.startswith('rj')
                          or ('liberacion' in n and 'fecha' not in n),
                          'r_j Liberación', False)
    c_lib   = _buscar_col(dfj, lambda n: 'liberacion' in n, 'Fecha de liberación', False)
    c_fent  = _buscar_col(dfj, lambda n: 'entrega' in n, 'Fechas de entrega', False)
    c_horas = _buscar_col(dfj, lambda n: 'horas' in n, 'd_j horas', False)
    if c_pares is None and c_doc is None:
        raise ValueError("La hoja de trabajos debe tener la cantidad en pares o en docenas.")

    dfj = dfj[dfj[c_orden].notna()]
    for _, fila in dfj.iterrows():
        j = str(fila[c_orden]).strip()
        if j in PRODUCTO:
            raise ValueError(f"La orden de trabajo {j} está repetida.")
        TRABAJOS.append(j)
        PRODUCTO[j] = str(fila[c_prodj]).strip()

        # Cantidad en docenas (si el libro la trae en pares, se convierte)
        if c_doc is not None and pd.notna(fila[c_doc]):
            DEMANDA[j] = float(fila[c_doc])
        else:
            DEMANDA[j] = float(fila[c_pares]) / 12.0

        # Fecha de entrega d_j [h hábiles]
        if c_horas is not None and pd.notna(fila[c_horas]):
            DUE_DATE[j] = float(fila[c_horas])
        elif c_fent is not None and pd.notna(fila[c_fent]) and CALENDARIO:
            DUE_DATE[j] = _horas_acumuladas_hasta(fila[c_fent], incluir_dia=True)
        else:
            raise ValueError(f"La orden {j} no tiene fecha de entrega.")
        FECHA_ENTREGA[j] = (pd.Timestamp(fila[c_fent]).normalize()
                            if c_fent is not None and pd.notna(fila[c_fent]) else None)

        # Liberación r_j [h hábiles]
        r = 0.0
        if c_rj is not None and pd.notna(fila[c_rj]):
            r = float(fila[c_rj])
        elif c_lib is not None and pd.notna(fila[c_lib]) and CALENDARIO:
            r = _horas_acumuladas_hasta(fila[c_lib], incluir_dia=False)
        RELEASE[j] = r

    # ── Validaciones ──
    if not TRABAJOS:
        raise ValueError("La hoja de trabajos no contiene órdenes.")
    for j in TRABAJOS:
        if DEMANDA[j] <= 0:
            raise ValueError(f"La orden {j} tiene cantidad no positiva.")
        for s in ETAPAS:
            if not ELEGIBLES.get((PRODUCTO[j], s)):
                raise ValueError(f"La referencia {PRODUCTO[j]} (orden {j}) no tiene "
                                 f"tiempos en la etapa {NOMBRE_ETAPA[s]}.")

    print(f"  Datos cargados desde: {ruta}")
    print(f"    Órdenes: {len(TRABAJOS)} | Etapas: " +
          ", ".join(f"{NOMBRE_ETAPA[s]} ({len(MAQUINAS_POR_ETAPA[s])} máq.)"
                    for s in ETAPAS))
    print()

# ---------------------------------------------------------------------------
# 5. TIEMPOS
# ---------------------------------------------------------------------------

def tiempo_horas(trabajo: str, maquina: str, cant_docenas: float) -> float:
    """Tiempo de proceso [h] = (min/docena) × docenas / 60."""
    return (TIEMPO_MIN_DOCENA[(PRODUCTO[trabajo], maquina)] * cant_docenas) / 60.0


def elegibles(trabajo: str, etapa: int) -> List[str]:
    """Máquinas de la etapa que procesan la referencia de la orden."""
    return ELEGIBLES[(PRODUCTO[trabajo], etapa)]


def tiempo_lote_etapa(trabajo: str, etapa: int) -> float:
    """Tiempo [h] de la orden completa en la máquina más rápida de la etapa
    (se usa para ordenar las reglas SPT, LPT, MST y CR)."""
    return min(tiempo_horas(trabajo, m, DEMANDA[trabajo]) for m in elegibles(trabajo, etapa))

# ---------------------------------------------------------------------------
# 6. REPRESENTACIÓN DE LA SOLUCIÓN
# ---------------------------------------------------------------------------
#
#  individuo = {
#    'k'           : {j: B_j}               número de sublotes de la orden j
#    'proporciones': {j: [p_1, ..., p_Bj]}  NIVEL 1: tamaños relativos de los
#                                           sublotes (iguales en todas las etapas)
#    'posiciones'  : {s: [(j, k), ...]}     NIVEL 2: secuencia de los sublotes
#                                           en cada etapa
#  }
# ---------------------------------------------------------------------------

def _min_unidades() -> int:
    """Tamaño mínimo de sublote en unidades de GRANULARIDAD_DOCENAS."""
    return max(1, math.ceil(MIN_DOCENAS_POR_SUBLOTE / GRANULARIDAD_DOCENAS - 1e-9))


def _unidades(trabajo: str) -> int:
    """Unidades de GRANULARIDAD_DOCENAS completas que caben en la orden."""
    return int(math.floor(DEMANDA[trabajo] / GRANULARIDAD_DOCENAS + 1e-9))


def num_sublotes(trabajo: str) -> int:
    """B_j: NUM_SUBLOTES, o menos si la orden no alcanza para ese número de
    sublotes del tamaño mínimo."""
    por_volumen = _unidades(trabajo) // _min_unidades()
    return max(1, min(NUM_SUBLOTES, por_volumen))


def _dirichlet(k: int) -> List[float]:
    """k proporciones aleatorias que suman uno."""
    muestras = [random.expovariate(1.0) for _ in range(k)]
    total = sum(muestras)
    props = [max(m / total, 1e-9) for m in muestras]
    total2 = sum(props)
    return [p / total2 for p in props]


def props_a_docenas(trabajo: str, props: List[float]) -> List[float]:
    """
    Convierte las proporciones del nivel 1 en tamaños de sublote [docenas]:
    múltiplos de GRANULARIDAD_DOCENAS, con el mínimo MIN_DOCENAS_POR_SUBLOTE y
    suma igual a la cantidad de la orden (método del mayor residuo).
    """
    total    = DEMANDA[trabajo]
    k        = len(props)
    unidades = _unidades(trabajo)
    residuo  = total - unidades * GRANULARIDAD_DOCENAS
    min_u    = _min_unidades()

    if k == 1 or unidades < k * min_u:
        tam = [0.0] * k
        tam[0] = total
        return tam

    libres = unidades - k * min_u
    crudos = [p * libres for p in props]
    base   = [int(math.floor(x)) for x in crudos]
    faltan = libres - sum(base)
    orden  = sorted(range(k), key=lambda i: crudos[i] - base[i], reverse=True)
    for i in orden[:faltan]:
        base[i] += 1

    tam = [(min_u + u) * GRANULARIDAD_DOCENAS for u in base]
    tam[-1] += residuo
    return tam


def _sublotes(k: Dict[str, int]) -> List[Tuple[str, int]]:
    """Lista de sublotes (j, k)."""
    return [(j, b) for j in TRABAJOS for b in range(1, k[j] + 1)]


def crear_individuo() -> dict:
    """
    Cromosoma aleatorio: proporciones aleatorias de los sublotes de cada orden
    (nivel 1) y secuencia aleatoria de los sublotes en cada etapa (nivel 2).
    """
    k = {j: num_sublotes(j) for j in TRABAJOS}
    proporciones = {j: _dirichlet(k[j]) for j in TRABAJOS}
    subs = _sublotes(k)
    posiciones = {}
    for s in ETAPAS:
        orden = subs[:]
        random.shuffle(orden)
        posiciones[s] = orden
    return {'k': k, 'proporciones': proporciones, 'posiciones': posiciones}

# ---------------------------------------------------------------------------
# 7. DECODIFICADOR
# ---------------------------------------------------------------------------

def _primer_hueco(intervalos: List[Tuple[float, float]], t_listo: float,
                  duracion: float) -> float:
    """Primer instante ≥ t_listo con un hueco libre de longitud 'duracion'."""
    t = t_listo
    for ini, fin in intervalos:
        if t + duracion <= ini + 1e-9:
            return t
        if fin > t:
            t = fin
    return t


def simular_hfs(individuo: dict) -> Tuple[Dict[str, float], Dict]:
    """
    Convierte el cromosoma en una programación (esquema serial, etapa por etapa).

    Para cada sublote (j, k), en el orden del nivel 2 de cada etapa:
      * está listo en la liberación r_j (troquelado) o al terminar la etapa
        anterior;
      * en troquelado se ubica después del último sublote de la máquina y se
        suma el alistamiento si es el primero de la máquina o si cambia la
        referencia; en las demás etapas ocupa el primer hueco libre;
      * se asigna a la máquina en la que termina primero (ECT).

    Retorna
      C     : {orden: terminación en la última etapa}
      gantt : {etapa: [(orden, sublote, máquina, inicio, fin), ...],
               'alistamientos': [(etapa, máquina, inicio, fin), ...]}
    """
    k   = individuo['k']
    doc = {j: props_a_docenas(j, individuo['proporciones'][j]) for j in TRABAJOS}

    listo = {(j, b): RELEASE[j] for j in TRABAJOS for b in range(1, k[j] + 1)}
    agenda: Dict[str, List[Tuple[float, float]]] = {}
    gantt: Dict = {s: [] for s in ETAPAS}
    gantt['alistamientos'] = []

    for s in ETAPAS:
        fin_s = {}
        setup_h = ALISTAMIENTO_MIN_POR_ETAPA.get(NOMBRE_ETAPA[s], 0.0) / 60.0
        ultimo: Dict[str, Tuple[str, float]] = {}      # máquina → (referencia, fin)
        for (j, b) in individuo['posiciones'][s]:
            cant = doc[j][b - 1]
            if cant <= 0:
                fin_s[(j, b)] = listo[(j, b)]
                continue
            t_listo = listo[(j, b)]

            mejor = None
            for m in elegibles(j, s):
                p = tiempo_horas(j, m, cant)
                if setup_h > 0:
                    prev  = ultimo.get(m)
                    libre = prev[1] if prev else 0.0
                    su    = setup_h if (prev is None or prev[0] != PRODUCTO[j]) else 0.0
                    ini   = max(libre + su, t_listo)
                    cand  = (m, ini, ini + p, libre, su)
                else:
                    ini  = _primer_hueco(agenda.get(m, []), t_listo, p)
                    cand = (m, ini, ini + p, None, 0.0)
                if mejor is None or cand[2] < mejor[2] - 1e-9:      # ECT
                    mejor = cand
            m, ini, fin, libre, su = mejor

            if setup_h > 0:
                ultimo[m] = (PRODUCTO[j], fin)
                if su > 0:
                    gantt['alistamientos'].append((s, m, libre, libre + su))
            else:
                bisect.insort(agenda.setdefault(m, []), (ini, fin))
            fin_s[(j, b)] = fin
            gantt[s].append((j, b, m, ini, fin))
        listo = fin_s

    C = {j: max(listo[(j, b)] for b in range(1, k[j] + 1)) for j in TRABAJOS}
    return C, gantt

# ---------------------------------------------------------------------------
# 8. INDICADORES Y APTITUD
# ---------------------------------------------------------------------------

def calcular_indicadores(C: Dict[str, float]) -> Dict:
    """Indicadores por orden y globales de la programación."""
    ind_j = {}
    for j in TRABAJOS:
        ci, ri, di = C[j], RELEASE[j], DUE_DATE[j]
        li = ci - di
        ti = max(0.0, li)
        ind_j[j] = {'Ci': ci, 'ri': ri, 'di': di, 'Fi': ci - ri, 'Li': li,
                    'Ti': ti, 'Ei': max(0.0, -li), 'delta_i': 1 if ti > 1e-9 else 0}
    return {
        'por_trabajo': ind_j,
        'Cmax'     : max(C[j] for j in TRABAJOS),
        'Tmax'     : max(ind_j[j]['Ti'] for j in TRABAJOS),
        'suma_Ti'  : sum(ind_j[j]['Ti'] for j in TRABAJOS),
        'suma_Ei'  : sum(ind_j[j]['Ei'] for j in TRABAJOS),
        'media_Fi' : sum(ind_j[j]['Fi'] for j in TRABAJOS) / len(TRABAJOS),
        'num_tardy': sum(ind_j[j]['delta_i'] for j in TRABAJOS),
    }


def evaluar(individuo: dict) -> Tuple[float, float]:
    """(ΣTj, Cmax) del individuo; se guarda para no recalcular."""
    if '_eval' not in individuo:
        C, _ = simular_hfs(individuo)
        ind = calcular_indicadores(C)
        individuo['_eval'] = (ind['suma_Ti'], ind['Cmax'])
    return individuo['_eval']


def fitness(individuo: dict) -> Tuple[float, float]:
    """Aptitud lexicográfica (menor es mejor): primero ΣTj, luego Cmax."""
    sum_ti, cmax = evaluar(individuo)
    return (round(sum_ti, 6), round(cmax, 6))

# ---------------------------------------------------------------------------
# 9. OPERADORES GENÉTICOS
# ---------------------------------------------------------------------------

def seleccion_torneo(poblacion: List[dict], tam: int) -> dict:
    """Selección por torneo."""
    return min(random.sample(poblacion, tam), key=fitness)


def _mezcla_props(a: List[float], b: List[float], lam: float) -> List[float]:
    """Cruce aritmético del nivel 1: λ·a + (1 − λ)·b, normalizado."""
    mezcla = [lam * x + (1.0 - lam) * y for x, y in zip(a, b)]
    t = sum(mezcla)
    return [x / t for x in mezcla]


def _cruce_lox(a: List[Tuple[str, int]], b: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
    """
    Cruce de orden lineal (LOX) de una secuencia: el hijo conserva un tramo
    aleatorio de 'a' en las mismas posiciones y completa el resto, de izquierda
    a derecha, con los sublotes que faltan en el orden en que aparecen en 'b'.
    """
    n = len(a)
    if n < 2:
        return a[:]
    i, j = sorted(random.sample(range(n), 2))
    tramo = a[i:j + 1]
    en_tramo = set(tramo)
    resto = [x for x in b if x not in en_tramo]
    return resto[:i] + tramo + resto[i:]


def cruce(p1: dict, p2: dict) -> Tuple[dict, dict]:
    """
    Nivel 1: cruce aritmético con un peso aleatorio λ por orden; el hijo 1
             recibe λ·p1 + (1 − λ)·p2 y el hijo 2 lo complementario, de modo
             que los dos hijos tienen tamaños distintos.
    Nivel 2: cruce de orden lineal (LOX) en cada etapa, que recombina las
             secuencias de los padres dentro de la etapa.
    """
    h1 = copy.deepcopy(p1)
    h2 = copy.deepcopy(p2)
    h1.pop('_eval', None)
    h2.pop('_eval', None)

    for j in TRABAJOS:
        lam = random.random()
        a, b = p1['proporciones'][j], p2['proporciones'][j]
        h1['proporciones'][j] = _mezcla_props(a, b, lam)
        h2['proporciones'][j] = _mezcla_props(a, b, 1.0 - lam)

    for s in ETAPAS:
        h1['posiciones'][s] = _cruce_lox(p1['posiciones'][s], p2['posiciones'][s])
        h2['posiciones'][s] = _cruce_lox(p2['posiciones'][s], p1['posiciones'][s])
    return h1, h2


def mutar(individuo: dict) -> dict:
    """
    Nivel 2: intercambio de dos sublotes en la secuencia de una etapa.
    Nivel 1: perturbación normal de la proporción de un sublote de la orden,
             seguida de normalización.
    """
    ind = copy.deepcopy(individuo)
    ind.pop('_eval', None)

    if random.random() < GA_PARAMS['prob_mut_pos']:
        s = random.choice(ETAPAS)
        orden = ind['posiciones'][s]
        if len(orden) >= 2:
            a, b = random.sample(range(len(orden)), 2)
            orden[a], orden[b] = orden[b], orden[a]

    for j in TRABAJOS:
        if random.random() < GA_PARAMS['prob_mut_prop']:
            props = ind['proporciones'][j][:]
            idx = random.randrange(ind['k'][j])
            props[idx] = max(1e-9, props[idx] + random.gauss(0, GA_PARAMS['desv_mut_prop']))
            t = sum(props)
            ind['proporciones'][j] = [p / t for p in props]
    return ind

# ---------------------------------------------------------------------------
# 10. ALGORITMO GENÉTICO
# ---------------------------------------------------------------------------

def algoritmo_genetico(verbose: bool = True,
                       individuo_semilla: Optional[dict] = None
                       ) -> Tuple[dict, List[Tuple[float, float]]]:
    """
    Ejecuta el algoritmo y retorna (mejor_individuo, historial).
    El individuo semilla (mejor regla de despacho) reemplaza al primero de la
    población inicial aleatoria.
    """
    if GA_PARAMS['semilla'] is not None:
        random.seed(GA_PARAMS['semilla'])

    poblacion = [crear_individuo() for _ in range(GA_PARAMS['poblacion'])]
    if individuo_semilla is not None:
        poblacion[0] = copy.deepcopy(individuo_semilla)
        poblacion[0].pop('_eval', None)
    for ind in poblacion:
        fitness(ind)

    mejor_global = copy.deepcopy(min(poblacion, key=fitness))
    historial = []
    ultima_mejora = 0

    if verbose:
        print(SEP)
        print("  ALGORITMO GENÉTICO — FLOW SHOP HÍBRIDO CON SUBLOTES CONSISTENTES")
        print(f"  Población: {GA_PARAMS['poblacion']} | Cruce: {GA_PARAMS['prob_cruce']} | "
              f"Mutación: {GA_PARAMS['prob_mutacion']} | Parada: "
              f"{GA_PARAMS['sin_mejora']} generaciones sin mejora "
              f"(máx. {GA_PARAMS['generaciones']})")
        print(SEP)
        print(f"  {'Gen':>5} | {'Mejor ΣTj':>11} | {'Mejor Cmax':>11} | "
              f"{'Media ΣTj':>11} | {'Media Cmax':>11}")
        print(f"  {'-'*62}")

    for gen in range(GA_PARAMS['generaciones']):
        nueva = [copy.deepcopy(min(poblacion, key=fitness))]          # elitismo

        while len(nueva) < GA_PARAMS['poblacion']:
            p1 = seleccion_torneo(poblacion, GA_PARAMS['tam_torneo'])
            p2 = seleccion_torneo(poblacion, GA_PARAMS['tam_torneo'])
            if random.random() < GA_PARAMS['prob_cruce']:
                h1, h2 = cruce(p1, p2)
            else:
                h1, h2 = copy.deepcopy(p1), copy.deepcopy(p2)
            if random.random() < GA_PARAMS['prob_mutacion']:
                h1 = mutar(h1)
            if random.random() < GA_PARAMS['prob_mutacion']:
                h2 = mutar(h2)
            nueva.extend([h1, h2])

        poblacion = nueva[:GA_PARAMS['poblacion']]
        for ind in poblacion:
            fitness(ind)

        mejor_gen = min(poblacion, key=fitness)
        if fitness(mejor_gen) < fitness(mejor_global):
            mejor_global = copy.deepcopy(mejor_gen)
            ultima_mejora = gen + 1
        historial.append(evaluar(mejor_global))

        if gen + 1 - ultima_mejora >= GA_PARAMS['sin_mejora']:
            if verbose:
                sti, cmx = evaluar(mejor_global)
                print(f"  {gen+1:>5} | {sti:>11.4f} | {cmx:>11.4f} |  parada: "
                      f"{GA_PARAMS['sin_mejora']} generaciones sin mejora")
            break

        if verbose and (gen % 50 == 0 or gen == GA_PARAMS['generaciones'] - 1):
            vals = [evaluar(i) for i in poblacion]
            sti, cmx = evaluar(mejor_global)
            print(f"  {gen+1:>5} | {sti:>11.4f} | {cmx:>11.4f} | "
                  f"{sum(v[0] for v in vals)/len(vals):>11.4f} | "
                  f"{sum(v[1] for v in vals)/len(vals):>11.4f}")

    if verbose:
        print(SEP + "\n")
    return mejor_global, historial

# ---------------------------------------------------------------------------
# 11. REGLAS DE DESPACHO (semilla del algoritmo y referencia de comparación)
# ---------------------------------------------------------------------------

def individuo_regla_ls(secuencia: List[str]) -> dict:
    """Cromosoma de una regla: sublotes iguales de cada orden, procesados en el
    orden de la regla en todas las etapas."""
    k = {j: num_sublotes(j) for j in TRABAJOS}
    return {
        'k'           : k,
        'proporciones': {j: [1.0 / k[j]] * k[j] for j in TRABAJOS},
        'posiciones'  : {s: [(j, b) for j in secuencia for b in range(1, k[j] + 1)]
                         for s in ETAPAS},
    }


def secuencias_reglas() -> Dict[str, List[str]]:
    """
    FIFO: orden de llegada | EDD: menor fecha de entrega |
    SPT / LPT: menor / mayor tiempo total de proceso |
    MST: menor holgura (d_j − p_j) | CR: menor razón crítica (d_j / p_j)
    """
    P = {j: sum(tiempo_lote_etapa(j, s) for s in ETAPAS) for j in TRABAJOS}
    return {
        "FIFO": list(TRABAJOS),
        "EDD" : sorted(TRABAJOS, key=lambda j: DUE_DATE[j]),
        "SPT" : sorted(TRABAJOS, key=lambda j: P[j]),
        "LPT" : sorted(TRABAJOS, key=lambda j: P[j], reverse=True),
        "MST" : sorted(TRABAJOS, key=lambda j: DUE_DATE[j] - P[j]),
        "CR"  : sorted(TRABAJOS, key=lambda j: DUE_DATE[j] / P[j]),
    }


def evaluar_reglas() -> List[dict]:
    """Indicadores de cada regla de despacho con los sublotes iguales."""
    resultados = []
    for nombre, seq in secuencias_reglas().items():
        C, _ = simular_hfs(individuo_regla_ls(seq))
        resultados.append({'regla': nombre, 'secuencia': seq, **calcular_indicadores(C)})
    return resultados


def mejor_de(resultados: List[dict]) -> dict:
    """Regla con menor (ΣTj, Cmax)."""
    return min(resultados, key=lambda x: (x['suma_Ti'], x['Cmax']))

# ---------------------------------------------------------------------------
# 12. REPORTES
# ---------------------------------------------------------------------------

SEP  = "=" * 76
SEP2 = "-" * 76


def _fmt_fecha(f) -> str:
    return f.strftime('%Y-%m-%d') if f is not None else '—'


def imprimir_trabajos():
    """Órdenes de trabajo leídas del Excel."""
    print(SEP)
    print("  ÓRDENES DE TRABAJO")
    print(SEP)
    print(f"  {'Orden':>6} | {'Ref.':>6} | {'Docenas':>8} | "
          f"{'rj (h)':>7} | {'dj (h)':>7} | {'Entrega':>10} | {'Sublotes':>8}")
    print(SEP2)
    for j in TRABAJOS:
        print(f"  {j:>6} | {PRODUCTO[j]:>6} | {DEMANDA[j]:>8.2f} | "
              f"{RELEASE[j]:>7.1f} | "
              f"{DUE_DATE[j]:>7.1f} | {_fmt_fecha(FECHA_ENTREGA[j]):>10} | "
              f"{num_sublotes(j):>8}")
    print()


def imprimir_reglas(resultados: List[dict]):
    """Resultados de las reglas de despacho."""
    print(SEP)
    print(f"  REGLAS DE DESPACHO ({NUM_SUBLOTES} sublotes iguales por orden)")
    print(SEP)
    print(f"  {'Regla':>6} | {'ΣTj':>10} | {'Tmax':>9} | {'Cmax':>9} | "
          f"{'Tardías':>7} | Secuencia")
    print(SEP2)
    for r in sorted(resultados, key=lambda x: (x['suma_Ti'], x['Cmax'])):
        print(f"  {r['regla']:>6} | {r['suma_Ti']:>10.2f} | {r['Tmax']:>9.2f} | "
              f"{r['Cmax']:>9.2f} | {r['num_tardy']:>7} | {', '.join(r['secuencia'])}")
    print()


def imprimir_solucion(individuo: dict):
    """Tamaños de los sublotes, indicadores y programación por etapa."""
    C, gantt = simular_hfs(individuo)
    ind = calcular_indicadores(C)

    print(SEP)
    print("  MEJOR SOLUCIÓN DEL ALGORITMO GENÉTICO")
    print(SEP)
    print("\n  Tamaños de los sublotes (iguales en todas las etapas):")
    print(f"  {'Orden':>6} | {'Sublote':>7} | {'Docenas':>8}")
    print("  " + "-" * 28)
    for j in TRABAJOS:
        for b, db in enumerate(props_a_docenas(j, individuo['proporciones'][j]), start=1):
            print(f"  {j if b == 1 else '':>6} | {b:>7} | {db:>8.2f}")

    print(f"\n  {'Orden':>6} | {'dj (h)':>7} | {'Cj (h)':>9} | {'Tj (h)':>8} | "
          f"{'Ej (h)':>8} | {'Entrega':>10} | {'Fin':>10}")
    print("  " + "-" * 76)
    for j in TRABAJOS:
        v = ind['por_trabajo'][j]
        print(f"  {j:>6} | {v['di']:>7.1f} | {v['Ci']:>9.2f} | {v['Ti']:>8.2f} | "
              f"{v['Ei']:>8.2f} | {_fmt_fecha(FECHA_ENTREGA[j]):>10} | "
              f"{_fmt_fecha(horas_a_fecha(v['Ci'])):>10}")

    print(f"\n  Tardanza total ΣTj      = {ind['suma_Ti']:>10.2f} h")
    print(f"  Órdenes tardías         = {ind['num_tardy']:>10}")
    print(f"  Tardanza máxima Tmax    = {ind['Tmax']:>10.2f} h")
    print(f"  Makespan Cmax           = {ind['Cmax']:>10.2f} h")
    print(f"  Adelanto total ΣEj      = {ind['suma_Ei']:>10.2f} h")
    print(f"  Tiempo de flujo medio   = {ind['media_Fi']:>10.2f} h")

    print("\n  PROGRAMACIÓN POR ETAPA")
    for s in ETAPAS:
        print(f"\n    Etapa {s} – {NOMBRE_ETAPA[s]}:")
        print(f"    {'Orden':>5} | {'Subl.':>5} | {'Docenas':>8} | {'Máq.':>5} | "
              f"{'Inicio (h)':>10} | {'Fin (h)':>10}")
        print("    " + "-" * 56)
        for (j, b, m, ini, fin) in sorted(gantt[s], key=lambda x: (x[3], _clave_maquina(x[2]))):
            cant = props_a_docenas(j, individuo['proporciones'][j])[b - 1]
            print(f"    {j:>5} | {b:>5} | {cant:>8.2f} | {m:>5} | {ini:>10.2f} | {fin:>10.2f}")
    al = gantt['alistamientos']
    print(f"\n  Alistamientos en troquelado: {len(al)} | "
          f"{sum(f - i for (_, _, i, f) in al):.2f} h")
    print()

# ---------------------------------------------------------------------------
# 13. DIAGRAMA DE GANTT
# ---------------------------------------------------------------------------

def graficar_gantt(individuo: dict, guardar_como: Optional[str] = None):
    """Diagrama de Gantt de la programación, con los alistamientos rayados."""
    C, gantt = simular_hfs(individuo)
    ind  = calcular_indicadores(C)
    cmax = ind['Cmax']

    colores = ['#4E79A7', '#F28E2B', '#59A14F', '#E15759', '#B07AA1',
               '#76B7B2', '#EDC948', '#FF9DA7', '#9C755F', '#BAB0AC']
    color_trabajo = {j: colores[i % len(colores)] for i, j in enumerate(TRABAJOS)}

    maquinas_usadas = {s: sorted({m for (_, _, m, _, _) in gantt[s]}, key=_clave_maquina)
                       for s in ETAPAS}
    alturas = [max(1, len(maquinas_usadas[s])) for s in ETAPAS]

    fig, axes = plt.subplots(len(ETAPAS), 1,
                             figsize=(20, max(8, sum(alturas) * 0.40 + 3)),
                             gridspec_kw={'height_ratios': alturas}, sharex=True)
    if len(ETAPAS) == 1:
        axes = [axes]
    fig.suptitle("Diagrama de Gantt — Flow Shop híbrido con sublotes consistentes (AG)",
                 fontsize=14, fontweight='bold', y=1.0)
    umbral_texto = (cmax if cmax > 0 else 1) * 0.025

    for idx, s in enumerate(ETAPAS):
        ax = axes[idx]
        pos_maq = {m: i for i, m in enumerate(maquinas_usadas[s])}

        for (j, b, m, ini, fin) in gantt[s]:
            dur = fin - ini
            ax.barh(pos_maq[m], dur, left=ini, height=0.72, color=color_trabajo[j],
                    edgecolor='white', linewidth=0.6, alpha=0.92)
            if dur >= umbral_texto:
                ax.text(ini + dur / 2, pos_maq[m], f"{j}-S{b}", ha='center', va='center',
                        fontsize=6.5, fontweight='bold', color='white', clip_on=True)

        for (s_al, m_al, a_ini, a_fin) in gantt['alistamientos']:
            if s_al == s and m_al in pos_maq:
                ax.barh(pos_maq[m_al], a_fin - a_ini, left=a_ini, height=0.72,
                        color='white', edgecolor='#555555', hatch='////', linewidth=0.4)

        ax.axvline(cmax, color='#333333', linewidth=1.2, linestyle='--', alpha=0.7)
        ax.set_yticks(range(len(pos_maq)))
        ax.set_yticklabels(maquinas_usadas[s], fontsize=8)
        ax.set_ylim(-0.6, max(len(pos_maq), 1) - 0.4)
        ax.set_ylabel(f"Etapa {s} — {NOMBRE_ETAPA[s]}", fontsize=9,
                      fontweight='bold', labelpad=8)
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(4))
        ax.grid(axis='x', which='major', linestyle='--', linewidth=0.5, alpha=0.5, color='#bbbbbb')
        ax.grid(axis='x', which='minor', linestyle=':', linewidth=0.3, alpha=0.35, color='#cccccc')
        ax.set_facecolor('#F8F9FA')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        if idx == len(ETAPAS) - 1:
            ax.annotate(f"Cmax = {cmax:.2f} h", xy=(cmax, -0.55),
                        xytext=(cmax * 0.99, -0.55), fontsize=8, color='#333333', ha='right')

    axes[-1].set_xlabel("Tiempo (horas laborables)", fontsize=10)
    axes[-1].xaxis.set_major_locator(ticker.MaxNLocator(integer=False, nbins=15))

    leyenda = [mpatches.Patch(color=color_trabajo[j], label=f"{j} ({PRODUCTO[j]})")
               for j in TRABAJOS]
    leyenda.append(mpatches.Patch(facecolor='white', edgecolor='#555555',
                                  hatch='////', label='Alistamiento'))
    fig.legend(handles=leyenda, loc='lower center', ncol=min(len(leyenda), 11),
               fontsize=9, frameon=True, framealpha=0.9, edgecolor='#cccccc',
               bbox_to_anchor=(0.5, 0.0))
    fig.text(0.5, 1.002,
             f"Sublotes por orden = {NUM_SUBLOTES}  |  ΣTj = {ind['suma_Ti']:.2f} h  |  "
             f"Cmax = {cmax:.2f} h  |  Órdenes tardías = {ind['num_tardy']}",
             ha='center', va='bottom', fontsize=8.5, color='#444444',
             transform=fig.transFigure)
    plt.tight_layout(rect=[0, 0.025, 1, 0.99])

    if guardar_como:                  # se guarda antes de mostrarla
        fig.savefig(guardar_como, dpi=150, bbox_inches='tight')
        print(f"  Gantt guardado en: {guardar_como}")
    plt.show()
    return fig

# ---------------------------------------------------------------------------
# 14. PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------

def main(ruta_excel: str = RUTA_EXCEL, guardar_gantt: Optional[str] = None):
    print()
    print(SEP)
    print("  FLOW SHOP HÍBRIDO CON SUBLOTES CONSISTENTES — ALGORITMO GENÉTICO")
    print("  Objetivo: minimizar la tardanza total")
    print(SEP)
    print()

    cargar_datos(ruta_excel)
    imprimir_trabajos()

    # Reglas de despacho: la mejor siembra la población inicial
    reglas = evaluar_reglas()
    imprimir_reglas(reglas)
    regla_sel = mejor_de(reglas)
    print(f"  Regla que siembra la población: {regla_sel['regla']} "
          f"(ΣTj = {regla_sel['suma_Ti']:.2f} h)\n")

    mejor, historial = algoritmo_genetico(
        verbose=True, individuo_semilla=individuo_regla_ls(regla_sel['secuencia']))

    imprimir_solucion(mejor)
    graficar_gantt(mejor, guardar_como=guardar_gantt)

    C, _ = simular_hfs(mejor)
    ind = calcular_indicadores(C)
    print(SEP)
    print("  RESUMEN")
    print(SEP)
    print(f"  Mejor regla ({regla_sel['regla']}): ΣTj = {regla_sel['suma_Ti']:.2f} h | "
          f"Cmax = {regla_sel['Cmax']:.2f} h | tardías = {regla_sel['num_tardy']}")
    print(f"  Algoritmo genético : ΣTj = {ind['suma_Ti']:.2f} h | "
          f"Cmax = {ind['Cmax']:.2f} h | tardías = {ind['num_tardy']}")
    print(SEP)
    print()
    return mejor, historial


if __name__ == "__main__":
    args_excel = [a for a in sys.argv[1:] if a.lower().endswith(('.xlsx', '.xlsm', '.xls'))]
    main(args_excel[0] if args_excel else RUTA_EXCEL)
