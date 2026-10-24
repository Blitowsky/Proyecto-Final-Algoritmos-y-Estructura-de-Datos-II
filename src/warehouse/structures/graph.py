from typing import Any, cast
import copy

from warehouse.structures.dictionary import *
from warehouse.structures.myqueue import *

class Graph:
    def __init__(self, v: lk.LinkedList, e: lk.LinkedList, m: int|None = None) -> None:
        self.v = v
        self.e = e
        self.m = m
        self.graph = self.createGraph()

    # Ejercicio 1
    def createGraph(self) -> CloseDictionary:
        v = self.v
        e = self.e

        len_v = self.m if self.m is not None else lk.length(v)
        graph = CloseDictionary(len_v)
        self._insert_vertices(graph)

        curr_e = e.head
        while curr_e is not None:
            v_i, v_j = cast(tuple[Any, Any], curr_e.value)

            if search(graph, v_i) is None or search(graph, v_j) is None:
                continue
            
            insert(graph, v_j, key = graph.hash_func(v_i))
            insert(graph, v_i, key = graph.hash_func(v_j))
            curr_e = curr_e.nextNode

        return graph

    def _insert_vertices(self, graph: CloseDictionary) -> None:
        curr_v = self.v.head
        while curr_v is not None:
            insert(graph, curr_v.value)
            curr_v = curr_v.nextNode

    def printGraph(self) -> None:
        d = self.graph
        for i in range(d.m):
            print(f"[{i}]", end=" ")
            current = d.dictionary[i].head
            while current is not None:
                entry = current.value
                if isinstance(entry, tuple):
                    neighbor, weight = entry
                    print(f"{neighbor}({weight})", end=" -> ")
                else:
                    print(entry, end=" -> ")
                current = current.nextNode
            print("None")


class WeightedGraph(Graph):
    def __init__(self, v: lk.LinkedList, e: lk.LinkedList) -> None:
        self.v = v
        self.e = e
        self.graph = self.createWeightedGraph()
 
    def createWeightedGraph(self) -> CloseDictionary:
        v = self.v
        e = self.e
 
        graph = CloseDictionary(lk.length(v))
        self._insert_vertices(graph)
 
        curr_e = e.head
        while curr_e is not None:
            v_i, v_j, weight = cast(tuple[Any, Any, float], curr_e.value)
            insert(graph, (v_j, weight), key = v_i)
            insert(graph, (v_i, weight), key = v_j)
            curr_e = curr_e.nextNode
 
        return graph

class WeightedDirectedGraph(Graph):
    def __init__(self, v: lk.LinkedList, e: lk.LinkedList, m: int|None = None) -> None:
        self.v = v
        self.e = e
        self.m = m
        self.graph = self.createWeightedDirectedGraph()
 
    def createWeightedDirectedGraph(self) -> CloseDictionary:
        v = self.v
        e = self.e
 
        len_v = self.m if self.m is not None else lk.length(v)
        graph = CloseDictionary(len_v)
        self._insert_vertices(graph)
 
        curr_e = e.head
        while curr_e is not None:
            v_i, v_j, weight = cast(tuple[Any, Any, float], curr_e.value)
            insert(graph, (v_j, weight), key = v_i)
            curr_e = curr_e.nextNode
 
        return graph

class DisjointSet:
    def __init__(self, v: lk.LinkedList) -> None:
        len_v = lk.length(v)
        self.parent = CloseDictionary(len_v)
        self.rank = CloseDictionary(len_v)

        curr_v = v.head
        while curr_v is not None:
            curr_v.value = int(curr_v.value) if str(curr_v.value).isdigit() else sum(ch for ch in curr_v.value) % len_v
            insert(self.parent, curr_v.value)
            insert(self.rank, 0, key = curr_v.value)
            curr_v = curr_v.nextNode

    def find_set(self, v):
        value = int(v) if str(v).isdigit() else sum(ch for ch in v) % self.parent.m
        key = self.parent.hash_func(v)
        
        if search(self.parent, value) != v:
            parent = self.parent.dictionary[key].head
            if parent is not None and isinstance(parent.value, tuple):
                parent = parent.value[1]
            self.parent.dictionary[key].head = None
            insert(self.parent, self.find_set(parent), key = value)

        return search(self.parent, value)

    def union(self, x, y):
        root_x = self.find_set(x)
        root_y = self.find_set(y)
        key_x = self.parent.hash_func(root_x)
        key_y = self.parent.hash_func(root_y)

        if root_x != root_y and root_x and root_y:
            rank_x = search(self.rank, root_x)
            rank_y = search(self.rank, root_y)
            if rank_x is not None and rank_y is not None:
                if rank_x < rank_y:
                    parent = self.parent.dictionary[key_x].head
                    if parent is not None and isinstance(parent.value, tuple):
                        parent = parent.value[1]
                    self.parent.dictionary[key_x].head = None
                    insert(self.parent, root_y, key = root_x)
                elif rank_x > rank_y:
                    parent = self.parent.dictionary[key_y].head
                    if parent is not None and isinstance(parent.value, tuple):
                        parent = parent.value[1]
                    self.parent.dictionary[key_y].head = None
                    insert(self.parent, root_x, key = root_y)
                else:
                    parent = self.parent.dictionary[key_y].head
                    if parent is not None and isinstance(parent.value, tuple):
                        parent = parent.value[1]
                    self.parent.dictionary[key_y].head = None
                    insert(self.parent, root_x, key = root_y)

                    rank = self.rank.dictionary[key_x].head
                    if rank is not None and isinstance(rank.value, tuple):
                        rank = rank.value[1]
                        self.rank.dictionary[key_y].head = None
                        insert(self.rank, rank + 1, key = root_x)

