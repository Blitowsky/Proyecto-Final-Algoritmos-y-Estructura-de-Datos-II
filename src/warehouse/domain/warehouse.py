from warehouse.structures.linkedlist import LinkedList
from warehouse.structures.dictionary import Dictionary
from warehouse.structures.graph import WeightedDirectedGraph

from warehouse.domain.rack import Rack
from warehouse.domain.wave import WaveConfig

class WareHouse:
    def __init__(
        self, width: int, 
        height: int, 
        graph: WeightedDirectedGraph, 
        halls: Dictionary, 
        racks: Dictionary, 
        zones: LinkedList,
        products: Dictionary,
        pickers: LinkedList,
        orders: LinkedList,
        orders_by_id: Dictionary,
        wave_config: WaveConfig|None,
        waves: LinkedList
    ) -> None:
        self.width: int = width
        self.height: int = height
        self.graph: WeightedDirectedGraph = graph
        self.halls: Dictionary = halls
        self.racks: Dictionary = racks
        self.zones: LinkedList = zones
        self.products: Dictionary = products
        self.pickers: LinkedList = pickers
        self.orders: LinkedList = orders
        self.orders_by_id: Dictionary = orders_by_id
        self.wave_config: WaveConfig|None = wave_config
        self.waves: LinkedList = waves
