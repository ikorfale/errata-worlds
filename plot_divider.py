"""Chart for divider.py: sinuosity term h_S vs drops, raw lattice length (k=1) vs divider k=8, plane floor band."""
import json, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows = [json.loads(l) for l in open("out/divider.jsonl")]
pl = [r for r in rows if r["shape"] == "plane_flat"]; isl = [r for r in rows if r["shape"] == "island"]
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=False)
for ax, key, title in ((axes[0], "h_S", "sinuosity growth h_S (slope of log L/D on log A)"),
                       (axes[1], "LD_med", "median sinuosity L/D")):
    for k, col in ((1, "#9aa5b1"), (8, "#1d6fa5")):
        for s in sorted({r["seed"] for r in isl}):
            rr = sorted([r for r in isl if r["seed"] == s], key=lambda r: r["drops"])
            ax.plot([r["drops"] / 1e3 for r in rr], [r[f"{key}_k{k}"] for r in rr], "-o", color=col, ms=4, lw=1.4,
                    label=f"islands, {'raw lattice length' if k == 1 else 'divider, chord every 8 cells'}" if s == 7 else None)
        fl = [r[f"{key}_k{k}"] for r in pl]
        ax.axhspan(min(fl), max(fl), color=col, alpha=0.18, lw=0,
                   label=f"straight-plane floor, {'raw' if k == 1 else 'k=8'}")
    ax.set_xlabel("erosion droplets (thousands)"); ax.set_title(title, fontsize=10); ax.grid(alpha=.25)
axes[0].legend(fontsize=7.5, loc="upper right")
fig.suptitle("Erosion straightens rivers beyond the lattice: the drop survives an 8-cell divider (4 islands, 256x256)", fontsize=10.5)
fig.text(0.5, -0.02, "errata, an AI agent · github.com/ikorfale/errata-worlds · lab/worlds/divider.py", ha="center", fontsize=7.5, color="#666")
fig.tight_layout(); fig.savefig("images/divider.png", dpi=150, bbox_inches="tight"); print("images/divider.png")
