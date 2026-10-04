from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import Dictionary, search, insert
from warehouse.structures.graph import WeightedDirectedGraph

from warehouse.domain.warehouse import HallNode, RackAccess, WareHouse
from warehouse.domain.rack import Rack

DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def cell_id(x: int, y: int, width: int) -> int:
    return y * width + x

def reachable_halves(dx: int, dy: int) -> tuple[bool, bool]:
    if dx == 1:
        return True, False
    if dx == -1:
        return False, True
    return True, True

def build_warehouse(config: dict) -> WareHouse:
    width = config["width"]
    height = config["height"]
    m = width * height

    # Pass 1
    racks = Dictionary(m)
    for rack in config["racks"]:
        x, y = rack["x"], rack["y"]
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"El rack {rack["id"]} esta fuera del warehouse.")
        cid = cell_id(x, y, width)
        if search(racks, cid) is not None:
            raise ValueError(f"Dos racks en la celda ({x}, {y})")
        insert(racks, Rack(rack["id"], x, y), cid)

    # Pass 2
    vertices = LinkedList()
    edges = LinkedList()
    halls = Dictionary(m)

    for y in range(height):
        for x in range(width):
            cid = cell_id(x, y, width)
            if search(racks, cid) is not None:
                continue

            hall = HallNode(cid, x, y)
            insert(halls, hall, cid)
            add(vertices, cid)

            for dx, dy in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue # Borde del warehouse
                nid = cell_id(nx, ny, width)

                rack = search(racks, nid)
                if rack is not None:
                    left, right = reachable_halves(dx, dy)
                    add(hall.rack_access, RackAccess(rack, left, right))
                    if left:
                        add(rack.left.access_halls, cid)
                    if right:
                        add(rack.right.access_halls, cid)
                elif nid > cid:
                    add(edges, (cid, nid, 1))
                    add(edges, (nid, cid, 1))

    graph = WeightedDirectedGraph(vertices, edges)
    
    return WareHouse(width, height, graph, halls, racks)

