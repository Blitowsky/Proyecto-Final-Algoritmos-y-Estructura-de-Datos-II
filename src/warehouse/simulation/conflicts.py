"""
Lógica pura: no sabe nada respecto al plan de piso, la 
estructura del grafo, solo quién está parado dónde y a
dónde quiere ir.

    Regla 1: dos pickers nunca terminan un tick en la misma celda.
    Regla 2: dos pickers nunca intercambian celdas en un tick.

Todos los que se estén moviendo, proponen UN paso por tick,
`resolve()` decide cuáles pasos están garantizados. Los otros
se quedan donde están. Un paso es rechadazo cuando está:

    OCCUPIED    la celda está ocupada por alguien que no
                se va a mover.

    CONTESTED   otro picker quiere la misma celda y tiene
                prioridad.

    HEAD_ON     hay dos pickers que quieren la celda del
                otro, el más fuerte tiene prioridad.
"""

from warehouse.structures.dictionary import Dictionary, insert, search

class Move:
    """Un paso propuesto en un tick

    Parámetros
    ----------
        picker (`srt`):
            ID del picker que propone.
        src (`int`):
            ID del pasillo donde está el picker.
        dst (`int`):
            ID del pasillo a donde quiere ir.
        rank (`tuple`):
            Mientras más chico más fuerte.
    """
    def __init__(self, picker: str, src: int, dst: int, rank: tuple[int, int, str]) -> None:
        self.picker: str = picker
        self.src: int = src
        self.dst: int = dst
        self.rank: tuple[int, int, str] = rank
        self.granted: bool = True
        self.reason: str|None = None
        self.blocker: str|None = None

def resolve(table_size: int, standing: list[tuple[str, int]], moves: list[Move]) -> list[Move]:
    """Resolución de conflictos de movimientos propuestos

    Parámetros
    ----------
        standing (`list`):
            Ubicaciones de cada picker.
        moves (`list`):
            Lista de movimientos propuestos.
        table_size (`int`):
            ancho * alto
    """
    holder = Dictionary(table_size)
    for picker, cell in standing:
        insert(holder, picker, cell)

    mover = Dictionary(2 * len(moves) + 1)
    for move in moves:
        insert(mover, move, move.picker)

    ordered = list(moves)
    ordered.sort(key=lambda m: m.rank)
    changed = True
    while changed:
        changed = _refuse_occupied(ordered, holder, mover)
        if not changed:
            changed = _refuse_contested(ordered)
    return moves

def _refuse(move: Move, reason: str, blocker: str) -> None:
    move.granted = False
    move.reason = reason
    move.blocker = blocker

def _refuse_occupied(ordered: list[Move], holder: Dictionary, mover: Dictionary) -> bool:
    """`True` si UN movimiento que quiere ocupar una celda ocupada o un intercambio."""
    for move in ordered:
        if not move.granted:
            continue
        other = search(holder, move.dst)
        if other is None:
            continue
        if other == move.picker:
            continue
        theirs = search(mover, other)
        if theirs is None or not theirs.granted:
            _refuse(move, "occupied", other) # Quien ocupa la celda no se mueve
            return True
        if theirs.dst == move.src: # Ambos quieren la celda del otro
            if move.rank > theirs.rank:
                _refuse(move, "head_on", other)
                return True
    return False

def _refuse_contested(ordered: list[Move]) -> bool:
    """De los movimientos garantizados que quieren la misma celda,
    solo el más fuerte se la queda."""
    for i in range(len(ordered)):
        first = ordered[i]
        if not first.granted:
            continue
        for j in range(i + 1, len(ordered)):
            second = ordered[j]
            if second.granted and second.dst == first.dst:
                _refuse(second, "contested", first.picker)
                return True
    return False
