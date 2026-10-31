"""
Los dos momentos en el ciclo de vida de una asignación `Assignment`
que no dependen de como se mueva el picker.

`services/wave_runner.run_assignment` recorre toda la ruta de una vez,
mientras que la simulación lo hace un tick a la vez.

`stop_orderer` es el hook a la función de wave picking que corresponda
usar. Si no se asigna, se visitan las paradas en el orden en que
`build_stops` las devuelve.
"""

from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Assignment, Wave
from warehouse.domain.route import Route

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
    if stop_orderer is not None:
        pass
        # TODO

    route = plan_route(warehouse, picker.node, stops, assignment.zone)
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
