"""
Cell: celda individual en la grilla del warehouse,
y qué hay en esa ubicación.
"""

from warehouse.domain.direction import AMBOS

HALL = "HALL"
RACK = "RACK"
DOOR = "DOOR"
ZONE = "ZONE"

class Cell:
    """Qué hay en una celda unitaria del warehouse

    Parámetros
    ----------
        kind (`str`):
            Tipo de objeto en esta ubicación.
        owner:
            Clase del objeto correspondiente.
    """
    def __init__(self, kind: str, owner=None) -> None:
        self.kind: str = kind
        self.owner = owner

    @property
    def sentido(self) -> str|None:
        """Dirección de una celda pasillo,
        `None` en caso que no lo sea."""
        if self.kind != HALL:
            return None
        return AMBOS if self.owner is None else self.owner.sentido

    @property
    def declared(self) -> bool:
        """`True` si la celda está asociada a un objeto."""
        return self.kind == HALL and self.owner is not None

    def label(self) -> str:
        """Nombre legible para imprimir en mensajes de error."""
        if self.owner is None:
            return "Una celda de pasillo no declarada"
        if self.kind == RACK:
            return f"El rack {self.owner.id}"
        if self.kind == DOOR:
            return f"La puerta {self.owner.id}"
        if self.kind == ZONE:
            return f"La zona de despacho {self.owner.id}"
        return f"La sección pasillo {self.owner.id}"
