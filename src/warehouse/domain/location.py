from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.rack import Rack
from warehouse.domain.rect import Rect

INBOUND = "INBOUND"
OUTBOUND = "OUTBOUND"
AMBOS = "AMBOS"
DOOR_KINDS = (INBOUND, OUTBOUND, AMBOS)

EPS = 1e-9

class HallSection:
    def __init__(self, section_id: str, rect: Rect, sentido: str):
        self.id: str = section_id
        self.rect: Rect = rect
        self.sentido: str = sentido

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
        self.access: LinkedList = LinkedList()
        self.items: LinkedList = LinkedList()
        self.load: float = 0.0

    @property
    def is_outbound(self) -> bool:
        return self.door is not None and self.door.is_outbound

    def can_accept(self, weight: float) -> bool:
        return self.load + weight <= self.max_weight + EPS
    
    def deposit(self, items: LinkedList, weight: float) -> None:
        if not self.can_accept(weight):
            raise ValueError(f"La zona de despacho {self.id} no puede tomar {weight}kg más ({self.max_weight - self.load}kg restantes).")
        i = items.head
        while i is not None:
            if i.value is None:
                i = i.nextNode
                continue
            item = i.value
            add(self.items, item)
            i = i.nextNode
        self.load += weight

    def reset(self):
        self.items = LinkedList()
        self.load = 0.0
