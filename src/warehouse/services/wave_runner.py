"""
Ejecuta todas las asignaciones de principio a fin, un picker
detrás del otro. La versión simultánea está en:
`simulation/simulation.py`

`stop_orderer` es el hook a la función a usar como
estrategia de wave picking, debe retornar las paradas
en el orden a visitar. Sino, se visitan en el orden
en el que `build_stops` las devuelve.
"""

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
    """Planifica y ejecuta la tarea de un picker"""

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
    """Ejecuta todas las asignaciones de `wave`, una detrás de la otra."""
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
    """
    Todo el proceso en una llamada: agrupar pedidos pendientes
    en waves, asignar tareas de esta wave a los pickers libres
    y ejecutarlas.

    Retorna 
    ----------
    (`waves`, `rejected`) del `builder`.
    """
    waves, rejected = WaveBuilder(warehouse, selector).build()
    wave = waves.head
    while wave is not None:
        if wave.value is not None:
            assign_wave(warehouse, wave.value, None, algorithm)
            run_wave(warehouse, wave.value, stop_orderer, algorithm)
        wave = wave.nextNode
    return waves, rejected

