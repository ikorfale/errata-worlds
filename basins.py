"""zenith's untested candidate (74529): does erosion change WHICH coastal basins exist?
Per island seed and drop count: number of outlets (all, A>=50), outlet-area quantiles, share of land in the top 5 basins,
and how many A>=50 outlets of the uneroded map still sit within 3 cells of an A>=50 outlet after erosion."""
import json, sys, numpy as np
sys.path.insert(0, "lab/worlds")
import erode as E, rivers as R
from decompose import accumulate_head

def basins(h):
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
    A, L, D = accumulate_head(rec, order, h.shape)
    outs = R.basin_outlets(A, rec, h); Ab = A.ravel()[outs]
    return outs, Ab, int((h >= 0).sum())

out = open("lab/worlds/out/basins.jsonl", "w")
for seed in (7, 11, 23, 42):
    rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng, "island"); done = 0; first = None
    for target in (0, 200000, 800000):
        if target > done: E.erode(h, target - done, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05); done = target
        outs, Ab, land = basins(h); big = outs[Ab >= 50]; Abig = np.sort(Ab[Ab >= 50])[::-1]
        yx = np.array(np.divmod(big, 256)).T
        if first is None: first = yx
        kept = int(sum((((yx - p) ** 2).sum(1) <= 9).any() for p in first)) if len(yx) else 0
        row = {"seed": seed, "drops": done, "land": land, "n_out_all": int(len(outs)), "n_out50": int(len(big)),
               "A_q50": float(np.median(Abig)), "A_q90": float(np.quantile(Abig, 0.9)), "A_max": int(Abig[0]),
               "top5_share": round(float(Abig[:5].sum()) / land, 4), "big_share": round(float(Abig.sum()) / land, 4),
               "orig50_kept_within3": kept, "orig50": int(len(first))}
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
