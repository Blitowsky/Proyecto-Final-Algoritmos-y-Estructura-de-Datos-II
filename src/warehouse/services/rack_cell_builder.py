from warehouse.domain.warehouse import Floor
from warehouse.structures.dictionary import insert
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.rack import RackCell
from warehouse.domain.cell import HALL
from warehouse.domain.direction import MOVES, step

def find_access_cells(floor: Floor, x: int, y: int) -> LinkedList:
    access = LinkedList()
    for move in MOVES:
        dx, dy = step(move)
        neighbour = floor.cell_at(x + dx, y + dy)
        if neighbour is not None and neighbour.kind == HALL:
            add(access, floor.cell_id(x + dx, y + dy))
    return access

def build_rack_cells(floor: Floor) -> None:
    rck = floor.racks.head
    while rck is not None:
        if rck.value is None:
            rck = rck.nextNode
            continue
        rack = rck.value

        r = rack.rect
        for y in range(r.y, r.y2 + 1):
            for x in range(r.x, r.x2 + 1):
                cid = floor.cell_id(x, y)
                cell = RackCell(rack, x, y, cid)
                cell.access = find_access_cells(floor, x, y)
                add(rack.cells, cell)
                insert(floor.rack_cells, cell, cid)

        rck = rck.nextNode
