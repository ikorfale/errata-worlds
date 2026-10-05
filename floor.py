"""Lattice sinuosity floor (zenith on 74249, seq 74412): L/D on straight synthetic channels.
1) geometry: best D8 path between two points at angle t has L/D = cos t + (sqrt2-1) sin t.
2) router: a tilted plane at a random angle, no noise, routed exactly as decompose.measure (flood + steepest, jitter 0.3);
   median L/D on cells with A >= 50, and h_S on that plane (what a 'perfectly straight' world reports).
3) bootstrap 95% CI of h_out (basin outlets) at 0 and 800k drops, to see if 0.566 -> 0.482 beats noise."""
import numpy as np, json, sys
sys.path.insert(0, ".")
import decompose as Dc, rivers as R, erode as E
t = np.random.default_rng(0).uniform(0, np.pi / 4, 100000)
print("geometric floor: mean", round(float(np.mean(np.cos(t) + (2**.5 - 1) * np.sin(t))), 4), "max", round(float(np.cos(np.pi/8) + (2**.5-1)*np.sin(np.pi/8)), 4))
n = 256; jj, ii = np.mgrid[0:n, 0:n]; rows = []
for k, ang in enumerate(np.random.default_rng(5).uniform(0, 2 * np.pi, 8)):
    h = 10 + 0.05 * (np.cos(ang) * (ii - n / 2) + np.sin(ang) * (jj - n / 2)); h -= h.min() - 0.01
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1))
    A, L, D = Dc.accumulate_head(rec, order, h.shape)
    s = (A >= 50) & (L > 0) & (D > 0)
    r = {"deg": round(float(np.degrees(ang)), 1), "n": int(s.sum()), "LD_med": round(float(np.median(L[s] / D[s])), 4),
         "h": round(Dc.slope(A[s], L[s]), 4), "h_S": round(Dc.slope(A[s], L[s] / D[s]), 4)}
    print(r, flush=True); rows.append(r)
print("router floor median of medians", round(float(np.median([r["LD_med"] for r in rows])), 4))
def boot(h, B=2000):
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
    A, L, D = Dc.accumulate_head(rec, order, h.shape)
    outs = R.basin_outlets(A, rec, h); Ab, Lb = A.ravel()[outs], L.ravel()[outs]; b = Ab >= 50
    x, y = np.log(Ab[b]), np.log(Lb[b]); g = np.random.default_rng(9); sl = []
    for _ in range(B):
        i = g.integers(0, len(x), len(x)); sl.append(np.polyfit(x[i], y[i], 1)[0])
    return len(x), float(np.polyfit(x, y, 1)[0]), np.percentile(sl, [2.5, 97.5])
for seed in (7, 11, 23, 42):
    rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng, "island")
    n0, s0, c0 = boot(h)
    E.erode(h, 800000, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05)
    n8, s8, c8 = boot(h)
    print(json.dumps({"seed": seed, "out0": [n0, round(s0, 3), [round(float(v), 3) for v in c0]],
                      "out800k": [n8, round(s8, 3), [round(float(v), 3) for v in c8]]}), flush=True)
