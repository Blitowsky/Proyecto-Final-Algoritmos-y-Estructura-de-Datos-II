from warehouse.structures.graph import WeightedDirectedGraph
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.direction import MOVES, allows, step
from warehouse.domain.cell import HALL

def build_hall_edges(floor) -> tuple[LinkedList, LinkedList]:
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
    vertices, edges = build_hall_edges(floor)
    return WeightedDirectedGraph(vertices, edges, floor.width * floor.height)
