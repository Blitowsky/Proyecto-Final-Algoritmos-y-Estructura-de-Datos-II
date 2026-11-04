import os
from pathlib import Path

OUT_DIR = Path("experiments_out")          # tables (csv/md), charts (png/svg), raw results

SCENARIOS = [
    {"name": "basico", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_basico.json")},
    # {"name": "medio",  "path": "data/escenario_medio.json"},
    {"name": "grande", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_grande.json")},
]

STRATEGIES = {
    "none":        "A - Sin estrategia", 
    "centroids":    "B - Centroide de pedidos",
}

SEARCH_ALGOS = ("bfs", "dijkstra", "astar")
SEARCH_LABELS = {"bfs": "BFS", "dijkstra": "Dijkstra", "astar": "A*"}

SEARCH_QUERIES = 40      # deterministic (src, dst) hall-cell pairs per scenario
SEARCH_REPEATS = 5       # timing repeats per query (median is kept)
SIM_REPEATS = 1          # full-simulation repeats per (scenario, strategy) for wall time
