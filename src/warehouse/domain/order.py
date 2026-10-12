from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.product import Product
from warehouse.domain.wave import Wave

class OrderLine:
    def __init__(self, product: Product, qty: int) -> None:
        self.product: Product = product
        self.qty: int = qty

    @property
    def weight(self) -> float:
        return self.product.weight * self.qty

class Order:
    def __init__(self, order_id: str, priority: int) -> None:
        if (isinstance(priority, bool) or not isinstance(priority, int)
            or priority <= 0):
            raise ValueError(f"La prioridad del pedido {order_id} debe ser un entero positivo.")

        self.id: str = order_id
        self.priority: int = priority

        self.lines: LinkedList = LinkedList()
        self.line_count: int = 0
        self.total_units: int = 0
        self.total_weight: float = 0.0
        self.state: str = "PENDIENTE"
        self.wave: Wave|None = None

    def add_line(self, product: Product, qty: int) -> None:
        if self.state != "PENDIENTE":
            raise ValueError(f"El pedido {self.id} está en estado {self.state}, no se pueden añadir nuevos productos.")
        if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
            raise ValueError(f"Pedido {self.id}: la cantidad del pedido {product.id} debe ser un entero positivo mayor a 0.")
        if product.stock is not None and qty > product.stock:
            raise ValueError(f"El pedido {self.id} pide {qty} unidades del producto {product.id} pero solo existen {product.stock} unidades.")

        line = self.lines.head
        while line is not None:
            if line.value and line.value.product is product:
                raise ValueError(f"El pedido {self.id} lista al producto {product.id} dos veces.")
            line = line.nextNode

        line = OrderLine(product, qty)
        add(self.lines, line)
        self.line_count += 1
        self.total_units += qty
        self.total_weight += line.weight
        
    def _move(self, expected: str, new: str) -> None:
        if self.state != expected:
            raise ValueError(f"El pedido {self.id} está {self.state}, debe ser {expected} antes de poder ser {new}.")
        self.state = new

    def assign_to(self, wave: Wave) -> None:
        self._move("PENDIENTE", "EN_WAVE")
        self.wave = wave

    def start_preparation(self) -> None:
        self._move("EN_WAVE", "EN_PREPARACION")

    def finish(self) -> None:
        self._move("EN_PREPARACION", "PREPARADO")

    def reset(self):
        self.state = "PENDIENTE"
        self.wave = None
