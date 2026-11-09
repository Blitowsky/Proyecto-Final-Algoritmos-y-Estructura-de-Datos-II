import json

import numpy as np

from experiments import adapters
from experiments import common
from experiments import config

PREFERRED = ["ticks", "assignments", "planned_distance", "steps", "waits",
             "reroutes", "side_steps"]


def run():
    results = {}
    for sc in config.SCENARIOS:
        floor0 = adapters.load_floor(sc["path"])
        kinds = adapters.grid_kinds(floor0)
        (common.out_dir() / f"kinds_{sc['name']}.json").write_text(json.dumps(kinds))
        H, W = len(kinds), len(kinds[0])
        results[sc["name"]] = {}
        for key in config.STRATEGIES:
            ms, (summary, visits) = common.time_runs(
                lambda: adapters.load_floor(sc["path"]),
                lambda f: adapters.run_simulation(f, key),
                config.SIM_REPEATS)
            grid = np.zeros((H, W), dtype=np.int64)
            for (x, y) in visits:
                grid[y, x] += 1
            np.save(common.out_dir() / f"visits_{sc['name']}_{key}.npy", grid)
            row = dict(summary)
            row["wall_ms"] = ms
            results[sc["name"]][key] = row
            print(f"[sim] {sc['name']} / {key}: {summary}")
    (common.out_dir() / "strategy_results.json").write_text(json.dumps(results, indent=1))
    return results


def load():
    return json.loads((common.out_dir() / "strategy_results.json").read_text())
