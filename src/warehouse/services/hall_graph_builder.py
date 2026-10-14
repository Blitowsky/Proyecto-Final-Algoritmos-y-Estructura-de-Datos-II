from warehouse.structures.graph import WeightedDirectedGraph
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.direction import MOVES, allows, step
from warehouse.domain.cell import HALL

def build_hall_edges(warehouse) -> tuple[LinkedList, LinkedList]:
    vertices = LinkedList()
    edges = LinkedList()

    for y in range(warehouse.height):
        for x in range(warehouse.width):
            cell = warehouse.cell_at(x, y)
            if cell.kind != HALL:
                continue
            from_id = warehouse.cell_id(x, y)
            add(vertices, from_id)

            for move in MOVES:
                dx, dy = step(move)
                neighbour = warehouse.cell_at(x + dx, y + dy)
                if neighbour is None or neighbour.kind != HALL:
                    continue
                if allows(cell.sentido, move) and allows(neighbour.sentido, move):
                    to_id = warehouse.cell_id(x + dx, y + dy)
                    add(edges, (from_id, to_id, 1))

    return vertices, edges

def build_hall_graph(warehouse):
    vertices, edges = build_hall_edges(warehouse)
    return WeightedDirectedGraph(vertices, edges, warehouse.width * warehouse.height)
