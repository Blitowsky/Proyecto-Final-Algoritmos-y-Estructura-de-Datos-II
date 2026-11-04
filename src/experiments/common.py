import csv
import statistics
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments import config

# --- palette (validated reference palette, light mode) -------------------------------
SURFACE, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]          # blue, orange, aqua (fixed order)
MARKERS = ["o", "s", "^"]                           # second channel besides colour
SEQ_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def out_dir():
    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    return config.OUT_DIR


def time_runs(setup, run, repeats):
    """setup() -> ctx (NOT timed); run(ctx) -> result (timed). Returns (median_ms, first_result)."""
    samples, first = [], None
    for i in range(repeats):
        ctx = setup()
        t0 = time.perf_counter_ns()
        out = run(ctx)
        samples.append((time.perf_counter_ns() - t0) / 1e6)
        if i == 0:
            first = out
    return statistics.median(samples), first


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:,.3f}" if abs(v) < 10 else f"{v:,.1f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def md_table(columns, rows):
    head = "| " + " | ".join(columns) + " |\n"
    sep = "|" + "|".join("---" for _ in columns) + "|\n"
    body = "".join("| " + " | ".join(fmt(r.get(c)) for c in columns) + " |\n" for r in rows)
    return head + sep + body


def write_csv(name, columns, rows):
    with open(out_dir() / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow([r.get(c, "") for c in columns])


def write_text(name, text):
    (out_dir() / name).write_text(text, encoding="utf-8")


def write_table(name, title, columns, rows, note=""):
    write_csv(name, columns, rows)
    write_text(f"{name}.md", f"## {title}\n\n{md_table(columns, rows)}\n{note}\n")
    print(f"[table] {name}")


# --- charts --------------------------------------------------------------------------
def new_fig(w=7.5, h=4.6, **kw):
    fig, ax = plt.subplots(figsize=(w, h), **kw)
    fig.patch.set_facecolor(SURFACE)
    return fig, ax


def style_axes(ax, grid_x=False):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, axis="both" if grid_x else "y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(INK2)
    ax.yaxis.label.set_color(INK2)
    ax.title.set_color(INK)


def draw_series(ax, xs, ys, i, label):
    ax.plot(xs, ys, color=SERIES[i], marker=MARKERS[i], markersize=7, linewidth=2,
            markeredgecolor=SURFACE, markeredgewidth=1.5, label=label, zorder=3)


def direct_labels(ax, ends):
    """ends: list of (x, y, text). Labels stay in ink colour; spread vertically if close."""
    order = sorted(range(len(ends)), key=lambda k: ends[k][1])
    for rank, k in enumerate(order):
        x, y, t = ends[k]
        ax.annotate(t, (x, y), xytext=(8, (rank - (len(ends) - 1) / 2) * 11),
                    textcoords="offset points", color=INK2, fontsize=9, va="center")


def finish(fig, name):
    d = out_dir()
    fig.savefig(d / f"{name}.png", dpi=200, facecolor=SURFACE, bbox_inches="tight")
    fig.savefig(d / f"{name}.svg", facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"[chart] {name}")
