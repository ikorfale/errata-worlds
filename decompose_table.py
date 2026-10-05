"""Mean over seeds of decompose.jsonl: h = h_D (basin shape) + h_S (sinuosity growth), plus checks."""
import json, statistics as st
rows = [json.loads(l) for l in open("out/decompose.jsonl")]
K = ["h", "h_D", "h_S", "sinuosity_med", "h_cut500", "h_out", "h_D_out", "h_S_out", "A_max"]
print("shape  drops  n " + " ".join(f"{k:>9}" for k in K))
for shape in ("island", "plane"):
    for d in (0, 200000, 800000):
        rs = [r for r in rows if r["shape"] == shape and r["drops"] == d]
        if rs: print(f"{shape:6} {d:6} {len(rs)} " + " ".join(f"{st.mean(r[k] for r in rs):9.3f}" for k in K))
