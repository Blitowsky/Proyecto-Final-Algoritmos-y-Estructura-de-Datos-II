from warehouse.structures.linkedlist import LinkedList

from warehouse.services.route_runner import plan_route, check_route, run_route

from warehouse.domain.route import Route
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Assignment, Wave


def run_assignment(
    warehouse: WareHouse,
    assignment: Assignment,
    stop_orderer = None,
    algorithm: str = "bfs"
) -> Route:
    if assignment.status != "assigned":
        raise ValueError(f"Esta asignación está '{assignment.status}', solo las 'assigned' pueden ejecutarse.")
    wave = assignment.wave
    picker = assignment.picker

    stops = assignment.stops
    if stop_orderer is not None:
        pass
        # TODO

    route = plan_route(warehouse, picker.node, stops, assignment.zone)
    # check_route

    if wave.status == "assigned":
        wave.status = "running"
        order = wave.orders.head
        while order is not None:
            if order.value is not None:
                order.value.start_preparation()
            order = order.nextNode

    assignment.route = route
    run_route(picker, warehouse, route)

    assignment.zone.release(assignment.weight)
    assignment.status = "done"
    picker.assignment = None

    if _all_done(wave):
        wave.status = "done"
        order = wave.orders.head
        while order is not None:
            if order.value is not None:
                order.value.finish()
            order = order.nextNode

    return route

def _all_done(wave: Wave) -> bool:
    assignment = wave.assignments.head
    while assignment is not None:
        if assignment.value is not None and assignment.value.status != "done":
            return False
        assignment = assignment.nextNode
    return True

def run_wave(
    warehouse: WareHouse,
    wave: Wave,
    stop_orderer = None,
    algorithm: str = "bfs"
) -> None:
    if wave.status not in ("assigned", "running"):
        raise ValueError(f"La wave {wave.id} está '{wave.status}', primero hay que asignarla.")
    assignment = wave.assignments.head
    while assignment is not None:
        if assignment.value is not None and assignment.value.status == "assigned":
            run_assignment(warehouse, assignment.value, stop_orderer, algorithm)
        assignment = assignment.nextNode

