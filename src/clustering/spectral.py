# src/clustering/spectral.py

import math
import numpy as np
import pandas as pd

from warehouse.domain.warehouse import WareHouse
from warehouse.domain.product import Product
from warehouse.structures.linkedlist import LinkedList, add, length
from warehouse.structures.dictionary import Dictionary, search, insert
from warehouse.algorithms.pathfinding import bfs_distances_targeted



# =====================================================================
# FASE 0: EXTRACCIÓN DE PRODUCTOS Y NODOS DESDE EL WAREHOUSE
# =====================================================================
def extract_pending_products(warehouse: WareHouse) -> list[Product]:
    """
    Recorre la LinkedList de pedidos (warehouse.orders) y sus líneas (order.lines)
    para extraer una lista sin duplicados de todos los productos demandados
    por pedidos en estado 'PENDIENTE'.
    """
    unique_products: list[Product] = []
    # Usamos el Dictionary propio del proyecto para evitar productos duplicados en O(1)
    seen = Dictionary(warehouse.width * warehouse.height)

    order_node = warehouse.orders.head
    while order_node is not None:
        order = order_node.value
        if order is not None and order.state == "PENDIENTE":
            line_node = order.lines.head
            while line_node is not None:
                line = line_node.value
                if line is not None and line.product is not None:
                    prod = line.product
                    if search(seen, prod.id) is None:
                        insert(seen, True, prod.id)
                        unique_products.append(prod)
                line_node = line_node.nextNode
        order_node = order_node.nextNode

    return unique_products


def get_product_access_node(product: Product) -> int:
    """
    Obtiene el ID del vértice del pasillo (en warehouse.graph) desde el cual
    el picker accede físicamente al producto.
    """
    if product.pick_cells is None or product.pick_cells.head is None:
        raise ValueError(f"El producto {product.id} no tiene celdas de acceso (pick_cells).")
    return product.pick_cells.head.value


# =====================================================================
# PASO 1: MATRIZ DE DISTANCIAS Y MATRIZ DE SIMILITUD (W)
# =====================================================================
def build_distance_matrix(
    products: list[Product],
    metric: str = "t",
    warehouse: WareHouse | None = None
) -> np.ndarray:
    """
    Construye la matriz simétrica de distancias (NxN) entre los productos.
    Soporta métrica 'e' (línea recta) o 't' (pasos reales de pasillo).
    """
    n = len(products)
    dist_matrix = np.full((n, n), np.inf, dtype=float)
    np.fill_diagonal(dist_matrix, 0.0)

    if metric == "e":
        for i in range(n):
            for j in range(i + 1, n):
                dx = products[i].x - products[j].x
                dy = products[i].y - products[j].y
                d = math.sqrt(dx * dx + dy * dy)
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d

    elif metric == "t":
        if warehouse is None:
            raise ValueError("Se requiere la instancia 'warehouse' para la distancia topológica.")

        # 1. Obtenemos el nodo de pasillo de acceso para cada producto
        access_nodes = [get_product_access_node(p) for p in products]


        # 2. Calculamos las distancias entre nodos a partir de BFS
        targets = LinkedList()
        unique_nodes = set()
        for node_id in access_nodes:
            if node_id not in unique_nodes:
                unique_nodes.add(node_id)
                add(targets, node_id)

        distance_maps = {}
        for node_id in unique_nodes:
            distance_maps[node_id] = bfs_distances_targeted(warehouse.graph, node_id, targets)
        # 3. Llenamos la matriz simetrizando los caminos de ida y vuelta

        for i in range(n):
            u = access_nodes[i]
            for j in range(i + 1, n):
                v = access_nodes[j]
                if u == v:
                    dist_efectiva = 0.0
                else:
                    d_uv = search(distance_maps[u], v)
                    d_vu = search(distance_maps[v], u)

                    d_uv = float(d_uv) if d_uv is not None else math.inf
                    d_vu = float(d_vu) if d_vu is not None else math.inf

                    # En pasillos con sentido único, tomamos la ruta más corta válida
                    dist_efectiva = min(d_uv, d_vu)

                dist_matrix[i, j] = dist_efectiva
                dist_matrix[j, i] = dist_efectiva
    else:
        raise ValueError("Métrica inválida. Use 'e' o 't'.")

    return dist_matrix


def build_similarity_matrix(distance_matrix: np.ndarray) -> np.ndarray:
    """Convierte la matriz de distancias en Matriz de Afinidad W usando Kernel Gaussiano (RBF)."""
    finite_dists = distance_matrix[(distance_matrix > 0) & np.isfinite(distance_matrix)]
    sigma = float(np.median(finite_dists)) if finite_dists.size > 0 else 1.0
    if sigma <= 0:
        sigma = 1.0

    similarity_matrix = np.exp(-(distance_matrix ** 2) / (2.0 * (sigma ** 2)))
    np.fill_diagonal(similarity_matrix, 0.0)
    return similarity_matrix


# =====================================================================
# PASO 2, 3 Y 4: LAPLACIANO, AUTOVECTORES Y EMBEDDING ESPECTRAL
# =====================================================================
def compute_laplacian_matrix(similarity_matrix: np.ndarray, normalized: bool = True) -> np.ndarray:
    n_points = similarity_matrix.shape[0]
    degrees = np.sum(similarity_matrix, axis=1)

    if not normalized:
        return np.diag(degrees) - similarity_matrix

    degrees_inv_sqrt = np.where(degrees > 1e-12, 1.0 / np.sqrt(degrees), 0.0)
    D_inv_sqrt = np.diag(degrees_inv_sqrt)
    I = np.eye(n_points)
    return I - (D_inv_sqrt @ similarity_matrix @ D_inv_sqrt)


def compute_eigenvectors(laplacian_matrix: np.ndarray, num_clusters: int) -> np.ndarray:
    _, eigenvectors = np.linalg.eigh(laplacian_matrix)
    return eigenvectors[:, :num_clusters]


def create_spectral_embedding(eigenvectors: np.ndarray) -> np.ndarray:
    row_norms = np.linalg.norm(eigenvectors, axis=1, keepdims=True)
    row_norms = np.where(row_norms > 1e-12, row_norms, 1.0)
    return eigenvectors / row_norms


# =====================================================================
# PASO 5: K-MEANS DETERMINISTA (MAXIMIN)
# =====================================================================
def initialize_centroids_maximin(k: int, data_np: np.ndarray) -> pd.DataFrame:
    centroides = [data_np[0]]
    for _ in range(1, k):
        dist_min = np.array([
            min(np.linalg.norm(p - c) ** 2 for c in centroides)
            for p in data_np
        ])
        centroides.append(data_np[int(np.argmax(dist_min))])
    return pd.DataFrame(centroides)


def assign_centroid(data_df: pd.DataFrame, centroids_df: pd.DataFrame) -> tuple[list[int], list[float]]:
    puntos = data_df.drop(columns=["centroid"], errors="ignore").values
    cent_vals = centroids_df.drop(columns=["centroid"], errors="ignore").values

    asignaciones = []
    errores = []
    for punto in puntos:
        distancias = [float(np.linalg.norm(punto - c) ** 2) for c in cent_vals]
        asignaciones.append(int(np.argmin(distancias)))
        errores.append(float(np.min(distancias)))

    return asignaciones, errores


def kmeans_espectral(k: int, spectral_embedding: np.ndarray):
    data = pd.DataFrame(spectral_embedding)
    centroids = initialize_centroids_maximin(k, spectral_embedding)
    error = []
    compr = True
    i = 0

    while compr:
        data["centroid"], iter_error = assign_centroid(data, centroids)
        error.append(sum(iter_error))
        centroids = data.groupby("centroid").agg("mean").reset_index(drop=True)

        if len(error) < 2:
            compr = True
        else:
            compr = round(error[i], 3) != round(error[i - 1], 3)
        i += 1

    return data["centroid"].values, error, centroids.values


# =====================================================================
# FUNCIÓN PRINCIPAL (MAIN) PARA INYECTAR EN TEST.PY
# =====================================================================
def main(
    warehouse: WareHouse,
    k_zones: int | None = None,
    metric: str = "t"
) -> list[list[tuple[int, int]]]:
    """
    Orquesta el proceso completo de Clustering Espectral sobre el Warehouse:
      1. Extrae los productos de los pedidos pendientes.
      2. Determina la cantidad de zonas K (por defecto, la cantidad de pickers).
      3. Ejecuta los 5 pasos del Clustering Espectral.
      4. Imprime el resumen legible por consola y retorna la lista de listas de coordenadas (x,y).
    """
    products = extract_pending_products(warehouse)
    if not products:
        print("[Clustering Espectral] No hay productos en pedidos pendientes.")
        return []

    # Si no se especifica k_zones, usamos la cantidad de pickers disponibles en el Warehouse
    if k_zones is None:
        k_zones = max(1, length(warehouse.pickers))
    k_zones = min(k_zones, len(products))

    # Ejecución secuencial de los 5 pasos
    dist_matrix = build_distance_matrix(products, metric=metric, warehouse=warehouse)
    sim_matrix = build_similarity_matrix(dist_matrix)
    laplacian = compute_laplacian_matrix(sim_matrix, normalized=True)
    eigenvectors = compute_eigenvectors(laplacian, k_zones)
    embedding = create_spectral_embedding(eigenvectors)
    labels, _, _ = kmeans_espectral(k_zones, embedding)

    # Agrupamos tanto las coordenadas (x, y) como los objetos Product para mostrarlos
    zones_coords: list[list[tuple[int, int]]] = [[] for _ in range(k_zones)]
    zones_products: list[list[Product]] = [[] for _ in range(k_zones)]

    for prod, cluster_id in zip(products, labels):
        zones_coords[int(cluster_id)].append((prod.x, prod.y))
        zones_products[int(cluster_id)].append(prod)

    # Impresión limpia de resultados para el test
    print("=" * 70)
    print(f" RESULTADO CLUSTERING ESPECTRAL (Métrica: {metric.upper()} | Zonas: {k_zones})")
    print("=" * 70)
    for idx, (prod_list, coord_list) in enumerate(zip(zones_products, zones_coords), start=1):
        nombres_prods = ", ".join(f"{p.id}@({p.x},{p.y})" for p in prod_list)
        print(f"  • Zona {idx} ({len(prod_list)} productos): {nombres_prods}")
        print(f"    Coordenadas (x, y) : {coord_list}")
    print("=" * 70)

    return [z for z in zones_coords if z]