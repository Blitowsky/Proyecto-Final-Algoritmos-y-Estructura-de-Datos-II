from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import Dictionary, search, insert
from warehouse.structures.graph import WeightedDirectedGraph

from warehouse.domain.warehouse import WareHouse
from warehouse.domain.location import DispatchZone, HallNode, RackAccess
from warehouse.domain.rack import Rack
from warehouse.domain.product import Product
from warehouse.domain.picker import Picker
from warehouse.domain.wave import Order, Wave, WaveConfig

DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def cell_id(x: int, y: int, width: int) -> int:
    return y * width + x

def reachable_halves(dx: int, dy: int) -> tuple[bool, bool]:
    if dx == 1:
        return True, False
    if dx == -1:
        return False, True
    return True, True

def require_int(value, label: str):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(label + " debe ser un entero.")
    return value

def require_keys(section: list, keys: tuple, label: str) -> None:
    for key in keys:
        if key not in section:
            raise ValueError(f"{label} le falta '{key}'")

def build_warehouse(config: dict) -> WareHouse:
    width = config["width"]
    height = config["height"]
    m = width * height

    racks = place_racks(config, width, height, m)
    vertices, edges, halls = build_halls(width, height, m, racks)

    graph = WeightedDirectedGraph(vertices, edges, m = m)

    zones = add_dispatch_zones(config, width, height, racks, halls)
    products = load_products(config, width, height, racks)
    pickers = add_pickers(config, width, height, halls)
    
    orders, orders_by_id = add_orders(config, products)
    wave_config = add_wave_config(config)
    waves = add_waves(config, orders_by_id, wave_config)

    return WareHouse(
        width, 
        height, 
        graph, 
        halls, 
        racks,
        zones,
        products,
        pickers,
        orders,
        orders_by_id,
        wave_config,
        waves
    )

def place_racks(config: dict, width: int, height: int, m: int) -> Dictionary:
    racks = Dictionary(m)

    for rack in config["racks"]:
        x = require_int(rack["x"], f"La componente x del rack {rack["id"]}")
        y = require_int(rack["y"], f"La componente y del rack {rack["id"]}")
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"El rack {rack["id"]} esta fuera del warehouse.")
        cid = cell_id(x, y, width)
        if search(racks, cid) is not None:
            raise ValueError(f"Dos racks en la celda ({x}, {y})")
        insert(racks, Rack(rack["id"], x, y), cid)

    return racks

def build_halls(width: int, height: int, m: int, racks: Dictionary) -> tuple[LinkedList, LinkedList, Dictionary]:
    vertices = LinkedList()
    edges = LinkedList()
    halls = Dictionary(m)

    for y in range(height):
        for x in range(width):
            cid = cell_id(x, y, width)
            if search(racks, cid) is not None:
                continue

            hall = HallNode(cid, x, y)
            insert(halls, hall, cid)
            add(vertices, cid)

            for dx, dy in DIRECTIONS:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue # Borde del warehouse
                nid = cell_id(nx, ny, width)

                rack = search(racks, nid)
                if rack is not None:
                    left, right = reachable_halves(dx, dy)
                    add(hall.rack_access, RackAccess(rack, left, right))
                    if left:
                        add(rack.left.access_halls, cid)
                    if right:
                        add(rack.right.access_halls, cid)
                elif nid > cid:
                    add(edges, (cid, nid, 1))
                    add(edges, (nid, cid, 1))
    return vertices, edges, halls

def add_dispatch_zones(
    config: dict, 
    width: int, 
    height: int, 
    racks: Dictionary, 
    halls: Dictionary
) -> LinkedList:
    zones = LinkedList()
    zone_list = config.get("dispatch_zones", [])

    for i in range(len(zone_list)):
        z = zone_list[i]
        zid = z.get("id", "D" + str(i + 1))
        label = "zona de despacho" + str(zid)

        ax = require_int(z["p1"]["x"], f"p1.x de la {label}")
        ay = require_int(z["p1"]["y"], f"p1.y de la {label}")
        bx = require_int(z["p2"]["x"], f"p2.x de la {label}")
        by = require_int(z["p2"]["y"], f"p2.y de la {label}")

        x1, x2 = min(ax, bx), max(ax, bx)
        y1, y2 = min(ay, by), max(ay, by)

        if not (0 <= x1 and x2 < width and 0 <= y1 and y2 < height):
            raise ValueError(f"La {label} esta fuera del warehouse.")
        if not (x1 == 0 or x2 == width - 1 or y1 == 0 or y2 == height - 1):
            raise ValueError(f"La {label} no toca una pared.")

        zone = DispatchZone(zid, x1, y1, x2, y2)
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                cid = cell_id(x, y, width)
                if search(racks, cid) is not None:
                    raise ValueError(f"La {label} esta sobre un rack en ({x}, {y}).")
                hall = search(halls, cid)
                if hall is None:
                    raise ValueError(f"Coordenadas inválidas para la {label}.")
                if hall.zone:
                    raise ValueError(f"La {label} se superpone con la zona {hall.zone.id}.")
                hall.zone = zone
                add(zone.cells, cid)
        add(zones, zone)

    return zones

def load_products(config: dict, width: int, height: int, racks: Dictionary) -> Dictionary:
    product_list = config.get("products", [])
    products = Dictionary(2 * len(product_list) + 1)

    for p in product_list:
        pid = p["id"]
        label = "producto " + str(pid)
        if search(products, pid, pid) is not None:
            raise ValueError(f"El {label} aparece dos veces.")

        weight = p["weight"]
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
            raise ValueError(f"El {label} tiene peso inválido.")

        stock = p.get("stock")
        if stock and require_int(stock, f"El stock del {label}") < 0:
            raise ValueError(f"El {label} tiene stock negativo.")

        loc = p["location"]
        x = require_int(loc["x"], f"La componente x del {label}")
        y = require_int(loc["y"], f"La componente y del {label}")
        z = require_int(loc["z"], f"La componente z del {label}")
        side = loc["side"]

        if side not in ("L", "R"):
            raise ValueError(f"El lado del {label} debe ser L o R.")
        if z < 0:
            raise ValueError(f"El {label} tiene altura negativa.")
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"La ubicación del {label} está fuera del warehouse.")

        cid = cell_id(x, y, width)
        rack = search(racks, cid)
        if rack is None:
            raise ValueError(f"El {label} está en ({x}, {y}), donde no hay un rack.")

        half = rack.left if side == "L" else rack.right
        if half.access_halls.head is None:
            raise ValueError(f"El {label} esta en un rack inalcanzable.")

        other = half.items.head
        while other is not None:
            if other.value.z == z:
                raise ValueError(f"El {label} y {other.value.id} comparten la misma ubicación.")
            other = other.nextNode

        product = Product(pid, p["name"], weight, stock, half, x, y, z)
        add(half.items, product)
        insert(products, product, pid)

    return products

def add_pickers(config: dict, width: int, height: int, halls: Dictionary) -> LinkedList:
    pickers = LinkedList()
    picker_list = config.get("pickers", [])

    for i in range(len(picker_list)):
        p = picker_list[i]
        pid = p.get("id", "W" + str(i + 1))
        label = f"picker {pid}"

        other = pickers.head
        while other is not None:
            if other.value and other.value.id == pid:
                raise ValueError(f"El {label} está repetido.")
            other = other.nextNode

        require_keys(p, ("start", "capacity"), f"Al {label}")

        capacity = p["capacity"]
        if isinstance(capacity, bool) or not isinstance(capacity, (int, float)) or capacity <= 0:
            raise ValueError(f"El {label} necesita una capacidad positiva.")

        require_keys(p["start"], ("x", "y"), f"Al nodo comienzo del {label}")
        x = require_int(p["start"]["x"], f"La componente x del nodo comienzo del {label}")
        y = require_int(p["start"]["y"], f"La componente y del nodo comienzo del {label}")
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(f"El {label} empieza fuera del warehouse.")

        start = cell_id(x, y, width)
        if search(halls, start) is None:
            raise ValueError(f"El {label} comienza en un pasillo inválido.")

        add(pickers, Picker(pid, start, capacity))

    return pickers
        
def add_orders(config: dict, products: Dictionary) -> tuple[LinkedList, Dictionary]:
    order_list = config.get("orders", [])
    orders = LinkedList()
    by_id = Dictionary(2 * len(order_list) + 1)

    for i in range(len(order_list)):
        o = order_list[i]
        label = f"pedido #{i + 1}"
        require_keys(o, ("id", "priority", "lines"), f"Al {label}")
        oid = o["id"]
        label = f"pedido {oid}"

        if search(by_id, oid) is not None:
            raise ValueError(f"El {label} aparece dos veces.")
        if len(o["lines"]) == 0:
            raise ValueError(f"El {label} no tiene productos.")

        order = Order(oid, o["priority"])
        for line in o["lines"]:
            require_keys(line, ("product", "qty"), f"A la linea del {label}")
            pid = line["product"]
            if search(products, pid) is None:
                raise ValueError(f"El {label} pide un producto inexistente: {pid}")
            order.add_line(search(products, pid), line["qty"])

        add(orders, order)
        insert(by_id, order, oid)

    return orders, by_id

def add_wave_config(config: dict) -> WaveConfig|None:
    if "wave_config" not in config:
        return None
    wc = config["wave_config"]
    require_keys(wc, ("max_orders", "max_products"), "A la configuración de las waves")
    return WaveConfig(wc["max_orders"], wc["max_products"])

def add_waves(config: dict, orders_by_id: Dictionary, wave_config: WaveConfig|None) -> LinkedList:
    waves = LinkedList()
    wave_list = config.get("waves", [])
    if len(wave_list) > 0 and wave_config is None:
        raise ValueError("La sección de 'waves' necesita una sección 'wave_config'.")

    for i in range(len(wave_list)):
        w = wave_list[i]
        require_keys(w, ("id", "orders"), f"A la wave #{i + 1}")
        wid = w["id"]
        label = f"wave {wid}"

        other = waves.head
        while other is not None:
            if other.value and other.value.id == wid:
                raise ValueError(f"La {label} aparece dos veces.")
            other = other.nextNode
        if len(w["orders"]) == 0:
            raise ValueError(f"La {label} no tiene pedidos.")

        wave = Wave(wid, wave_config)
        for oid in w["orders"]:
            if search(orders_by_id, oid) is None:
                raise ValueError(f"La {label} tiene un pedido {oid} inexistente.")
            wave.add_order(search(orders_by_id, oid))
        add(waves, wave)

    return waves

