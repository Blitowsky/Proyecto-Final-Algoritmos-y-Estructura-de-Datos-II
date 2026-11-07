from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import CloseDictionary, Dictionary, search, insert

from warehouse.domain.order import Order
from warehouse.persistence.scenario_loader import require_keys, require_id

def add_orders(config: dict, products: Dictionary) -> tuple[LinkedList, Dictionary]:
    """Retorna lista y hash table de pedidos (`Order`) del JSON
        
    Parámetros
    ----------
        config (`dict`):
            JSON de configuración parseado.
        products (`Dictionary`):
            Hash table de productos.

    Retorna
    ----------
        [0] orders (`LinkedList`):
            Lista de objetos pedido.
        [1] by_id (`Dictionary`):
            Hash table con (ID pedido) -> (`Order`)

    """
    order_list = config.get("pedidos", [])
    orders = LinkedList()
    by_id = CloseDictionary(2 * len(order_list) + 1)

    for i in range(len(order_list)):
        o = order_list[i]
        oid = require_id(o, "El pedido #" + str(i + 1))
        label = "El pedido " + oid
        require_keys(o, ("prioridad", "items"), label)

        if search(by_id, oid) is not None:
            raise ValueError(label + " aparece dos veces.")
        if len(o["items"]) == 0:
            raise ValueError(label + " no tiene productos.")

        estado = o.get("estado", "PENDIENTE")
        if estado != "PENDIENTE":
            raise ValueError(f"{label} tiene estado {estado}, solo pedidos en PENDIENTE pueden ser cargados.")

        order = Order(oid, o["prioridad"])
        for item in o["items"]:
            require_keys(item, ("producto_id", "cantidad"), label + " tiene un pedido que")
            pid = item["producto_id"]
            product = search(products, pid)
            if product is None:
                raise ValueError(f"{label} pide un producto desconocido: {pid}")
            order.add_line(product, item["cantidad"])

        add(orders, order)
        insert(by_id, order, oid)

    return orders, by_id

def update_orders_from_deliveries(warehouse) -> list[Order]:
    """Actualiza el estado de avance de los pedidos a partir de los productos
    efectivamente entregados en las zonas de despacho (cuando las waves se
    arman por productos y no por pedidos completos).

    Retorna la lista de pedidos que pasaron a `PREPARADO` en esta actualización.
    """
    delivered: dict = {}
    z_node = warehouse.zones.head
    while z_node is not None:
        zone = z_node.value
        if zone is not None and zone.is_outbound:
            item_node = zone.items.head
            while item_node is not None:
                item = item_node.value
                if item is not None and item.product is not None:
                    pid = item.product.id
                    delivered[pid] = delivered.get(pid, 0) + item.qty
                item_node = item_node.nextNode
        z_node = z_node.nextNode

    if not delivered:
        return []

    unlinked_orders: list[Order] = []
    o_node = warehouse.orders.head
    while o_node is not None:
        order = o_node.value
        if order is not None and order.wave is None:
            if order.state == "PREPARADO":
                line_node = order.lines.head
                while line_node is not None:
                    if line_node.value is not None:
                        pid = line_node.value.product.id
                        delivered[pid] = max(0, delivered.get(pid, 0) - line_node.value.qty)
                    line_node = line_node.nextNode
            else:
                unlinked_orders.append(order)
        o_node = o_node.nextNode

    unlinked_orders.sort(key=lambda o: (-o.priority, str(o.id)))

    completed_now: list[Order] = []
    for order in unlinked_orders:
        can_complete = True
        any_available = False
        line_node = order.lines.head
        while line_node is not None:
            line = line_node.value
            if line is not None:
                avail = delivered.get(line.product.id, 0)
                if avail > 0:
                    any_available = True
                if avail < line.qty:
                    can_complete = False
            line_node = line_node.nextNode

        if can_complete:
            line_node = order.lines.head
            while line_node is not None:
                line = line_node.value
                if line is not None:
                    pid = line.product.id
                    delivered[pid] -= line.qty
                line_node = line_node.nextNode

            if order.state == "PENDIENTE":
                order.assign_to(None)
            if order.state == "EN_WAVE":
                order.start_preparation()
            if order.state == "EN_PREPARACION":
                order.finish()
            completed_now.append(order)
        elif any_available:
            if order.state == "PENDIENTE":
                order.assign_to(None)
            if order.state == "EN_WAVE":
                order.start_preparation()

    return completed_now
