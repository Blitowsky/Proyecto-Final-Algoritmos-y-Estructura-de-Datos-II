"""
Una ruta (`Route`) es un PLAN: el recorrido que va a hacer un picker,
pierna por pierna, con sus métricas. Planear la ruta no toca a los
pickers, solo la ejecución (`run_route()`).
"""

from warehouse.structures.linkedlist import LinkedList, add, length
from warehouse.structures.dictionary import Dictionary, insert, search

from warehouse.domain.product import Product
from warehouse.domain.location import DispatchZone

class PickLine:
    """Un producto y cuántas unidades tomar."""
    def __init__(self, product: Product, qty: int) -> None:
        self.product: Product = product
        self.qty: int = qty

class Stop:
    """Una parada a la que tiene que ir un picker: cualquier
    pasillo en `cells` sirve, desde ahí debe poder alcanzar
    todas las lineas de productos en `picks`.
    """
    def __init__(self, cells: LinkedList, picks: LinkedList) -> None:
        self.cells: LinkedList = cells
        self.picks: LinkedList = picks
        self.weight: float = 0.0
        self.units: int = 0

        if cells.head is None:
            raise ValueError("Una parada necesita al menos una celda.")
        if picks.head is None:
            raise ValueError("Una parada necesita al menos un producto.")
        line = picks.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            cell = cells.head
            while cell is not None:
                if cell.value is None:
                    cell = cell.nextNode
                    continue
                if not _contains(line.value.product.pick_cells, cell.value):
                    raise ValueError(f"El producto {line.value.product.id} no es alcanzable desde el pasillo {cell.value}.")
                cell = cell.nextNode
            self.weight += line.value.product.weight * line.value.qty
            self.units += line.value.qty
            line = line.nextNode

    @classmethod
    def for_product(cls, product: Product, qty: int):
        """Una parada (`Stop`) para un producto: todos los pasillos
        adyacentes a su celda de rack son aceptables."""
        picks = LinkedList()
        add(picks, PickLine(product, qty))
        return cls(product.pick_cells, picks)

def _contains(cells: LinkedList, wanted: int):
    cell = cells.head
    while cell is not None:
        if cell.value and cell.value == wanted:
            return True
        cell = cell.nextNode
    return False

class Leg:
    """
    Un recorrido (pierna) de punto A a punto B.

    Parámetros
    ----------
        kind (`str`):
            Objetivo del recorrido.
        path (`LinkedList`):
            Lista de IDs de pasillo en el recorrido.
        distance (`float`):
            Suma de pesos en las aristas del recorrido.
        stop (`Stop`):
            Parada final del recorrido.
    """
    def __init__(self, kind: str, path: LinkedList, distance: float, stop: Stop|None = None) -> None:
        self.kind: str = kind
        self.path: LinkedList = path
        self.nodes: int = 0
        i = path.head
        while i is not None:
            self.nodes += 1
            i = i.nextNode
        self.edges: int = self.nodes - 1
        self.distance: float = distance
        self.stop: Stop|None = stop
        self.items: LinkedList = LinkedList()

    @property
    def start(self) -> int|None:
        return self.path.head.value if self.path.head else None

    @property
    def end(self) -> int|None:
        return self.path.tail.value if self.path.tail else None

class Route:
    """Plan del recorrido total a realizar en una `Wave`
    por un picker.

    Parámetros
    ----------
        start (`int`):
            ID del pasillo donde empieza la ruta.
        zone (`DispatchZone`):
            Zona de despacho donde termina la `Wave`.
    """
    def __init__(self, start: int, zone: DispatchZone) -> None:
        self.start: int = start
        self.zone: DispatchZone = zone
        self.legs: LinkedList = LinkedList()
        self.leg_count: int = 0
        self.distance: float = 0.0
        self.edges: int = 0
        self.executed: bool = False

    @property
    def nodes(self) -> int:
        return self.edges + 1

    @property
    def end(self) -> int:
        tail = None
        if self.legs.tail and self.legs.tail.value:
            tail = self.legs.tail.value
        return tail.end if tail is not None else self.start

    def add(self, leg: Leg) -> None:
        add(self.legs, leg)
        self.leg_count += 1
        self.distance += leg.distance
        self.edges += leg.edges

    def distinct_nodes(self, table_size: int) -> int:
        """
        Pasillos distintos visitados (una celda visitada dos veces cuenta una),
        `table_size` = ancho * alto.
        """
        seen = Dictionary(table_size)
        count = 0
        start = self.start
        insert(seen, True, start)
        count += 1
        leg = self.legs.head
        while leg is not None:
            if leg.value is None:
                leg = leg.nextNode
                continue
            node = leg.value.path.head
            while node is not None:
                if node.value is None:
                    node = node.nextNode
                    continue
                if search(seen, node) is None:
                    insert(seen, True, node)
                    count += 1
                node = node.nextNode
            leg = leg.nextNode
        return count
