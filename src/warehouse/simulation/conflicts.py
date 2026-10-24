from warehouse.structures.dictionary import Dictionary, insert, search


class Move:
    def __init__(self, picker: str, src: int, dst: int, rank: tuple[int, int, str]) -> None:
        self.picker: str = picker
        self.src: int = src
        self.dst: int = dst
        self.rank: tuple[int, int, str] = rank
        self.granted: bool = True
        self.reason: str|None = None
        self.blocker: str|None = None

def resolve(table_size: int, standing: list[tuple[str, int]], moves: list[Move]):
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
        if theirs.dst == move.src: # Ambos quieren la misma celda
            if move.rank > theirs.rank:
                _refuse(move, "head_on", other)
                return True
    return False

def _refuse_contested(ordered: list[Move]) -> bool:
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
