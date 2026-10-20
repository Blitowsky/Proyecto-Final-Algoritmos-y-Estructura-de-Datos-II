from warehouse.structures.graph import WeightedDirectedGraph
from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import Dictionary, search, insert
from warehouse.structures.queue import Queue
from warehouse.structures.min_queue import MinQueue
from warehouse.algorithms.graph_queries import neighbors

class SearchResult:
    def __init__(self, path: LinkedList, distance: float, expanded, examined) -> None:
        self.path: LinkedList = path
        self.nodes: int = 0
        node = path.head
        while node is not None:
            self.nodes += 1
            node = node.nextNode

        self.edges: int = self.nodes - 1
        self.distance: float = distance
        self.expanded = expanded
        self.examined = examined

    @property
    def source(self):
        return self.path.head.value if self.path.head else None

    @property
    def target(self):
        return self.path.tail.value if self.path.tail else None


def _table_size(graph: WeightedDirectedGraph) -> int:
    if graph.m is None:
        raise ValueError("El grafo debe estar construido con m = ancho * alto.")
    return graph.m

def _target_ids(targets: LinkedList|int) -> list[int]:
    if isinstance(targets, int):
        return [targets]
    ids = []
    target = targets.head
    while target is not None:
        ids.append(target.value)
        target = target.nextNode
    if len(ids) == 0:
        raise ValueError("Una búsqueda necesita al menos un objetivo.")
    return ids

def _target_set(ids: list[int], size: int) -> Dictionary:
    found = Dictionary(size)
    for target in ids:
        insert(found, True, target)
    return found

def _build_path(parent: Dictionary, source: int, last: int) -> LinkedList:
    reversed_nodes = [last]
    node = last
    while node != source:
        node = search(parent, node)
        if node:
            reversed_nodes.append(node)
    path = LinkedList()
    for i in range(len(reversed_nodes) - 1, -1, -1):
        add(path, reversed_nodes[i])
    return path

def _single_node_result(source: int) -> SearchResult:
    path = LinkedList()
    add(path, source)
    return SearchResult(path, 0, 0, 0)

def _is_blocked(blocked: Dictionary|None, node: int) -> bool:
    return blocked is not None and search(blocked, node) is not None


def bfs_path(
    graph: WeightedDirectedGraph, 
    source: int, 
    targets: LinkedList,
    blocked: Dictionary|None = None,
    trace: LinkedList|None = None
) -> SearchResult|None:
    size = _table_size(graph)
    goal = _target_set(_target_ids(targets), size)
    if search(goal, source) is not None:
        return _single_node_result(source)

    parent = Dictionary(size)
    cost = Dictionary(size)
    insert(cost, 0, source)
    insert(parent, source)

    queue = Queue()
    queue.enqueue(source)
    expanded = 0
    examined = 0

    while not queue.is_empty():
        current = queue.dequeue()
        expanded += 1
        if trace is not None:
            add(trace, current)

        neighbor_list = neighbors(graph, current)
        step = neighbor_list.head
        while step is not None:
            if step.value is None or not isinstance(step.value, tuple):
                step = step.nextNode
                continue
            nxt, weight = step.value
            examined += 1
            if search(parent, nxt) is not None or _is_blocked(blocked, nxt):
                continue
            insert(parent, current, nxt)
            insert(cost, search(cost, current) + weight, nxt)
            nxt_goal = search(goal, nxt)
            if nxt_goal is not None:
                return SearchResult(
                    _build_path(parent, source, nxt),
                    nxt_goal,
                    expanded,
                    examined
                )
            queue.enqueue(nxt)
            step = step.nextNode
    return None

def bfs_distances(graph: WeightedDirectedGraph, source: int, blocked: Dictionary|None = None) -> Dictionary:
    size = _table_size(graph)
    steps = Dictionary(size)
    insert(steps, 0, source)
    queue = Queue()
    queue.enqueue(source)
    while not queue.is_empty():
        current = queue.dequeue()
        neighbor_list = neighbors(graph, current)
        step = neighbor_list.head
        while step is not None:
            if step.value is None or not isinstance(step, tuple):
                step = step.nextNode
                continue
            nxt = step[0]
            current_steps = search(steps, current)
            if search(steps, nxt) is not None or _is_blocked(blocked, nxt) or current_steps is None:
                continue
            insert(steps, current_steps + 1, nxt)
            queue.enqueue(nxt)
            step = step.nextNode
    return steps

