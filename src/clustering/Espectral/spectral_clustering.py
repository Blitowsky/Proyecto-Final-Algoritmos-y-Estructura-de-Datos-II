# src/core/wave_manager/spectral_clustering.py

import math
import numpy as np


# =====================================================================
# 1. ESTRUCTURA AUXILIAR PROPIA: COLA FIFO PARA BFS EN O(1)
# =====================================================================
class _NodoCola:
    """Nodo para la lista enlazada de la Cola FIFO."""
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None


class _ColaFIFO:
    """
    Cola FIFO implementada desde cero con punteros de cabecera y cola.
    Garantiza operaciones encolar() y desencolar() en tiempo O(1) real
    sin requerir la librería externa 'collections'.
    """
    def __init__(self):
        self.frente = None
        self.final = None
        self.tamaño = 0

    def esta_vacia(self) -> bool:
        return self.frente is None

    def encolar(self, valor) -> None:
        nuevo = _NodoCola(valor)
        if self.final is not None:
            self.final.siguiente = nuevo
        self.final = nuevo
        if self.frente is None:
            self.frente = nuevo
        self.tamaño += 1

    def desencolar(self):
        if self.frente is None:
            return None
        valor = self.frente.valor
        self.frente = self.frente.siguiente
        if self.frente is None:
            self.final = None
        self.tamaño -= 1
        return valor


# =====================================================================
# 2. DISTANCIA REAL EN EL GRAFO DE PASILLOS (BFS SOBRE EL WAREHOUSE)
# =====================================================================
def _obtener_vecinos_en_grafo(grafo, coord: tuple[int, int]) -> list[tuple[int, int]]:
    """
    Adaptador universal para leer vecinos desde distintos formatos de grafo
    sin acoplar el módulo a una única clase previa.
    Soporta:
      - Diccionario de adyacencia con claves (x, y) o "N_x_y".
      - Estructura propia TablaHashCuadratica (método .buscar()).
    """
    x, y = coord
    clave_str = f"N_{x}_{y}"
    datos = None

    # Caso 1: TablaHashCuadratica u objeto con método buscar()
    if hasattr(grafo, "buscar"):
        datos = grafo.buscar(coord)
        if datos is None:
            datos = grafo.buscar(clave_str)
    # Caso 2: Diccionario nativo de Python
    elif isinstance(grafo, dict):
        datos = grafo.get(coord)
        if datos is None:
            datos = grafo.get(clave_str)

    if datos is None:
        return []

    # Si el valor guardado es un diccionario con metadatos: {"pos": (x,y), "adyacentes": [...]}
    vecinos_crudos = datos["adyacentes"] if isinstance(datos, dict) and "adyacentes" in datos else datos

    vecinos_coord = []
    for v in vecinos_crudos:
        if isinstance(v, tuple) and len(v) >= 2:
            vecinos_coord.append((int(v[0]), int(v[1])))
        elif isinstance(v, str) and v.startswith("N_"):
            partes = v.split("_")
            vecinos_coord.append((int(partes[1]), int(partes[2])))

    return vecinos_coord


def _bfs_distancias_desde_origen(
    grafo, 
    origen: tuple[int, int], 
    destinos_objetivo: set[tuple[int, int]]
) -> dict[tuple[int, int], int]:
    """
    Calcula la cantidad exacta de pasos de pasillo desde 'origen' hasta
    las coordenadas en 'destinos_objetivo' respetando paredes y sentidos.
    """
    cola = _ColaFIFO()
    cola.encolar(origen)
    visitados = {origen: 0}
    encontrados = {}

    if origen in destinos_objetivo:
        encontrados[origen] = 0

    while not cola.esta_vacia() and len(encontrados) < len(destinos_objetivo):
        actual = cola.desencolar()
        dist_actual = visitados[actual]

        for vecino in _obtener_vecinos_en_grafo(grafo, actual):
            if vecino not in visitados:
                visitados[vecino] = dist_actual + 1
                if vecino in destinos_objetivo:
                    encontrados[vecino] = dist_actual + 1
                cola.encolar(vecino)

    return encontrados


def construir_matriz_distancias_pasillos(
    coordenadas: list[tuple[int, int]], 
    grafo_pasillos=None,
    funcion_distancia_custom=None
) -> np.ndarray:
    """
    Construye la matriz de distancias reales D_dist (P x P) entre los P puntos.
    Como los pasillos del Warehouse tienen sentido de circulación (N, S, E, O),
    la distancia de A -> B puede ser distinta a la de B -> A.
    Para el Clustering Espectral (que exige una matriz simétrica), se toma la
    distancia simétrica efectiva: min(d(i, j), d(j, i)) o su promedio.
    """
    p = len(coordenadas)
    matriz_dist = np.full((p, p), np.inf, dtype=float)
    np.fill_diagonal(matriz_dist, 0.0)

    # Opción A: Usar función de distancia inyectada externamente
    if funcion_distancia_custom is not None:
        for i in range(p):
            for j in range(i + 1, p):
                d_ij = funcion_distancia_custom(coordenadas[i], coordenadas[j])
                d_ji = funcion_distancia_custom(coordenadas[j], coordenadas[i])
                dist_simetrica = 0.5 * (d_ij + d_ji)
                matriz_dist[i, j] = dist_simetrica
                matriz_dist[j, i] = dist_simetrica
        return matriz_dist

    # Opción B: Calcular distancia real sobre el grafo de pasillos mediante BFS
    if grafo_pasillos is not None:
        conjunto_coords = set(coordenadas)
        mapa_bfs = {}
        for coord in conjunto_coords:
            mapa_bfs[coord] = _bfs_distancias_desde_origen(grafo_pasillos, coord, conjunto_coords)

        for i in range(p):
            u = coordenadas[i]
            for j in range(i + 1, p):
                v = coordenadas[j]
                d_uv = mapa_bfs[u].get(v, math.inf)
                d_vu = mapa_bfs[v].get(u, math.inf)

                # Simetrización topológica para grafos dirigidos de pasillos
                if d_uv < math.inf and d_vu < math.inf:
                    dist_real = 0.5 * (d_uv + d_vu)
                else:
                    dist_real = min(d_uv, d_vu)

                matriz_dist[i, j] = dist_real
                matriz_dist[j, i] = dist_real
        return matriz_dist

    raise ValueError(
        "Se debe proporcionar 'grafo_pasillos' o 'funcion_distancia_custom' "
        "para calcular la distancia real en los pasillos."
    )


# =====================================================================
# 3. ÁLGEBRA ESPECTRAL Y K-MEANS DETERMINISTA PROPIO
# =====================================================================
def _construir_matriz_afinidad(matriz_distancias: np.ndarray) -> np.ndarray:
    """
    Convierte la matriz de distancias de pasillos en una Matriz de Afinidad (W)
    mediante un Kernel Gaussiano (RBF): W_ij = exp(-d(i,j)^2 / (2 * sigma^2)).
    Sigma se ajusta automáticamente a la mediana de las distancias finitas.
    """
    distancias_finitas = matriz_distancias[
        (matriz_distancias > 0) & np.isfinite(matriz_distancias)
    ]

    if distancias_finitas.size == 0:
        sigma = 1.0
    else:
        sigma = float(np.median(distancias_finitas))
        if sigma <= 0:
            sigma = 1.0

    # Donde la distancia es infinita (sin conexión), exp(-inf) = 0.0 automáticamente
    afinidad = np.exp(-(matriz_distancias ** 2) / (2.0 * (sigma ** 2)))
    np.fill_diagonal(afinidad, 0.0)
    return afinidad


def _kmeans_determinista(matriz_puntos: np.ndarray, k: int, max_iter: int = 100) -> list[int]:
    """
    Implementación propia y 100% determinista de K-Means en el espacio espectral.
    Utiliza inicialización por punto más lejano (Maximin / Farthest-First)
    para evitar el uso de semillas aleatorias o metaheurísticas.
    """
    n_puntos = matriz_puntos.shape[0]

    # 1. Inicialización determinista de centroides:
    # Elegimos como primer centroide el punto con mayor norma (o el índice 0)
    centroides = [matriz_puntos[0].copy()]

    for _ in range(1, k):
        dist_min_a_centroides = np.array([
            min(np.linalg.norm(punto - c) ** 2 for c in centroides)
            for punto in matriz_puntos
        ])
        idx_mas_lejano = int(np.argmax(dist_min_a_centroides))
        centroides.append(matriz_puntos[idx_mas_lejano].copy())

    centroides = np.array(centroides)
    etiquetas = [0] * n_puntos

    # 2. Refinamiento iterativo de Lloyd
    for _ in range(max_iter):
        nuevas_etiquetas = []
        for i in range(n_puntos):
            distancias = [np.linalg.norm(matriz_puntos[i] - c) ** 2 for c in centroides]
            nuevas_etiquetas.append(int(np.argmin(distancias)))

        if nuevas_etiquetas == etiquetas:
            break
        etiquetas = nuevas_etiquetas

        # Recalcular centroides
        for cluster_id in range(k):
            indices = [i for i, etiq in enumerate(etiquetas) if etiq == cluster_id]
            if indices:
                centroides[cluster_id] = np.mean(matriz_puntos[indices], axis=0)

    return etiquetas


# =====================================================================
# 4. FUNCIÓN PÚBLICA PRINCIPAL DEL MÓDULO
# =====================================================================
def agrupar_por_clustering_espectral(
    coordenadas: list[tuple[int, int]],
    cantidad_zonas: int,
    grafo_pasillos=None,
    funcion_distancia_custom=None
) -> list[list[tuple[int, int]]]:
    """
    Agrupa una lista de coordenadas (x, y) en 'cantidad_zonas' clústeres
    utilizando Clustering Espectral Normalizado (Ng, Jordan & Weiss) basado
    en la distancia real de los pasillos del Warehouse.

    Parámetros:
        coordenadas: Lista de tuplas [(x1, y1), (x2, y2), ...] a agrupar.
        cantidad_zonas: Número entero K de zonas deseadas.
        grafo_pasillos: Grafo del Warehouse (TablaHashCuadratica o dict de adyacencia).
        funcion_distancia_custom: Función opcional f(coord1, coord2) -> distancia_pasillos.

    Retorna:
        Lista de listas con las coordenadas de cada zona:
        [ [(x, y), (x, y)], [(x, y), ...], ... ]
    """
    if not coordenadas:
        return []

    n_puntos = len(coordenadas)
    if cantidad_zonas <= 1:
        return [list(coordenadas)]

    if cantidad_zonas >= n_puntos:
        return [[coord] for coord in coordenadas]

    # Paso 1: Matriz de distancias reales en el grafo de pasillos (P x P)
    matriz_dist = construir_matriz_distancias_pasillos(
        coordenadas, grafo_pasillos, funcion_distancia_custom
    )

    # Paso 2: Matriz de Afinidad / Similitud W (P x P)
    W = _construir_matriz_afinidad(matriz_dist)

    # Paso 3: Matriz Diagonal de Grados D y Laplaciano Simétrico Normalizado (L_sym)
    # L_sym = I - D^(-1/2) @ W @ D^(-1/2)
    grados = np.sum(W, axis=1)
    grados_inv_sqrt = np.where(grados > 1e-12, 1.0 / np.sqrt(grados), 0.0)
    D_inv_sqrt = np.diag(grados_inv_sqrt)

    I = np.eye(n_puntos)
    L_sym = I - (D_inv_sqrt @ W @ D_inv_sqrt)

    # Paso 4: Descomposición en Autovalores y Autovectores
    # np.linalg.eigh explota la simetría de L_sym y devuelve los autovalores ordenados ascendentemente
    autovalores, autovectores = np.linalg.eigh(L_sym)

    # Tomamos los primeros K autovectores (los asociados a los K autovalores más pequeños)
    U = autovectores[:, :cantidad_zonas]

    # Normalizamos las filas de U para proyectarlas sobre la esfera unitaria
    normas_filas = np.linalg.norm(U, axis=1, keepdims=True)
    normas_filas = np.where(normas_filas > 1e-12, normas_filas, 1.0)
    T = U / normas_filas

    # Paso 5: Agrupamiento en el espacio espectral con nuestro K-Means determinista
    etiquetas = _kmeans_determinista(T, cantidad_zonas)

    # Paso 6: Empaquetar el resultado como lista de listas de coordenadas
    zonas_dict = {z: [] for z in range(cantidad_zonas)}
    for coord, zona_id in zip(coordenadas, etiquetas):
        zonas_dict[zona_id].append(coord)

    # Filtramos zonas vacías (si las hubiera) y devolvemos la lista de listas
    zonas_resultado = [lista_pts for lista_pts in zonas_dict.values() if lista_pts]
    return zonas_resultado