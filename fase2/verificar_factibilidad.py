"""
Verifica que las programaciones del decodificador cumplan las restricciones
del MILP y evalúa escenarios de referencia (FIFO/EDD con lote completo y con
sublotes iguales).

Uso:  python verificar_factibilidad.py ruta/modelo.py ruta/BD_HFS.xlsx
"""
import sys, time, random, importlib.util, os

os.environ.setdefault('MPLBACKEND', 'Agg')


def _cargar_modelo(ruta):
    spec = importlib.util.spec_from_file_location('modelo', ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M = _cargar_modelo(sys.argv[1] if len(sys.argv) > 1 else 'final_sc_hfsagls_S2_4.py')

EPS = 1e-6


def verificar(ind):
    C, g = M.simular_hfs(ind)
    doc = {j: M.props_a_docenas(j, ind['proporciones'][j]) for j in M.TRABAJOS}
    errores = []
    # (1)-(2) suma de sublotes y tamaño mínimo
    for j in M.TRABAJOS:
        if abs(sum(doc[j]) - M.DEMANDA[j]) > EPS:
            errores.append(f"suma sublotes {j}")
        if any(x < M.MIN_DOCENAS_POR_SUBLOTE - EPS for x in doc[j]):
            errores.append(f"sublote < mínimo en {j}")
    ops = {}
    for s in M.ETAPAS:
        vistos = set()
        for (j, b, m, ini, fin) in g[s]:
            # (3) una sola máquina por etapa y elegible
            if (j, b) in vistos:
                errores.append(f"{j}-{b} dos veces en etapa {s}")
            vistos.add((j, b))
            if m not in M.elegibles(j, s):
                errores.append(f"máquina no elegible {m}")
            # (4) tiempo de proceso
            p = M.tiempo_horas(j, m, doc[j][b - 1])
            if abs((fin - ini) - p) > EPS:
                errores.append(f"duración {j}-{b} etapa {s}")
            ops[(j, b, s)] = (m, ini, fin)
    # (5)-(6) liberación y precedencia entre etapas
    for (j, b, s), (m, ini, fin) in ops.items():
        if s == M.ETAPAS[0] and ini < M.RELEASE[j] - EPS:
            errores.append(f"{j}-{b} inicia antes de r_j")
        if s > M.ETAPAS[0]:
            prev = ops.get((j, b, s - 1))
            if prev and ini < prev[2] - EPS:
                errores.append(f"{j}-{b} etapa {s} antes de terminar etapa {s-1}")
    # (8)-(11) no solapamiento y alistamientos
    setup = M.ALISTAMIENTO_MIN_POR_ETAPA.get(M.NOMBRE_ETAPA[1], 0) / 60
    por_maq = {}
    for (j, b, s), (m, ini, fin) in ops.items():
        por_maq.setdefault(m, []).append((ini, fin, j, s))
    for m, lst in por_maq.items():
        lst.sort()
        for k, (ini, fin, j, s) in enumerate(lst):
            if s == 1:
                req = setup if k == 0 or M.PRODUCTO[lst[k-1][2]] != M.PRODUCTO[j] else 0
                libre = lst[k-1][1] if k else 0.0
                if ini < libre + req - EPS:
                    errores.append(f"solape/alistamiento en {m} t={ini:.2f}")
            elif k and ini < lst[k-1][1] - EPS:
                errores.append(f"solape en {m} t={ini:.2f}")
    return errores, M.calcular_indicadores(C)


def ind_lote_completo(secuencia):
    """FIFO sin lot streaming: cada orden es un único lote (B_j = 1)."""
    return {'k': {j: 1 for j in M.TRABAJOS},
            'proporciones': {j: [1.0] for j in M.TRABAJOS},
            'posiciones': {s: [(j, 1) for j in secuencia] for s in M.ETAPAS}}


if __name__ == '__main__':
    M.cargar_datos(sys.argv[2] if len(sys.argv) > 2 else 'BD_HFS.xlsx')
    seqs = M.secuencias_reglas()
    print("Escenario                         ΣTj     Tmax    Cmax  tardías  errores")
    for nombre in ['FIFO', 'EDD']:
        for etiqueta, ind in [(f'{nombre} lote completo (B=1)', ind_lote_completo(seqs[nombre])),
                              (f'{nombre} 10 sublotes iguales', M.individuo_regla_ls(seqs[nombre]))]:
            err, r = verificar(ind)
            print(f"{etiqueta:30s} {r['suma_Ti']:8.2f} {r['Tmax']:8.2f} {r['Cmax']:8.2f} "
                  f"{r['num_tardy']:6d}   {len(err)}")
    # Verificación de individuos aleatorios (prueba de robustez del decodificador)
    random.seed(1)
    malos = sum(1 for _ in range(200) if verificar(M.crear_individuo())[0])
    print(f"Individuos aleatorios con violaciones: {malos}/200")
    # Tiempo por evaluación
    ind = M.crear_individuo(); t = time.time()
    for _ in range(50):
        ind.pop('_eval', None); M.evaluar(ind)
    print(f"Tiempo medio por evaluación: {(time.time()-t)/50*1000:.1f} ms")
