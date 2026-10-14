from warehouse.structures.linkedlist import LinkedList, add, length
from warehouse.structures.dictionary import Dictionary, search, insert
from warehouse.structures.graph import WeightedDirectedGraph

from warehouse.domain.warehouse import Floor, WareHouse
from warehouse.domain.location import DispatchZone
from warehouse.domain.rack import Rack
from warehouse.domain.product import Product
from warehouse.domain.picker import Picker
from warehouse.domain.wave import Order, Wave, WaveConfig
from warehouse.domain.rect import Rect
from warehouse.domain.cell import DOOR, HALL, RACK, ZONE, Cell
from warehouse.domain.direction import MOVES, step

from warehouse.services.hall_graph_builder import build_hall_graph
from warehouse.services.rack_cell_builder import build_rack_cells
from warehouse.services.order_service import add_orders
from warehouse.services.product_loader import load_products

from warehouse.persistence.scenario_loader import (
    read_dimensions, read_point, read_door, read_zone, read_rack, read_hall_section,
    require_keys, require_id, require_positive_number)

def build_floor(config: dict) -> Floor:
    wh = config["warehouse"]
    width, height = read_dimensions(wh)

    racks_raw = wh.get("racks", [])
    doors_raw = wh.get("puertas", [])
    zones_raw = wh.get("zonas_despacho", [])
    sections_raw = wh.get("pasillos", [])

    if len(doors_raw) == 0:
        raise ValueError("El warehouse debe tener al menos una puerta.")
    if len(zones_raw) == 0:
        raise ValueError("El warehouse necesita al menos una zona de despacho.")

    floor = Floor(
        width, 
        height, 
        len(racks_raw), 
        len(doors_raw), 
        len(zones_raw), 
        len(sections_raw)
    )

    place_racks(floor, racks_raw)
    place_doors(floor, doors_raw)
    place_zones(floor, zones_raw)
    place_hall_sections(floor, sections_raw)
    fill_undeclared_halls(floor)
    check_every_door_has_a_zone(floor)

    return floor

def build_warehouse(config: dict) -> WareHouse:
    floor = build_floor(config)
    graph = build_hall_graph(floor)
    build_rack_cells(floor)
    build_dropoff_cells(floor)

    products = load_products(config, floor)
    pickers = load_pickers(config, floor)
    orders, orders_by_id = add_orders(config, products)
    wave_config = add_wave_config(config)

    return WareHouse(
        floor,
        graph,
        products,
        pickers,
        orders,
        orders_by_id,
        wave_config
    )


def add_unique(items: LinkedList, by_id: Dictionary, item, label: str) -> None:
    if search(by_id, item.id) is not None:
        raise ValueError(f"{label} aparece dos veces.")
    insert(by_id, item, item.id)
    add(items, item)

def stamp(floor: Floor, rect: Rect, label: str, kind: str, owner) -> None:
    if not rect.inside(floor.width, floor.height):
        raise ValueError(f"{label} está fuera del warehouse ({floor.width} x {floor.height})")
    for y in range(rect.y, rect.y2 + 1):
        for x in range(rect.x, rect.x2 + 1):
            cid = floor.cell_id(x, y)
            current = search(floor.grid, cid)
            if current is not None:
                raise ValueError(f"{label} se superpone con: {current.label()} en ({x}, {y}).")
            insert(floor.grid, Cell(kind, owner), cid)
            if kind == HALL:
                floor.hall_count += 1

def place_racks(floor: Floor, racks_raw: dict) -> None:
    for i in range(len(racks_raw)):
        rack = read_rack(racks_raw[i], i)
        label = "El rack " + rack.id
        add_unique(floor.racks, floor.racks_by_id, rack, label)
        if rack.rect.width != 2 and rack.rect.height != 2:
            raise ValueError(f"{label} necesita una dimension igual a 2 ({rack.rect.width}, {rack.rect.height})")
        stamp(floor, rack.rect, label, RACK, rack)

def place_doors(floor: Floor, doors_raw: dict) -> None:
    for i in range(len(doors_raw)):
        door = read_door(doors_raw[i], i)
        label = "La puerta " + door.id
        add_unique(floor.doors, floor.doors_by_id, door, label)
        if not floor.in_bounds(door.x, door.y):
            raise ValueError(f"{label} está fuera del warehouse.")
        on_border = (door.x == 0 or door.x == floor.width - 1
                     or door.y == 0 or door.y == floor.height - 1)
        if not on_border:
            raise ValueError(f"{label} en ({door.x}, {door.y}) no está en el borde del warehouse.")
        stamp(floor, Rect(door.x, door.y, 1, 1), label, DOOR, door)

def place_zones(floor: Floor, zones_raw: dict) -> None:
    for i in range(len(zones_raw)):
        zone = read_zone(zones_raw[i], i)
        label = "La zona de despacho " + zone.id
        add_unique(floor.zones, floor.zones_by_id, zone, label)

        door = search(floor.doors_by_id, zone.door_id)
        if door is None:
            raise ValueError(f"{label} apunta a una puerta desconocida: {zone.door_id}")

        if zone.rect.contains(door.x, door.y):
            raise ValueError(f"{label} cubre su propia puerta: {door.id}")
        if not zone.rect.touches(door.x, door.y):
            raise ValueError(f"{label} no es adyacente a su propia puerta {door.id} en ({door.x}, {door.y}).")

        zone.door = door
        add(door.zones, zone)
        stamp(floor, zone.rect, label, ZONE, zone)

def place_hall_sections(floor: Floor, sections_raw: dict) -> None:
    for i in range(len(sections_raw)):
        section = read_hall_section(sections_raw[i], i)
        label = "El pasillo " + section.id
        add_unique(floor.sections, floor.sections_by_id, section, label)
        stamp(floor, section.rect, label, HALL, section)

def fill_undeclared_halls(floor: Floor) -> None:
    for y in range(floor.height):
        for x in range(floor.width):
            cid = floor.cell_id(x, y)
            if search(floor.grid, cid) is None:
                insert(floor.grid, Cell(HALL, None), cid)
                floor.hall_count += 1

def check_every_door_has_a_zone(floor: Floor) -> None:
    door = floor.doors.head
    while door is not None:
        if door.value and length(door.value.zones) == 0:
            raise ValueError(f"La puerta {door.value.id} no tiene una zona de despacho en frente.")
        door = door.nextNode

def check_picker_starts(config: dict, floor: Floor) -> None:
    pickers_raw = config.get("pickers", [])
    seen = Dictionary(2 * len(pickers_raw) + 1)

    for i in range(len(pickers_raw)):
        p = pickers_raw[i]
        pid = require_id(p, "El picker #" + str(i + 1))
        label = "El picker " + pid
        if search(seen, pid) is not None:
            raise ValueError(f"{label} aparece dos veces.")
        insert(seen, True, pid)

        require_keys(p, ("posicion_inicial", "capacidad_carga_kg"), label)
        require_positive_number(p["capacidad_carga_kg"], label + " con capacidad_carga_kg")
        x, y = read_point(p["posicion_inicial"], label + " con posicion_inicial")

        cell = floor.cell_at(x, y)
        if cell is None:
            raise ValueError(f"{label} empieza fuera del warehouse.")
        if cell.kind != HALL:
            raise ValueError(f"{label} debe empezar en un pasillo, pero ({x}, {y}) es {cell.label()}.")

def load_pickers(config: dict, floor: Floor) -> LinkedList:
    check_picker_starts(config, floor)

    pickers = LinkedList()
    picker_list = config.get("pickers", [])
    for i in range(len(picker_list)):
        p = picker_list[i]
        x, y = read_point(p["posicion_inicial"], "El picker " + p["id"] + " con posicion_inicial")
        add(pickers, Picker(p["id"], floor.cell_id(x, y), p["capacidad_carga_kg"]))
    return pickers

def add_wave_config(config: dict) -> WaveConfig|None:
    if "configuracion" not in config:
        return None
    wc = config["configuracion"]
    require_keys(wc, ("wave_max_pedidos", "wave_max_productos"), "La configuración de wave")
    return WaveConfig(wc["wave_max_pedidos"], wc["wave_max_productos"])

def build_dropoff_cells(floor) -> None:
    z = floor.zones.head
    while z is not None:
        if z.value is None:
            z = z.nextNode
            continue
        zone = z.value
        r = zone.rect
        for y in range(r.y, r.y2 + 1):
            for x in range(r.x, r.x2 + 1):
                for move in MOVES:
                    dx, dy = step(move)
                    neighbour = floor.cell_at(x + dx, y + dy)
                    if neighbour is None or neighbour.kind != HALL:
                        continue
                    cid = floor.cell_id(x + dx, y + dy)
                    add(zone.access, cid)
                    dropoff = search(floor.dropoff, cid)
                    if dropoff is not None:
                        add(dropoff, zone)
                    else:
                        zones_here = LinkedList()
                        add(zones_here, zone)
                        insert(floor.dropoff, zones_here, cid)
        z = z.nextNode
