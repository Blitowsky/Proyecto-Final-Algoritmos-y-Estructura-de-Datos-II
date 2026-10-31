from warehouse.domain.warehouse import WareHouse

class Event:
    """Lo que reporta la simulación: un evento por cada acción
    que hace un picker por tick.
    """
    def __init__(
        self,
        tick: int,
        picker: str,
        kind: str,
        src: int,
        dst: int|None = None,
        detail: str = ""
    ) -> None:
        self.tick: int = tick
        self.picker: str = picker
        self.kind: str = kind
        self.src: int = src
        self.dst: int|None = dst
        self.detail: str = detail

    def describe(self, warehouse: WareHouse) -> str:
        text = f"t={self.tick} {self.picker} {self.kind} {_xy(warehouse, self.src)}"
        if self.dst is not None:
            text += " -> " + _xy(warehouse, self.dst)
        if self.detail != "":
            text += " " + self.detail
        return text

def _xy(warehouse: WareHouse, cell: int) -> str:
    x, y = warehouse.node_xy(cell)
    return f"({x}, {y})"
