"""
Ordenamiento dirigido de paradas sobre el grafo de pasillos (`warehouse.graph`).

Minimiza el recorrido real (respetando pasillos unidireccionales y múltiples
celdas de acceso por parada) mediante:
1. Cálculo exacto de distancias dirigidas con `bfs_distances_targeted`.
2. Construcción inicial por vecino más cercano dirigido.
3. Refinamiento local (Or-opt de 1 y 2 paradas + intercambios) evaluando el
   costo exacto de ruta desde la entrada en zona hasta el retorno a despacho.
"""

from warehouse.algorithms.pathfinding import bfs_distances_targeted, find_path
from warehouse.domain.location import DispatchZone
from warehouse.domain.warehouse import WareHouse
from warehouse.structures.dictionary import search
from warehouse.structures.linkedlist import LinkedList, add

INF_DIST = 1e9


def _collect_ll(ll: LinkedList | None) -> list[int]:
    out: list[int] = []
    if ll is None:
        return out
    node = ll.head
    while node is not None:
        if node.value is not None:
            out.append(node.value)
        node = node.nextNode
    return out


def order_node_groups_directed(
    warehouse: WareHouse,
    start_node: int,
    stop_cell_lists: list[list[int]],
    return_cells: list[int] | None = None,
) -> list[int]:
    """Retorna la permutación de índices `[0..m-1]` que minimiza la distancia
    dirigida total `start_node -> stop[p_0] -> ... -> stop[p_{m-1}] -> return_cells`.
    """
    m = len(stop_cell_lists)
    if m <= 1:
        return list(range(m))

    ret_nodes = return_cells if return_cells else [start_node]

    unique_nodes: list[int] = []
    seen: set[int] = set()
    for cid in [start_node, *ret_nodes]:
        if cid not in seen:
            seen.add(cid)
            unique_nodes.append(cid)
    for cells in stop_cell_lists:
        for cid in cells:
            if cid not in seen:
                seen.add(cid)
                unique_nodes.append(cid)

    targets_ll = LinkedList()
    for cid in unique_nodes:
        add(targets_ll, cid)

    dist_maps = {}
    for u in unique_nodes:
        dist_maps[u] = bfs_distances_targeted(warehouse.graph, u, targets_ll)

    pair_dist: dict[int, dict[int, float]] = {}
    for u in unique_nodes:
        row: dict[int, float] = {}
        d_map = dist_maps[u]
        for v in unique_nodes:
            if u == v:
                row[v] = 0.0
            else:
                d = search(d_map, v)
                row[v] = float(d) if d is not None else INF_DIST
        pair_dist[u] = row

    def route_cost(seq: list[int]) -> float:
        curr = start_node
        total = 0.0
        for idx in seq:
            cells = stop_cell_lists[idx]
            row = pair_dist[curr]
            best_c = cells[0]
            best_d = row[best_c]
            for c in cells[1:]:
                d = row[c]
                if d < best_d:
                    best_d = d
                    best_c = c
            total += best_d
            curr = best_c
        row = pair_dist[curr]
        total += min(row[r] for r in ret_nodes)
        return total

    # Fase 1: Vecino más cercano dirigido
    unvisited = list(range(m))
    seq: list[int] = []
    curr = start_node
    while unvisited:
        row = pair_dist[curr]
        best_idx = unvisited[0]
        best_c = stop_cell_lists[best_idx][0]
        best_d = row[best_c]
        for idx in unvisited:
            for c in stop_cell_lists[idx]:
                d = row[c]
                if d < best_d:
                    best_d = d
                    best_c = c
                    best_idx = idx
        unvisited.remove(best_idx)
        seq.append(best_idx)
        curr = best_c

    # Fase 2: Búsqueda local dirigida (Or-opt de longitud 1 y 2 + swap)
    best_cost = route_cost(seq)
    improved = True
    passes = 0
    while improved and passes < 50:
        improved = False
        passes += 1

        # Or-opt: mover bloque de 1 o 2 paradas a otra posición
        for block_len in (1, 2):
            if m <= block_len:
                continue
            for i in range(m - block_len + 1):
                block = seq[i : i + block_len]
                rest = seq[:i] + seq[i + block_len :]
                for j in range(len(rest) + 1):
                    if j == i:
                        continue
                    cand = rest[:j] + block + rest[j:]
                    c_cost = route_cost(cand)
                    if c_cost < best_cost - 1e-9:
                        seq = cand
                        best_cost = c_cost
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break

        if improved:
            continue

        # Intercambios entre pares de paradas
        for i in range(m):
            for j in range(i + 1, m):
                cand = list(seq)
                cand[i], cand[j] = cand[j], cand[i]
                c_cost = route_cost(cand)
                if c_cost < best_cost - 1e-9:
                    seq = cand
                    best_cost = c_cost
                    improved = True
                    break
            if improved:
                break

    return seq


def order_stops_directed(
    warehouse: WareHouse,
    start: int,
    stops: LinkedList,
    zone: DispatchZone,
    algorithm: str = "bfs",
) -> LinkedList:
    """Ordena una `LinkedList` de `Stop`s minimizando la distancia dirigida real
    en `warehouse.graph` considerando el punto de partida y regreso a `zone`."""
    stop_list = []
    node = stops.head
    while node is not None:
        if node.value is not None:
            stop_list.append(node.value)
        node = node.nextNode

    if len(stop_list) <= 1:
        ordered = LinkedList()
        for s in stop_list:
            add(ordered, s)
        return ordered

    # plan_route primero camina a zone.access si start todavía no está junto a la zona
    begin = start
    approach = find_path(warehouse, start, zone.access, algorithm)
    if approach is not None and approach.target is not None:
        begin = approach.target

    stop_cell_lists = [_collect_ll(s.cells) for s in stop_list]
    ret_cells = _collect_ll(zone.access)

    perm = order_node_groups_directed(warehouse, begin, stop_cell_lists, ret_cells)
    ordered = LinkedList()
    for idx in perm:
        add(ordered, stop_list[idx])
    return ordered

