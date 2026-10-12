from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import Dictionary, search, insert

from warehouse.domain.product import Product
from warehouse.domain.order import Order

class WaveConfig:
    def __init__(self, max_orders: int, max_products: int) -> None:
        for name, value in (("max_orders", max_orders), ("max_products", max_products)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} en la config del wave debe ser un entero positivo.")
        self.max_orders: int = max_orders
        self.max_products: int = max_products

class WaveLine:
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

    def why_not(self, order: Order) -> str|None:
        if order.state != "PENDIENTE":
            return f"El pedido {order.id} está {order.state}, solo se pueden añadir pedidos en PENDIENTE a una nueva wave."
        if self.order_count >= self.config.max_orders:
            return f"La wave {self.id} esta llena (max_orders {self.config.max_orders})."

        new_products = 0
        line = order.lines.head
        while line is not None:
            if line.value and search(self.line_index, line.value.product.id) is None:
                new_products += 1
            line = line.nextNode

        if self.product_count + new_products > self.config.max_products:
            return f"El pedido {order.id} llevaría a la wave {self.id} a {self.product_count + new_products} productos distintos (max_products {self.config.max_products})."

        return None

    def fits(self, order: Order) -> bool:
        return self.why_not(order) is None

    def add_order(self, order: Order) -> None:
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

            line = line.nextNode

        add(self.orders, order)
        self.order_count += 1
        if order.priority > self.top_priority:
            self.top_priority = order.priority
        order.assign_to(self)




