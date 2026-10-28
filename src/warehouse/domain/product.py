"""
Product: cada producto, con stock y ubicación asignadas.

DISEÑO
----------
Cada producto apunta a la celda de `Rack` en la que se encuentra (`product.cell`).
A su vez, `product.half.access` contiene la lista de nodos en los que el picker 
puede situarse para recogerlo.
"""

from warehouse.structures.linkedlist import LinkedList

from warehouse.domain.rack import Rack, RackCell

class Product:
    def __init__(self, product_id, name: str, weight: float, stock: int, cell: RackCell, z: int) -> None:
        self.id = product_id
        self.name: str = name
        self.weight: float = weight
        self.stock: int = stock
        self.cell: RackCell = cell
        self.z: int = z
        self.reserved: int = 0

    @property
    def available(self) -> int|None:
        if self.stock is None:
            return None
        return self.stock - self.reserved

    def reserve(self, qty: int) -> None:
        self.reserved += qty

    def release(self, qty: int) -> None:
        self.reserved = max(0, self.reserved - qty)

    @property
    def x(self) -> int:
        return self.cell.x

    @property
    def y(self) -> int:
        return self.cell.y

    @property
    def rack(self) -> Rack:
        return self.cell.rack

    @property
    def location(self) -> tuple[int, int, int]:
        return self.cell.x, self.cell.y, self.z

    @property
    def pick_cells(self) -> LinkedList:
        """`LinkedList` con IDs de pasillos (vértices del grafo)
        desde los que un picker puede acceder a este producto."""
        return self.cell.access
