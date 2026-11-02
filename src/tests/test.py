# src/tests/test.py
import os

from warehouse.algorithms.pathfinding import find_path
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

config = load_config(SCENARIO)
warehouse = build_warehouse(config)

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

test_grid(warehouse.floor)
print()

# =====================================================================
# PASO DE CLUSTERING ESPECTRAL
# =====================================================================
zonas_espectrales = cs.main(
    warehouse=warehouse,
    metric="t" 
)
print()

simulation = Simulation(
    warehouse,
    algorithm="bfs",
    auto_assign=True
)

simulation.run()

print(simulation.summary())
print()

for event in simulation.events:
    if event.kind != "move":
        print(event.describe(warehouse))
print()

print(render_map(warehouse.floor, picker_current_cells(warehouse)))