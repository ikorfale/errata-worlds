"""Why do river mouths stay low under bank erosion? (task #140)
Saved 800k-drop islands (latd_*), lateral 0 vs 2.0, seeds 7/11/23/42. For basin outlets only: split h_out = h_D_out + h_S_out
(decompose.py), and h_out by outlet size band (A<=500 vs A>500), to see whether the gap is basin shape or the island's edge.
Pre-registered 05.10 21:25 UTC, before any run:
 M1: lateral 2.0 raises h_D_out by less than half of what it raises within-basin h_D (+0.08) on >= 3 of 4 seeds.
 M2: the gap is in the big outlets: on lateral 2.0 maps, h_out over outlets with A<=500 exceeds h_out over all outlets on >= 3 of 4.
"""
import numpy as np, json, sys, os
sys.path.insert(0, "lab/worlds")  # run from the parent of lab/worlds, like the other scripts
import rivers as R, decompose as Dc
def slope(x, y): return Dc.slope(x, y)
out = open("lab/worlds/out/mouths.jsonl", "a")
for seed in (7, 11, 23, 42):
    for lat in (0.0, 2.0):
        h = np.load(f"lab/worlds/out/latd_{seed}_{lat}_800000.npy").astype(float)
        filled, rec_f, _ = R.flood(h)
        rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
        A, L, D = Dc.accumulate_head(rec, order, h.shape)
        land = h >= 0; s = land & (A >= 50) & (L > 0) & (D > 0)
        outs = R.basin_outlets(A, rec, h); Ab, Lb, Db = A.ravel()[outs], L.ravel()[outs], D.ravel()[outs]
        b = (Ab >= 50) & (Db > 0); sm = b & (Ab <= 500); bg = b & (Ab > 500)
        row = {"seed": seed, "lateral": lat, "h_D": slope(A[s], D[s]), "h_S": slope(A[s], L[s] / D[s]),
               "h_out": slope(Ab[b], Lb[b]), "h_D_out": slope(Ab[b], Db[b]), "h_S_out": slope(Ab[b], Lb[b] / Db[b]),
               "h_out_small": slope(Ab[sm], Lb[sm]), "h_out_big": slope(Ab[bg], Lb[bg]),
               "n_out": int(b.sum()), "n_small": int(sm.sum()), "n_big": int(bg.sum()),
               "W_out_med": float(np.median(Ab[b] / Db[b]**2)), "A_out_max": int(Ab.max())}
        row = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
