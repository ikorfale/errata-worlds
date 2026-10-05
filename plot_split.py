"""Stacked bars: Hack's h = h_D (basin shape) + h_S (sinuosity growth), mean of 4 seeds, from out/decompose.jsonl."""
import json, statistics as st, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows = [json.loads(l) for l in open("out/decompose.jsonl")]
labels, hd, hs = [], [], []
for shape in ("island", "plane"):
    for d in (0, 200000, 800000):
        rs = [r for r in rows if r["shape"] == shape and r["drops"] == d]
        labels.append(f"{shape}\n{d // 1000}k drops" if d else f"{shape}\nno rain")
        hd.append(st.mean(r["h_D"] for r in rs)); hs.append(st.mean(r["h_S"] for r in rs))
fig, ax = plt.subplots(figsize=(9, 5.2), dpi=130)
x = range(len(labels))
ax.bar(x, hd, color="#8a9bb0", label="basin shape  (h_D)")
ax.bar(x, hs, bottom=hd, color="#d9822b", label="stream wiggle growing with size  (h_S)")
ax.axhspan(0.56, 0.60, color="#4c9a5b", alpha=0.15, label="real rivers, h ≈ 0.56–0.60")
for i in x: ax.text(i, hd[i] + hs[i] + 0.005, f"{hd[i] + hs[i]:.3f}", ha="center", fontsize=9)
ax.set_xticks(list(x), labels, fontsize=9); ax.set_ylim(0.40, 0.63); ax.set_ylabel("Hack's exponent h")
ax.set_title("Rain straightens the streams; basin shape barely moves\n(mean of 4 seeds, 256×256, droplet erosion)", fontsize=11)
ax.legend(loc="upper right", fontsize=8.5, frameon=False); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig("images/hack-split.png")
