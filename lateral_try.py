"""Meander-lite: does cutting the outer bank on turns keep sinuosity (h_S) under erosion? seed(s) x lateral."""
import numpy as np, json, sys
sys.path.insert(0, ".")
import erode as E, decompose as Dc
seeds = [int(a) for a in sys.argv[1].split(",")] if len(sys.argv) > 1 else [7]
lats = [float(a) for a in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0.0, 0.5, 2.0]
drops = int(sys.argv[3]) if len(sys.argv) > 3 else 200000
out = open("out/lateral.jsonl", "a")
for seed in seeds:
    for lat in lats:
        rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng)
        E.erode(h, drops, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05, lateral=lat)
        row = {"seed": seed, "lateral": lat, "drops": drops, "relief": round(float(h.max()), 3), **Dc.measure(h)}
        row = {k: row[k] for k in ("seed", "lateral", "drops", "relief", "land", "h", "h_D", "h_S", "sinuosity_med", "h_out", "h_cut500")}
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
        if seed == 7: np.save(f"out/lat7_{lat}_{drops}.npy", h.astype(np.float32))
