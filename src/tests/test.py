import os

from warehouse.algorithms.pathfinding import find_path
from warehouse.persistence.scenario_loader import load_config
from warehouse.services.hall_graph_builder import build_hall_graph
from warehouse.services.route_runner import move_picker
from warehouse.services.warehouse_loader import build_floor, build_warehouse
from warehouse.services.wave_builder import WaveBuilder
from warehouse.services.wave_runner import process_pending
from warehouse.simulation.simulation import Simulation
from warehouse.structures.linkedlist import LinkedList, add, length
from warehouse.visualization.ascii_map import render_map, render_rows

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

# warehouse.graph.printGraph()

# 55 (picker) -> (1, 3); 92 -> (2, 5); 177 -> (15, 9); 95 -> (5, 5) 
# picker0 = warehouse.pickers.head.value
# targets = LinkedList()
# # add(targets, 177)
# add(targets, 95)
# path_bfs = find_path(warehouse, 55, targets, "bfs")
# path_dijkstra = find_path(warehouse, 55, targets, "dijkstra")
# path_astar = find_path(warehouse, 55, targets, "astar")
#
# print("BFS:")
# if path_bfs:
#     print(f"Expanded: {path_bfs.expanded}; Examined: {path_bfs.examined}; Nodes: {path_bfs.nodes}")
#     node = path_bfs.path.head
#     while node is not None:
#         if node.value:
#             print((node.value % warehouse.width, node.value // warehouse.width), end=" -> ")
#         node = node.nextNode
#     print("None")
# print("DIJKSTRA:")
# if path_dijkstra:
#     print(f"Expanded: {path_dijkstra.expanded}; Examined: {path_dijkstra.examined}; Nodes: {path_dijkstra.nodes}")
#     node = path_dijkstra.path.head
#     while node is not None:
#         if node.value:
#             print((node.value % warehouse.width, node.value // warehouse.width), end=" -> ")
#         node = node.nextNode
#     print("None")
# print("A*:")
# if path_astar:
#     print(f"Expanded: {path_astar.expanded}; Examined: {path_astar.examined}; Nodes: {path_astar.nodes}")
#     node = path_astar.path.head
#     while node is not None:
#         if node.value:
#             print((node.value % warehouse.width, node.value // warehouse.width), end=" -> ")
#         node = node.nextNode
#     print("None")
# print()
#
# route = move_picker(picker0, warehouse, targets, "astar")
# picker0_node = LinkedList()
# add(picker0_node, picker0.node)
# print(render_map(warehouse.floor, picker0_node))

# waves, rejected = process_pending(warehouse)
# print("WAVES: ")
# for wave in list(waves):
#     if wave is None:
#         continue
#     print(f"Wave {wave.id} ({wave.status})")
#     print(f"Orders: {", ".join([o.id for o in list(wave.orders)])}")
#     for line in list(wave.lines):
#         if line is None:
#             continue
#         x = line.product.cell.x
#         y = line.product.cell.y
#         z = line.product.z
#         print(f"{line.product.id}; {line.product.weight}kg ({line.qty}) <{x}, {y}, {z}>")
#     print("Assignments:")
#     for i, assignment in enumerate(list(wave.assignments)):
#         if assignment is None:
#             continue
#         print(f"Assignment {i}; picker {assignment.picker.id} ({assignment.picker.capacity}kg); dispatch zone {assignment.zone.id}:")
#         for leg in list(assignment.route.legs):
#             if leg is None:
#                 continue
#             node = leg.path.head
#             while node is not None:
#                 if node.value:
#                     print((node.value % warehouse.width, node.value // warehouse.width), end=" -> ")
#                 node = node.nextNode
#             print("None")
#     print()
#
# print("REJECTED: ", length(rejected))
# print()
#
# print(render_map(warehouse.floor, picker_current_cells(warehouse)))

waves, rejected = WaveBuilder(warehouse, pickers=warehouse.pickers).build()

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
