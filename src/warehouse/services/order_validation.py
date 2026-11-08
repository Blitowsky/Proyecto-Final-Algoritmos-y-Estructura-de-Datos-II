"""Valida demanda acumulada de pedidos sin reservar inventario.

Se ejecuta una sola vez al construir el Warehouse, antes de generar waves.
Si varias ordenes comparten producto, solo se admiten aquellas cuya demanda
acumulada cabe en el stock. Se conserva el orden del JSON para desempatar.
"""
from dataclasses import dataclass

from warehouse.structures.linkedlist import LinkedList, add
from warehouse.structures.dictionary import CloseDictionary, insert


@dataclass(frozen=True)
class RejectedOrder:
    order_id: str
    reason: str


def validate_orders_stock(warehouse) -> list[RejectedOrder]:
    """Filtra ``warehouse.orders`` y almacena rechazos en ``rejected_orders``.

    No escribe en product.reserved ni crea waves. Se debe invocar antes de
    generar cualquier wave (cuando los pedidos todavía están PENDIENTE).
    """
    if warehouse.waves.head is not None:
        raise ValueError("La validación de pedidos debe realizarse antes de generar Waves.")

    orders = list(warehouse.orders)
    accepted = LinkedList()
    accepted_by_id = CloseDictionary(2 * len(orders) + 1)
    rejected = list(getattr(warehouse, "rejected_orders", []))
    demanded = {}  # pid -> unidades comprometidas por otros pedidos aceptados

    for order in orders:
        reason = None
        if order.state != "PENDIENTE":
            reason = f"El pedido está en estado {order.state}."
        else:
            for line in order.lines:
                if line is None:
                    continue
                product = line.product
                qty = line.qty
                current = demanded.get(product.id, 0)
                stock = product.available  # consulta: NO reserva
                if stock is not None and current + qty > stock:
                    reason = (
                        f"Stock insuficiente de {product.id}: el pedido necesita {qty}, "
                        f"ya hay {current} comprometidas y quedan {stock} disponibles."
                    )
                    break

        if reason is not None:
            rejected.append(RejectedOrder(order.id, reason))
            continue

        add(accepted, order)
        insert(accepted_by_id, order, order.id)
        for line in order.lines:
            if line is not None:
                demanded[line.product.id] = demanded.get(line.product.id, 0) + line.qty

    warehouse.orders = accepted
    warehouse.orders_by_id = accepted_by_id
    warehouse.rejected_orders = rejected
    return rejected
