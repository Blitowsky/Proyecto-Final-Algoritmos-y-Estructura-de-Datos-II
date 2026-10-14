from warehouse.structures.linkedlist import LinkedList
from warehouse.structures.dictionary import Dictionary, search
from warehouse.structures.graph import WeightedDirectedGraph

from warehouse.domain.rack import Rack
from warehouse.domain.wave import WaveConfig
from warehouse.domain.cell import Cell

class WareHouse:
    def __init__(
        self, width: int, 
        height: int, 
        rack_count: int,
        door_count: int,
        zone_count: int,
        section_count: int,
        # products: Dictionary,
        # pickers: LinkedList,
        # orders: LinkedList,
        # orders_by_id: Dictionary,
        # wave_config: WaveConfig|None,
        # waves: LinkedList
    ) -> None:
        self.width: int = width
        self.height: int = height
        # self.graph: WeightedDirectedGraph = graph

        self.grid: Dictionary = Dictionary(width * height)
        self.hall_count: int = 0
        # self.halls: Dictionary = halls
        # self.zones: LinkedList = zones
        # self.racks: LinkedList = racks
        self.racks: LinkedList = LinkedList()
        self.racks_by_id: Dictionary = Dictionary(2 * rack_count + 1)
        self.doors: LinkedList = LinkedList()
        self.doors_by_id = Dictionary(2 * door_count + 1)
        self.zones = LinkedList()
        self.zones_by_id = Dictionary(2 * zone_count + 1)
        self.sections = LinkedList()
        self.sections_by_id = Dictionary(2 * section_count + 1)
        #
        # self.products: Dictionary = products
        # self.pickers: LinkedList = pickers
        # self.orders: LinkedList = orders
        # self.orders_by_id: Dictionary = orders_by_id
        # self.wave_config: WaveConfig|None = wave_config
        # self.waves: LinkedList = waves

    def cell_id(self, x: int, y: int) -> int:
        return y * self.width + x

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def cell_at(self, x: int, y: int) -> Cell|None:
        if not self.in_bounds(x, y):
            return None
        return search(self.grid, self.cell_id(x, y))
