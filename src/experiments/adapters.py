from warehouse.structures.dictionary import Dictionary, search
from warehouse.structures.linkedlist import LinkedList, add, length

from warehouse.domain.warehouse import WareHouse
from warehouse.domain.cell import DOOR, HALL, RACK, ZONE

from warehouse.algorithms.pathfinding import SearchResult, find_path
from warehouse.algorithms.wave_generation.order_centroids.product_centroids import ProductCentroidSelector

from warehouse.services.warehouse_loader import build_warehouse
from warehouse.services.wave_builder import WaveBuilder

from warehouse.persistence.scenario_loader import load_config

from warehouse.simulation.simulation import Simulation

def load_floor(json_path):
    config = load_config(json_path)
    return build_warehouse(config)

def graph_size(warehouse: WareHouse):
    v = length(warehouse.graph.v)
    e = length(warehouse.graph.e)
    return v, e

def hall_cells(warehouse: WareHouse):
    vertices = warehouse.graph.v
    cells = []
    v = vertices.head
    while v is not None:
        if v.value is not None:
            cells.append(warehouse.node_xy(v.value))
        v = v.nextNode
    return cells

def run_search(warehouse: WareHouse, algo, src: tuple[int, int], dst: tuple[int, int]):
    src_id = warehouse.floor.cell_id(*src)
    dst_id = warehouse.floor.cell_id(*dst)
    target = LinkedList()
    add(target, dst_id)
    result: SearchResult|None = find_path(warehouse, src_id, target, algo)
    if result:
        return { "cost": result.distance, "expanded": result.expanded, "examined": result.examined }
    return { "cost": 0, "expanded": 0, "examined": 0 }


def run_simulation(warehouse: WareHouse, strategy_key):
    match strategy_key:
        case "centroids":
            selector = ProductCentroidSelector(warehouse, warehouse.orders)
        case _:
            selector = None
    waves, rejected = WaveBuilder(warehouse, selector=selector, pickers=warehouse.pickers).build()
    simulation = Simulation(
            warehouse,
            algorithm="astar",
            auto_assign=True
        )
    simulation.run(with_visits=True)
    summary = simulation.summary()
    return summary, summary["summary_visits"]


def grid_kinds(warehouse: WareHouse):
    floor = warehouse.floor
    rows = []
    for y in range(warehouse.height - 1, -1, -1):
        row = []
        for x in range(warehouse.width):
            cid = floor.cell_id(x, y)
            cell = search(floor.grid, cid)
            if cell is None:
                continue
            elif cell.kind == RACK:
                row.append("rack")
            elif cell.kind == DOOR:
                row.append("door")
            elif cell.kind == ZONE:
                row.append("zone")
            elif cell.kind == HALL:
                row.append("hall")
        rows.append(row)
    return rows[::-1]
