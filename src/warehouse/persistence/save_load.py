
import pickle
"""
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
"""
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