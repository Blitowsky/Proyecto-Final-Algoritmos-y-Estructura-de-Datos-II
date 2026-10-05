from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse

config = load_config("/home/mati/Desktop/Proyecto-Final-Algoritmos-y-Estructura-de-Datos-II/src/tests/init2.json")

warehouse = build_warehouse(config)

warehouse.graph.printGraph()
print("==========")
print()

for rack in warehouse.racks.dictionary:
    if rack.head is not None:
        if not (rack.head.value and isinstance(rack.head.value, tuple)):
            continue
        r = rack.head.value[1]
        print("Left access of rack:", r.id)
        r.left.access_halls.print_list()
        print("Right access of rack:", r.id)
        r.right.access_halls.print_list()
print("==========")
print()

for h in warehouse.halls.dictionary:
    if h.head is not None:
        if not (h.head.value and isinstance(h.head.value, tuple)):
            continue
        hall = h.head.value[1]
        print("Rack access of hall:", hall.id)

        current = hall.rack_access.head
        while current is not None:
            rack_acc = current.value
            side = "L" * rack_acc.left + "R" * rack_acc.right
            print(f"{rack_acc.rack.id}, {side}", end=" -> ")
            current = current.nextNode
        print("None")
print("==========")
print()

z = warehouse.zones.head
while z is not None:
    zone = z.value
    if zone is None:
        continue
    print(f"Nodes in {zone.id}:")
    zone.cells.print_list()
    z = z.nextNode
