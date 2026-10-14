import json

from warehouse.domain.rect import Rect
from warehouse.domain.location import Door
from warehouse.domain.location import DispatchZone
from warehouse.domain.rack import Rack
from warehouse.domain.location import HallSection
from warehouse.domain.direction import is_sentido, SENTIDOS

def require_keys(section: dict, keys: tuple, label: str) -> None:
    for key in keys:
        if key not in section:
            raise ValueError(f"{label} no tiene '{key}'.")

def require_int(value, label: str):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} debe ser un entero.")
    return value

def require_positive_int(value, label: str):
    if require_int(value, label) <= 0:
        raise ValueError(f"{label} debe ser un entero mayor a 0.")
    return value

def require_positive_number(value, label: str):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{label} debe ser mayor a 0.")
    return value

def require_id(entry: dict, label: str):
    require_keys(entry, ("id",), label)
    value = entry["id"]
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} necesita un id de tipo str.")
    return value

def load_config(path):
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    require_keys(config, ("warehouse",), "El escenario")
    return config


def read_dimensions(warehouse: dict) -> tuple[int, int]:
    require_keys(warehouse, ("dimensiones",), "El warehouse")
    dim = warehouse["dimensiones"]
    require_keys(dim, ("ancho_x", "largo_y"), "Las dimensiones")
    width = require_positive_int(dim["ancho_x"], "dimensiones.ancho_x")
    height = require_positive_int(dim["largo_y"], "dimensiones.largo_y")
    return width, height

def read_point(section: dict, label: str) -> tuple[int, int]:
    require_keys(section, ("x", "y"), label)
    return require_int(section["x"], label + ".x"), require_int(section["y"], label + ".y")

def read_rect(entry: dict, label: str) -> Rect:
    require_keys(entry, ("ubicacion", "ancho", "alto"), label)
    x, y = read_point(entry["ubicacion"], label + " ubicacion")
    width = require_positive_int(entry["ancho"], f"El ancho de {label}")
    height = require_positive_int(entry["alto"], f"El alto de {label}")
    return Rect(x, y, width, height)

def read_door(entry: dict, index: int) -> Door:
    label = "La puerta #" + str(index + 1)
    door_id = require_id(entry, label)
    label = "La puerta " + door_id
    require_keys(entry, ("tipo", "ubicacion"), label)
    x, y = read_point(entry["ubicacion"], label + " con ubicacion")
    return Door(door_id, entry["tipo"], x, y)

def read_zone(entry: dict, index: int) -> DispatchZone:
    label = "La zona de despacho #" + str(index + 1)
    zone_id = require_id(entry, label)
    label = "La zona de despacho " + zone_id
    require_keys(entry, ("puerta_id", "peso_max_kg"), label)
    rect = read_rect(entry, label)
    max_weight = require_positive_number(entry["peso_max_kg"], label + " con peso_max_kg")
    return DispatchZone(zone_id, entry["puerta_id"], rect, max_weight)

def read_rack(entry: dict, index: int) -> Rack:
    label = "El rack #" + str(index + 1)
    rack_id = require_id(entry, label)
    return Rack(rack_id, read_rect(entry, "rack " + rack_id))

def read_hall_section(entry: dict, index: int) -> HallSection:
    label = "El pasillo #" + str(index + 1)
    section_id = require_id(entry, label)
    label = "El pasillo " + section_id
    require_keys(entry, ("sentido",), label)
    if not is_sentido(entry["sentido"]):
        raise ValueError(f"{label} tiene sentido {entry["sentido"]}, se esperaba uno de {", ".join(SENTIDOS)}")
    return HallSection(section_id, read_rect(entry, label), entry["sentido"])
