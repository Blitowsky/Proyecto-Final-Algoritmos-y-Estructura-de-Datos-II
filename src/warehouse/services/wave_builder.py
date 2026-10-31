"""
Agrupa los pedidos en estado `PENDIENTE` en waves. La regla
de agrupamiento se corresponde con la estrategia a usar,
indicada en `selector`.
"""

from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.queue import Queue

from warehouse.domain.order import Order
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Wave

from warehouse.services.wave_assignment import cancel_assignments, merge_lines, split_load


class Rejection:
    """Un pedido que no pudo tomar ninguna `wave`."""
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

    def _reason_alone(self, order: Order) -> str:
        probe = Wave("probe", self.warehouse.wave_config)
        reason = probe.why_not(order)
        if reason is not None:
            return reason
        return f"El pedido {order.id} ({order.total_weight}kg) no puede ser cargado por ningún picker: {", ".join([f"{p.id} {p.capacity}kg" for p in list(self.pickers) if p is not None])}"

    def build(self) -> tuple[LinkedList, LinkedList]:
        """Agrupa todos los pedidos PENDIENTEs en el warehouse

        Retorna
        ----------
            waves (`LinkedList`):
                Lista de waves `Wave` creadas.
            rejected (`LinkedList`):
                Lista de waves rechazadas `Rejection`.
        """
        pending = []
        pending = Queue()
        order = self.warehouse.orders.head
        while order is not None:
            if order.value and order.value.state == "PENDIENTE":
                pending.enqueue(order.value)
            order = order.nextNode
        
        # TODO Ordenar 'pending' con las estrategias que desarrollemos

        waves = LinkedList()
        rejected = LinkedList()

        while not pending.is_empty():
            wave = Wave(self.id_prefix + str(self.created + 1), self.warehouse.wave_config)
            order = pending.dequeue()

            if self._fits(wave, order):
                wave.add_order(order)
            else:
                add(rejected, Rejection(order, self._reason_alone(order)))
                continue
            
            self.created += 1
            add(waves, wave)
            add(self.warehouse.waves, wave)

        return waves, rejected

def discard_wave(wave: Wave) -> None:
    if wave.status in ("running", "done"):
        raise ValueError(f"La wave {wave.id} está '{wave.status}', no puede ser descartada.")
    if wave.status == "canceled":
        return
    cancel_assignments(wave)
    wave.release_stock()
    order = wave.orders.head
    while order is not None:
        if order.value is not None:
            order.value.reset()
        order = order.nextNode
    wave.status = "canceled"
