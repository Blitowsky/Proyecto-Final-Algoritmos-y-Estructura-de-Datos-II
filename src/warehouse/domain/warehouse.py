from warehouse.structures.linkedlist import LinkedList
from warehouse.structures.dictionary import Dictionary, search
from warehouse.structures.graph import WeightedDirectedGraph

from warehouse.domain.rack import Rack
from warehouse.domain.wave import WaveConfig
from warehouse.domain.cell import Cell

class Floor:
    def __init__(
        self, width: int, 
        height: int, 
        rack_count: int,
        door_count: int,
        zone_count: int,
        section_count: int,
    ) -> None:
        self.width: int = width
        self.height: int = height

        self.grid: Dictionary = Dictionary(width * height)
        self.hall_count: int = 0

        self.rack_cells: Dictionary = Dictionary(width * height)
        self.racks: LinkedList = LinkedList()
        self.racks_by_id: Dictionary = Dictionary(2 * rack_count + 1)

        self.doors: LinkedList = LinkedList()
        self.doors_by_id = Dictionary(2 * door_count + 1)
        self.zones = LinkedList()
        self.zones_by_id = Dictionary(2 * zone_count + 1)
        self.dropoff: Dictionary = Dictionary(width * height)

        self.sections = LinkedList()
        self.sections_by_id = Dictionary(2 * section_count + 1)

    def cell_id(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def cell_at(self, x: int, y: int) -> Cell|None:
        if not self.in_bounds(x, y):
            return None
        return search(self.grid, self.cell_id(x, y))

class WareHouse:
    def __init__(
        self,
        floor: Floor,
        graph: WeightedDirectedGraph,
        products: Dictionary,
        pickers: LinkedList,
        orders: LinkedList,
        orders_by_id: Dictionary,
        wave_config: WaveConfig
    ) -> None:
        self.floor: Floor = floor
        self.width: int = floor.width
        self.height: int = floor.height
        self.graph: WeightedDirectedGraph = graph

        self.racks: LinkedList = floor.racks
        self.doors: LinkedList = floor.doors
        self.zones: LinkedList = floor.zones

        self.products: Dictionary = products
        self.pickers: LinkedList = pickers
        self.orders: LinkedList = orders
        self.orders_by_id: Dictionary = orders_by_id
        self.wave_config: WaveConfig = wave_config
        self.waves: LinkedList = LinkedList()

    def node_xy(self, node_id: int) -> tuple[int, int]:
        return node_id % self.width, node_id // self.width

    def dropoff_zones_at(self, node_id: int) -> LinkedList|None:
        if search(self.floor.dropoff, node_id) is None:
            return None
        return search(self.floor.dropoff, node_id)

        
