"""Resolution test on Tasmania: L and A computed by the same code from HydroSHEDS v1 DIR at 3s and 15s.
Bet (plan #135, recorded before running): basins 100-1000 km2, h(3s)-h(15s) >= +0.02 and median L3/L15 >= 1.05."""
import numpy as np, json, gc
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
LAT0, LAT1, LON0, LON1 = -43.7, -40.0, 144.4, 148.5
R = 6371.0
CODES = {1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)}

def window(path, top, left, res):
    im = Image.open(path)
    r0, r1 = int(round((top - LAT1) / res)), int(round((top - LAT0) / res))
    c0, c1 = int(round((LON0 - left) / res)), int(round((LON1 - left) / res))
    a = np.array(im.crop((c0, r0, c1, r1)), dtype=np.uint8); im.close(); gc.collect()
    return a

def route(d, res):
    ny, nx = d.shape
    lat = LAT1 - (np.arange(ny) + .5) * res
    dyk = R * np.radians(res); dxk = (R * np.cos(np.radians(lat)) * np.radians(res)).astype(np.float32)
    df = d.ravel()
    land = (df != 255) & (df != 247)
    rec = np.full(d.size, -1, np.int32); edge = np.zeros(d.size, bool)
    DI = np.zeros(256, np.int8); DJ = np.zeros(256, np.int8)
    for code, (di, dj) in CODES.items():
        DI[code], DJ[code] = di, dj
        src = np.flatnonzero(df == code)
        i2, j2 = src // nx + di, src % nx + dj
        inside = (i2 >= 0) & (i2 < ny) & (j2 >= 0) & (j2 < nx)
        t = (i2 * nx + j2)
        ok = inside.copy(); ok[inside] = land[t[inside]]
        rec[src[ok]] = t[ok]; edge[src[~inside]] = True
        del src, i2, j2, inside, t, ok
    A = np.where(land, (dyk * dxk)[np.arange(d.size) // nx], 0).astype(np.float32)
    L = np.zeros(d.size, np.float32)
    touch = edge
    indeg = np.bincount(rec[rec >= 0], minlength=d.size).astype(np.int32)
    front = np.flatnonzero(land & (indeg == 0))
    while front.size:
        r = rec[front]; ok = r >= 0; f, r = front[ok], r[ok]
        c = df[f]; dist = np.hypot(dyk * DI[c], dxk[f // nx] * DJ[c]).astype(np.float32)
        np.add.at(A, r, A[f]); np.maximum.at(L, r, L[f] + dist); np.logical_or.at(touch, r, touch[f])
        np.subtract.at(indeg, r, 1)
        u = np.unique(r); front = u[indeg[u] == 0]
    del indeg
    return A.reshape(d.shape), L.reshape(d.shape), rec.reshape(d.shape), touch.reshape(d.shape), None

def fit(A, L):
    x, y = np.log10(A), np.log10(L); b = np.polyfit(x, y, 1)
    rng = np.random.default_rng(1); bs = []
    for _ in range(500):
        i = rng.integers(0, len(x), len(x)); bs.append(np.polyfit(x[i], y[i], 1)[0])
    return {'h': round(b[0], 4), 'ci': [round(v, 4) for v in np.percentile(bs, [2.5, 97.5])], 'n': int(len(x))}

out = {}
grids = {}
for name, path, top, left, res in [('15s', 'data/hyd_au_dir_15s.tif', 25.0, 94.0, 1/240), ('3s', 'data/s50e140_dir.tif', -40.0, 140.0, 1/1200)]:
    d = window(path, top, left, res)
    A, L, rec, touch, bl = route(d, res)
    # a basin is clean if its outlet's 'touch' flag is false; propagate outlet cleanliness upstream is costly, so use outlets only + channel cells whose own touch flag is false
    outlet = (rec == -1) & (A > 0)
    clean_cells = (~touch) & (A > 0)
    vals = {'cells': int(d.size), 'land': int((A > 0).sum()), 'outlets_clean_100_1000': None}
    s = outlet & clean_cells & (A >= 100) & (A <= 1000)
    if s.sum() >= 5: vals['outlets_clean_100_1000'] = fit(A[s], L[s])
    s = outlet & clean_cells & (A >= 10)
    vals['outlets_clean_ge10'] = fit(A[s], L[s])
    s = clean_cells & (A >= 100) & (A <= 1000) & (L > 0)
    vals['channel_cells_100_1000'] = fit(A[s], L[s])
    s = clean_cells & (A >= 10) & (A <= 100) & (L > 0)
    vals['channel_cells_10_100'] = fit(A[s], L[s])
    big = np.argsort(-(A * outlet * clean_cells).ravel())[:5]
    vals['largest'] = [[round(float(A.ravel()[i]), 1), round(float(L.ravel()[i]), 1)] for i in big]
    out[name] = vals; print(name, json.dumps(vals), flush=True)
    grids[name] = (A, L, clean_cells)
    del d, rec, touch; gc.collect()
# matched: each 15s cell with A >= 10 vs the max-A 3s cell inside its 5x5 block
A15, L15, c15 = grids['15s']; A3, L3, c3 = grids['3s']
ny, nx = A15.shape
A3b = A3[:ny*5, :nx*5].reshape(ny, 5, nx, 5).transpose(0, 2, 1, 3).reshape(ny, nx, 25)
L3b = L3[:ny*5, :nx*5].reshape(ny, 5, nx, 5).transpose(0, 2, 1, 3).reshape(ny, nx, 25)
k = A3b.argmax(axis=2)
Am = np.take_along_axis(A3b, k[..., None], 2)[..., 0]; Lm = np.take_along_axis(L3b, k[..., None], 2)[..., 0]
s = c15 & (A15 >= 10) & (Am > 0) & (np.abs(Am / np.maximum(A15, 1e-9) - 1) < 0.1) & (L15 > 0)
ratio = Lm[s] / L15[s]; a = A15[s]
out['matched'] = {'n': int(s.sum()), 'median_L3_over_L15': round(float(np.median(ratio)), 4)}
for lo, hi in [(10, 100), (100, 1000), (1000, 1e5)]:
    m = (a >= lo) & (a < hi)
    if m.sum(): out['matched'][f'{lo:g}-{hi:g}'] = {'n': int(m.sum()), 'median_ratio': round(float(np.median(ratio[m])), 4)}
m = a >= 10
out['matched']['slope_logratio_vs_logA'] = round(float(np.polyfit(np.log10(a[m]), np.log10(ratio[m]), 1)[0]), 4)
json.dump(out, open('out/tasmania.json', 'w'), indent=1); print(json.dumps(out['matched']))
