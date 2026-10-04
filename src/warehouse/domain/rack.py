from warehouse.structures.linkedlist import LinkedList

class RackHalf:
    def __init__(self, rack_id: int, side: str) -> None:
        self.rack_id: int = rack_id
        self.side: str = side
        self.items: LinkedList = LinkedList()
        self.access_halls: LinkedList = LinkedList()

class Rack:
    def __init__(self, rack_id: int, x: int, y: int) -> None:
        self.id: int = rack_id
        self.x: int = x
        self.y: int = y
        self.left: RackHalf = RackHalf(rack_id, "L")
        self.right: RackHalf = RackHalf(rack_id, "R")

