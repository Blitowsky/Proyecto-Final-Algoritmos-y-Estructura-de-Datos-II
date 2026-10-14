import os

from warehouse.persistence.scenario_loader import load_config
from warehouse.services.hall_graph_builder import build_hall_graph
from warehouse.services.warehouse_loader import build_floor, build_warehouse
from warehouse.structures.linkedlist import LinkedList, add
from warehouse.visualization.ascii_map import render_map, render_rows

SCENARIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "escenario_basico.json")

config = load_config(SCENARIO)
warehouse = build_warehouse(config)

def picker_start_cells(config, floor):
    cells = LinkedList()
    for p in config["pickers"]:
        pos = p["posicion_inicial"]
        add(cells, floor.cell_id(pos["x"], pos["y"]))
    return cells

def test_grid(floor):
    rows = render_rows(floor, picker_start_cells(config, floor))
    print(render_map(floor, picker_start_cells(config, floor)))

test_grid(warehouse.floor)
print()

