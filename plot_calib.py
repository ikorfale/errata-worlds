"""Chart for calib.jsonl: sim h vs erosion drops against the real HydroRIVERS band."""
import json, collections, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows = [json.loads(l) for l in open("lab/worlds/out/calib.jsonl")]
steps = sorted({r["drops"] for r in rows}); pos = {d: i for i, d in enumerate(steps)}
col = {"island": "#2a78d6", "plane": "#eb6834"}
fig, axs = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True)
for ax, key, title, band in [(axs[0], "h", "Within basins (every cell, A ≥ 50)", (0.53, 0.55)),
                             (axs[1], "h_out", "River mouths (one point per basin)", (0.533, 0.553))]:
    ax.axhspan(*band, color="#bbbbbb", alpha=0.45, lw=0)
    ax.text(len(steps) - 1, band[1] + 0.003, "real rivers, 6 regions (HydroRIVERS)", ha="right", va="bottom", fontsize=9, color="#555")
    for shape in ("island", "plane"):
        g = collections.defaultdict(list)
        for r in rows:
            if r["shape"] == shape: g[r["drops"]].append(r[key])
        x = [pos[d] for d in steps if g[d]]; m = [np.mean(g[d]) for d in steps if g[d]]
        for d in steps:
            ax.scatter([pos[d]] * len(g[d]), g[d], s=14, color=col[shape], alpha=0.35, lw=0)
        ax.plot(x, m, color=col[shape], lw=2, marker="o", ms=6, label=f"{shape} (mean of {len(g[0])} seeds)")
    ax.set_xticks(range(len(steps))); ax.set_xticklabels(["0" if d == 0 else f"{d//1000}k" for d in steps])
    ax.set_xlabel("raindrops of erosion"); ax.set_title(title, fontsize=11, loc="left")
    ax.grid(axis="y", color="#e5e5e5", lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
axs[0].set_ylabel("Hack exponent h  (L ∝ A^h)"); axs[0].legend(frameon=False, fontsize=9, loc="lower left")
fig.suptitle("Erosion matches real rivers early, then overshoots below them", x=0.06, ha="left", fontsize=13)
fig.text(0.06, 0.005, "256×256 worlds, 4 seeds per shape, same erosion law throughout. errata · errata.page", fontsize=8, color="#777")
fig.tight_layout(rect=(0, 0.03, 1, 0.95)); fig.savefig("lab/worlds/out/calib.png", dpi=130)
