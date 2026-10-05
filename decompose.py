"""Split Hack's h into stream sinuosity and basin elongation (zenith, deadpool-hermes on 74249).

For every land cell: L = longest upstream path, D = straight distance to the head of that path, A = area.
  L ~ D^d_l   (d_l > 1: wiggly main stream; 1: straight)
  A ~ D^(1+H) (H: width W = A/D grows as D^H; H = 1 self-similar, < 1 elongated)
OLS slopes on different regressors do not compose, so the split used is exact on a common regressor log A:
  log L = log D + log(L/D)  =>  h = h_D + h_S,  h_D = slope(log D ~ log A) ~ 1/(1+H) (basin shape),
  h_S = slope(log L/D ~ log A) (how sinuosity grows with size). d_l, 1+H are reported too, for reference.
Also: h on cells with A in [50, 500] only (domain cutoff check) and h on basin outlets only.
Islands and tilted planes, 4 seeds, 0 / 200k / 800k drops (eroded incrementally, same law as sweep.py).
"""
import numpy as np, json, sys
sys.path.insert(0, ".")
import erode as E, rivers as R

def accumulate_head(rec, order, shape):
    n, m = shape; N = n * m
    A = np.ones(N); L = np.zeros(N); head = np.arange(N); r = rec.ravel()
    for c in order[::-1]:
        t = r[c]
        if t >= 0:
            A[t] += A[c]
            d = 1.0 if (abs(t - c) in (1, m)) else np.sqrt(2)
            if L[c] + d > L[t]: L[t] = L[c] + d; head[t] = head[c]
    hj, hi = np.divmod(head, m); jj, ii = np.divmod(np.arange(N), m)
    D = np.hypot(hj - jj, hi - ii)
    return A.reshape(shape), L.reshape(shape), D.reshape(shape)

def slope(x, y):
    return float(np.polyfit(np.log(x), np.log(y), 1)[0]) if len(x) > 5 else float("nan")

def measure(h):
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
    A, L, D = accumulate_head(rec, order, h.shape)
    land = h >= 0
    s = land & (A >= 50) & (L > 0) & (D > 0)
    row = {"land": int(land.sum()), "n": int(s.sum())}
    row["h"] = slope(A[s], L[s]); row["d_l"] = slope(D[s], L[s]); row["1+H"] = slope(D[s], A[s])
    row["h_D"] = slope(A[s], D[s]); row["h_S"] = slope(A[s], L[s] / D[s])
    row["sinuosity_med"] = float(np.median(L[s] / D[s]))
    c = s & (A <= 500); row["h_cut500"] = slope(A[c], L[c]); row["n_cut"] = int(c.sum())
    row["A_max"] = int(A[land].max())
    outs = R.basin_outlets(A, rec, h); Ab, Lb, Db = A.ravel()[outs], L.ravel()[outs], D.ravel()[outs]
    b = (Ab >= 50) & (Db > 0)
    row["h_out"] = slope(Ab[b], Lb[b]); row["d_l_out"] = slope(Db[b], Lb[b]); row["1+H_out"] = slope(Db[b], Ab[b])
    row["h_D_out"] = slope(Ab[b], Db[b]); row["h_S_out"] = slope(Ab[b], Lb[b] / Db[b]); row["n_out"] = int(b.sum())
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}

if __name__ == "__main__":
    out = open("out/decompose.jsonl", "w")
    for shape in ("island", "plane"):
        for seed in (7, 11, 23, 42):
            rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng, shape); done = 0
            for target in (0, 200000, 800000):
                if target > done: E.erode(h, target - done, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05); done = target
                row = {"shape": shape, "seed": seed, "drops": done, **measure(h)}
                out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
