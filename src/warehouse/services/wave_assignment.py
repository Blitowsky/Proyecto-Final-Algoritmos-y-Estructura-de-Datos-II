import math

from warehouse.structures.dictionary import Dictionary, insert, search
from warehouse.structures.linkedlist import LinkedList, add

from warehouse.algorithms.pathfinding import find_path

from warehouse.domain.route import PickLine, Stop
from warehouse.domain.picker import Picker
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.location import DispatchZone

EPS = 1e-9

def merge_lines(*sources) -> list[PickLine]:
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
    free = []
    picker = warehouse.pickers.head
    while picker is not None:
        if picker.value is None:
            picker = picker.nextNode
            continue
        if picker.value.assignment is None:
            free.append(picker.value)
        picker = picker.nextNode
    return free

def choose_zone(warehouse: WareHouse, picker: Picker, weight: float, algorithm: str = "bfs") -> DispatchZone|None:
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
