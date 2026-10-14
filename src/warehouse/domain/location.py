from warehouse.structures.linkedlist import LinkedList

from warehouse.domain.rack import Rack
from warehouse.domain.rect import Rect

INBOUND = "INBOUND"
OUTBOUND = "OUTBOUND"
AMBOS = "AMBOS"
DOOR_KINDS = (INBOUND, OUTBOUND, AMBOS)

# class RackAccess:
#     def __init__(self, rack: Rack, left: bool, right: bool) -> None:
#         self.rack: Rack = rack
#         self.left: bool = left
#         self.right: bool = right

class HallSection:
    def __init__(self, section_id: str, rect: Rect, sentido: str):
        self.id: str = section_id
        self.rect: Rect = rect
        self.sentido: str = sentido

# class HallNode:
#     def __init__(self, node_id: int, x: int, y: int) -> None:
#         self.id: int = node_id
#         self.x: int = x
#         self.y: int = y
#         self.rack_access: LinkedList = LinkedList()
#         self.zone: DispatchZone|None = None

class Door:
    def __init__(self, door_id: str, kind: str, x: int, y: int) -> None:
        if kind not in DOOR_KINDS:
            raise ValueError(f"La puerta {door_id} tiene tipo {kind}, se esperaba uno de {", ".join(DOOR_KINDS)}.")
        self.id: str = door_id
        self.kind: str = kind
        self.x: int = x
        self.y: int = y
        self.zones: LinkedList = LinkedList()

    @property
    def is_outbound(self) -> bool:
        return self.kind != INBOUND

class DispatchZone:
    def __init__(self, zone_id: str, door_id: str, rect: Rect, max_weight: float) -> None:
        self.id: str = zone_id
        self.door_id: str = door_id
        self.rect: Rect = rect
        self.max_weight: float = max_weight
        self.door: Door|None = None

    @property
    def is_outbound(self) -> bool:
        return self.door is not None and self.door.is_outbound
