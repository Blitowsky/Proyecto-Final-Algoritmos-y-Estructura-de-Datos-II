"""
Convierte la lista de picks de una ´wave´ en asignaciones ´Assigment´,
qué `picker` lleva qué, dónde para, y a que zona de despacho lo tiene
que llevar.
"""

import math

from warehouse.structures.dictionary import Dictionary, insert, search
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.algorithms.pathfinding import find_path

from warehouse.domain.route import PickLine, Stop
from warehouse.domain.picker import Picker
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.location import DispatchZone
from warehouse.domain.wave import Assignment, Wave

EPS = 1e-9

def merge_lines(*sources) -> list[PickLine]:
    """
    Suma varias listas de picks (iterables con .product y .qty),
    wave.lines, order.lines, etc; en UNA lista de `PickLine`.
    """
    items = []
    for source in sources:
        line = source.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            items.append(line.value)
            line = line.nextNode

    merged = []
    index = Dictionary(2 * len(items) + 1)
    for line in items:
        pid = line.product.id
        position = search(index, pid)
        if position is not None:
            merged[position].qty += line.qty
        else:
            insert(index, len(merged), pid)
            merged.append(PickLine(line.product, line.qty))
    return merged

def split_load(lines: list[PickLine], pickers) -> list[tuple[Picker, list[PickLine]]]|None:
    """Decide quién lleva qué. Si un picker puede llevar todo, el más débil lo hace
    (así los pickers más fuertes quedan disponibles para waves más grandes). Sino,
    se llenan los pickers secuencialmente, desde el más fuerte.

    Parámetros
    ----------
        lines (`list`):
            Iterable con líneas de productos.
        pickers (`LinkedList`):
            Lista de pickers a asignar.

    Retorna
    ----------
    Una matriz, donde la primer columna son los pickers, y el resto de elementos
    en cada fila son las líneas de productos asignadas a él.
    """
    total = 0.0
    for line in lines:
        total += line.product.weight * line.qty

    ordered = list(pickers)
    ordered.sort(key=lambda p: (-p.remaining(), str(p.id)))

    for p in reversed(ordered):
        if p.fits(total):
            return [(p, [PickLine(l.product, l.qty) for l in lines])]

    room = [p.remaining() for p in ordered]
    shares = [[] for _ in ordered]
    for line in lines:
        left = line.qty
        unit = line.product.weight
        for i in range(len(ordered)):
            if left == 0:
                break
            take = min(left, int((room[i] + EPS) // unit))
            if take > 0:
                shares[i].append(PickLine(line.product, take))
                room[i] -= take * unit
                left -= take
        if left > 0:
            return None

    result = []
    for i in range(len(ordered)):
        if len(shares[i]) > 0:
            result.append((ordered[i], shares[i]))
    return result

def build_stops(warehouse: WareHouse, shares: list[PickLine]) -> LinkedList:
    """Agrupa las líneas asignadas a un picker en paradas `Stop`. Todos
    los productos que comparten la misma celda de rack se toman en una
    misma parada.

    Retorna
    ---------
    `LinkedList` de `Stop`s.
    """
    """
    Groups a picker's shares into Stops: all the products of ONE rack cell are picked in one stop
    (P001 and P002 both sit in cell (3, 5)). Returns a LinkedList of Stop, in the order each rack
    cell first appears in the shares. Deciding the order the stops are VISITED in is M4's job.
    """
    groups = []
    where = Dictionary(warehouse.width * warehouse.height)
    for line in shares:
        cell = line.product.cell
        position = search(where, cell.id)
        if position is not None:
            add(groups[position][1], line)
        else:
            picks = LinkedList()
            add(picks, line)
            insert(where, len(groups), cell.id)
            groups.append((cell, picks))
    stops = LinkedList()
    for cell, picks in groups:
        add(stops, Stop(cell.access, picks))
    return stops

def free_pickers(warehouse: WareHouse) -> list[Picker]:
    """Array de pickers que no tienen tareas asignadas."""
    free = []
    picker = warehouse.pickers.head
    while picker is not None:
        if picker.value is not None and picker.value.assignment is None:
            free.append(picker.value)
        picker = picker.nextNode
    return free

def choose_zone(warehouse: WareHouse, picker: Picker, weight: float, algorithm: str = "bfs") -> DispatchZone|None:
    """La primer zona de despacho de tipo `OUTBOUND` o `AMBOS` que esté más
    cerca del `picker` y que tenga espacio disponible para `weight` kg más"""
    best = None
    best_distance = math.inf
    z = warehouse.zones.head
    while z is not None:
        if z.value is None:
            z = z.nextNode
            continue
        zone = z.value
        if not zone.is_outbound or not zone.can_reserve(weight):
            z = z.nextNode
            continue
        found = find_path(warehouse, picker.node, zone.access, algorithm)
        if found is None:
            z = z.nextNode
            continue
        if best is None or found.distance < best_distance:
            best = zone
            best_distance = found.distance
        z = z.nextNode
    return best

def assign_wave(
    warehouse: WareHouse,
    wave: Wave,
    pickers: list[Picker]|None = None,
    algorithm: str = "bfs"
) -> LinkedList:
    """
    Asigna los pickers, tareas, paradas y zonas a una wave 
    recién creada. El espacio de las zonas de despacho queda
    reservado por cada asignación.

    Retorna
    ----------
    wave.assignments (`LinkedList` de asignaciones `Assignment`).
    """
    if wave.status != "created" or wave.assignment_count > 0:
        raise ValueError(f"La wave {wave.id} está '{wave.status}' y ya tiene {wave.assignment_count} asignaciones.")

    candidates = free_pickers(warehouse) if pickers is None else list(pickers)
    if len(candidates) == 0:
        raise ValueError(f"No hay pickers libres para la wave {wave.id}.")

    parts = split_load(merge_lines(wave.lines), candidates)
    if parts is None:
        raise ValueError(f"Los {wave.total_weight}kg de la wave {wave.id} no pueden ser cargados por los pickers disponibles: " +
        ", ".join(str(p.id) + " " + str(p.remaining()) + "kg" for p in candidates))

    try:
        for picker, shares in parts:
            share_list = LinkedList()
            weight = 0.0
            for line in shares:
                add(share_list, line)
                weight += line.product.weight * line.qty

            zone = choose_zone(warehouse, picker, weight, algorithm)
            if zone is None:
                raise ValueError(f"Ninguna zona de despacho puede aceptar los {weight}kg del picker {picker.id}.")
            zone.reserve(weight)
            assignment = Assignment(
                    wave,
                    picker,
                    zone,
                    share_list,
                    build_stops(warehouse, shares)
                )
            picker.assignment = assignment
            add(wave.assignments, assignment)
            wave.assignment_count += 1
    except ValueError:
        cancel_assignments(wave)
        raise
    
    wave.status = "assigned"
    return wave.assignments

def cancel_assignments(wave: Wave) -> None:
    """Deshace el trabajo de `assign_wave`: libera los pickers y
    libera el espacio reservado de las zonas de despacho."""
    if wave.status not in ("created", "assigned"):
        raise ValueError(f"La wave {wave.id} está '{wave.status}', sus asignaciones no pueden ser canceladas.")
    assignment = wave.assignments.head
    while assignment is not None:
        if assignment.value is None:
            assignment = assignment.nextNode
            continue
        assignment.value.zone.release(assignment.value.weight)
        assignment.value.picker.assignment = None
        assignment = assignment.nextNode
    wave.assignments = LinkedList()
    wave.assignment_count = 0
    wave.status = "created"
