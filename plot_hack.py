"""Chart: Hack's exponent vs amount of rain, two routings, four seeds; real-river band."""
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows = [json.loads(l) for l in open("out/sweep.jsonl")]
fig, ax = plt.subplots(figsize=(8, 5), dpi=130)
ax.axhspan(0.56, 0.60, color="#bcd7e8", alpha=0.6, lw=0); ax.text(270, 0.587, "real rivers, h ≈ 0.56–0.60", fontsize=9, color="#2f5d7c")
ax.axhline(2 / 3, color="#999", lw=0.8, ls=":"); ax.text(11, 0.673, "Scheidegger random network, 2/3", fontsize=8, color="#777")
for key, col, lab in (("steep0.3", "#1f6f50", "steepest descent (jittered)"), ("flood", "#c0613a", "flood-order routing (my first, wrong)")):
    seeds = sorted({r["seed"] for r in rows}); X = None; Ys = []
    for s in seeds:
        rr = [r for r in rows if r["seed"] == s]; x = np.array([max(r["drops"], 1e4) / 1e3 for r in rr]); y = [r[key][0] for r in rr]
        ax.plot(x, y, color=col, alpha=0.3, lw=1); Ys.append(y); X = x
    n = min(map(len, Ys)); m = np.mean([y[:n] for y in Ys], 0)
    ax.plot(X[:n], m, color=col, lw=2.4, marker="o", label=f"{lab}, mean of {len(Ys)} worlds")
ax.set_xscale("log"); ax.set_xticks([10, 25, 50, 100, 200, 400, 800]); ax.set_xticklabels(["none", "25k", "50k", "100k", "200k", "400k", "800k"])
ax.set_xlabel("raindrops simulated on a 256×256 island"); ax.set_ylabel("Hack exponent h  (L ∝ A^h, cells with A ≥ 50)")
ax.set_title("More rain made my rivers less like real ones", fontsize=12); ax.legend(fontsize=8.5, loc="lower left", frameon=False)
ax.set_ylim(0.33, 0.7); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("out/hack_vs_rain.png", facecolor="white")
