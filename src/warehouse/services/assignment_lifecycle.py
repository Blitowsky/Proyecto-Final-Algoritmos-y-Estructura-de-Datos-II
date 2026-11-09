"""
Los dos momentos en el ciclo de vida de una asignación `Assignment`
que no dependen de como se mueva el picker.

`services/wave_runner.run_assignment` recorre toda la ruta de una vez,
mientras que la simulación lo hace un tick a la vez.

`stop_orderer` es el hook a la función de wave picking que corresponda
usar. Si no se asigna, se visitan las paradas en el orden en que
`build_stops` las devuelve.
"""
import time

from warehouse.structures.linkedlist import LinkedList, add, length

from warehouse.domain.location import DispatchZone
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Assignment, Wave
from warehouse.domain.route import Route, Stop

from warehouse.services.route_runner import _check_can_serve, plan_route, run_route

def start_assignment(
    warehouse: WareHouse,
    assignment: Assignment,
    stop_orderer: None,
    algorithm: str = "bfs"
) -> Route:
    """
    Planifica la ruta de la asignación desde donde está
    parado el picker y verifica que se pueda cumplir.
    """
    if assignment.status != "assigned":
        raise ValueError(f"Esta asignación está '{assignment.status}', solo las 'assigned' pueden ejecutarse.")
    wave = assignment.wave
    picker = assignment.picker

    stops = assignment.stops
    order_time = None
    if stop_orderer is not None:
        begin = picker.node
        stops, order_time = _order_stops(warehouse, begin, stops, assignment.zone, stop_orderer)

    route = plan_route(warehouse, picker.node, stops, assignment.zone, algorithm)
    route.order_time = order_time
    _check_can_serve(picker, route)

    if wave.status == "assigned":
        wave.status = "running"
        order = wave.orders.head
        while order is not None:
            if order.value is not None:
                order.value.start_preparation()
            order = order.nextNode

    assignment.route = route
    assignment.status = "running"
    return route

def _order_stops(
    warehouse: WareHouse,
    start: int,
    stops: LinkedList,
    zone: DispatchZone,
    stop_orderer
) -> tuple[LinkedList, float]:
    method = getattr(stop_orderer, "order_stops", None)
    call = stop_orderer if method is None else method

    began = time.perf_counter()
    result = call(warehouse, start, stops, zone)
    seconds = time.perf_counter() - began

    expected = []
    stop = stops.head
    while stop is not None:
        if stop.value is not None:
            expected.append(stop.value)
        stop = stop.nextNode
    ordered = LinkedList()
    used = [False] * len(expected)
    stop = result.head
    while stop is not None:
        if stop.value is None:
            stop = stop.nextNode
            continue
        position = -1
        for i in range(len(expected)):
            if expected[i] is stop.value and not used[i]:
                position = i
                break
        if position < 0:
            raise ValueError("El ordenador de paradas devolvió una parada que no está en la asignación, o alguna dos veces.")
        used[position] = True
        add(ordered, stop.value)
        stop = stop.nextNode
    ordered_length = length(ordered)
    if ordered_length != len(expected):
        raise ValueError(f"El ordenador de paradas devolvió {ordered_length} paradas, la asignación tenía {len(expected)}.")
    return ordered, seconds

def finish_assignment(assignment: Assignment) -> None:
    """
    El picker terminó su asignación. El espacio reservado
    de la zona de despacho se libera (porque ya está usado) y
    el picker es liberado.
    """
    if assignment.status != "running":
        raise ValueError(f"Esta asignación está '{assignment.status}', solo las que están 'running' pueden terminar.")
    wave = assignment.wave

    assignment.zone.release(assignment.weight)
    assignment.status = "done"
    assignment.picker.assignment = None

    if _all_done(wave):
        wave.status = "done"
        order = wave.orders.head
        while order is not None:
            if order.value is not None:
                order.value.finish()
            order = order.nextNode

def _all_done(wave: Wave) -> bool:
    assignment = wave.assignments.head
    while assignment is not None:
        if assignment.value is not None and assignment.value.status != "done":
            return False
        assignment = assignment.nextNode
    return True
