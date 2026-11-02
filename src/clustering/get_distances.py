import warehouse.structures.linkedlist
import warehouse.structures.graph
import math 


def bfs_distances_targeted(graph: WeightedDirectedGraph, source: int, targets: LinkedList, blocked: Dictionary|None = None) -> Dictionary:
    size = _table_size(graph)
    # Convertimos la LinkedList de targets a una estructura Hash para búsquedas en O(1)
    goal = _target_set(_target_ids(targets), size)
    
    steps = Dictionary(size)
    insert(steps, 0, source)
    
    queue = Queue()
    queue.enqueue(source)
    
    # Llevamos la cuenta de cuántos objetivos hemos encontrado para poder cortar antes
    found_count = 0
    total_targets = _count_elements(targets) # Asumiendo una función auxiliar que cuente los nodos
    
    # Diccionario exclusivo para retornar solo los resultados de los objetivos
    target_distances = Dictionary(size)

    # Si el origen es un objetivo, lo registramos inmediatamente
    if search(goal, source) is not None:
        insert(target_distances, 0, source)
        found_count += 1

    while not queue.is_empty() and found_count < total_targets:
        current = queue.dequeue()
        neighbor_list = neighbors(graph, current)
        step = neighbor_list.head
        
        while step is not None:
            if step.value is None or not isinstance(step.value, tuple):
                step = step.nextNode
                continue
            
            nxt = step.value[0]
            current_steps = search(steps, current)
            
            if search(steps, nxt) is not None or _is_blocked(blocked, nxt) or current_steps is None:
                step = step.nextNode
                continue
            
            new_distance = current_steps + 1
            insert(steps, new_distance, nxt)
            
            # Si el vecino es uno de los objetivos, guardamos su distancia en el diccionario de retorno
            if search(goal, nxt) is not None:
                insert(target_distances, new_distance, nxt)
                found_count += 1
                
                # Si ya encontramos todos, podemos romper el bucle interno
                if found_count >= total_targets:
                    break
                    
            queue.enqueue(nxt)
            step = step.nextNode
            
    return target_distances


def topologicall_distance(graph: WeightedDirectedGraph, source: int, targets: LinkedList):

    return bfs_distances_targeted(graph,source,targets, None)

import math

def calcular_distancia_euclidiana(producto_a, producto_b) -> float:
    """
    Calcula la distancia euclidiana entre dos productos
    basándose en sus coordenadas (x, y) en el plano del Warehouse.
    """
    # Se extraen las coordenadas de los atributos dados
    x1 = producto_a.x
    y1 = producto_a.y
    x2 = producto_b.x
    y2 = producto_b.y
    
    # Se aplica la fórmula matemática euclidiana y se calcula la raíz cuadrada
    distancia = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    return distancia

    