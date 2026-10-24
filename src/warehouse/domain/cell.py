from warehouse.domain.direction import AMBOS

HALL = "HALL"
RACK = "RACK"
DOOR = "DOOR"
ZONE = "ZONE"

class Cell:
    def __init__(self, kind: str, owner=None) -> None:
        self.kind: str = kind
        self.owner = owner

    @property
    def sentido(self) -> str|None:
        if self.kind != HALL:
            return None
        return AMBOS if self.owner is None else self.owner.sentido

    @property
    def declared(self) -> bool:
        return self.kind == HALL and self.owner is not None

    def label(self) -> str:
        if self.owner is None:
            return "Una celda de pasillo no declarada"
        if self.kind == RACK:
            return f"El rack {self.owner.id}"
        if self.kind == DOOR:
            return f"La puerta {self.owner.id}"
        if self.kind == ZONE:
            return f"La zona de despacho {self.owner.id}"
        return f"La sección pasillo {self.owner.id}"
