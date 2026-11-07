import json

import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgba
from matplotlib.patches import Patch

from experiments import common
from experiments import config

KIND_COLOR = {"rack": "#9c9a93", "zone": "#52514e", "door": "#0b0b0b"}
ZERO = "#f0efec"


def c12():
    d = common.out_dir()
    cmap = LinearSegmentedColormap.from_list("seq", common.SEQ_RAMP)
    for sc in config.SCENARIOS:
        name = sc["name"]
        kinds = json.loads((d / f"kinds_{name}.json").read_text())
        H, W = len(kinds), len(kinds[0])
        grids = {k: np.load(d / f"visits_{name}_{k}.npy") for k in config.STRATEGIES}
        vmax = max(1, max(int(g.max()) for g in grids.values()))
        norm = Normalize(vmin=1, vmax=vmax)
        n = len(grids)
        fig, axes = common.plt.subplots(1, n, figsize=(5.2 * n + 1.2, 5.2 * H / W + 1.4),
                                        squeeze=False)
        fig.patch.set_facecolor(common.SURFACE)
        im = None
        for ax, (k, g) in zip(axes[0], grids.items()):
            rgb = np.zeros((H, W, 4))
            for y in range(H):
                for x in range(W):
                    kind = kinds[y][x]
                    if kind != "hall":
                        rgb[y, x] = to_rgba(KIND_COLOR.get(kind, "#c3c2b7"))
                    elif g[y, x] == 0:
                        rgb[y, x] = to_rgba(ZERO)
                    else:
                        rgb[y, x] = cmap(norm(g[y, x]))
            ax.imshow(rgb, origin="lower", interpolation="nearest",
                      extent=(0, W, 0, H))
            im = common.plt.cm.ScalarMappable(norm=norm, cmap=cmap)
            ax.set_title(config.STRATEGIES[k], loc="left", fontsize=11, color=common.INK)
            ax.set_xlabel("x"); ax.set_ylabel("y")
            ax.tick_params(colors=common.MUTED, labelsize=8)
            for s in ax.spines.values():
                s.set_color(common.AXIS)
            ax.set_facecolor(common.SURFACE)
        cb = fig.colorbar(im, ax=axes[0].tolist(), shrink=0.8, pad=0.02)
        cb.set_label("Visitas de Picker por tick por pasillo", color=common.INK2)
        cb.ax.tick_params(colors=common.MUTED, labelsize=8)
        handles = [Patch(color=ZERO, label="hall, never visited"),
                   Patch(color=KIND_COLOR["rack"], label="rack"),
                   Patch(color=KIND_COLOR["zone"], label="dispatch zone"),
                   Patch(color=KIND_COLOR["door"], label="door")]
        fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
                   fontsize=9, labelcolor=common.INK2)
        fig.suptitle(f"Mapa de calor de pasillos ({name}, misma escala de color)",
                     x=0.01, ha="left", color=common.INK, fontsize=12)
        common.finish(fig, f"Heatmap_{name}")
