"""
Convierte las celdas de pasillo de `Floor` en un grafo DIRIGIDO y ponderado.

- Vértice: una celda de pasillo, identificada por su ID de celda (`y * width + x`).
- Arista: un picker situado en `u` puede desplazarse a `v` en un solo paso. 
El peso es `1` (una celda recorrida).

Las celdas de racks, las celdas de puertas y las celdas de zonas de despacho
NO son vértices: nadie puede situarse sobre ellas.

La regla para una arista dirigida `u -> v`, donde `v` es la celda vecina de `u` en la dirección `d` (`N`, `S`, `E` u `O`):

1. Tanto `u` como `v` deben ser celdas de pasillo.
2. La dirección `d` debe estar permitida por el `sentido` de `u` 
(se puede salir de `u` en esa dirección).
3. La dirección `d` debe estar permitida por el `sentido` de `v` 
(se puede entrar en `v` desde esa dirección).
"""

from warehouse.structures.graph import WeightedDirectedGraph
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.direction import MOVES, allows, step
from warehouse.domain.cell import HALL

def build_hall_edges(floor) -> tuple[LinkedList, LinkedList]:
    """Construcción de las listas de vértices y aristas para el grafo.

    Parámetros
    ----------
        floor (`Floor`):
            El plan de piso del warehouse.

    Retorna
    ----------
        (`vertices`, `edges`) como LinkedLists:
        vertices:
            Lista de IDs de cada pasillo.
        edges:
            Lista con (`desde_id`, `hacia_id`, `peso`).
    """
    vertices = LinkedList()
    edges = LinkedList()

    for y in range(floor.height):
        for x in range(floor.width):
            cell = floor.cell_at(x, y)
            if cell.kind != HALL:
                continue
            from_id = floor.cell_id(x, y)
            add(vertices, from_id)

            for move in MOVES:
                dx, dy = step(move)
                neighbour = floor.cell_at(x + dx, y + dy)
                if neighbour is None or neighbour.kind != HALL:
                    continue
                if allows(cell.sentido, move) and allows(neighbour.sentido, move):
                    to_id = floor.cell_id(x + dx, y + dy)
                    add(edges, (from_id, to_id, 1))

    return vertices, edges

def build_hall_graph(floor):
    """Construcción del grafo `WeightedDirectedGraph` de los pasillos."""
    vertices, edges = build_hall_edges(floor)
    return WeightedDirectedGraph(vertices, edges, floor.width * floor.height)
