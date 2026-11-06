import json

from experiments import adapters
from experiments import common
from experiments import config


def _queries(cells, k):
    n = len(cells)
    out = []
    for i in range(k):
        s = cells[(i * n) // k]
        d = cells[(i * 7919 + n // 2) % n]
        if s != d:
            out.append((s, d))
    return out


def run():
    rows = []
    for sc in config.SCENARIOS:
        floor = adapters.load_floor(sc["path"])
        V, E = adapters.graph_size(floor)
        cells = sorted(adapters.hall_cells(floor), key=lambda c: (c[1], c[0]))
        qs = _queries(cells, config.SEARCH_QUERIES)
        per_algo = {}
        for algo in config.SEARCH_ALGOS:
            res = []
            for s, d in qs:
                ms, r = common.time_runs(lambda: floor,
                                         lambda f: adapters.run_search(f, algo, s, d),
                                         config.SEARCH_REPEATS)
                res.append((ms, r))
            per_algo[algo] = res
        # correctness cross-check: unit weights -> all three must agree on the cost
        mismatches = 0
        for qi in range(len(qs)):
            costs = [per_algo[a][qi][1]["cost"] for a in config.SEARCH_ALGOS]
            known = [c for c in costs if c is not None]
            if len(known) != len(costs) or max(known) - min(known) > 1e-9:
                mismatches += 1
        for algo in config.SEARCH_ALGOS:
            ok = [(ms, r) for ms, r in per_algo[algo] if r["cost"] is not None]
            m = max(len(ok), 1)
            rows.append({
                "scenario": sc["name"], "V": V, "E": E, "algo": algo,
                "queries": len(qs), "reachable": len(ok),
                "time_ms": sum(t for t, _ in ok) / m,
                "expanded": sum(r["expanded"] for _, r in ok) / m,
                "examined": sum(r["examined"] for _, r in ok) / m,
                "cost": sum(r["cost"] for _, r in ok) / m,
                "cost_mismatches": mismatches,
            })
        print(f"[search] {sc['name']}: V={V} E={E} queries={len(qs)} mismatches={mismatches}")
    (common.out_dir() / "search_results.json").write_text(json.dumps(rows, indent=1))
    return rows


def load():
    return json.loads((common.out_dir() / "search_results.json").read_text())
