from warehouse.structures.linkedlist import LinkedList

from warehouse.domain.rect import Rect

class Rack:
    def __init__(self, rack_id: str, rect: Rect) -> None:
        self.id: str = rack_id
        self.rect: Rect = rect
        self.cells: LinkedList = LinkedList()

class RackCell:
    def __init__(self, rack: Rack, x: int, y: int, cell_id: int) -> None:
        self.rack: Rack = rack
        self.x: int = x
        self.y: int = y
        self.id: int = cell_id
        self.items: LinkedList = LinkedList()
        self.access: LinkedList = LinkedList()



