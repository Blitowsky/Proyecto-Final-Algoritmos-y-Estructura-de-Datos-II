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
from warehouse.structures.dictionary import CloseDictionary, search, insert

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
        self.line_index: CloseDictionary = CloseDictionary(2 * config.max_products + 1)

        self.order_count: int = 0
        self.product_count: int = 0
        self.total_units: int = 0
        self.total_weight: float = 0.0
        self.top_priority: int = 0

        self.status: str = "created"
        self.assignments: LinkedList = LinkedList()
        self.assignment_count: int = 0
        self.planned_shares: list | None = None

    def why_not(self, order: Order) -> str | None:
        """Determina si cabe un pedido COMPLETO todavía no asignado."""
        if order.state != "PENDIENTE":
            return f"El pedido {order.id} está {order.state}; no puede agregarse completo de nuevo."
        if self.order_count >= self.config.max_orders:
            return f"La wave {self.id} ya alcanzó max_orders={self.config.max_orders}."

        new_products = 0
        for line in order.lines:
            if line is None:
                continue
            if line.resto != line.qty:
                return f"El pedido {order.id} ya se asignó parcialmente."
            if search(self.line_index, line.product.id) is None:
                new_products += 1
            if line.product.available is not None and line.qty > line.product.available:
                return (
                    f"No queda stock suficiente de {line.product.id}: "
                    f"{line.qty} solicitadas, {line.product.available} disponibles."
                )
        if self.product_count + new_products > self.config.max_products:
            return f"La wave {self.id} superaría max_products={self.config.max_products}."
        return None

    def fits(self, order: Order) -> bool:
        return self.why_not(order) is None

    def _take(self, product: Product, qty: int) -> None:
        """Único punto para contabilizar y reservar unidades de una wave."""
        if qty <= 0:
            return
        if product.available is not None and qty > product.available:
            raise ValueError(
                f"Stock insuficiente de {product.id}: {qty} solicitadas, "
                f"{product.available} disponibles."
            )
        product_line = search(self.line_index, product.id)
        if product_line is None:
            if self.product_count >= self.config.max_products:
                raise ValueError(f"La wave {self.id} alcanzó max_products={self.config.max_products}.")
            product_line = WaveLine(product, 0)
            add(self.lines, product_line)
            insert(self.line_index, product_line, product.id)
            self.product_count += 1
        product_line.qty += qty
        self.total_units += qty
        self.total_weight += product.weight * qty
        product.reserve(qty)

    def add_order(self, order: Order) -> None:
        """Agrega un pedido completo; reserva y marca sus cantidades asignadas."""
        reason = self.why_not(order)
        if reason is not None:
            raise ValueError(reason)
        for line in order.lines:
            if line is not None:
                self._take(line.product, line.qty)
                line.usado += line.qty
        order.peso_restante = 0.0
        add(self.orders, order)
        self.order_count += 1
        self.top_priority = max(self.top_priority, order.priority)
        order.assign_to(self)

    def add_partial_order(self, order: Order, capacity: float) -> int:
        """Reparte unidades pendientes sin superar capacidad, stock ni max_products.

        Devuelve la cantidad de unidades agregadas; 0 significa que no hubo avance.
        Mantiene ``OrderLine.usado`` y ``Order.peso_restante`` sincronizados.
        """
        if self.order_count >= self.config.max_orders or capacity <= 0:
            return 0
        if order.state not in ("PENDIENTE", "EN_WAVE"):
            return 0
        if any(existing is order for existing in self.orders):
            return 0

        added = 0
        for line in order.lines:
            if line is None or line.resto <= 0:
                continue
            product = line.product
            if search(self.line_index, product.id) is None and self.product_count >= self.config.max_products:
                continue
            weight = product.weight
            # EPS permite usar exactamente la capacidad con pesos decimales.
            units_by_weight = int((capacity + 1e-9) / weight)
            qty = min(line.resto, units_by_weight)
            if product.available is not None:
                qty = min(qty, product.available)
            if qty <= 0:
                continue
            self._take(product, qty)
            line.usado += qty
            order.peso_restante = max(0.0, order.peso_restante - qty * weight)
            capacity -= qty * weight
            added += qty

        if added > 0:
            add(self.orders, order)
            self.order_count += 1
            self.top_priority = max(self.top_priority, order.priority)
            order.assign_to(self)
        return added

    def add_product_line(self, product: Product, qty: int, priority: int = 0) -> None:
        """Agrega unidades de un `Product` directamente a la wave (sin acoplarla
        a un `Order` completo) y reserva su stock."""
        if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
            raise ValueError(f"La cantidad del producto {product.id} debe ser un entero positivo.")
        available = product.available
        if available is not None and qty > available:
            raise ValueError(
                f"Se pidieron {qty} unidades de {product.id}, pero solo quedan {available} sin reservar."
            )

        pid = product.id
        product_line = search(self.line_index, pid)
        if product_line is not None and product_line.product.id == pid:
            product_line.qty += qty
        else:
            wave_line = WaveLine(product, qty)
            add(self.lines, wave_line)
            insert(self.line_index, wave_line, pid)
            self.product_count += 1

        self.total_units += qty
        self.total_weight += product.weight * qty
        if priority > self.top_priority:
            self.top_priority = priority
        product.reserve(qty)

    def release_stock(self) -> None:
        line = self.lines.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            line.value.product.release(line.value.qty)
            line = line.nextNode    

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



