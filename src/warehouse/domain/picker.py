from warehouse.structures.dictionary import search
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.product import Product
from warehouse.domain.warehouse import Floor, WareHouse
from warehouse.domain.wave import Assignment

# Por errores de punto flotante
EPS = 1e-9

class PickedItem:
    def __init__(self, product: Product, qty: int) -> None:
        self.product: Product = product
        self.qty: int = qty

    @property
    def weight(self):
        return self.product.weight * self.qty

class Picker:
    def __init__(self, picker_id: str, start_node: int, capacity: float) -> None:
        self.id: str = picker_id
        self.start_node: int = start_node
        self.capacity: float = capacity

        self.node: int = start_node
        self.load: float = 0.0
        self.carried: LinkedList = LinkedList()
        self.delivered: LinkedList = LinkedList()

        self.distance: int = 0
        self.assignment: Assignment|None = None

    @property
    def nodes_visited(self) -> int:
        return self.distance + 1

    def remaining(self) -> float:
        return self.capacity - self.load

    def fits(self, extra_weight: float) -> bool:
        return self.load + extra_weight <= self.capacity + EPS

    def move_to(self, next_id: int, warehouse: WareHouse) -> float:
        graph = warehouse.graph.graph

        if search(graph, self.node) is None:
            raise ValueError(f"El picker {self.id} está en un pasillo inválido.")

        weight = None
        edge = graph.dictionary[graph.hash_func(self.node)].head
        while edge is not None:
            if isinstance(edge.value, tuple) and isinstance(edge.value[1], tuple):
                if edge.value[1][0] == next_id:
                    weight = edge.value[1][1]
            edge = edge.nextNode

        if weight is None:
            raise ValueError(f"El picker {self.id} no puede ir desde el nodo {self.node} al nodo {next_id}.")

        self.node = next_id
        self.distance += 1
        return weight

    def is_at_access_hall(self, product: Product) -> bool:
        hall_id = product.cell.access.head
        while hall_id is not None:
            if hall_id.value == self.node:
                return True
            hall_id = hall_id.nextNode
        return False

    def pick(self, product: Product, qty: int) -> PickedItem:
        if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
            raise ValueError("La cantidad debe ser un entero positivo.")
        if not self.is_at_access_hall(product):
            raise ValueError(f"El picker {self.id} en el nodo {self.node} no puede alcanzar el producto {product.id} desde aquí.")
        if product.stock is not None and qty > product.stock:
            raise ValueError(f"Solo quedan {product.stock} unidades del producto {product.id}, se pidieron {qty}.")

        extra = product.weight * qty
        if not self.fits(extra):
            raise ValueError(f"El picker {self.id} no puede llevar {extra}kg más: {self.remaining()}kg de capacidad restantes.")

        item = PickedItem(product, qty)
        add(self.carried, item)
        self.load += extra
        if product.stock is not None:
            product.stock -= qty
        return item


    def drop_off(self, warehouse: WareHouse) -> LinkedList:
        zones = warehouse.dropoff_zones_at(self.node)

        if zones is None:
            raise ValueError(f"El picker {self.id} está en el nodo {self.node}, que no está junto a ninguna zona de despacho.")

        chosen_zone = None
        any_outbound = False
        node = zones.head
        while node is not None:
            if node.value is None:
                node = node.nextNode
                continue
            zone = node.value
            if zone.is_outbound:
                any_outbound = True
                if chosen_zone is None and zone.can_accept(self.load):
                    chosen_zone = zone
            node = node.nextNode

        if not any_outbound:
            raise ValueError(f"El picker {self.id} está junto a zonas cuya puerta es INBOUND: no se puede despachar desde ahí.")
        if chosen_zone is None:
            raise ValueError(f"Ninguna zona de despacho vecina puede recibir {self.load}kg más.")

        dropped = self.carried
        chosen_zone.deposit(dropped, self.load)
        item = dropped.head
        while item is not None:
            add(self.delivered, item.value)
            item = item.nextNode
        self.carried = LinkedList()
        self.load = 0.0
        return dropped

    @staticmethod
    def _return_to_stock(items: LinkedList) -> None:
        item = items.head
        while item is not None:
            if item.value is None:
                item = item.nextNode
                continue
            product = item.value.product
            if product.stock is not None:
                product.stock += item.value.qty
            item = item.nextNode

    def reset(self) -> None:
        self._return_to_stock(self.carried)
        self._return_to_stock(self.delivered)
        self.node = self.start_node
        self.load = 0.0
        self.carried = LinkedList()
        self.delivered = LinkedList()
        self.distance = 0
        self.assignment = None
            
