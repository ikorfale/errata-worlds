"""ice_touch.py (zenith 75692): truncation at the ice margin vs narrow strip vs planar walls, 10-50 km2 mouths at 60-70N.
Based on hr_flats.py. Bets T1-T3 in ../bets_ice.txt.
Original hr_flats doc: zenith 75539/75517 tested where the deficit lives: do HydroRIVERS mouths at 60-70N Greenland with flatter basins have a
lower Hack exponent? Basins from the HydroSHEDS 15" D8 grid (pointer doubling), flats from the raw 15" DEM (no strictly lower
8-neighbour, sea = lower). Each HydroRIVERS mouth is snapped to the basin of one of its reach end points (the one whose
basin area is closer to UPLAND_SKM); kept if that area is within 25%. Window 59.5-72N, 60-15W; basins cut by the frame dropped."""
import numpy as np, json, sys, os, struct, tifffile, warnings
warnings.simplefilter('ignore')
sys.path.insert(0, '..'); from hack import fit, load, D
R = 6371000.0; ND = 32767; d = 1 / 240; LAT0, LON0 = 84.0, -74.0
ra, rb, ca, cb = int((84 - 72) * 240), int((84 - 59.5) * 240), int((-60 + 74) * 240), int((-15 + 74) * 240)
n, m = rb - ra, cb - ca; N = n * m
with tifffile.TiffFile('../data/dir/hyd_gr_dir_15s.tif') as t: dr = t.pages[0].asarray()[ra:rb, ca:cb].copy()
code = {1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)}
jj, ii = np.divmod(np.arange(N, dtype=np.int32), m); p = np.arange(N, dtype=np.int32); fr = dr.ravel()
for c, (dj, di) in code.items():
    k = np.flatnonzero(fr == c); y, x = jj[k] + dj, ii[k] + di; ok = (y >= 0) & (y < n) & (x >= 0) & (x < m)
    p[k[ok]] = (y[ok] * m + x[ok]).astype(np.int32)
del jj, ii
land = fr != 255
while True:
    q = p[p]
    if np.array_equal(q, p): break
    p = q
del q; root = p
edge = np.zeros((n, m), bool); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
cut = np.zeros(N, bool); cut[root[(edge.ravel()) & land]] = True

del dr, fr, edge
sys.path.insert(0, '..'); exec(open('../ice.py').read().split('\ndef centres')[0])
recs = rings(f'{D}/ne_glac/ne_10m_glaciated_areas.shp', (-75, -10, 59, 84))
# ice raster at 1' over the window, then 15" cells inherit it
lat1 = 72 - (np.arange(int(12.5 * 60)) + 0.5) / 60; lon1 = -60 + (np.arange(45 * 60) + 0.5) / 60
LO, LA = np.meshgrid(lon1, lat1); P = np.c_[LO.ravel(), LA.ravel()]; ice1 = np.zeros(len(P), bool)
for rs in recs:
    par = np.zeros(len(P), np.int8)
    for pth in rs:
        (x0, y0), (x1, y1) = pth.vertices.min(0), pth.vertices.max(0)
        k = np.flatnonzero((P[:, 0] >= x0) & (P[:, 0] <= x1) & (P[:, 1] >= y0) & (P[:, 1] <= y1))
        if len(k): par[k] += pth.contains_points(P[k])
    ice1 |= (par % 2 == 1)
ice1 = ice1.reshape(len(lat1), len(lon1)); print('ice share of 1-min window', round(float(ice1.mean()), 3), flush=True)
ice15 = np.repeat(np.repeat(ice1, 4, 0), 4, 1)[:n, :m].ravel()
# slope from the raw 15" DEM, central differences, metric
with tifffile.TiffFile('../data/dir/hyd_gr_dem_15s.tif') as t: dem = t.pages[0].asarray()
z = dem[ra - 1:rb + 1, ca - 1:cb + 1].copy(); del dem
z[z == ND] = 0
lat = LAT0 - (ra + np.arange(n) + 0.5) * d
dy = R * np.radians(d); dx = (dy * np.cos(np.radians(lat))).astype(np.float32)
slope = np.empty(N, np.float32)
for j0 in range(0, n, 500):
    j1 = min(j0 + 500, n); zc = z[j0:j1 + 2].astype(np.float32)
    gx = (zc[1:-1, 2:] - zc[1:-1, :-2]) / (2 * dx[j0:j1, None]); gy = (zc[2:, 1:-1] - zc[:-2, 1:-1]) / (2 * dy)
    slope[j0 * m:j1 * m] = np.hypot(gx, gy).ravel()
del z, zc, gx, gy
carea = ((R * np.radians(d)) ** 2 * np.cos(np.radians(lat)) / 1e6).astype(np.float32); area_w = np.repeat(carea, m)
rl = root[land]; AREA = np.bincount(rl, area_w[land], minlength=N).astype(np.float32)
CELLS = np.bincount(rl, minlength=N).astype(np.int32)
ICE = np.bincount(root[land & ice15], minlength=N).astype(np.int32)
SLO = np.bincount(rl, slope[land], minlength=N).astype(np.float32); del rl, area_w, slope
V = np.vstack([p.vertices for rs in recs for p in rs])
def unit(ll): la, lo = np.radians(ll[:, 1]), np.radians(ll[:, 0]); return np.c_[np.cos(la)*np.cos(lo), np.cos(la)*np.sin(lo), np.sin(la)]
U = unit(V)
dd = load('gr', {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
oo = np.flatnonzero((dd['NEXT_DOWN'] == 0) & (dd['UPLAND_SKM'] >= 10) & (dd['UPLAND_SKM'] <= 1e6) & (dd['DIST_UP_KM'] > 0))
base = f'{D}/HydroRIVERS_v10_gr_shp/HydroRIVERS_v10_gr'; shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2)
rows = []
with open(base + '.shp', 'rb') as f:
    for k in oo:
        f.seek(int(shx[k, 0]) * 2 + 8 + 4 + 32); npart, npt = struct.unpack('<2i', f.read(8)); f.read(4 * npart)
        pts = np.frombuffer(f.read(16 * npt), '<f8').reshape(-1, 2); best = None
        for x, y in (pts[0], pts[-1]):
            if not (60 <= y < 70): continue
            j, i = int((LAT0 - y) / d) - ra, int((x - LON0) / d) - ca
            if not (0 <= j < n and 0 <= i < m): continue
            r = root[j * m + i]; a = AREA[r]
            if a > 0 and (best is None or abs(np.log(a / dd['UPLAND_SKM'][k])) < best[0]): best = (abs(np.log(a / dd['UPLAND_SKM'][k])), r, x, y)
        if best and best[0] < np.log(1.25) and not cut[best[1]]:
            r = best[1]; rows.append((dd['UPLAND_SKM'][k], dd['DIST_UP_KM'][k], ICE[r] / CELLS[r], SLO[r] / CELLS[r], best[2], best[3]))
X = np.array(rows); A, L, ice, slo = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
Mx = unit(X[:, 4:6]); dmin = np.empty(len(X))
for i in range(0, len(X), 64): dmin[i:i+64] = 6371 * np.arccos(np.clip((Mx[i:i+64] @ U.T).max(1), -1, 1))
dmin[ice1.ravel()[np.clip(((72 - X[:, 5]) * 60).astype(int), 0, len(lat1) - 1) * len(lon1) + np.clip(((X[:, 4] + 60) * 60).astype(int), 0, len(lon1) - 1)]] = 0.0
E = L / np.sqrt(A)
def rho(a, b):
    ra_, rb_ = np.argsort(np.argsort(a)), np.argsort(np.argsort(b)); return float(np.corrcoef(ra_, rb_)[0, 1])
rng = np.random.default_rng(75692)
def rho_ci(a, b):
    bs = [rho(a[i], b[i]) for i in (rng.integers(0, len(a), len(a)) for _ in range(500))]; return [round(float(v), 3) for v in np.percentile(bs, [2.5, 97.5])]
out = {'matched': len(X)}
s = (A >= 10) & (A <= 50); t = ice > 0
print(f'matched 60-70N: {len(X)}; 10-50 km2: {s.sum()}; touching ice: {(s & t).sum()}; not: {(s & ~t).sum()}')
for tag, k in (('touch', s & t), ('no touch', s & ~t)):
    out[tag] = {'n': int(k.sum()), 'median E': round(float(np.median(E[k])), 3), 'median A': round(float(np.median(A[k])), 1),
                'median dist km': round(float(np.median(dmin[k])), 1), 'median slope': round(float(np.median(slo[k])), 3),
                'median ice share': round(float(np.median(ice[k])), 3)}
    print(tag, out[tag])
out['T1 ratio'] = round(out['touch']['median E'] / out['no touch']['median E'], 3)
k = s & ~t
for name, v in (('rho(E,dist) no touch', dmin), ('rho(E,slope) no touch', slo), ('rho(E,A) no touch', A)):
    out[name] = {'rho': round(rho(E[k], v[k]), 3), 'ci': rho_ci(E[k], v[k])}; print(name, out[name])
k2 = s & t
for name, v in (('rho(E,dist) touch', dmin), ('rho(E,slope) touch', slo), ('rho(E,ice share) touch', ice)):
    out[name] = {'rho': round(rho(E[k2], v[k2]), 3), 'ci': rho_ci(E[k2], v[k2])}; print(name, out[name])
# E by distance bins in the non-touching group
for lo_, hi_ in ((0, 2), (2, 5), (5, 10), (10, 30), (30, 1e9)):
    kk = k & (dmin >= lo_) & (dmin < hi_)
    if kk.sum(): out[f'no touch d {lo_}-{hi_}'] = {'n': int(kk.sum()), 'median E': round(float(np.median(E[kk])), 3)}; print(f'no touch d {lo_}-{hi_}', out[f'no touch d {lo_}-{hi_}'])
np.save('ice_touch.npy', X); json.dump(out, open('ice_touch.json', 'w'), indent=1); print('__END__')
