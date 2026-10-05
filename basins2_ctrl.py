"""control for basins2.py: same uneroded map, routing jitter seed 1 vs 2. If J is low here, the overlap test is noise."""
import json, sys, numpy as np
sys.path.insert(0, "lab/worlds")
import erode as E, rivers as R
def labels(h, s):
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(s)); rec.ravel()[(h < 0).ravel()] = -1
    r = rec.ravel(); land = (h >= 0).ravel(); n = r.size
    nxt = np.where((r >= 0) & land, r, np.arange(n)); nxt = np.where(land[np.clip(nxt, 0, n - 1)], nxt, np.arange(n))
    for _ in range(20): nxt = nxt[nxt]
    return np.where(land, nxt, -1)
out = open("lab/worlds/out/basins2_ctrl.jsonl", "w")
for seed in (7, 11, 23, 42):
    rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng, "island")
    a, b = labels(h, 1), labels(h, 2); ids, cnt = np.unique(a[a >= 0], return_counts=True); J, W = [], []
    for i in ids[cnt >= 50]:
        m0 = a == i; hit = b[m0]; v, c = np.unique(hit[hit >= 0], return_counts=True); best = v[c.argmax()]
        J.append(c.max() / (m0 | (b == best)).sum()); W.append(m0.sum())
    J, W = np.array(J), np.array(W)
    row = {"seed": seed, "control": "jitter 1 vs 2, drops 0", "J_median": round(float(np.median(J)), 3),
           "J_area_weighted": round(float((J * W).sum() / W.sum()), 3), "share_J_gt_0.5": round(float((J > 0.5).mean()), 3)}
    out.write(json.dumps(row) + "\n"); print(row, flush=True)
