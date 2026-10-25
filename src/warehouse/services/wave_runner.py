from warehouse.services.assignment_lifecycle import finish_assignment, start_assignment
from warehouse.services.wave_assignment import assign_wave
from warehouse.services.wave_builder import WaveBuilder
from warehouse.structures.linkedlist import LinkedList

from warehouse.services.route_runner import plan_route, _check_can_serve, run_route

from warehouse.domain.route import Route
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Assignment, Wave


def run_assignment(
    warehouse: WareHouse,
    assignment: Assignment,
    stop_orderer = None,
    algorithm: str = "bfs"
) -> Route:

    route = start_assignment(warehouse, assignment, stop_orderer, algorithm)
    run_route(assignment.picker, warehouse, route)
    finish_assignment(assignment)
    return route

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

def process_pending(
    warehouse: WareHouse,
    selector = None,
    stop_orderer = None,
    algorithm: str = "bfs"
) -> tuple[LinkedList, LinkedList]:
    waves, rejected = WaveBuilder(warehouse, selector).build()
    wave = waves.head
    while wave is not None:
        if wave.value is not None:
            assign_wave(warehouse, wave.value, None, algorithm)
            run_wave(warehouse, wave.value, stop_orderer, algorithm)
        wave = wave.nextNode
    return waves, rejected

