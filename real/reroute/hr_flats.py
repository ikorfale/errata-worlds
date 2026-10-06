"""zenith 75539/75517 tested where the deficit lives: do HydroRIVERS mouths at 60-70N Greenland with flatter basins have a
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
# flats from the raw DEM (with a 1-cell halo from the full file)
with tifffile.TiffFile('../data/dir/hyd_gr_dem_15s.tif') as t: dem = t.pages[0].asarray()
z = dem[max(ra - 1, 0):rb + 1, ca - 1:cb + 1].astype(np.float32); del dem
zl = z != ND; z[~zl] = -1e9; core = z[1:-1, 1:-1]; lower = np.zeros(core.shape, bool)
for dj in (-1, 0, 1):
    for di in (-1, 0, 1):
        if dj or di: lower |= z[1 + dj:z.shape[0] - 1 + dj, 1 + di:z.shape[1] - 1 + di] < core
demland = zl[1:-1, 1:-1].ravel(); flat = demland & ~lower.ravel(); del z, zl, core, lower
lat = LAT0 - (ra + np.arange(n) + 0.5) * d; carea = ((R * np.radians(d)) ** 2 * np.cos(np.radians(lat)) / 1e6).astype(np.float32)
area_w = np.repeat(carea, m)
rl = root[land]; AREA = np.bincount(rl, area_w[land], minlength=N).astype(np.float32)
CELLS = np.bincount(rl, minlength=N).astype(np.int32)
FLAT = np.bincount(root[land & flat], minlength=N).astype(np.int32); del rl, area_w
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
            if a > 0 and (best is None or abs(np.log(a / dd['UPLAND_SKM'][k])) < best[0]): best = (abs(np.log(a / dd['UPLAND_SKM'][k])), r)
        if best and best[0] < np.log(1.25) and not cut[best[1]]:
            r = best[1]; rows.append((dd['UPLAND_SKM'][k], dd['DIST_UP_KM'][k], FLAT[r] / max(CELLS[r], 1)))
X = np.array(rows); A, L, s = X[:, 0], X[:, 1], X[:, 2]; rng = np.random.default_rng(1); out = {'matched': len(X), 'of': int(len(oo))}
print(f'HydroRIVERS mouths in gr: {len(oo)} (all latitudes); matched at 60-70N: {len(X)}; median flat share {np.median(s):.3f}')
out['all'] = fit(A, L, rng, 300); print('all matched:', out['all'])
for amin in (10, 50):
    k0 = A >= amin; med = np.median(s[k0])
    for tag, k in (('low', k0 & (s <= med)), ('high', k0 & (s > med))):
        r = fit(A[k], L[k], rng, 300); out[f'A>={amin} {tag}'] = dict(r, mean_share=float(s[k].mean()), medA=float(np.median(A[k])))
        print(f'A>={amin:2d} {tag:4s} (mean flat {s[k].mean():.2f}, split {med:.2f}, median A {np.median(A[k]):5.0f}): h {r["h"]:.3f} [{r["ci"][0]:.3f}, {r["ci"][1]:.3f}] n {r["n"]}')
    Xm = np.c_[np.ones(k0.sum()), np.log10(A[k0]), s[k0]]; y = np.log10(L[k0]); beta = np.linalg.lstsq(Xm, y, rcond=None)[0]; bs = []
    for _ in range(300):
        i = rng.integers(0, k0.sum(), k0.sum()); bs.append(np.linalg.lstsq(Xm[i], y[i], rcond=None)[0])
    bs = np.array(bs); out[f'A>={amin} joint'] = {'h': float(beta[1]), 'b_share': float(beta[2]), 'b_ci': np.percentile(bs[:, 2], [2.5, 97.5]).tolist()}
    print(f'   joint: h {beta[1]:.3f}, share coef {beta[2]:+.3f} [{out[f"A>={amin} joint"]["b_ci"][0]:+.3f}, {out[f"A>={amin} joint"]["b_ci"][1]:+.3f}]')
json.dump(out, open('hr_flats.json', 'w'), indent=1); print('__END__')
