import numpy as np


def _extraer_diccionario(standard_graph):
    """
    Función auxiliar privada.
    Extrae los datos de la TablaHashCuadratica (o de un dict de prueba)
    y devuelve un diccionario ordenado determinísticamente.
    """
    if isinstance(standard_graph, dict):
        return {k: sorted(v) for k, v in sorted(standard_graph.items())}

    adj = {}
    for celda in standard_graph.tabla:
        estado, clave, vecinos = celda
        if estado == standard_graph.OCUPADO:
            adj[clave] = sorted(vecinos)

    # Retornamos el diccionario ordenado por clave para mantener consistencia en matrices
    return dict(sorted(adj.items()))


def _obtener_aristas_unicas(adj_dict):
    """
    Función auxiliar privada.
    Recorre la lista de adyacencia y extrae las aristas sin duplicar 
    conexiones bidireccionales, es decir, evita agregar (v, u) si ya existe (u, v).
    """
    aristas = []
    vistas = set()

    for u, vecinos in adj_dict.items():
        for v in vecinos:
            par = frozenset([u, v])
            if par not in vistas:
                vistas.add(par)
                aristas.append((u, v))

    return aristas


def export_ev_set(standard_graph):
    """
    1. Exporta a Conjunto Arista-Vértice (Edge-Vertex Set).
    Retorna: {"V": [...], "E": [(u, v), ...]}
    """
    adj = _extraer_diccionario(standard_graph)
    vertices = list(adj.keys())
    aristas = _obtener_aristas_unicas(adj)

    return {
        "V": vertices,
        "E": aristas
    }


def export_adj_list(standard_graph):
    """
    2. Exporta a Lista de Adyacencia (diccionario nativo de Python).
    Retorna: {"N1": ["N2", ...], ...}
    """
    return _extraer_diccionario(standard_graph)


def export_inc_list(standard_graph):
    """
    3. Exporta a Lista de Incidencia.
    Mapea cada vértice con una lista de los índices de las aristas que inciden en él.
    Retorna: {"DESPACHO": [0], "N1": [0, 1], ...}
    """
    adj = _extraer_diccionario(standard_graph)
    aristas = _obtener_aristas_unicas(adj)

    inc_list = {u: [] for u in adj.keys()}

    for idx_arista, (u, v) in enumerate(aristas):
        inc_list[u].append(idx_arista)
        inc_list[v].append(idx_arista)

    return inc_list


def export_adj_matrix(standard_graph):
    """
    4. Exporta a Matriz de Adyacencia utilizando NumPy.
    Retorna una tupla: (lista_nodos, matriz_numpy_nxn)
    """
    adj = _extraer_diccionario(standard_graph)
    nodos = list(adj.keys())
    n = len(nodos)

    # Mapa rápido para saber en qué índice de fila/columna va cada nodo
    nodo_a_idx = {nodo: i for i, nodo in enumerate(nodos)}

    matriz = np.zeros((n, n), dtype=int)

    for u, vecinos in adj.items():
        i = nodo_a_idx[u]
        for v in vecinos:
            j = nodo_a_idx[v]
            matriz[i, j] = 1

    return nodos, matriz


def export_inc_matrix(standard_graph):
    """
    5. Exporta a Matriz de Incidencia utilizando NumPy.
    Filas: Nodos | Columnas: Aristas.
    Retorna una tupla: (lista_nodos, matriz_numpy_nxm)
    """
    adj = _extraer_diccionario(standard_graph)
    nodos = list(adj.keys())
    aristas = _obtener_aristas_unicas(adj)

    n = len(nodos)
    m = len(aristas)

    nodo_a_idx = {nodo: i for i, nodo in enumerate(nodos)}
    matriz = np.zeros((n, m), dtype=int)

    for j, (u, v) in enumerate(aristas):
        fila_u = nodo_a_idx[u]
        fila_v = nodo_a_idx[v]
        matriz[fila_u, j] = 1
        matriz[fila_v, j] = 1

    return nodos, matriz