"""
Generación de waves a partir de las K zonas obtenidas por Clustering Espectral.

Reglas de negocio implementadas:
1. Al momento del recorrido se consideran únicamente los productos demandados
   (con sus cantidades acumuladas sobre los pedidos PENDIENTES), sin acoplar
   el armado de la wave a pedidos indivisibles. El avance de los pedidos se
   releva dinámicamente al momento de la entrega en las zonas de despacho.
2. Dentro de cada zona espectral, los productos se ponderan por prioridad y
   cercanía al centroide de la zona (lógica de centroides), y cada picker toma
   un subconjunto compacto de productos cercanos a su semilla (`muestra`).
3. Al finalizar una zona:
   - Caso 1: Si los productos restantes cubren exactamente la capacidad de los
     pickers disponibles en la wave actual, se cierra la wave completa y la
     siguiente zona comienza en una nueva wave con todos los pickers libres.
   - Caso 2: Si el peso restante de la zona es menor que la capacidad libre de
     la wave, se cubre con los pickers disponibles de mayor capacidad. A lo
     sumo UN único picker (el último usado en la zona si le quedó capacidad
     remanente) puede compartir su recorrido con la primera wave de la zona
     siguiente, y el resto de pickers libres pasan directamente a cubrir esa
     siguiente zona dentro de la misma wave.
"""

import math

from warehouse.algorithms.stop_ordering import order_node_groups_directed, order_stops_directed
from warehouse.domain.picker import Picker
from warehouse.domain.product import Product
from warehouse.domain.route import PickLine
from warehouse.domain.warehouse import WareHouse
from warehouse.domain.wave import Wave
from warehouse.structures.linkedlist import LinkedList, add

EPS = 1e-9


class _ProductDemand:
    """Demanda pendiente acumulada de un único `Product`."""

    def __init__(self, product: Product, qty: int, priority: int) -> None:
        self.product: Product = product
        self.qty: int = qty
        self.priority: int = priority
        self.score: float = 0.0

    @property
    def coord(self) -> tuple[float, float]:
        return (float(self.product.x), float(self.product.y))

    @property
    def remaining_weight(self) -> float:
        return self.product.weight * self.qty


class SpectralWaveSelector:
    """Estrategia compatible con `WaveBuilder` (`generate_waves()`) que conecta
    las zonas de `clustering.spectral` con la generación de waves por capacidad
    de pickers.
    """

    def __init__(
        self,
        warehouse: WareHouse,
        spectral_zones: list,
        pickers: LinkedList | None = None,
        id_prefix: str = "W",
        verbose: bool = True,
    ) -> None:
        self.warehouse: WareHouse = warehouse
        self.spectral_zones: list = spectral_zones
        self.pickers_ll: LinkedList = warehouse.pickers if pickers is None else pickers
        self.id_prefix: str = id_prefix
        self.verbose: bool = verbose

    # ------------------------------------------------------------------
    # Punto de entrada invocado por WaveBuilder.build()
    # ------------------------------------------------------------------
    def generate_waves(self) -> LinkedList:
        waves = LinkedList()
        demands_by_pid, pending_orders = self._extract_product_demands()
        if not demands_by_pid:
            return waves

        all_pickers = self._sorted_pickers()
        if not all_pickers:
            raise ValueError("No hay pickers configurados en el warehouse para generar waves.")

        max_picker_cap = all_pickers[0].capacity
        for demand in demands_by_pid.values():
            if demand.product.weight > max_picker_cap + EPS:
                raise ValueError(
                    f"Una unidad del producto {demand.product.id} ({demand.product.weight}kg) "
                    f"supera la capacidad máxima de cualquier picker ({max_picker_cap}kg)."
                )

        # Marcamos los pedidos pendientes como incorporados al flujo de waves (EN_WAVE).
        # Su paso a EN_PREPARACION / PREPARADO ocurre al entregar productos en despacho.
        for order in pending_orders:
            order.assign_to(None)

        ordered_zones = self._build_and_order_zones(demands_by_pid)
        if not ordered_zones:
            return waves

        wave_counter = 0
        round_counter = 0
        free_pool: list[Picker] = list(all_pickers)
        completed_shares: list[tuple[Picker, list[PickLine], list[int]]] = []
        # boundary_picker: (picker, shares, remaining_cap, [zone_idx])
        boundary_picker: tuple[Picker, list[PickLine], float, list[int]] | None = None
        wave_summaries_log: list[tuple[int, list[tuple[Wave, Picker, list[PickLine], list[int]]]]] = []

        def flush_current_wave() -> None:
            nonlocal wave_counter, round_counter, free_pool, completed_shares, boundary_picker
            if boundary_picker is not None:
                b_p, b_s, _, b_z = boundary_picker
                if b_s:
                    completed_shares.append((b_p, b_s, b_z))
                boundary_picker = None
            if not completed_shares:
                free_pool = list(all_pickers)
                return
            round_counter += 1
            round_entries: list[tuple[Wave, Picker, list[PickLine], list[int]]] = []
            # Emitimos una Wave independiente por picker para que al terminar su recorrido
            # pueda tomar la siguiente wave disponible sin esperar al resto de los pickers.
            for picker, shares, zones_touched in completed_shares:
                wave_counter += 1
                wave = self._create_wave(
                    f"{self.id_prefix}{wave_counter}",
                    [(picker, shares, zones_touched)],
                    demands_by_pid,
                )
                add(waves, wave)
                round_entries.append((wave, picker, shares, zones_touched))
            wave_summaries_log.append((round_counter, round_entries))
            free_pool = list(all_pickers)
            completed_shares = []

        for zone_number, zone_items in ordered_zones:
            self._weight_and_sort_zone(zone_items)

            # 1) Si quedó UN picker con capacidad remanente de la zona anterior,
            #    completa su carga con los productos más cercanos de esta zona
            #    (a lo sumo 2 zonas distintas para ese único picker).
            if boundary_picker is not None and zone_items:
                b_picker, b_shares, b_rem, b_zones = boundary_picker
                boundary_picker = None
                last_prod = b_shares[-1].product
                ref_xy = (float(last_prod.x), float(last_prod.y))

                extra_shares, _ = self._pack_into_picker(zone_items, b_rem, seed_xy=ref_xy)
                if extra_shares:
                    extra_shares = self._chain_shares_from(extra_shares, ref_xy)
                    b_shares.extend(extra_shares)
                    b_zones.append(zone_number)

                completed_shares.append((b_picker, b_shares, b_zones))
                if not free_pool:
                    flush_current_wave()

            # 2) Cubrimos los productos restantes de la zona actual
            while zone_items:
                if not free_pool:
                    flush_current_wave()

                peso_restante = sum(it.remaining_weight for it in zone_items)
                cap_libre_wave = sum(p.capacity for p in free_pool)

                # Caso 1 (o zona que excede una wave completa):
                # Los productos restantes alcanzan para llenar todos los pickers libres de la wave.
                if peso_restante >= cap_libre_wave - EPS:
                    progressed = False
                    while free_pool and zone_items:
                        picker = free_pool.pop(0)
                        shares, _ = self._pack_into_picker(zone_items, picker.capacity)
                        if shares:
                            shares = self._chain_shares(shares)
                            completed_shares.append((picker, shares, [zone_number]))
                            progressed = True
                    flush_current_wave()
                    if not progressed:
                        break
                else:
                    # Caso 2: La zona tiene menos carga que la capacidad libre de la wave.
                    # Se busca cubrir con los pickers de mayor capacidad disponibles y
                    # dejar los restantes libres para la primera wave de la siguiente zona.
                    progressed = False
                    while zone_items and free_pool:
                        picker = free_pool.pop(0)
                        shares, rem_cap = self._pack_into_picker(zone_items, picker.capacity)
                        if not shares:
                            # Ninguna unidad restante entra en este picker menor; cerramos
                            # la wave actual para reintentar con el pool completo.
                            flush_current_wave()
                            break
                        progressed = True
                        shares = self._chain_shares(shares)

                        if not zone_items:
                            # Se cubrió todo el excedente de la zona en este picker.
                            if rem_cap > EPS:
                                boundary_picker = (picker, shares, rem_cap, [zone_number])
                            else:
                                completed_shares.append((picker, shares, [zone_number]))
                                if not free_pool:
                                    flush_current_wave()
                        else:
                            completed_shares.append((picker, shares, [zone_number]))
                            if not free_pool:
                                flush_current_wave()

                    if zone_items and not progressed:
                        flush_current_wave()

        # Cerramos la última wave abierta si tiene asignaciones pendientes
        if boundary_picker is not None or completed_shares:
            flush_current_wave()

        if self.verbose:
            self._print_summary(ordered_zones, wave_summaries_log)

        return waves

    # ------------------------------------------------------------------
    # Extracción de demanda y armado de zonas
    # ------------------------------------------------------------------
    def _extract_product_demands(self) -> tuple[dict[str, _ProductDemand], list]:
        demands: dict[str, _ProductDemand] = {}
        pending_orders = []

        o_node = self.warehouse.orders.head
        while o_node is not None:
            order = o_node.value
            if order is not None and order.state == "PENDIENTE":
                pending_orders.append(order)
                l_node = order.lines.head
                while l_node is not None:
                    line = l_node.value
                    if line is not None and line.product is not None:
                        pid = line.product.id
                        if pid in demands:
                            demands[pid].qty += line.qty
                            if order.priority > demands[pid].priority:
                                demands[pid].priority = order.priority
                        else:
                            demands[pid] = _ProductDemand(line.product, line.qty, order.priority)
                    l_node = l_node.nextNode
            o_node = o_node.nextNode

        return demands, pending_orders

    def _sorted_pickers(self) -> list[Picker]:
        pickers: list[Picker] = []
        p_node = self.pickers_ll.head
        while p_node is not None:
            if p_node.value is not None:
                pickers.append(p_node.value)
            p_node = p_node.nextNode
        pickers.sort(key=lambda p: (-p.capacity, str(p.id)))
        return pickers

    def _build_and_order_zones(
        self, demands_by_pid: dict[str, _ProductDemand]
    ) -> list[tuple[int, list[_ProductDemand]]]:
        # Soporte tanto para list[list[Product]] como list[list[tuple[int, int]]]
        by_coord: dict[tuple[int, int], list[_ProductDemand]] = {}
        for d in demands_by_pid.values():
            by_coord.setdefault((d.product.x, d.product.y), []).append(d)

        seen_pids: set[str] = set()
        raw_zones: list[tuple[int, list[_ProductDemand]]] = []

        for idx, z_entries in enumerate(self.spectral_zones, start=1):
            bucket: list[_ProductDemand] = []
            for entry in z_entries:
                if isinstance(entry, Product):
                    d = demands_by_pid.get(entry.id)
                    if d is not None and d.product.id not in seen_pids:
                        seen_pids.add(d.product.id)
                        bucket.append(d)
                elif isinstance(entry, tuple) and len(entry) >= 2:
                    coord = (int(entry[0]), int(entry[1]))
                    for d in by_coord.get(coord, []):
                        if d.product.id not in seen_pids:
                            seen_pids.add(d.product.id)
                            bucket.append(d)
            if bucket:
                raw_zones.append((idx, bucket))

        # Respaldo por si algún producto pendiente no figuraba en spectral_zones
        missing = [d for pid, d in demands_by_pid.items() if pid not in seen_pids]
        if missing:
            if not raw_zones:
                raw_zones.append((1, missing))
            else:
                for d in missing:
                    best_zone = min(
                        raw_zones,
                        key=lambda zb: math.dist(d.coord, self._zone_centroid(zb[1]))
                    )
                    best_zone[1].append(d)

        if len(raw_zones) <= 1:
            return raw_zones

        # Encadenamos las zonas por cercanía de centroides comenzando por la de mayor prioridad
        remaining = list(raw_zones)
        remaining.sort(
            key=lambda zb: (
                -max(it.priority for it in zb[1]),
                -sum(it.remaining_weight for it in zb[1]),
                zb[0],
            )
        )
        ordered = [remaining.pop(0)]
        while remaining:
            last_centroid = self._zone_centroid(ordered[-1][1])
            nxt = min(
                remaining,
                key=lambda zb: (math.dist(last_centroid, self._zone_centroid(zb[1])), zb[0])
            )
            remaining.remove(nxt)
            ordered.append(nxt)

        return ordered

    # ------------------------------------------------------------------
    # Lógica de centroides y empaquetado espacial por picker
    # ------------------------------------------------------------------
    @staticmethod
    def _zone_centroid(items: list[_ProductDemand]) -> tuple[float, float]:
        sx = sum(it.product.x for it in items)
        sy = sum(it.product.y for it in items)
        n = len(items)
        return (sx / n, sy / n)

    @staticmethod
    def _ponderar(prioridad: int, val_normalizado: float) -> float:
        return 0.7 * prioridad + 0.3 * (1.0 - val_normalizado)

    def _weight_and_sort_zone(self, items: list[_ProductDemand]) -> None:
        if not items:
            return
        cx, cy = self._zone_centroid(items)
        dists = [abs(it.product.x - cx) + abs(it.product.y - cy) for it in items]
        d_min = min(dists)
        d_max = max(dists)

        for it, d in zip(items, dists):
            if d_max == 0:
                norm = 0.0
            elif d_min == d_max:
                norm = 0.5
            else:
                norm = (d - d_min) / (d_max - d_min)
            it.score = self._ponderar(it.priority, norm)

        items.sort(key=lambda it: (-it.score, str(it.product.id)))

    def _pack_into_picker(
        self,
        zone_items: list[_ProductDemand],
        capacity: float,
        seed_xy: tuple[float, float] | None = None,
    ) -> tuple[list[PickLine], float]:
        """Selecciona productos cercanos a `seed_xy` (o al primer producto
        ponderado `muestra` de la zona) hasta cubrir `capacity`."""
        rem_cap = capacity
        shares: list[PickLine] = []

        if not zone_items or rem_cap <= EPS:
            return shares, rem_cap

        if seed_xy is None:
            # Elegimos como semilla el primer producto mejor ponderado que quepa (al menos 1 unidad)
            seed_item = None
            for it in zone_items:
                if it.product.weight <= rem_cap + EPS:
                    seed_item = it
                    break
            if seed_item is None:
                return shares, rem_cap
            ref_xy = seed_item.coord
        else:
            ref_xy = seed_xy

        # Ordenamos candidatos por cercanía euclidiana a la referencia (_listaPedMinimo)
        candidates = sorted(
            zone_items,
            key=lambda it: (math.dist(ref_xy, it.coord), -it.score, str(it.product.id))
        )

        for item in candidates:
            if rem_cap <= EPS:
                break
            unit_w = item.product.weight
            max_units = int((rem_cap + EPS) // unit_w)
            take = min(item.qty, max_units)
            if take > 0:
                shares.append(PickLine(item.product, take))
                rem_cap -= take * unit_w
                item.qty -= take

        # Limpiamos productos cuya cantidad pendiente llegó a 0
        zone_items[:] = [it for it in zone_items if it.qty > 0]
        return shares, max(0.0, rem_cap)

    @staticmethod
    def _chain_shares(shares: list[PickLine]) -> list[PickLine]:
        if len(shares) <= 2:
            return shares
        start = shares[0]
        return SpectralWaveSelector._chain_shares_from(shares, (float(start.product.x), float(start.product.y)))

    @staticmethod
    def _chain_shares_from(
        shares: list[PickLine], start_xy: tuple[float, float]
    ) -> list[PickLine]:
        if len(shares) <= 1:
            return shares
        pending = list(shares)
        ordered: list[PickLine] = []
        curr_xy = start_xy
        while pending:
            nxt = min(
                pending,
                key=lambda pl: (
                    math.dist(curr_xy, (float(pl.product.x), float(pl.product.y))),
                    str(pl.product.id),
                ),
            )
            pending.remove(nxt)
            ordered.append(nxt)
            curr_xy = (float(nxt.product.x), float(nxt.product.y))
        return ordered

    def order_stops(self, warehouse: WareHouse, start: int, stops: LinkedList, zone) -> LinkedList:
        """Hook invocado por `start_assignment` para optimizar el orden de
        paradas usando distancias dirigidas reales sobre el grafo del almacén."""
        return order_stops_directed(warehouse, start, stops, zone)

    def _create_wave(
        self,
        wave_id: str,
        completed_shares: list[tuple[Picker, list[PickLine], list[int]]],
        demands_by_pid: dict[str, _ProductDemand],
    ) -> Wave:
        wave = Wave(wave_id, self.warehouse.wave_config)
        planned_shares: list[tuple[Picker, list[PickLine]]] = []

        for picker, shares, _ in completed_shares:
            ordered_shares = self._order_shares_directed(shares)
            planned_shares.append((picker, ordered_shares))
            for pl in ordered_shares:
                prio = demands_by_pid[pl.product.id].priority if pl.product.id in demands_by_pid else 1
                wave.add_product_line(pl.product, pl.qty, priority=prio)

        wave.planned_shares = planned_shares
        return wave

    def _order_shares_directed(self, shares: list[PickLine]) -> list[PickLine]:
        """Ordena las líneas de picking usando distancias dirigidas reales del grafo
        desde la zona de despacho OUTBOUND más cercana."""
        if len(shares) <= 1:
            return shares

        sx = sum(pl.product.x for pl in shares) / len(shares)
        sy = sum(pl.product.y for pl in shares) / len(shares)

        best_access: list[int] = []
        best_dist = math.inf
        z_node = self.warehouse.zones.head
        while z_node is not None:
            zone = z_node.value
            if zone is not None and zone.is_outbound:
                cells: list[int] = []
                acc = zone.access.head
                while acc is not None:
                    if acc.value is not None:
                        cells.append(acc.value)
                        zx, zy = self.warehouse.node_xy(acc.value)
                        d = math.dist((sx, sy), (zx, zy))
                        if d < best_dist:
                            best_dist = d
                    acc = acc.nextNode
                if cells and best_access == []:
                    best_access = cells
                elif cells:
                    zx0, zy0 = self.warehouse.node_xy(cells[0])
                    bx0, by0 = self.warehouse.node_xy(best_access[0])
                    if math.dist((sx, sy), (zx0, zy0)) < math.dist((sx, sy), (bx0, by0)):
                        best_access = cells
            z_node = z_node.nextNode

        if not best_access:
            return shares

        stop_cell_lists: list[list[int]] = []
        for pl in shares:
            p_cells: list[int] = []
            c_node = pl.product.pick_cells.head if pl.product.pick_cells else None
            while c_node is not None:
                if c_node.value is not None:
                    p_cells.append(c_node.value)
                c_node = c_node.nextNode
            if not p_cells:
                return shares
            stop_cell_lists.append(p_cells)

        perm = order_node_groups_directed(
            self.warehouse,
            best_access[0],
            stop_cell_lists,
            best_access,
        )
        return [shares[i] for i in perm]

    @staticmethod
    def _print_summary(
        ordered_zones: list[tuple[int, list[_ProductDemand]]],
        wave_summaries_log: list[tuple[int, list[tuple[Wave, Picker, list[PickLine], list[int]]]]],
    ) -> None:
        total_waves = sum(len(entries) for _, entries in wave_summaries_log)
        print("=" * 70)
        print(
            f" GENERACIÓN DE WAVES POR ZONAS ESPECTRALES "
            f"({total_waves} waves independientes en {len(wave_summaries_log)} rondas)"
        )
        print("=" * 70)
        for round_num, picker_entries in wave_summaries_log:
            round_weight = sum(w.total_weight for w, _, _, _ in picker_entries)
            round_units = sum(w.total_units for w, _, _, _ in picker_entries)
            print(
                f"  • Ronda {round_num} | Peso total: {round_weight:.2f}kg | "
                f"Unidades: {round_units} | Pickers asignados: {len(picker_entries)}"
            )
            for wave, picker, shares, zones_touched in picker_entries:
                w_picker = sum(s.product.weight * s.qty for s in shares)
                units_picker = sum(s.qty for s in shares)
                zonas_str = " + ".join(f"Zona {z}" for z in zones_touched)
                shared_tag = " [COMPARTIDO ENTRE 2 ZONAS]" if len(zones_touched) > 1 else ""
                print(
                    f"      - Wave {wave.id} -> {picker.id} (cap {picker.capacity:.1f}kg): "
                    f"{w_picker:.2f}kg ({units_picker} u., {len(shares)} prods) -> {zonas_str}{shared_tag}"
                )
        print("=" * 70)

