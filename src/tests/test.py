from warehouse.persistence.scenario_loader import load_config
from warehouse.services.warehouse_loader import build_warehouse

config = load_config("/home/mati/Desktop/Proyecto-Final-Algoritmos-y-Estructura-de-Datos-II/src/tests/init.json")

build_warehouse(config).graph.printGraph()


