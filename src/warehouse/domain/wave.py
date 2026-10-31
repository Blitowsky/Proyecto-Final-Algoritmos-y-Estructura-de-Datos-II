"""
Una wave representa UN recorrido por picker, como cada una 
puede tener más de un `Picker` asignado, las wave.assignments 
indican la tarea de cada picker individual, la lista de picks
puede estar distribuida entre varios pickers.

What changed from your version (every change is marked "M3"):
  - Wave.status and the status constants: the life of a wave.
  - Wave.assignments: the pickers serving it. A wave is ONE trip per picker, and its pick list may be
    split among several pickers when no single one can carry it all.
  - why_not() also checks stock: an order cannot ask for more units than are still unclaimed
    (product.available = stock minus what other waves already reserved).
  - add_order() reserves those units; release_stock() gives them back when a wave is discarded.
  - There is NO weight check here any more: the weight rule is "every picker's share fits that
    picker's capacity", which depends on the pickers, so services/wave_assignment.py enforces it.
"""

from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import Dictionary, search, insert

from warehouse.domain.product import Product
from warehouse.domain.order import Order
from warehouse.domain.location import DispatchZone
# from warehouse.domain.picker import Picker
from warehouse.domain.route import Route

class WaveConfig:
    def __init__(self, max_orders: int, max_products: int) -> None:
        for name, value in (("max_orders", max_orders), ("max_products", max_products)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} en la config del wave debe ser un entero positivo.")
        self.max_orders: int = max_orders
        self.max_products: int = max_products

class WaveLine:
    """Un producto en la lista de picks de la `Wave`,
    con la cantidad total entre todas las ordenes."""
    def __init__(self, product: Product, qty: int) -> None:
        self.product: Product = product
        self.qty: int = qty

    @property
    def weight(self) -> float:
        return self.product.weight * self.qty

class Wave:
    def __init__(self, wave_id: str, config: WaveConfig) -> None:
        self.id = wave_id
        self.config: WaveConfig = config

        self.orders: LinkedList = LinkedList()
        self.lines: LinkedList = LinkedList()
        self.line_index: Dictionary = Dictionary(2 * config.max_products + 1)

        self.order_count: int = 0
        self.product_count: int = 0
        self.total_units: int = 0
        self.total_weight: float = 0.0
        self.top_priority: int = 0

        self.status: str = "created"
        self.assignments: LinkedList = LinkedList()
        self.assignment_count: int = 0

    def why_not(self, order: Order) -> str|None:
        if order.state != "PENDIENTE":
            return f"El pedido {order.id} está {order.state}, solo se pueden añadir pedidos en PENDIENTE a una nueva wave."
        if self.order_count >= self.config.max_orders:
            return f"La wave {self.id} esta llena (max_orders {self.config.max_orders})."

        new_products = 0
        line = order.lines.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            if search(self.line_index, line.value.product.id) is None:
                new_products += 1
            available = line.value.product.available
            if available is not None and line.value.qty > available:
                return f"El pedido {order.id} pide {line.value.qty} {line.value.product.id}, pero solo quedan {available} sin reservar."
            line = line.nextNode

        if self.product_count + new_products > self.config.max_products:
            return f"El pedido {order.id} llevaría a la wave {self.id} a {self.product_count + new_products} productos distintos (max_products {self.config.max_products})."

        return None

    def fits(self, order: Order) -> bool:
        return self.why_not(order) is None

    def add_order(self, order: Order) -> None:
        """Asigna un pedido `Order` a la wave, y deja las
        unidades correspondientes al pedido reservadas."""
        reason = self.why_not(order)
        if reason is not None:
            raise ValueError(reason)

        line = order.lines.head
        while line is not None:
            if line.value is None:
                continue

            pid = line.value.product.id
            product_line = search(self.line_index, pid)
            if product_line is not None:
                product_line.qty += line.value.qty
            else:
                wave_line = WaveLine(line.value.product, line.value.qty)
                add(self.lines, wave_line)
                insert(self.line_index, wave_line, pid)
                self.product_count += 1
            self.total_units += line.value.qty
            self.total_weight += line.value.weight
            line.value.product.reserve(line.value.qty)

            line = line.nextNode

        add(self.orders, order)
        self.order_count += 1
        if order.priority > self.top_priority:
            self.top_priority = order.priority
        order.assign_to(self)

    def release_stock(self) -> None:
        line = self.lines.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            line.value.product.release(line.value.qty)

class Assignment:
    """
    La tarea de un `picker` en una `wave`: UN recorrido
    desde donde está parado el picker, pasando por las
    paradas en `stops` hasta la zona de despacho `zone`.

    Cada `Wave` tiene una asignación por cada picker que
    pertenezca a ella, generalmente uno.
    """
    def __init__(
        self, 
        wave: Wave, 
        picker, 
        zone: DispatchZone,
        shares: LinkedList,
        stops: LinkedList
    ) -> None:
        self.wave: Wave = wave
        self.picker = picker
        self.zone: DispatchZone = zone
        self.shares: LinkedList = shares
        self.stops: LinkedList = stops
        self.weight: float = 0.0
        self.units: int = 0

        line = shares.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            self.weight += line.value.product.weight * line.value.qty
            self.units += line.value.qty
            line = line.nextNode

        self.route: Route|None = None
        self.status: str = "assigned"



