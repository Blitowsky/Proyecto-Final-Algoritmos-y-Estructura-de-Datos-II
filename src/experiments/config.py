import os
from pathlib import Path

OUT_DIR = Path("experiments_out")          # tables (csv/md), charts (png/svg), raw results

SCENARIOS = [
     {"name": "basico", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_basico.json")},
     {"name": "grande", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_grande.json")},
 ]
"""
SCENARIOS = [
    {"name": "01_m_v", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_01_mini_vertical.json")},
    {"name": "01_v", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_01_vertical.json")},
    {"name": "02_p_h", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_02_pequeno_horizontal.json")},
    {"name": "02_v", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_02_vertical.json")},
    {"name": "03_m_m", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_03_mediano_mixto.json")},
    {"name": "03_v", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_03_vertical.json")},
    {"name": "04_a_h", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_04_amplio_horizontal.json")},
    {"name": "04_v", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_04_vertical.json")},
    {"name": "05_g_m", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_05_grande_mixto.json")},
    {"name": "05_v", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_05_vertical.json")},
    {"name": "06_e_m", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_06_extragrande_mixto.json")},
    {"name": "06_v", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_06_vertical.json")},  
    {"name": "basico", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_basico.json")},
    {"name": "grande", "path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "escenario_grande.json")},
]
"""
STRATEGIES = {
    "none":        "A - Sin estrategia", 
    "centroids":   "B - Centroide de pedidos",
    "spectral":    "C - Clustering espectral",
}

SEARCH_ALGOS = ("bfs", "dijkstra", "astar")
SEARCH_LABELS = {"bfs": "BFS", "dijkstra": "Dijkstra", "astar": "A*"}

SEARCH_QUERIES = 40      # deterministic (src, dst) hall-cell pairs per scenario
SEARCH_REPEATS = 5       # timing repeats per query (median is kept)
SIM_REPEATS = 1          # full-simulation repeats per (scenario, strategy) for wall time
