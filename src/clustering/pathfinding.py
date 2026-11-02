"""
El único módulo que busca por los pasillos del warehouse.
Las waves, estrategias de enrutamiento y la simulación
llaman estas funciones, nadie lo reimplementa.
"""

from warehouse.structures.graph import WeightedDirectedGraph
from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import Dictionary, search, insert, delete
from warehouse.structures.queue import Queue
from warehouse.structures.min_queue import MinQueue

from warehouse.domain.warehouse import WareHouse

from warehouse.algorithms.graph_queries import neighbors

class SearchResult:
    """Resultado de una búsqueda, más métricas de valor.

    Parámetros
    ----------
    path (`LinkedList`):
        Lista con IDs de los nodos del camino encontrado, en orden
    distance (`float`):
        Suma de pesos de las aristas en el camino encontrado.
    expanded (`int`):
        Cantidad de nodos expandidos durante la búsqueda.
    examined (`int`):
        Cantidad de nodos examinados durante la búsqueda.
    """
    def __init__(self, path: LinkedList, distance: float, expanded: int, examined: int) -> None:
        self.path: LinkedList = path
        self.nodes: int = 0
        node = path.head
        while node is not None:
            self.nodes += 1
            node = node.nextNode

        self.edges: int = self.nodes - 1
        self.distance: float = distance
        self.expanded: int = expanded
        self.examined: int = examined

    @property
    def source(self):
        return self.path.head.value if self.path.head else None

    @property
    def target(self):
        return self.path.tail.value if self.path.tail else None


def _table_size(graph: WeightedDirectedGraph) -> int:
    """Tamaño total del warehouse.

    Parámetros
    ----------
    graph (`WeightedDirectedGraph`):
        Grafo que representa los pasillos del warehouse.

    Retorna
    ----------
        Un `int` representando el ancho * alto del warehouse.
    """
    if graph.m is None:
        raise ValueError("El grafo debe estar construido con m = ancho * alto.")
    return graph.m

def _target_ids(targets: LinkedList|int) -> list[int]:
    """Convierte una `LinkedList` o `int` en una lista de objetivos.

    Parámetros
    ----------
        targets (`LinkedList`|`int`):
            Lista de objetivos, u objetivo individual.

    Retorna
    ----------
        Una lista de enteros, donde cada uno es el ID del objetivo.
    """
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
    """Guarda los objetivos como vistos en una hash table.

    Parámetros
    ----------
        ids (`list[int]`):
            Lista de objetivos.
        size (`int`):
            Tamaño del warehouse.

    Retorna
    ----------
        Un diccionario, con valores `True` con los objetivos como keys.
    """
    found = Dictionary(size)
    for target in ids:
        insert(found, True, target)
    return found

def _build_path(parent: Dictionary, source: int, last: int) -> LinkedList:
    """Convierte un diccionario de padres en una lista con el recorrido

    Parámetros
    ----------
        parent (`Dictionary`):
            Hash table con (ID nodo) -> (padre).
        source (`int`):
            ID del nodo al principio del camino.
        last (`int`):
            ID del nodo al final del camino.

    Retorna
    ----------
        LinkedList con los IDs del camino en orden.
    """
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
    """Genera un resultado de búsqueda, donde el resultado es un solo nodo.

    Parámetros
    ----------
        source (`int`):
            ID del único nodo del recorrido.

    Retorna
    ----------
        `SearchResult` con un nodo como `path`.
    """
    path = LinkedList()
    add(path, source)
    return SearchResult(path, 0, 0, 0)

def _is_blocked(blocked: Dictionary|None, node: int) -> bool:
    """Revisa si el nodo `node` está bloqueado por alguien.

    Parámetros
    ----------
        blocked (`Dictionary`|`None`):
            Hash table del warehouse donde (ID nodo) -> (`bool`)
            si está bloqueado o no.
        node (`int`):
            ID del nodo a revisar

    Retorna
    ----------
        El valor del diccionario en la posición `node`.
    """
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
                step = step.nextNode
                continue
            insert(parent, current, nxt)
            insert(cost, search(cost, current) + weight, nxt)
            nxt_cost = search(cost, nxt)
            if search(goal, nxt) is not None and nxt_cost is not None:
                return SearchResult(
                    _build_path(parent, source, nxt),
                    nxt_cost,
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
                step = step.nextNode
                continue
            insert(steps, current_steps + 1, nxt)
            queue.enqueue(nxt)
            step = step.nextNode
    return steps

def _best_first(
    graph: WeightedDirectedGraph,
    source: int,
    ids: list[int],
    heuristic,
    blocked: Dictionary|None,
    trace: LinkedList|None
) -> SearchResult|None:
    size = _table_size(graph)
    goal = _target_set(ids, size)
    if search(goal, source) is not None:
        return _single_node_result(source)

    cost = Dictionary(size)
    parent = Dictionary(size)
    closed = Dictionary(size)
    insert(cost, 0, source)

    queue = MinQueue()
    queue.push(0 if heuristic is None else heuristic(source), source)

    expanded = 0
    examined = 0

    while not queue.is_empty():
        _, current = queue.pop()
        if search(closed, current) is not None:
            continue
        insert(closed, True, current)
        expanded += 1
        if trace is not None:
            add(trace, current)

        current_cost = search(cost, current)
        if search(goal, current) is not None and current_cost is not None:
            return SearchResult(
                _build_path(parent, source, current),
                current_cost,
                expanded,
                examined
            )

        neighbor_list = neighbors(graph, current)
        step = neighbor_list.head
        while step is not None:
            if step.value is None or not isinstance(step.value, tuple):
                step = step.nextNode
                continue
            nxt, weight = step.value
            examined += 1
            if search(closed, nxt) is not None or _is_blocked(blocked, nxt):
                step = step.nextNode
                continue
            new_cost = current_cost + weight
            nxt_cost = search(cost, nxt)
            if nxt_cost is None or new_cost < nxt_cost:
                delete(cost, nxt, nxt_cost)
                insert(cost, new_cost, nxt)
                delete(parent, nxt, search(parent, nxt))
                insert(parent, current, nxt)
                queue.push(new_cost + (0 if heuristic is None else heuristic(nxt)), nxt)
            step = step.nextNode
    return None
                
def dijkstra_path(
    graph: WeightedDirectedGraph,
    source: int,
    targets: LinkedList,
    blocked: Dictionary|None = None,
    trace: LinkedList|None = None
) -> SearchResult|None:
    return _best_first(graph, source, _target_ids(targets), None, blocked, trace)

def dijkstra_distances(graph: WeightedDirectedGraph, source: int, blocked: Dictionary|None = None) -> Dictionary:
    size = _table_size(graph)
    cost = Dictionary(size)
    closed = Dictionary(size)
    insert(cost, 0, source)
    queue = MinQueue()
    queue.push(0, source)
    while not queue.is_empty():
        _, current = queue.pop()
        if search(closed, current) is not None:
            continue
        insert(closed, True, current)
        neighbor_list = neighbors(graph, current)
        step = neighbor_list.head
        while step is not None:
            if step.value is None or not isinstance(step.value, tuple):
                step = step.nextNode
                continue
            nxt, weight = step.value
            current_cost = search(cost, current)
            if search(closed, nxt) is not None or _is_blocked(blocked, nxt) or current_cost is None:
                step = step.nextNode
                continue
            new_cost = current_cost + weight
            nxt_cost = search(cost, nxt)
            if nxt_cost is None or new_cost < nxt_cost:
                delete(cost, nxt, nxt_cost)
                insert(cost, new_cost, nxt)
                queue.push(new_cost, nxt)
            step = step.nextNode
    return cost

def astar_path(
    graph: WeightedDirectedGraph,
    width: int,
    source: int,
    targets: LinkedList,
    step_cost: int = 1,
    blocked: Dictionary|None = None,
    trace: LinkedList|None = None
):
    ids = _target_ids(targets)
    goals = []
    for target in ids:
        goals.append((target % width, target // width))

    def heuristic(node):
        x = node % width
        y = node // width
        best = abs(x - goals[0][0]) + abs(y - goals[0][1])
        for i in range(1, len(goals)):
            d = abs(x - goals[i][0]) + abs(y - goals[i][1])
            if d < best:
                best = d
        return best * step_cost

    return _best_first(graph, source, ids, heuristic, blocked, trace)

def find_path(
    warehouse: WareHouse,
    source: int,
    targets: LinkedList,
    algorithm: str = "bfs",
    blocked: Dictionary|None = None,
    trace: LinkedList|None = None
) -> SearchResult|None:
    """
    Realiza la búsqueda en el grafo mediante el
    algoritmo `algorithm`, y termina en el PRIMER 
    nodo que se encuentre en los objetivos.

    Parámetros
    ----------
        graph (`WeightedDirectedGraph`):
            Grafo a recorrer.
        source (`int`):
            ID del nodo raíz.
        targets (`LinkedList`):
            Lista de objetivos a encontrar.
        blocked (`Dictionary`|`None`):
            Hash table de nodos bloqueados
            (ID nodo) -> (`bool`).
        trace (`LinkedList`|`None`):
            Lista de nodos recorridos
            (fines para renderizado).

    Retorna
    ----------
        Un resultado de búsqueda `SearchResult`
        si se encuentra un camino, `None` en
        caso contrario.
    """
    match algorithm:
        case "bfs":
            return bfs_path(warehouse.graph, source, targets, blocked, trace)
        case "dijkstra":
            return dijkstra_path(warehouse.graph, source, targets, blocked, trace)
        case "astar":
            return astar_path(warehouse.graph, warehouse.width, source, targets, 1, blocked, trace)
        case _:
            raise ValueError("Algoritmo desconocido: " + str(algorithm))
