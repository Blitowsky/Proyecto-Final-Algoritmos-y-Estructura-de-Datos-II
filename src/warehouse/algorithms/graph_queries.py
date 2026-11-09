from warehouse.structures.graph import WeightedDirectedGraph
from warehouse.structures.linkedlist import LinkedList, add

def neighbors(graph: WeightedDirectedGraph, vertex: int) -> LinkedList:
    """Nodos conectados a `vertex` a través de una arista.

    Parámetros
    ----------
    graph (`WeightedDirectedGraph`):
        Grafo sobre el cual se está trabjando.
    vertex (`int`):
        ID del vértice del que se quieren saber los vecinos.

    Retorna
    ----------
    LinkedList con IDs de los nodos vecinos.
    """
    table = graph.graph
    bucket = table.dictionary[table.hash_func(vertex)]
    result = LinkedList()
    node = bucket.head
    while node is not None:
        if node.value is None:
            node = node.nextNode
            continue
        key, value = node.value
        if key == vertex and isinstance(value, tuple):
            add(result, value)
        node = node.nextNode
    return result
