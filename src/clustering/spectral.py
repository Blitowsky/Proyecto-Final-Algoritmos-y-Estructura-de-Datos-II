
import math
import numpy as np
import pandas as pd
import warehouse.structures.linkedlist as ll
import warehouse.structures.graph


def build_distance_matrix(points: list, metric: str = 'e', graph=None) -> np.ndarray:
    """
    Construye la Matriz de Distancias.
    
    Soporta dos métricas:
    - 'e': Distancia geométrica en línea recta ignorando obstáculos.
    - 't': Cantidad real de pasos a través de los pasillos del Warehouse.
    
    Args:
        points: Lista de objetos Producto que poseen atributos .id, .x, .y
        metric: 'euclidean' o 'topological'
        graph: Instancia del WeightedDirectedGraph. Requerido si la métrica es topológica.
        
    Returns:
        np.ndarray: Matriz simétrica de NxN con las distancias.
    """
    n_points = len(points)
    
    # Inicializamos una matriz NxN llena de infinitos (np.inf). 
    # Usar NumPy aquí garantiza máxima eficiencia espacial y temporal en memoria contigua.
    distance_matrix = np.full((n_points, n_points), np.inf, dtype=float)
    
    # La distancia de un nodo a sí mismo siempre es 0
    np.fill_diagonal(distance_matrix, 0.0)
    
    if metric == 'e':
        # Calculamos solo el triángulo superior de la matriz para evitar trabajo duplicado
        for i in range(n_points):
            for j in range(i + 1, n_points):
                x1, y1 = points[i].x, points[i].y
                x2, y2 = points[j].x, points[j].y
                
                # Fórmula matemática de distancia euclidiana
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                # Simetrizamos la matriz
                distance_matrix[i, j] = dist
                distance_matrix[j, i] = dist
                
    elif metric == 't':
        if graph is None:
            raise ValueError("Se debe proporcionar un 'graph' para usar la métrica topológica.")
            
        # Convertimos la lista de productos a la estructura LinkedList 
        # requerida por tu función bfs_distances_targeted
        targets_list = ll.LinkedList()
        for p in points:
            targets_list.add(p.id)
            
        # Calculamos los caminos óptimos.
        # Iteramos sobre cada producto actuando como nodo 'origen'
        for i in range(n_points):
            source_id = points[i].id
            
            # topologicall_distance devuelve tu estructura 'Dictionary' 
            # con las distancias desde 'source_id' a todos los nodos en 'targets_list'
            resultados_bfs = gd.topologicall_distance(graph, source_id, targets_list)
            
            for j in range(i + 1, n_points):
                target_id = points[j].id
                
                # Buscamos la distancia de ida (i -> j) en tu Dictionary personalizado
                dist_ida = search(resultados_bfs, target_id)
                dist_ida = dist_ida if dist_ida is not None else math.inf
                
                # Para asegurar la simetría exigida por el Laplaciano del clustering espectral
                # en grafos dirigidos, debemos calcular también el camino inverso (j -> i) 
                # (Lo cual podrías optimizar pre-calculando el diccionario inverso si es necesario)
                resultados_inversos = gd.topologicall_distance(graph, target_id, targets_list)
                dist_vuelta = search(resultados_inversos, source_id)
                dist_vuelta = dist_vuelta if dist_vuelta is not None else math.inf
                
                # Simetrización: Tomamos la ruta transitable más corta (o su promedio)
                dist_efectiva = min(dist_ida, dist_vuelta)
                
                distance_matrix[i, j] = dist_efectiva
                distance_matrix[j, i] = dist_efectiva
                
    else:
        raise ValueError("Métrica inválida. Utilice 'euclidean' o 'topological'.")
        
    return distance_matrix

def compute_laplacian_matrix(similarity_matrix: np.ndarray, normalized: bool = True) -> np.ndarray:
    """
    Paso 2 del Clustering Espectral: Calcular la Matriz Laplaciana.
    
    Esta función toma la Matriz de Similitud (W) generada en el Paso 1 y 
    construye el Laplaciano del grafo, el cual captura la información 
    esencial de la conectividad y los "cuellos de botella" topológicos.
    
    Args:
        similarity_matrix (np.ndarray): La matriz W (NxN) del Paso 1.
        normalized (bool): Si es True, calcula el Laplaciano Simétrico Normalizado.
                           Si es False, calcula el Laplaciano estándar (L = D - W).
                           
    Returns:
        np.ndarray: La matriz Laplaciana resultante (NxN).
    """
    n_points = similarity_matrix.shape[0]
    
    # 1. Matriz Diagonal de Grados (D)
    # Sumamos los pesos de las aristas por cada fila para saber qué tan "conectado" está cada nodo.
    degrees = np.sum(similarity_matrix, axis=1)
    
    if not normalized:
        # Laplaciano No Normalizado: L = D - W
        D = np.diag(degrees)
        L = D - similarity_matrix
        return L
    
    else:
        # Laplaciano Simétrico Normalizado: L_sym = I - D^(-1/2) @ W @ D^(-1/2)
        # Protegemos matemáticamente la división por cero si un nodo quedó aislado
        degrees_inv_sqrt = np.where(degrees > 1e-12, 1.0 / np.sqrt(degrees), 0.0)
        
        # Convertimos el vector en una matriz diagonal
        D_inv_sqrt = np.diag(degrees_inv_sqrt)
        
        # Matriz Identidad (I)
        I = np.eye(n_points)
        
        # Multiplicación matricial (operador @ de NumPy para producto punto)
        L_sym = I - (D_inv_sqrt @ similarity_matrix @ D_inv_sqrt)
        
        return L_sym    

def compute_eigenvectors(laplacian_matrix: np.ndarray, num_clusters: int) -> np.ndarray:
    """
    Paso 3 del Clustering Espectral: Calcular Autovectores (Eigenvectors).
    
    Toma la Matriz Laplaciana (simétrica) y extrae los 'k' autovectores 
    asociados a los autovalores más pequeños. Opcionalmente normaliza 
    las filas para preparar los datos para K-Means.
    
    Args:
        laplacian_matrix (np.ndarray): La Matriz Laplaciana (NxN) del Paso 2.
        num_clusters (int): La cantidad K de zonas/olas que deseas generar.
        
    Returns:
        np.ndarray: Matriz de tamaño NxK que contiene los autovectores seleccionados.
    """
    # 1. Descomposición Espectral
    # Usamos np.linalg.eigh en lugar de eig porque eigh está altamente optimizado 
    # y diseñado matemáticamente para matrices simétricas (como nuestro Laplaciano).
    # Además, garantiza que los autovalores devueltos estén ordenados de menor a mayor.
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian_matrix)
    
    # 2. Selección de los "K" autovectores principales
    # Tomamos todas las filas, pero solo las primeras 'num_clusters' columnas.
    # El primer autovalor siempre será cercano a 0 (autovector trivial), y los 
    # siguientes capturan los "cortes mínimos" del grafo.
    k_eigenvectors = eigenvectors[:, :num_clusters]
    
    # 3. Normalización de filas (Algoritmo de Ng, Jordan & Weiss)
    # Proyecta los puntos resultantes sobre una esfera unitaria. Esto hace que 
    # la agrupación posterior con K-Means sea mucho más precisa y estable.
    row_norms = np.linalg.norm(k_eigenvectors, axis=1, keepdims=True)
    
    # Prevenimos divisiones por cero en nodos completamente desconectados
    row_norms = np.where(row_norms > 1e-12, row_norms, 1.0)
    
    normalized_eigenvectors = k_eigenvectors / row_norms
    
    return normalized_eigenvectors

def create_spectral_embedding(eigenvectors: np.ndarray) -> np.ndarray:
    """
    Paso 4 del Clustering Espectral: Crear el Embedding Espectral.
    
    Toma la matriz de autovectores (NxK) del Paso 3, donde cada columna es un 
    autovector y cada fila representa a un producto de tu Warehouse.
    Normaliza cada fila para proyectar los datos en un nuevo espacio geométrico
    (esfera unitaria) de baja dimensión, volviendo los grupos linealmente separables.
    
    Args:
        eigenvectors (np.ndarray): Matriz de autovectores (NxK) crudos del Paso 3.
        
    Returns:
        np.ndarray: Matriz de Embedding (NxK). Las filas son las nuevas coordenadas
                    de tus productos listas para pasar por K-Means.
    """
    # 1. Calcular la norma L2 (magnitud euclidiana) de cada fila.
    # El parámetro axis=1 indica que sumamos a lo largo de las columnas por cada fila.
    row_norms = np.linalg.norm(eigenvectors, axis=1, keepdims=True)
    
    # 2. Estabilidad Numérica.
    # Prevenimos divisiones por cero en caso de que algún nodo (producto) 
    # haya quedado matemáticamente aislado en el grafo del Warehouse.
    row_norms = np.where(row_norms > 1e-12, row_norms, 1.0)
    
    # 3. Creación del Embedding.
    # Dividimos cada componente de la fila por la magnitud total de esa fila.
    spectral_embedding = eigenvectors / row_norms
    
    return spectral_embedding


def initialize_centroids_maximin(k, data_np):
    """
    Inicialización 100% determinista (Maximin / Farthest-First).
    Selecciona el primer punto del arreglo y luego busca secuencialmente 
    los puntos más alejados de los centroides ya elegidos.
    """
    centroides = [data_np[0]]
    for _ in range(1, k):
        # Calcula la distancia de todos los puntos al centroide más cercano
        dist_min = np.array([min(np.linalg.norm(p - c)**2 for c in centroides) for p in data_np])
        # Elige como nuevo centroide el punto con la máxima de esas distancias mínimas
        centroides.append(data_np[np.argmax(dist_min)])
    
    return pd.DataFrame(centroides)

def assign_centroid(data_df, centroids_df):
    """
    Calcula la distancia euclidiana al cuadrado de cada fila a todos los centroides.
    Devuelve la lista de índices del centroide más cercano y los errores.
    """
    # Excluímos la columna 'centroid' de los cálculos matemáticos
    puntos = data_df.drop(columns=['centroid'], errors='ignore').values
    cent_vals = centroids_df.drop(columns=['centroid'], errors='ignore').values
    
    asignaciones = []
    errores = []
    
    for punto in puntos:
        distancias = [np.linalg.norm(punto - c)**2 for c in cent_vals]
        asignaciones.append(np.argmin(distancias))
        errores.append(np.min(distancias))
        
    return asignaciones, errores

def kmeans_espectral(k, spectral_embedding):
    '''
    Recibe la matriz generada en el Paso 4 y el número de clusters.
    Devuelve las asignaciones, el error y los centroides finales.
    '''
    # 1. Adaptación de entrada: Convertimos el array de NumPy (Paso 4) a DataFrame
    data = pd.DataFrame(spectral_embedding)
    
    # 2. Inicializamos con nuestro algoritmo determinista
    centroids = initialize_centroids_maximin(k, spectral_embedding)
    error = []
    compr = True
    i = 0

    while compr:
        # Obtain centroids and error
        data['centroid'], iter_error = assign_centroid(data, centroids)
        error.append(sum(iter_error))
        
        # Recalculate centroids
        centroids = data.groupby('centroid').agg('mean').reset_index(drop=True)

        # Check if the error has decreased
        if len(error) < 2:
            compr = True
        else:
            if round(error[i], 3) != round(error[i-1], 3):
                compr = True
            else:
                compr = False
        i += 1 

    # Retornamos los valores limpios listos para inyectarse en el Wave Manager
    return data['centroid'].values, error, centroids.values

def main(graph: WeightedDirectedGraph, orders):

    list = ll.LinkedList()
    
    for order in orders:
        for product in order:
            list.add((product.x, product.y, product.id))

    ll.print_list(list)


