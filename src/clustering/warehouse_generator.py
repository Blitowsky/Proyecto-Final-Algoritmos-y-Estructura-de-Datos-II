# src/core/warehouse_generator.py
from src.warehouse.structures.dictionary import OpenDictionary

def _clasificar_celda_paralela(x: int, y: int, ancho_x: int, largo_y: int) -> str:
    """Clasifica el tipo de nodo para el Grafo 1 (Pasillos Paralelos Estándar)."""
    # 1. Puerta sobre el borde inferior
    if y == 0 and x == ancho_x // 2:
        return "PUERTA"
    # 2. Zona de despacho frente a la puerta
    if y == 1 and abs(x - (ancho_x // 2)) <= 1:
        return "DESPACHO"
    # 3. Bordes inferiores/superiores libres para circulación transversal
    if y <= 2 or y >= largo_y - 2:
        return "PASILLO_TRANSVERSAL"
    # 4. Distribución periódica en X: 2 columnas de Rack seguidas de 2 columnas de Pasillo
    patron_x = (x - 1) % 4
    if 0 < x < ancho_x - 1 and patron_x in (1, 2):
        return "RACK"
    return "PASILLO"


def _clasificar_celda_cruzada(x: int, y: int, ancho_x: int, largo_y: int) -> str:
    """Clasifica el tipo de nodo para el Grafo 2 (Layout con Pasillo Central / Islas)."""
    if y == 0 and (x == ancho_x // 4 or x == (3 * ancho_x) // 4):
        return "PUERTA"
    if y == 1 and (abs(x - (ancho_x // 4)) <= 1 or abs(x - ((3 * ancho_x) // 4)) <= 1):
        return "DESPACHO"
    # Pasillo central horizontal (Cross-aisle) que parte los racks en islas
    mitad_y = largo_y // 2
    if y in (mitad_y, mitad_y - 1) or y <= 1 or y >= largo_y - 2:
        return "PASILLO_TRANSVERSAL"
    
    patron_x = (x - 1) % 4
    if 0 < x < ancho_x - 1 and patron_x in (1, 2):
        return "RACK"
    return "PASILLO"


def _construir_grafo(ancho_x: int, largo_y: int, funcion_clasificadora) -> OpenDictionary:
    """
    Construye el grafo en una TablaHashCuadratica.
    Cada nodo almacena: {"pos": (x, y), "tipo": str, "adyacentes": [id_vecinos]}
    """
    total_celdas = ancho_x * largo_y
    grafo = OpenDictionary(max(13, total_celdas * 2))

    # Mapeo temporal de tipos para armar conexiones válidas
    grilla_tipos = {}
    for y in range(largo_y):
        for x in range(ancho_x):
            grilla_tipos[(x, y)] = funcion_clasificadora(x, y, ancho_x, largo_y)

    # Creación de nodos y aristas según reglas del Warehouse
    movimientos = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for (x, y), tipo in grilla_tipos.items():
        node_id = f"N_{x}_{y}"
        vecinos = []

        for dx, dy in movimientos:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in grilla_tipos:
                continue
            
            tipo_vecino = grilla_tipos[(nx, ny)]
            
            # Regla del Warehouse: Un RACK no se conecta con otro RACK (no se puede caminar a través de estantes),
            # solo se accede desde un pasillo lateral (dx != 0).
            if tipo == "RACK":
                if dx != 0 and tipo_vecino in ("PASILLO", "PASILLO_TRANSVERSAL"):
                    vecinos.append(f"N_{nx}_{ny}")
            else:
                # Si estamos en un pasillo/despacho, conectamos con pasillos o con racks adyacentes lateralmente
                if tipo_vecino != "RACK" or (tipo_vecino == "RACK" and dx != 0):
                    vecinos.append(f"N_{nx}_{ny}")

        grafo.insertar(node_id, {
            "pos": (x, y),
            "tipo": tipo,
            "adyacentes": vecinos
        })

    return grafo


def generar_dos_grafos_warehouse(ancho_x: int, largo_y: int) -> tuple[OpenDictionary, OpenDictionary]:
    """Genera y retorna los dos grafos con topologías distintas para el tamaño solicitado."""
    grafo_1 = _construir_grafo(ancho_x, largo_y, _clasificar_celda_paralela)
    grafo_2 = _construir_grafo(ancho_x, largo_y, _clasificar_celda_cruzada)
    return grafo_1, grafo_2