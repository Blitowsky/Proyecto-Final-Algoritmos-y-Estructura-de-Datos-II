import numpy as np
# Reemplaza esta ruta por la ruta real donde guardaste tu clase
from hash_table import TablaHashCuadratica 

def _crear_tabla_estandar(diccionario_adyacencia):
    """
    Función auxiliar privada.
    Toma un diccionario de adyacencia de Python y lo convierte a la
    estructura de datos oficial del equipo (TablaHashCuadratica).
    """
    # Para la tabla hash con quadratic probing, iniciamos con una capacidad 
    # de al menos el doble de los vértices para evitar un rehashing inmediato.
    capacidad_inicial = max(11, len(diccionario_adyacencia) * 2)
    tabla = TablaHashCuadratica(capacidad_inicial)
    
    for nodo, vecinos in diccionario_adyacencia.items():
        # Eliminamos duplicados por si el formato crudo venía sucio
        vecinos_unicos = list(set(vecinos))
        tabla.insertar(nodo, vecinos_unicos)
        
    return tabla


def parse_ev_set(data):
    """
    Convierte un Conjunto Arista-Vértice a la Tabla Hash estándar.
    Asume que el grafo es no dirigido (los pasillos son bidireccionales).
    """
    adj = {v: [] for v in data["V"]}
    
    for u, v in data["E"]:
        if u in adj and v in adj:
            adj[u].append(v)
            adj[v].append(u) # Remover esta línea si el grafo fuera dirigido
            
    return _crear_tabla_estandar(adj)


def parse_adj_list(data):
    """
    Convierte una Lista de Adyacencia (dict nativo) a la Tabla Hash estándar.
    """
    # Como los datos ya vienen en el formato lógico correcto, 
    # solo los inyectamos en la estructura personalizada.
    return _crear_tabla_estandar(data)


def parse_inc_list(data):
    """
    Convierte una Lista de Incidencia a la Tabla Hash estándar.
    Relaciona vértices que comparten el mismo ID de arista (e0, e1, etc.).
    """
    adj = {v: [] for v in data.keys()}
    
    # 1. Agrupar los nodos por cada arista
    edge_to_nodes = {}
    for nodo, aristas in data.items():
        for e in aristas:
            if e not in edge_to_nodes:
                edge_to_nodes[e] = []
            edge_to_nodes[e].append(nodo)
            
    # 2. Conectar los nodos que comparten la misma arista
    for e, nodos_conectados in edge_to_nodes.items():
        if len(nodos_conectados) == 2:
            u, v = nodos_conectados
            adj[u].append(v)
            adj[v].append(u)
            
    return _crear_tabla_estandar(adj)


def parse_adj_matrix(data):
    """
    Convierte una Matriz de Adyacencia (NumPy) a la Tabla Hash estándar.
    data[0] = lista ordenada de nodos
    data[1] = matriz numpy n x n
    """
    nodes = data[0]
    matrix = data[1]
    adj = {v: [] for v in nodes}
    
    n = len(nodes)
    for i in range(n):
        for j in range(n):
            if matrix[i][j] != 0: # 1 o peso mayor a 0 significa conexión
                adj[nodes[i]].append(nodes[j])
                
    return _crear_tabla_estandar(adj)


def parse_inc_matrix(data):
    """
    Convierte una Matriz de Incidencia (NumPy) a la Tabla Hash estándar.
    data[0] = lista ordenada de nodos
    data[1] = matriz numpy n x m (filas: nodos, columnas: aristas)
    """
    nodes = data[0]
    matrix = data[1]
    adj = {v: [] for v in nodes}
    
    num_edges = matrix.shape[1]
    
    for j in range(num_edges):
        nodos_conectados = []
        # Buscamos qué nodos tienen un 1 en la columna (arista) j
        for i in range(len(nodes)):
            if matrix[i][j] != 0:
                nodos_conectados.append(nodes[i])
                
        # Una arista válida conecta exactamente dos vértices
        if len(nodos_conectados) == 2:
            u, v = nodos_conectados
            adj[u].append(v)
            adj[v].append(u)
            
    return _crear_tabla_estandar(adj)