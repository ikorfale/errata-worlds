"""Does lateral (outer-bank) erosion keep sinuosity once the D8 stair-step is filtered? (task #124)
Same islands and erosion as lateral_try.py (seeds 7/11/23/42, 800k drops, lateral 0 vs 2.0), measured with
divider.py's Richardson divider at k=1/4/8. Floor: noiseless planes h_S_k8 0.004-0.011 (out/divider.jsonl).
Pre-registered bet (05.10 13:20, before any run): at k=8, lateral 2.0 has larger h_S than lateral 0 on >= 3 of 4
seeds, and lateral 2.0 median L/D stays below lateral 0 (it straightens the long path while bending the small ones)."""
import numpy as np, json, sys, os
sys.path.insert(0, "lab/worlds")  # run from the parent of lab/worlds, like the other scripts
import erode as E, divider as Dv
out = open("lab/worlds/out/divider_lateral.jsonl", "a")
for seed in (7, 11, 23, 42):
    for lat in (0.0, 2.0):
        p = f"lab/worlds/out/latd_{seed}_{lat}_800000.npy"
        if os.path.exists(p): h = np.load(p).astype(float)
        else:
            rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng)
            E.erode(h, 800000, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05, lateral=lat)
            np.save(p, h.astype(np.float32))
        row = {"seed": seed, "lateral": lat, "drops": 800000, **Dv.measure(h)}
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
