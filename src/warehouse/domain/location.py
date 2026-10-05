from warehouse.structures.linkedlist import LinkedList

from warehouse.domain.rack import Rack

class RackAccess:
    def __init__(self, rack: Rack, left: bool, right: bool) -> None:
        self.rack: Rack = rack
        self.left: bool = left
        self.right: bool = right

class HallNode:
    def __init__(self, node_id: int, x: int, y: int) -> None:
        self.id: int = node_id
        self.x: int = x
        self.y: int = y
        self.rack_access: LinkedList = LinkedList()
        self.zone: DispatchZone|None = None

class DispatchZone:
    def __init__(self, zone_id, x1: int, y1: int, x2: int, y2: int) -> None:
        self.id = zone_id
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2
        self.cells: LinkedList = LinkedList()

