"""#165 (zenith 76188, check 1): how much of each main stem runs where the terrain does not set the route?
Longest flow path on the HydroSHEDS 15" D8 grid (the grid HydroRIVERS was cut from): source = basin cell farthest from the
mouth by D8 path length; walk it down to the mouth, read each step's drop from the raw 15" DEM. A step that does not descend
(z_next >= z_cur) is routed by fill / flat resolution / carving, not by the terrain.
(First try used HydroRIVERS polylines: invalid, they omit headwaters above 10 km2 and are simplified to few vertices.)
Basins: 60-70N Greenland HydroRIVERS mouths with UPLAND 10-50 km2 snapped to D8 basins as in ice_touch.py; ice share and mean
slope joined from ice_touch.npy by exact (UPLAND_SKM, DIST_UP_KM)."""
import numpy as np, json, sys, struct, tifffile, warnings
warnings.simplefilter('ignore')
sys.path.insert(0, '..'); from hack import load, D
R = 6371000.0; ND = 32767; d = 1 / 240; LAT0, LON0 = 84.0, -74.0
ra, rb, ca, cb = int((84 - 72) * 240), int((84 - 59.5) * 240), int((-60 + 74) * 240), int((-15 + 74) * 240)
n, m = rb - ra, cb - ca; N = n * m
with tifffile.TiffFile('../data/dir/hyd_gr_dir_15s.tif') as t: fr = t.pages[0].asarray()[ra:rb, ca:cb].ravel().copy()
lat = LAT0 - (ra + np.arange(n) + 0.5) * d
dy = R * np.radians(d) / 1000; dxr = (dy * np.cos(np.radians(lat))).astype(np.float32)
code = {1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)}
p = np.arange(N, dtype=np.int32); w = np.zeros(N, np.float32)
for c, (dj, di) in code.items():
    k = np.flatnonzero(fr == c); y, x = k // m + dj, k % m + di; ok = (y >= 0) & (y < n) & (x >= 0) & (x < m)
    p[k[ok]] = (y[ok] * m + x[ok]).astype(np.int32)
    w[k[ok]] = np.hypot(dxr[(k[ok] // m)] * abs(di), dy * abs(dj))
land = fr != 255; del fr
p0 = p.copy(); dist = w.copy(); del w
for it in range(40):
    q = p[p]
    if np.array_equal(q, p): break
    dist += dist[p]; p = q
del q; root = p; print('doubling iterations', it, flush=True)
jj = np.arange(N) // m
edge = (jj == 0) | (jj == n - 1) | (np.arange(N) % m == 0) | (np.arange(N) % m == m - 1)
cut = np.zeros(N, bool); cut[root[edge & land]] = True; del edge
carea = ((R * np.radians(d)) ** 2 * np.cos(np.radians(lat)) / 1e6).astype(np.float32)
AREA = np.bincount(root[land], carea[jj[land]], minlength=N).astype(np.float32); del jj
lidx = np.flatnonzero(land); o = lidx[np.argsort(dist[lidx], kind='stable')]
src = np.full(N, -1, np.int64); src[root[o]] = o; del o, lidx           # last write = farthest cell
with tifffile.TiffFile('../data/dir/hyd_gr_dem_15s.tif') as t: z = t.pages[0].asarray()[ra:rb, ca:cb].ravel().astype(np.float32)
z[z == ND] = np.nan
noLower = np.zeros(N, bool); Z = z.reshape(n, m)
for j0 in range(0, n, 300):                                                 # strips, float32: no lower 8-neighbour (sea = lower)
    j1 = min(j0 + 300, n); a0, a1 = max(j0 - 1, 0), min(j1 + 1, n)
    blk = np.where(np.isnan(Z[a0:a1]), np.float32(-1e9), Z[a0:a1]).astype(np.float32)
    P = np.pad(blk, ((1 if j0 == 0 else 0, 1 if j1 == n else 0), (1, 1)), constant_values=np.inf); c = blk[j0 - a0:j0 - a0 + j1 - j0]
    low = np.zeros(c.shape, bool)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            if dj or di: low |= P[1 + dj:1 + dj + j1 - j0, 1 + di:1 + di + m] < c
    noLower[j0 * m:j1 * m] = (~low).ravel()
noLower &= land; del Z, P, blk, low
dd = load('gr', {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
oo = np.flatnonzero((dd['NEXT_DOWN'] == 0) & (dd['UPLAND_SKM'] >= 10) & (dd['UPLAND_SKM'] < 50) & (dd['DIST_UP_KM'] > 0))
base = f'{D}/HydroRIVERS_v10_gr_shp/HydroRIVERS_v10_gr'; shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2)
X = np.load('ice_touch.npy'); join = {(round(float(a), 3), round(float(l), 3)): (ic, sl) for a, l, ic, sl in X[:, :4]}
rows = []
with open(base + '.shp', 'rb') as f:
    for k in oo:
        f.seek(int(shx[k, 0]) * 2 + 8 + 4 + 32); npart, npt = struct.unpack('<2i', f.read(8)); f.read(4 * npart)
        pts = np.frombuffer(f.read(16 * npt), '<f8').reshape(-1, 2); best = None
        for x, y in (pts[0], pts[-1]):
            if not (60 <= y < 70): continue
            j, i = int((LAT0 - y) / d) - ra, int((x - LON0) / d) - ca
            if not (0 <= j < n and 0 <= i < m): continue
            rr = root[j * m + i]; a = AREA[rr]
            if a > 0 and (best is None or abs(np.log(a / dd['UPLAND_SKM'][k])) < best[0]): best = (abs(np.log(a / dd['UPLAND_SKM'][k])), rr)
        if not best or best[0] >= np.log(1.25) or cut[best[1]]: continue
        jn = join.get((round(float(dd['UPLAND_SKM'][k]), 3), round(float(dd['DIST_UP_KM'][k]), 3)))
        if jn is None: continue
        c = src[best[1]]; path = [c]
        while p0[c] != c: c = p0[c]; path.append(c)
        path = np.array(path); zz = z[path]; seg = (dist[path[:-1]] - dist[path[1:]])
        dz = zz[1:] - zz[:-1]; nond = ~(dz < 0)                    # nan (sea/void) counts as not terrain-set
        rows.append((dd['UPLAND_SKM'][k], dd['DIST_UP_KM'][k], jn[0], jn[1], seg.sum(), seg[nond].sum(), seg[dz == 0].sum(), len(seg), seg[noLower[path[:-1]]].sum()))
Y = np.array(rows); A0, L0, ice, slo, Lg, Ln, Lz, ns, Lf = Y.T; shf = Lf / Lg; Ef = L0 * (1 - shf) / np.sqrt(A0)
print('basins', len(Y), 'median Lgrid/DIST_UP %.3f [p10 %.3f p90 %.3f]' % tuple(np.percentile(Lg / L0, [50, 10, 90])), flush=True)
t = ice > 0; E = L0 / np.sqrt(A0); sh = Ln / Lg; Ed = L0 * (1 - sh) / np.sqrt(A0)
edges = np.quantile(slo, np.linspace(0, 1, 7)); out = {'n': len(Y), 'Lgrid/DIST_UP median': float(np.median(Lg / L0)), 'bins': []}
def summ(g): return {'n': int(g.sum()), 'share_nondesc': round(float(np.median(sh[g])), 3), 'mean_share': round(float(np.mean(sh[g])), 3),
                     'share_zero': round(float(np.median(Lz[g] / Lg[g])), 3), 'E': round(float(np.median(E[g])), 2), 'E_desc': round(float(np.median(Ed[g])), 2), 'share_nolower': round(float(np.median(shf[g])), 3), 'E_off_nolower': round(float(np.median(Ef[g])), 2)}
for b in range(6):
    s = (slo >= edges[b]) & (slo <= edges[b + 1])
    row = {'bin': b, 'lo': round(float(edges[b]), 3), 'hi': round(float(edges[b + 1]), 3), 'touch': summ(s & t), 'no': summ(s & ~t)}
    row['ratio_E'] = round(row['touch']['E'] / row['no']['E'], 2); row['ratio_E_desc'] = round(row['touch']['E_desc'] / row['no']['E_desc'], 2)
    out['bins'].append(row); print(row, flush=True)
f3 = slo <= edges[3]
out['flat3 touch'], out['flat3 no'] = summ(f3 & t), summ(f3 & ~t)
out['flat3 ratio E'] = round(out['flat3 touch']['E'] / out['flat3 no']['E'], 2); out['flat3 ratio E_desc'] = round(out['flat3 touch']['E_desc'] / out['flat3 no']['E_desc'], 2)
out['flat3 ratio E_off_nolower'] = round(out['flat3 touch']['E_off_nolower'] / out['flat3 no']['E_off_nolower'], 2); print('flat3 ratio E_off_nolower', out['flat3 ratio E_off_nolower']); print('flat3 touch', out['flat3 touch']); print('flat3 no', out['flat3 no']); print('flat3 ratio E', out['flat3 ratio E'], 'E_desc', out['flat3 ratio E_desc'])
np.save('flatpath.npy', Y); json.dump(out, open('flatpath.json', 'w'), indent=1); print('__END__')
