"""
Planificación (sin efectos) y ejecución (mueve al picker).

El orden de las paradas no se decide acá, quien sea que 
llame decide la estrategia a usar. Entre dos paradas posibles,
el planificador camina a la más cercana siempre.
"""

from warehouse.structures.linkedlist import LinkedList, add

from warehouse.domain.route import Leg, Route
from warehouse.domain.picker import Picker
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.location import DispatchZone

from warehouse.algorithms.pathfinding import SearchResult, find_path

def move_picker(
    picker: Picker,
    warehouse: WareHouse,
    targets: LinkedList,
    algorithm: str = "bfs"
) -> Leg:
    """A -> B, encuentra el camino al objetivo más cercano
    en `targets` y ejecuta el recorrido."""
    result = find_path(warehouse, picker.node, targets, algorithm)
    if result is None:
        raise ValueError(f"El picker {picker.id} no puede alcanzar el objetivo desde el pasillo {picker.node}.")
    leg = Leg("move", result.path, result.distance)
    _walk(picker, warehouse, leg)
    return leg

def plan_route(
    warehouse: WareHouse,
    start: int,
    stops: LinkedList,
    zone: DispatchZone,
    algorithm: str = "bfs"
) -> Route:
    """Planifica la ruta hasta la zona de despacho `zone`,
    luego de ahí a cada una de las paradas en `stops`, y
    de vuelta hacia la zona de despacho indicada.
    """
    route = Route(start, zone)
    here = start

    approach = _search(warehouse, here, zone.access, algorithm, "la zona de despacho " + str(zone.id))
    if approach.edges > 0:
        route.add(Leg("approach", approach.path, approach.distance))
        here = approach.target

    stop = stops.head
    while stop is not None:
        if stop.value is None:
            stop = stop.nextNode
            continue
        found = _search(warehouse, here, stop.value.cells, algorithm, "una parada")
        route.add(Leg("pick", found.path, found.distance, stop.value))
        here = found.target
        stop = stop.nextNode

    back = _search(warehouse, here, zone.access, algorithm, "la zona de despacho " + str(zone.id))
    route.add(Leg("return", back.path, back.distance))
    return route

def _search(
    warehouse: WareHouse,
    source,
    targets: LinkedList,
    algorithm: str,
    what: str
) -> SearchResult:
    result = find_path(warehouse, source, targets, algorithm)
    if result is None:
        raise ValueError(f"No se puede alcanzar {what} desde el pasillo {source}")
    return result

def _walk(picker: Picker, warehouse: WareHouse, leg: Leg) -> None:
    """Mueve el picker a lo largo de leg.path, una arista a la vez."""
    first = True
    walked = 0
    node = leg.path.head
    while node is not None:
        if node.value is None:
            node = node.nextNode
            continue
        if first:
            if node.value != picker.node:
                raise ValueError(f"El picker {picker.id} esta en el pasillo {picker.node}, pero el camino empieza en el pasillo {node}.")
            first = False
            node = node.nextNode
            continue
        walked += picker.move_to(node.value, warehouse)
        node = node.nextNode
    
    if walked != leg.distance:
        raise ValueError(f"El camino planeado tenía distancia {leg.distance} pero la suma de pesos del recorrido en el grafo es {walked}.")

def _check_can_serve(picker: Picker, route: Route) -> None:
    """Deniega una ruta que fallaría a mitad de camino: muy pesada o no hay suficiente stock."""
    total = 0.0
    leg = route.legs.head
    while leg is not None:
        if leg.value is None or leg.value.stop is None:
            leg = leg.nextNode
            continue
        line = leg.value.stop.picks.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            total += line.value.product.weight * line.value.qty
            stock = line.value.product.stock
            if stock is not None and line.value.qty > stock:
                raise ValueError(f"El producto {line.value.product.id} tiene {stock} unidades disponibles, pero la ruta pide {line.value.qty}.")
            line = line.nextNode
        leg = leg.nextNode
    if not picker.fits(total):
        raise ValueError(f"El picker {picker.id} no puede llevar {total}kg (capacidad: {picker.capacity}kg)")

    zone = route.zone
    if not zone.is_outbound:
        raise ValueError(f"La zona de despacho {zone.id} es INBOUND, nada puede ser despachado allí.")
    if not zone.can_accept(picker.load + total):
        raise ValueError(f"La zona de despacho {zone.id} no puede aceptar {picker.load + total}kg ({zone.max_weight - zone.load}kg disponibles).")

def run_route(picker: Picker, warehouse: WareHouse, route: Route) -> Route:
    """Recorre la ruta `Route` con el `Picker`: movimientos, picks
    y el despacho final.
    """
    if route.executed:
        raise ValueError(f"Esta ruta ya fue ejecutada, planear una nueva.")
    if route.start != picker.node:
        raise ValueError(f"El picker {picker.id} está en el pasillo {picker.node}, y la zona empieza en el pasillo {route.start}.")
    _check_can_serve(picker, route)

    route.executed = True
    leg = route.legs.head
    while leg is not None:
        if leg.value is None:
            leg = leg.nextNode
            continue
        _walk(picker, warehouse, leg.value)
        perform_leg_action(picker, warehouse, leg.value)
        leg = leg.nextNode
    return route

def perform_leg_action(picker: Picker, warehouse: WareHouse, leg: Leg) -> None:
    if leg.kind == "pick" and leg.stop is not None:
        line = leg.stop.picks.head
        while line is not None:
            if line.value is None:
                line = line.nextNode
                continue
            add(leg.items, picker.pick(line.value.product, line.value.qty))
            line.value.product.release(line.value.qty)
            line = line.nextNode
    elif leg.kind == "return":
        leg.items = picker.drop_off(warehouse)

def visit(
    picker: Picker,
    warehouse: WareHouse,
    stops: LinkedList,
    zone: DispatchZone,
    algorithm: str = "bfs"
) -> Route:
    """`plan_route` y `run_route` en una llamada 
    (primero planifica y luego recorre)."""
    route = plan_route(warehouse, picker.node, stops, zone, algorithm)
    return run_route(picker, warehouse, route)
