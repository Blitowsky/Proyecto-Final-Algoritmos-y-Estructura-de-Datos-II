import os
import pickle

from warehouse.persistence.scenario_loader import load_config
from warehouse.services.hall_graph_builder import build_hall_graph
from warehouse.services.warehouse_loader import build_floor, build_warehouse
from warehouse.structures.linkedlist import LinkedList, add, length
from warehouse.visualization.ascii_map import render_map, render_rows
from warehouse.persistence.save_load import load, save



from contextlib import redirect_stdout, redirect_stderr
from collections import Counter
import sys
SCENARIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_grande.json")
config = load_config(SCENARIO)

warehouse = load()

if warehouse is None:
    print("paso por aca")
    config = load_config(SCENARIO)
    warehouse = build_warehouse(config)
    save(warehouse)


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

