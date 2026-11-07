from experiments import common
from experiments import config


def _metric_order(rows):
    keys = []
    for r in rows:
        for k, v in r.items():
            if isinstance(v, (int, float)) and k not in keys:
                keys.append(k)
    ordered = [k for k in PREFERRED if k in keys]
    ordered += [k for k in keys if k not in ordered and k != "wall_ms"]
    return ordered + (["wall_ms"] if "wall_ms" in keys else [])


PREFERRED = ["ticks", "assignments", "planned_distance", "steps", "waits",
             "reroutes", "side_steps"]


def t1(results):
    keys = list(config.STRATEGIES)
    labels = config.STRATEGIES
    cols = ["scenario", "metric"] + [labels[k] for k in keys] + \
           [f"{labels[k]} vs {labels[keys[0]][:1]} (%)" for k in keys[1:]]
    flat, md = [], "## T1 - Route strategy comparison (same scenario, same waves)\n\n"
    for scn, per in results.items():
        metrics = _metric_order(list(per.values()))
        sc_rows = []
        for m in metrics:
            row = {"scenario": scn, "metric": m}
            base = per[keys[0]].get(m)
            for k in keys:
                row[labels[k]] = per[k].get(m)
            for k in keys[1:]:
                v = per[k].get(m)
                row[f"{labels[k]} vs {labels[keys[0]][:1]} (%)"] = (
                    100 * (v - base) / base if base not in (None, 0) and v is not None else None)
            sc_rows.append(row)
        flat += sc_rows
        md += f"### {scn}\n\n" + common.md_table(cols[1:], sc_rows) + "\n"
    md += ("`wall_ms` es la media de tiempo que le tomó a la simulación terminar "
           f"({config.SIM_REPEATS} repeticiones), no solo planear la ruta. "
           "% negativo = menos que la primer estrategia.\n")
    common.write_csv("T1_strategy_comparison", cols, flat)
    common.write_text("T1_strategy_comparison.md", md)
    print("[table] T1_strategy_comparison")
