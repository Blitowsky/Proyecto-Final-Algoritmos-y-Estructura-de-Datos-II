from warehouse.domain.rack import RackHalf

class Product:
    def __init__(self, product_id, name: str, weight: float, stock: int, half: RackHalf, x: int, y: int, z: int) -> None:
        self.id = product_id
        self.name: str = name
        self.weight: float = weight
        self.stock: int = stock
        self.half: RackHalf = half
        self.x: int = x
        self.y: int = y
        self.z: int = z

    @property
    def side(self):
        return self.half.side
