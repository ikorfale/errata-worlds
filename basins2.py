"""follow-up to basins.py: outlet positions move with the coast, so match basins by the land they drain instead.
For every A>=50 basin of the uneroded map: the eroded basin sharing most cells with it, and their Jaccard overlap."""
import json, sys, numpy as np
sys.path.insert(0, "lab/worlds")
import erode as E, rivers as R

def labels(h):
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
    r = rec.ravel(); land = (h >= 0).ravel(); n = r.size
    nxt = np.where((r >= 0) & land, r, np.arange(n)); nxt = np.where(land[np.clip(nxt, 0, n - 1)], nxt, np.arange(n))
    for _ in range(20): nxt = nxt[nxt]
    return np.where(land, nxt, -1)

out = open("lab/worlds/out/basins2.jsonl", "w")
for seed in (7, 11, 23, 42):
    rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng, "island"); done = 0
    lab0 = labels(h); ids, cnt = np.unique(lab0[lab0 >= 0], return_counts=True); big = ids[cnt >= 50]
    for target in (200000, 800000):
        E.erode(h, target - done, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05); done = target
        lab = labels(h); J, W = [], []
        for b in big:
            m0 = lab0 == b; hit = lab[m0]; hit = hit[hit >= 0]
            if not len(hit): J.append(0.0); W.append(m0.sum()); continue
            v, c = np.unique(hit, return_counts=True); best = v[c.argmax()]; inter = c.max()
            J.append(inter / (m0 | (lab == best)).sum()); W.append(m0.sum())
        J, W = np.array(J), np.array(W)
        row = {"seed": seed, "drops": done, "basins50": int(len(big)), "J_median": round(float(np.median(J)), 3),
               "J_area_weighted": round(float((J * W).sum() / W.sum()), 3), "share_J_gt_0.5": round(float((J > 0.5).mean()), 3),
               "share_J_lt_0.2": round(float((J < 0.2).mean()), 3)}
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
