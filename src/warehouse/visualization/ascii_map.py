from warehouse.structures.dictionary import Dictionary, search, insert
from warehouse.domain.cell import HALL, RACK, DOOR, ZONE
from warehouse.domain.direction import N, S, E, O, AMBOS


def hall_symbol(cell):
    if cell.sentido == N:
        return "^"
    if cell.sentido == S:
        return "v"
    if cell.sentido == E:
        return ">"
    if cell.sentido == O:
        return "<"
    return "+" if cell.declared else "."          # AMBOS


def render_rows(floor, marks=None):
    """
    Returns one string per row, from y = height-1 (first) down to y = 0 (last).
    marks: optional LinkedList of cell ids to draw as K (for example the pickers' start cells).
    """
    marked = Dictionary(floor.width * floor.height)  # cell id -> True, only used while drawing
    if marks is not None:
        cid = marks.head
        while cid is not None:
            insert(marked, True, cid.value)
            cid = cid.nextNode

    rows = []
    for y in range(floor.height - 1, -1, -1):
        row = ""
        for x in range(floor.width):
            cid = floor.cell_id(x, y)
            cell = search(floor.grid, cid)
            if cell is None:
                continue
            if search(marked, cid) and cell.kind == HALL:
                row += "K"
            elif cell.kind == RACK:
                row += "#"
            elif cell.kind == DOOR:
                row += "P"
            elif cell.kind == ZONE:
                row += "D"
            elif cell.kind == HALL:
                row += hall_symbol(cell)
        rows.append(row)
    return rows


def render_map(floor, marks=None):
    """Same rows with the x ruler and y labels, ready to print."""
    rows = render_rows(floor, marks)
    ruler = ""
    for x in range(floor.width):
        ruler += str(x % 10)
    lines = ["      " + ruler]
    for i in range(len(rows)):
        y = floor.height - 1 - i
        lines.append("y=" + str(y).rjust(2) + "  " + rows[i])
    return "\n".join(lines)
