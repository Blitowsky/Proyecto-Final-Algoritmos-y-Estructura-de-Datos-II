"""
Rectángulo definido por el JSON.

DISEÑO
----------
Esquina inferior izquierda (`x`, `y`), más
`width` (ancho en celdas desde `x`) y `height`
(alto en celdas desde `y`).

Los `Racks`, las `Zonas de Despacho` y los
`Pasillos` están descriptos por rectángulos.
"""

class Rect:
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.x: int = x
        self.y: int = y
        self.width: int = width
        self.height: int = height

    @property
    def x2(self) -> int:
        return self.x + self.width - 1

    @property
    def y2(self) -> int:
        return self.y + self.height - 1

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x <= self.x2 and self.y <= y <= self.y2

    def inside(self, floor_width: int, floor_height: int) -> bool:
        """`True` si el rectángulo está contenido en el warehouse"""
        return self.x >= 0 and self.y >= 0 and self.x2 < floor_width and self.y2 < floor_height

    def touches(self, x: int, y: int) -> bool:
        """`True` si la celda (`x`, `y`) esta FUERA
        del rectángulo, pero ortogonalmente adyacente
        a alguna de sus celdas.

        Parámetros
        ----------
            `x`; `y` (`int`):
                Coordenadas de la celda en cuestión.
        """
        if self.contains(x, y):
            return False
        return (self.contains(x + 1, y) or self.contains(x - 1, y)
                or self.contains(x, y + 1) or self.contains(x, y - 1))
