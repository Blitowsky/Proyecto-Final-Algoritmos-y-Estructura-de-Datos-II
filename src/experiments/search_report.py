import math

import numpy as np

from experiments import common
from experiments import config

L = config.SEARCH_LABELS


def _by_algo(rows):
    out = {a: [] for a in config.SEARCH_ALGOS}
    for r in sorted(rows, key=lambda r: r["V"]):
        out[r["algo"]].append(r)
    return out


def t3(rows):
    cols = ["scenario", "V", "E", "algorithm", "queries", "reachable", "time_ms",
            "expanded", "examined", "expanded_vs_BFS_%", "avg_route_cost", "cost_mismatches"]
    base = {r["scenario"]: r["expanded"] for r in rows if r["algo"] == "bfs"}
    table = []
    for r in sorted(rows, key=lambda r: (r["V"], config.SEARCH_ALGOS.index(r["algo"]))):
        b = base.get(r["scenario"])
        table.append({"scenario": r["scenario"], "V": r["V"], "E": r["E"],
                      "algorithm": L[r["algo"]], "queries": r["queries"],
                      "reachable": r["reachable"], "time_ms": r["time_ms"],
                      "expanded": r["expanded"], "examined": r["examined"],
                      "expanded_vs_BFS_%": (100 * r["expanded"] / b) if b else None,
                      "avg_route_cost": r["cost"], "cost_mismatches": r["cost_mismatches"]})
    note = ("Per-query significa pares de pasillos alcanzables (src, dst); time es la media de "
            f"{config.SEARCH_REPEATS} repeticiones. `expanded` = nodos procesados, `examined` = aristas "
            "observadas. `cost_mismatches` debe ser 0 (los 3 encontraron el mejor recorrido posible).")
    common.write_table("T3_search_algorithms", "BFS vs Dijkstra vs A*", cols, table, note)


def _fit(xs, ys):
    pts = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len({p[0] for p in pts}) < 3:
        return None
    X = np.array([p[0] for p in pts])
    Y = np.array([p[1] for p in pts])
    b, a = np.polyfit(X, Y, 1)
    ss_res = float(((Y - (a + b * X)) ** 2).sum())
    ss_tot = float(((Y - Y.mean()) ** 2).sum()) or 1.0
    return b, 1 - ss_res / ss_tot


THEORY = {
    "bfs":      ("O(V + E)",         "O(V)", "O(1): dst adyacente a src", "O(V + E)"),
    "dijkstra": ("O((V + E) log V)", "O(V)", "O(1): dst adyacente a src", "O((V + E) log V)"),
    "astar":    ("O((V + E) log V)", "O(V)", "O(1): dst adyacente a src",
                 "O((V + E) log V); en realidad muchos menos nodos con la heurística Manhattan"),
}


def t4(rows):
    by = _by_algo(rows)
    cols = ["algorithm", "time (theory)", "space", "best case", "worst case",
            "measured time ~ V^b", "R2 (time)", "measured expanded ~ V^b", "R2 (expanded)"]
    table = []
    for a in config.SEARCH_ALGOS:
        rs = by[a]
        ft = _fit([r["V"] for r in rs], [r["time_ms"] for r in rs])
        fe = _fit([r["V"] for r in rs], [r["expanded"] for r in rs])
        t, sp, best, worst = THEORY[a]
        table.append({"algorithm": L[a], "time (theory)": t, "space": sp, "best case": best,
                      "worst case": worst,
                      "measured time ~ V^b": f"b = {ft[0]:.2f}" if ft else "n/a (<3 sizes)",
                      "R2 (time)": f"{ft[1]:.3f}" if ft else "-",
                      "measured expanded ~ V^b": f"b = {fe[0]:.2f}" if fe else "n/a (<3 sizes)",
                      "R2 (expanded)": f"{fe[1]:.3f}" if fe else "-"})
    note = ("b es la pendiente de la escala log-log entre escenarios con V de distintos tamaños. "
            "En este grafo grilla, E es alrededor de 4V, entonces O(V + E) se comporta como O(V): b ~ 1 para BFS; "
            "Dijkstra/A* se espera un poco arriba de 1 (factor logarítmico) o menor si A* poda bien.")
    common.write_table("T4_complexity", "Complejidad teórica vs medida", cols, table, note)


def c1(rows):
    by = _by_algo(rows)
    fig, ax = common.new_fig()
    ends = []
    for i, a in enumerate(config.SEARCH_ALGOS):
        rs = by[a]
        xs, ys = [r["V"] for r in rs], [r["time_ms"] for r in rs]
        common.draw_series(ax, xs, ys, i, L[a])
        ends.append((xs[-1], ys[-1], L[a]))
    first = by[config.SEARCH_ALGOS[0]]
    if len(first) >= 2:   # O(V) reference line anchored on the BFS first point
        x0, y0 = first[0]["V"], first[0]["time_ms"]
        xr = [first[0]["V"], first[-1]["V"]]
        ax.plot(xr, [y0, y0 * xr[1] / x0], color=common.MUTED, linestyle="--", linewidth=1.5,
                label="O(V) reference", zorder=2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Vértices pasillo V (log)"); ax.set_ylabel("Tiempo por query, ms (log)")
    ax.set_title("Tiempo de búsqueda vs tamaño del Warehouse", loc="left", fontsize=12)
    common.style_axes(ax, grid_x=True)
    common.direct_labels(ax, ends)
    ax.legend(frameon=False, fontsize=9, labelcolor=common.INK2)
    common.finish(fig, "C1_time_vs_size")


def c2(rows):
    by = _by_algo(rows)
    fig, (a1, a2) = common.plt.subplots(1, 2, figsize=(11, 4.6))
    fig.patch.set_facecolor(common.SURFACE)
    ends = []
    for i, a in enumerate(config.SEARCH_ALGOS):
        rs = by[a]
        xs, ys = [r["V"] for r in rs], [r["expanded"] for r in rs]
        common.draw_series(a1, xs, ys, i, L[a])
        ends.append((xs[-1], ys[-1], L[a]))
    a1.set_xscale("log"); a1.set_yscale("log")
    a1.set_xlabel("Vértices pasillo V (log)"); a1.set_ylabel("Nodos expandidos por query (log)")
    a1.set_title("Trabajo vs tamaño", loc="left", fontsize=11)
    common.style_axes(a1, grid_x=True); common.direct_labels(a1, ends)
    a1.legend(frameon=False, fontsize=9, labelcolor=common.INK2)

    bfs = {r["V"]: r["expanded"] for r in by["bfs"]}
    ends = []
    for i, a in enumerate(config.SEARCH_ALGOS):
        if a == "bfs":
            continue
        rs = [r for r in by[a] if bfs.get(r["V"])]
        xs = [r["V"] for r in rs]
        ys = [r["expanded"] / bfs[r["V"]] for r in rs]
        common.draw_series(a2, xs, ys, i, f"{L[a]} / BFS")
        ends.append((xs[-1], ys[-1], f"{L[a]} / BFS"))
    a2.axhline(1.0, color=common.MUTED, linestyle="--", linewidth=1.5)
    a2.set_xscale("log")
    a2.set_xlabel("Vértices pasillo V (log)"); a2.set_ylabel("Ratio BFS, por expandidos (1.0 = same)")
    a2.set_title("Poda respecto a BFS", loc="left", fontsize=11)
    common.style_axes(a2, grid_x=True); common.direct_labels(a2, ends)
    a2.legend(frameon=False, fontsize=9, labelcolor=common.INK2)
    fig.suptitle("Nodos expandidos vs tamaño del Warehouse", x=0.01, ha="left",
                 color=common.INK, fontsize=12)
    fig.tight_layout()
    common.finish(fig, "C2_expanded_vs_size")
