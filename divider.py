"""Is 'erosion removes sinuosity' physics or the D8 lattice? (lattice floor, zenith 74412)
Length of the main stem measured by Richardson's divider: chords between every k-th cell of the path
from the head to the cell (plus the last chord). k=1 is the raw lattice length; k=4, 8 filter the
stair-step of D8 paths. Floor = noiseless tilted planes (should go to ~1.00 at k>=4).
Islands, seeds 7/11/23/42, 0 / 200k / 800k drops, same erosion law as decompose.py.
Pre-registered bet (journal 05.10 11:45): the h_S drop 0 -> 800k survives k=8 (> 0.02 on >= 3 of 4 maps)."""
import numpy as np, json, sys
sys.path.insert(0, ".")
import decompose as Dc, rivers as R, erode as E
KS = (1, 4, 8)

def route(h):
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
    return rec, order

def head_map(rec, order, shape):
    n, m = shape; N = n * m; A = np.ones(N); L = np.zeros(N); head = np.arange(N); r = rec.ravel()
    for c in order[::-1]:
        t = r[c]
        if t >= 0:
            A[t] += A[c]; d = 1.0 if abs(t - c) in (1, m) else 2 ** .5
            if L[c] + d > L[t]: L[t] = L[c] + d; head[t] = head[c]
    return A, L, head

def divider_lengths(rec, cells, head, m):
    """for each target cell: path head -> cell following rec, chord length at each k"""
    r = rec.ravel(); out = {k: np.zeros(len(cells)) for k in KS}; D = np.zeros(len(cells))
    for n_, c in enumerate(cells):
        p = [head[c]]
        while p[-1] != c:
            p.append(r[p[-1]])
        y, x = np.divmod(np.array(p), m)
        D[n_] = np.hypot(y[-1] - y[0], x[-1] - x[0])
        for k in KS:
            idx = np.arange(0, len(p), k)
            if idx[-1] != len(p) - 1: idx = np.append(idx, len(p) - 1)
            out[k][n_] = np.hypot(np.diff(y[idx]), np.diff(x[idx])).sum()
    return out, D

def measure(h, land_only=True):
    rec, order = route(h); A, L, head = head_map(rec, order, h.shape)
    land = (h >= 0).ravel() if land_only else np.ones(h.size, bool)
    cells = np.where(land & (A >= 50) & (L > 0))[0]
    Lk, D = divider_lengths(rec, cells, head, h.shape[1]); ok = D > 0
    row = {"n": int(ok.sum())}
    for k in KS:
        s = Lk[k][ok] / D[ok]
        row[f"LD_med_k{k}"] = round(float(np.median(s)), 4)
        row[f"h_S_k{k}"] = round(Dc.slope(A[cells][ok], s), 4)
        row[f"h_k{k}"] = round(Dc.slope(A[cells][ok], Lk[k][ok]), 4)
    return row

if __name__ == "__main__":
    out = open("out/divider.jsonl", "w")
    n = 256; jj, ii = np.mgrid[0:n, 0:n]
    for ang in np.random.default_rng(5).uniform(0, 2 * np.pi, 4):
        h = 10 + 0.05 * (np.cos(ang) * (ii - n / 2) + np.sin(ang) * (jj - n / 2)); h -= h.min() - 0.01
        row = {"shape": "plane_flat", "deg": round(float(np.degrees(ang)), 1), **measure(h, land_only=False)}
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
    for seed in (7, 11, 23, 42):
        rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng, "island"); done = 0
        for target in (0, 200000, 800000):
            if target > done: E.erode(h, target - done, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05); done = target
            row = {"shape": "island", "seed": seed, "drops": done, **measure(h)}
            out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
