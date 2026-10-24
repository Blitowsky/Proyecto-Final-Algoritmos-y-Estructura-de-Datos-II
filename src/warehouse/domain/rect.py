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
        return self.x >= 0 and self.y >= 0 and self.x2 < floor_width and self.y2 < floor_height

    def touches(self, x: int, y: int) -> bool:
        if self.contains(x, y):
            return False
        return (self.contains(x + 1, y) or self.contains(x - 1, y)
                or self.contains(x, y + 1) or self.contains(x, y - 1))
