from warehouse.structures.dictionary import Dictionary, insert, search

from warehouse.domain.warehouse import WareHouse

from warehouse.algorithms.graph_queries import neighbors
from warehouse.algorithms.pathfinding import find_path

from warehouse.simulation.walker import Walker


def reroute_around(
    warehouse: WareHouse,
    walker: Walker,
    cell: int,
    others: list[int],
    algorithm: str = "bfs"
) -> int|None:
    goal = walker.goal_cells()
    if goal is None:
        return None
    size = warehouse.width * warehouse.height
    algorithm = walker.algorithm if algorithm is None else algorithm

    blocked = Dictionary(size)
    insert(blocked, True, cell)
    for other in others:
        insert(blocked, True, other)
    found = find_path(warehouse, walker.picker.node, goal, algorithm, blocked)

    if found is None:
        only_cell = Dictionary(1)
        insert(only_cell, True, cell)
        found = find_path(warehouse, walker.picker.node, goal, algorithm, only_cell)
        if found is not None and found.edges > 0 and found.path.head:
            first_step = found.path.head.nextNode.value if found.path.head.nextNode else None
            for other in others:
                if other == first_step:
                    found = None
                    break
    if found is None:
        return None

    path = []
    node = found.path.head
    while node is not None:
        if node.value is not None:
            path.append(node.value)
        node = node.nextNode
    extra = (len(path) - 1) - walker.remaining_steps
    walker.reroute(path)
    return extra

def free_neighbor(
    warehouse: WareHouse,
    cell: int,
    occupied: Dictionary,
    claimed: Dictionary,
    avoid: Dictionary|None = None
):
    best = None
    best_in_the_way = None
    edge = neighbors(warehouse.graph, cell).head
    while edge is not None:
        if edge.value is None or not isinstance(edge.value, tuple):
            edge = edge.nextNode
            continue
        to, weight = edge.value
        if search(occupied, to) is not None or search(claimed, to) is not None:
            edge = edge.nextNode
            continue
        if avoid is not None and search(avoid, to) is not None:
            if best_in_the_way is None or to < best_in_the_way:
                best_in_the_way = to
        elif best is None or to < best:
            best = to
        edge = edge.nextNode
    return best if best is not None else best_in_the_way

