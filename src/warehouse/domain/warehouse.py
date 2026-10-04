from warehouse.structures.linkedlist import LinkedList
from warehouse.structures.dictionary import Dictionary
from warehouse.structures.graph import WeightedDirectedGraph

from warehouse.domain.rack import Rack

class RackAccess:
    def __init__(self, rack: Rack, left: bool, right: bool) -> None:
        self.rack: Rack = rack
        self.left: bool = left
        self.right: bool = right

class HallNode:
    def __init__(self, node_id: int, x: int, y: int) -> None:
        self.id: int = node_id
        self.x: int = x
        self.y: int = y
        self.rack_access: LinkedList = LinkedList()

class WareHouse:
    def __init__(self, width: int, height: int, graph: WeightedDirectedGraph, halls: Dictionary, racks: Dictionary) -> None:
        self.width: int = width
        self.height: int = height
        self.graph: WeightedDirectedGraph = graph
        self.halls: Dictionary = halls
        self.racks: Dictionary = racks
