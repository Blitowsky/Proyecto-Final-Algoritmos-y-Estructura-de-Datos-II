import os

from warehouse.algorithms.pathfinding import find_path
from warehouse.persistence.scenario_loader import load_config
from warehouse.services.hall_graph_builder import build_hall_graph
from warehouse.services.warehouse_loader import build_floor, build_warehouse
from warehouse.structures.linkedlist import LinkedList, add
from warehouse.visualization.ascii_map import render_map, render_rows

SCENARIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_basico.json")

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

# warehouse.graph.printGraph()

# 92 -> (2, 5); 177 -> (15, 9); 95 -> (5, 5) 
targets = LinkedList()
# add(targets, 177)
add(targets, 95)
path_bfs = find_path(warehouse, 5, targets, "bfs")
path_dijkstra = find_path(warehouse, 5, targets, "dijkstra")
path_astar = find_path(warehouse, 5, targets, "astar")

print("BFS:")
if path_bfs:
    print(f"Expanded: {path_bfs.expanded}; Examined: {path_bfs.examined}; Nodes: {path_bfs.nodes}")
    node = path_bfs.path.head
    while node is not None:
        if node.value:
            print((node.value % warehouse.width, node.value // warehouse.width), end=" -> ")
        node = node.nextNode
    print("None")
print("DIJKSTRA:")
if path_dijkstra:
    print(f"Expanded: {path_dijkstra.expanded}; Examined: {path_dijkstra.examined}; Nodes: {path_dijkstra.nodes}")
    node = path_dijkstra.path.head
    while node is not None:
        if node.value:
            print((node.value % warehouse.width, node.value // warehouse.width), end=" -> ")
        node = node.nextNode
    print("None")
print("A*:")
if path_astar:
    print(f"Expanded: {path_astar.expanded}; Examined: {path_astar.examined}; Nodes: {path_astar.nodes}")
    node = path_astar.path.head
    while node is not None:
        if node.value:
            print((node.value % warehouse.width, node.value // warehouse.width), end=" -> ")
        node = node.nextNode
    print("None")
