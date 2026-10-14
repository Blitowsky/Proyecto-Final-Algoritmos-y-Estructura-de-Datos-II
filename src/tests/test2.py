import os

from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse
from warehouse.structures.linkedlist import LinkedList, add
from warehouse.visualization.ascii_map import render_map, render_rows

SCENARIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "escenario_grande.json")

def picker_start_cells(config, warehouse):
    cells = LinkedList()
    for p in config["pickers"]:
        pos = p["posicion_inicial"]
        add(cells, warehouse.cell_id(pos["x"], pos["y"]))
    return cells

def test_grid():
    config = load_config(SCENARIO)
    warehouse = build_warehouse(config)
    rows = render_rows(warehouse, picker_start_cells(config, warehouse))
    print(render_map(warehouse, picker_start_cells(config, warehouse)))

test_grid()
