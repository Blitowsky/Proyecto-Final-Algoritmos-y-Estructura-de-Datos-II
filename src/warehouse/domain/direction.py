"""
Funciones auxiliares para determinar
el sentido de una celda pasillo.
"""

N = "N"
S = "S"
E = "E"
O = "O"
AMBOS = "AMBOS"

SENTIDOS = (N, S, E, O, AMBOS)
MOVES = (N, S, E, O)

def is_sentido(value: str) -> bool:
    return value in SENTIDOS

def step(direction: str) -> tuple[int, int]:
    """(`dx`, `dy`) de un paso."""
    if direction == N:
        return 0, 1
    if direction == S:
        return 0, -1
    if direction == E:
        return 1, 0
    if direction == O:
        return -1, 0
    raise ValueError(f"{direction} no es una dirección válida.")

def opposite(direction: str) -> str:
    if direction == N:
        return S
    if direction == S:
        return N
    if direction == E:
        return O
    if direction == O:
        return E
    raise ValueError(f"{direction} no es una dirección válida.")

def allows(sentido: str, move: str) -> bool:
    """Determina si un `Picker` se puede mover
    en ese `sentido`.

    Parámetros
    ----------
        sentido (`str`):
            Sentido del pasillo donde está.
        move (`str`):
            N, S, E u O.

    Retorna
    ----------
        `True` mientras no sea el sentido opuesto.
    """
    if sentido == AMBOS:
        return True
    return move != opposite(sentido)
