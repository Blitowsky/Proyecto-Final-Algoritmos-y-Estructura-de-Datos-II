from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse

config = load_config("/home/mati/Desktop/Proyecto-Final-Algoritmos-y-Estructura-de-Datos-II/src/tests/init2.json")

warehouse = build_warehouse(config)

# warehouse.graph.printGraph()
# print()
# print("==========")
# print()

for rack in warehouse.racks.dictionary:
    if rack.head is not None:
        if not (rack.head.value and isinstance(rack.head.value, tuple)):
            continue
        r = rack.head.value[1]
        print("Left access of rack:", r.id)
        r.left.access_halls.print_list()
        print("Right access of rack:", r.id)
        r.right.access_halls.print_list()
print()
print("==========")
print()

# for h in warehouse.halls.dictionary:
#     if h.head is not None:
#         if not (h.head.value and isinstance(h.head.value, tuple)):
#             continue
#         hall = h.head.value[1]
#         print("Rack access of hall:", hall.id)
#
#         current = hall.rack_access.head
#         while current is not None:
#             rack_acc = current.value
#             side = "L" * rack_acc.left + "R" * rack_acc.right
#             print(f"{rack_acc.rack.id}, {side}", end=" -> ")
#             current = current.nextNode
#         print("None")
# print()
# print("==========")
# print()
#
# z = warehouse.zones.head
# while z is not None:
#     zone = z.value
#     if zone is None:
#         continue
#     print(f"Nodes in {zone.id}:")
#     zone.cells.print_list()
#     z = z.nextNode
# print()
# print("==========")
# print()

for p in warehouse.products.dictionary:
    if p.head and p.head.value and isinstance(p.head.value, tuple):
        product = p.head.value[1]
        print(f"{product.id}: {product.name} ({product.half.rack_id}); stock {product.stock}")
print()
print("==========")
print()

picker = warehouse.pickers.head
while picker is not None:
    if picker.value is not None:
        print(f"Picker {picker.value.id} at ({picker.value.node})")
    picker = picker.nextNode
print()
print("==========")
print()

for o in warehouse.orders_by_id.dictionary:
    if o.head and isinstance(o.head.value, tuple):
        order = o.head.value[1]
        wave = order.wave.id if order.wave else "None"
        print(f"Order {order.id} (Prio: {order.priority}; Wave: {wave}):")
        line = order.lines.head
        while line is not None:
            if line.value:
                print(f"{line.value.product.name}, {line.value.qty}")
            line = line.nextNode
        print()
print("==========")
print()

w = warehouse.waves.head
while w is not None:
    if w.value:
        wave = w.value
        orders = []
        order = wave.orders.head
        while order is not None:
            if order.value:
                orders.append(order.value.id)
            order = order.nextNode
        print(f"Wave {wave.id} ({", ".join(orders)}) products:")
        line = wave.lines.head
        while line is not None:
            if line.value:
                print(f"{line.value.product.name}, {line.value.qty}")
            line = line.nextNode
        print()
    w = w.nextNode
print("==========")
print()
