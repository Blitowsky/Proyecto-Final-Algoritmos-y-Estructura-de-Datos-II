
import os
from warehouse.algorithms.pathfinding import find_path
from warehouse.algorithms.wave_generation.spectral_waves import SpectralWaveSelector
from warehouse.algorithms.wave_generation.order_centroids.product_centroids import ProductCentroidSelector
from warehouse.persistence.scenario_loader import load_config
from warehouse.services.hall_graph_builder import build_hall_graph
from warehouse.services.route_runner import move_picker
from warehouse.services.warehouse_loader import build_floor, build_warehouse
from warehouse.services.wave_builder import WaveBuilder
from warehouse.services.wave_runner import process_pending
from warehouse.simulation.simulation import Simulation
from warehouse.structures.linkedlist import LinkedList, add, length
from warehouse.visualization.ascii_map import render_map, render_rows
import clustering.spectral as cs

SCENARIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_grande.json")


def picker_start_cells(config, floor):
    cells = LinkedList()
    for p in config["pickers"]:
        pos = p["posicion_inicial"]
        add(cells, floor.cell_id(pos["x"], pos["y"]))
    return cells

def picker_current_cells(warehouse):
    cells = LinkedList()
    picker = warehouse.pickers.head
    while picker is not None:
        if picker.value is not None:
            add(cells, picker.value.node)
        picker = picker.nextNode
    return cells

def test_grid(floor):
    rows = render_rows(floor, picker_start_cells(config, floor))
    print(render_map(floor, picker_start_cells(config, floor)))


if __name__ == "__main__":
    config = load_config(SCENARIO)
    warehouse = build_warehouse(config)

    test_grid(warehouse.floor)
    print()


    K_ZONAS = 4

    zonas_espectrales = cs.main(
        warehouse=warehouse,
        k_zones=K_ZONAS,
        metric="t"
    )
    print()

    selector = SpectralWaveSelector(
        warehouse=warehouse,
        spectral_zones=zonas_espectrales,
        pickers=warehouse.pickers
    )
    waves, rejected = WaveBuilder(warehouse, selector=selector, pickers=warehouse.pickers).build()
    print()

    # selector = ProductCentroidSelector(warehouse, warehouse.orders)
    # waves, rejected = WaveBuilder(warehouse, selector=selector, pickers=warehouse.pickers).build()
    # CON generacion de waves
    # {'ticks': 1366, 'assignments': 11, 'planned_distance': 4739.0, 'steps': 4751, 'waits': 15, 'reroutes': 7, 'side_steps': 0}

    # SIN generacion de waves (solo ordenando pedidos)
    # {'ticks': 1930, 'assignments': 12, 'planned_distance': 5416.0, 'steps': 5432, 'waits': 25, 'reroutes': 8, 'side_steps': 2}

    # waves, rejected = WaveBuilder(warehouse, selector=None, pickers=warehouse.pickers).build()
    # {'ticks': 1714, 'assignments': 40, 'planned_distance': 6183.0, 'steps': 6191, 'waits': 14, 'reroutes': 4, 'side_steps': 0}

    simulation = Simulation(
            warehouse,
            algorithm="bfs",
            auto_assign=True
        )

    simulation.run()

    print(simulation.summary())
    preparados = sum(1 for o in warehouse.orders if o is not None and o.state == "PREPARADO")
    print(f"Pedidos preparados tras entregas: {preparados}/{length(warehouse.orders)}")
    print()

    for event in simulation.events:
        if event.kind != "move":
            print(event.describe(warehouse))
    print()

    print(render_map(warehouse.floor, picker_current_cells(warehouse)))
