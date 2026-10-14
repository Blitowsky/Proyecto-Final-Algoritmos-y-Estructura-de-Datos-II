from warehouse.structures.linkedlist import LinkedList

from warehouse.domain.rect import Rect

class RackHalf:
    def __init__(self, rack_id: int, side: str) -> None:
        self.rack_id: int = rack_id
        self.side: str = side
        self.items: LinkedList = LinkedList()
        self.access_halls: LinkedList = LinkedList()

class Rack:
    def __init__(self, rack_id: str, rect: Rect) -> None:
        self.id: str = rack_id
        self.rect: Rect = rect

