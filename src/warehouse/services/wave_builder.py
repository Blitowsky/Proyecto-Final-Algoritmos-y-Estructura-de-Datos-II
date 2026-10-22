from warehouse.domain.wave import Wave
from warehouse.structures.linkedlist import LinkedList

from warehouse.domain.order import Order
from warehouse.domain.warehouse import WareHouse


class Rejection:
    def __init__(self, order: Order, reason: str) -> None:
        self.order: Order = order
        self.reason: str = reason

class WaveBuilder:
    def __init__(
        self,
        warehouse: WareHouse,
        selector = None,
        pickers: LinkedList|None = None,
        id_prefix: str = "W"
    ) -> None:
        self.warehouse: WareHouse = warehouse
        self.selector = selector # Wave picking strategy

        self.pickers: LinkedList = warehouse.pickers if pickers is None else pickers
        self.id_prefix: str = id_prefix
        self.created: int = 0

    def _fits(self, wave: Wave, order: Order) -> bool:
        if wave.why_not(order) is not None:
            return False
        lines = merge_lines(wave.lines, order.lines)
        return split_load(lines, self.pickers) is not None
