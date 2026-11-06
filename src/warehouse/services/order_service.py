from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import Dictionary, search, insert

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
    by_id = Dictionary(2 * len(order_list) + 1)

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
