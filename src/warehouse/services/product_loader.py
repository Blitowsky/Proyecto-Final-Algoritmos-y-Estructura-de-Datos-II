from warehouse.domain.warehouse import Floor
from warehouse.structures.dictionary import Dictionary, search, insert
from warehouse.domain.product import Product
from warehouse.persistence.scenario_loader import (require_keys, require_int, require_id, require_positive_number, read_point)
from warehouse.structures.linkedlist import add, length

def load_products(config: dict, floor: Floor) -> Dictionary:
    product_list = config.get("productos", [])
    products = Dictionary(2 * len(product_list) + 1)

    for i in range(len(product_list)):
        p = product_list[i]
        pid = require_id(p, "El producto #" + str(i + 1))
        label = "El producto " + pid
        if search(products, pid) is not None:
            raise ValueError(f"{label} aparece dos veces.")

        require_keys(p, ("nombre", "rack_id", "ubicacion", "cantidad_disponible", "peso_kg"), label)

        if not isinstance(p["nombre"], str) or p["nombre"] == "":
            raise ValueError(f"{label} necesita un nombre no vacío.")
        weight = require_positive_number(p["peso_kg"], f"{label} con peso_kg")
        stock = require_int(p["cantidad_disponible"], label + " con cantidad_disponible")
        if stock < 0:
            raise ValueError(f"{label} tiene cantidad disponible negativa.")

        rack_id = p["rack_id"]
        rack = search(floor.racks_by_id, rack_id)
        if rack is None:
            raise ValueError(f"{label} está en un rack que no existe: {rack_id}")

        loc = p["ubicacion"]
        x, y = read_point(loc, label + " con ubicacion")
        require_keys(loc, ("z",), "La ubicacion de " + label)
        z = require_int(loc["z"], label + " con ubicacion.z")
        if z < 1:
            raise ValueError(f"{label} tiene z = {z}, los niveles empiezan en 1.")

        if not rack.rect.contains(x, y):
            raise ValueError(f"{label} en ({x}, {y}), esta fuera del rack {rack.id} (x {rack.rect.x} .. {rack.rect.x2}, y {rack.rect.y} .. {rack.rect.y2})")
        cell = search(floor.rack_cells, floor.cell_id(x, y))

        if cell is None:
            raise ValueError(f"{label} está en un nodo inexistente.")

        if length(cell.access) == 0:
            raise ValueError(f"{label} esta en una celda de rack ({x}, {y}) que no es accesiple por ningún pasillo.")

        other = cell.items.head
        while other is not None:
            if other.value and other.value.z == z:
                raise ValueError(f"{label} y {other.value.id} comparten el mismo slot <{x}, {y}, {z}>")
            other = other.nextNode

        product = Product(pid, p["nombre"], weight, stock, cell, z)
        add(cell.items, product)
        insert(products, product, pid)

    return products
