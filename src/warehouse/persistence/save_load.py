"""Persistencia del warehouse y de la simulacion (archivos Pickle .pkl).

Uso desde la UI:
    save_simulation(simulation, ruta, metadata={...})
    simulation, metadata = load_simulation(ruta)

Los archivos .pkl solo deben abrirse si vienen de una fuente confiable.
"""

import os
import pickle
import tempfile
from pathlib import Path

WAREHOUSE_PATH = "./warehouse.pkl"
SIMULATION_PATH = "./simulation.pkl"
FORMATO_VERSION = 1


def _escribir(objeto, ruta):
    """Guardado atomico: no destruye el archivo anterior si falla pickle.dump."""
    destino = Path(ruta).expanduser().resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=f".{destino.name}.", suffix=".tmp",
            dir=destino.parent, delete=False
        ) as archivo:
            temporal = archivo.name
            pickle.dump(objeto, archivo, protocol=pickle.HIGHEST_PROTOCOL)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, destino)
        return str(destino)
    finally:
        if temporal and os.path.exists(temporal):
            os.unlink(temporal)


def _leer(ruta):
    with open(Path(ruta).expanduser(), "rb") as archivo:
        return pickle.load(archivo)


def save_warehouse(warehouse, ruta=WAREHOUSE_PATH):
    """Guarda el warehouse, no el avance en ticks de Simulation."""
    return _escribir(warehouse, ruta)


def load_warehouse(ruta=WAREHOUSE_PATH):
    """Compatible con los warehouse.pkl antiguos del proyecto."""
    from warehouse.domain.warehouse import WareHouse
    objeto = _leer(ruta)
    if not isinstance(objeto, WareHouse):
        raise ValueError("El archivo elegido no contiene un WareHouse.")
    return objeto


def save_simulation(simulation, ruta=SIMULATION_PATH, metadata=None):
    """Guarda Simulation y metadatos visuales; Simulation incluye warehouse."""
    from warehouse.simulation.simulation import Simulation
    if not isinstance(simulation, Simulation):
        raise TypeError("Se esperaba un objeto Simulation.")
    contenido = {
        "tipo": "simulacion_warehouse",
        "version": FORMATO_VERSION,
        "simulation": simulation,
        "metadata": dict(metadata or {}),
    }
    return _escribir(contenido, ruta)


def load_simulation(ruta=SIMULATION_PATH):
    """Retorna (simulation, metadata); admite .pkl antiguos con Simulation sola."""
    from warehouse.simulation.simulation import Simulation
    contenido = _leer(ruta)
    if isinstance(contenido, Simulation):
        return contenido, {}
    if not isinstance(contenido, dict) or contenido.get("tipo") != "simulacion_warehouse":
        raise ValueError("El archivo elegido no contiene una simulacion guardada.")
    if contenido.get("version") != FORMATO_VERSION:
        raise ValueError("Version de guardado de simulacion no compatible.")
    simulation = contenido.get("simulation")
    if not isinstance(simulation, Simulation):
        raise ValueError("El archivo contiene una simulacion invalida.")
    return simulation, dict(contenido.get("metadata") or {})


# Compatibilidad con los tests originales que usan save(warehouse) y load().
def save(warehouse):
    return save_warehouse(warehouse)


def load():
    try:
        return load_warehouse()
    except (FileNotFoundError, pickle.UnpicklingError, EOFError) as error:
        print(f'No se pudo cargar el WareHouse "{WAREHOUSE_PATH}": {error}')
        return None
"""
import pickle

WAREHOUSE_PATH = "./warehouse.pkl"

def save(self):
        with open(WAREHOUSE_PATH, "bw") as file:
            pickle.dump(self, file)

        print("WareHouse creado satisfactoriamente")

def load():
    try: 
        with open(WAREHOUSE_PATH, "br") as file:
            return pickle.load(file)
    except FileNotFoundError:
        print(f"No se encontró el WareHouse en \"{WAREHOUSE_PATH}\"")
    except pickle.UnpicklingError:
        print(f"Error deserializando el WareHouses \"{WAREHOUSE_PATH}\"")
    except Exception as error:
        print(f"Ocurrió un error inesperado: {error}")
    return None

SIMULATION_PATH = "./simulation.pkl"

def save(self):
        with open(SIMULATION_PATH, "bw") as file:
            pickle.dump(self, file)

        print("simulation creado satisfactoriamente")

def load():
    try: 
        with open(SIMULATION_PATH, "br") as file:
            return pickle.load(file)
    except FileNotFoundError:
        print(f"No se encontró la simulation en \"{SIMULATION_PATH}\"")
    except pickle.UnpicklingError:
        print(f"Error deserializando el simulation \"{SIMULATION_PATH}\"")
    except Exception as error:
        print(f"Ocurrió un error inesperado: {error}")
    return None

VENTANA_PATH = "./ventana.pkl"

def saved(self):
        with open(VENTANA_PATH, "bw") as file:
            pickle.dump(self, file)

        print("simulation creado satisfactoriamente")

def loadd():
    try: 
        with open(VENTANA_PATH, "br") as file:
            return pickle.load(file)
    except FileNotFoundError:
        print(f"No se encontró la simulation en \"{VENTANA_PATH}\"")
    except pickle.UnpicklingError:
        print(f"Error deserializando el simulation \"{VENTANA_PATH}\"")
    except Exception as error:
        print(f"Ocurrió un error inesperado: {error}")
    return None
"""
"""
import pickle
import traceback

WAREHOUSE_PATH = "./warehouse.pkl"


def save(warehouse):
    try:
        with open(WAREHOUSE_PATH, "bw") as file:
            pickle.dump(warehouse, file)

        print("WareHouse creado satisfactoriamente")

    except Exception:
        traceback.print_exc()
        raise


def load():
    try:
        with open(WAREHOUSE_PATH, "br") as file:
            return pickle.load(file)

    except FileNotFoundError:
        print(f'No se encontró el WareHouse en "{WAREHOUSE_PATH}"')
    except pickle.UnpicklingError:
        print(f'Error deserializando el WareHouse "{WAREHOUSE_PATH}"')

    return None
"""