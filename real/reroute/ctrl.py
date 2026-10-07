"""#168: Baffin and Iceland as low-slope controls for the Greenland ice/no-ice gap (zenith 75936, 76188). Bets C1-C3 in ../bets_ice.txt.
Same pipeline as ice_touch.py (HydroSHEDS 15" D8 basins, Natural Earth ice, slope from the raw 15" DEM, 10-50 km2 HydroRIVERS
mouths snapped within 25% area) plus check2.py (my route.c, mode 1, best cell within +-1 whose A is within 25%).
usage: ctrl.py baffin|iceland  -> ctrl_<name>.npy rows (A, L, ice_share, slope, x, y, A_me, L_me)"""
import numpy as np, json, sys, struct, subprocess, os
sys.path.insert(0, '..'); from hack import load, D; from win import window
R = 6371000.0; ND = 32767; d = 1 / 240
REG = {'baffin': ('ar', -180.0, (-91, -61, 59.5, 72), (60, 70)), 'iceland': ('eu', -25.0, (-25, -13, 62.5, 67.5), (60, 70))}
name = sys.argv[1]; reg, LON0, (x0, x1, y0, y1), (ylo, yhi) = REG[name]; LAT0 = 84.0
ra, rb, ca, cb = int((LAT0 - y1) * 240), int((LAT0 - y0) * 240), int((x0 - LON0) * 240), int((x1 - LON0) * 240)
n, m = rb - ra, cb - ca; N = n * m; print(name, n, m, flush=True)
dr = window(f'../data/dir/hyd_{reg}_dir_15s.tif', ra, rb, ca, cb)
code = {1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)}
jj, ii = np.divmod(np.arange(N, dtype=np.int32), m); p = np.arange(N, dtype=np.int32); fr = dr.ravel()
for c, (dj, di) in code.items():
    k = np.flatnonzero(fr == c); y, x = jj[k] + dj, ii[k] + di; ok = (y >= 0) & (y < n) & (x >= 0) & (x < m)
    p[k[ok]] = (y[ok] * m + x[ok]).astype(np.int32)
del jj, ii
land = fr != 255; sea2d = ~land.reshape(n, m).copy()
while True:
    q = p[p]
    if np.array_equal(q, p): break
    p = q
del q; root = p
edge = np.zeros((n, m), bool); edge[0] = edge[-1] = True; edge[:, 0] = edge[:, -1] = True
cut = np.zeros(N, bool); cut[root[(edge.ravel()) & land]] = True; del dr, fr, edge
exec(open('../ice.py').read().split('\ndef centres')[0])
recs = rings(f'{D}/ne_glac/ne_10m_glaciated_areas.shp', (x0 - 1, x1 + 1, y0 - 1, y1 + 1))
lat1 = y1 - (np.arange(int((y1 - y0) * 60)) + 0.5) / 60; lon1 = x0 + (np.arange(int((x1 - x0) * 60)) + 0.5) / 60
LO, LA = np.meshgrid(lon1, lat1); P = np.c_[LO.ravel(), LA.ravel()]; ice1 = np.zeros(len(P), bool)
for rs in recs:
    par = np.zeros(len(P), np.int8)
    for pth in rs:
        (a0, b0), (a1, b1) = pth.vertices.min(0), pth.vertices.max(0)
        k = np.flatnonzero((P[:, 0] >= a0) & (P[:, 0] <= a1) & (P[:, 1] >= b0) & (P[:, 1] <= b1))
        if len(k): par[k] += pth.contains_points(P[k])
    ice1 |= (par % 2 == 1)
ice1 = ice1.reshape(len(lat1), len(lon1)); print('ice share of window', round(float(ice1.mean()), 3), flush=True)
ice15 = np.repeat(np.repeat(ice1, 4, 0), 4, 1)[:n, :m].ravel(); del LO, LA, P
z = window(f'../data/dir/hyd_{reg}_dem_15s.tif', ra - 1, rb + 1, ca - 1, cb + 1)
lat = LAT0 - (ra + np.arange(n) + 0.5) * d
dy = R * np.radians(d); dx = (dy * np.cos(np.radians(lat))).astype(np.float32)
zf = z[1:-1, 1:-1].astype(np.float32); zf[sea2d | (zf == ND)] = np.nan; zf.tofile(f'ctrl_{name}.f32'); dx.tofile(f'ctrl_{name}.dx.f32'); del zf
z[z == ND] = 0
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
dd = load(reg, {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
oo = np.flatnonzero((dd['NEXT_DOWN'] == 0) & (dd['UPLAND_SKM'] >= 10) & (dd['UPLAND_SKM'] < 50) & (dd['DIST_UP_KM'] > 0))
base = f'{D}/HydroRIVERS_v10_{reg}_shp/HydroRIVERS_v10_{reg}'; shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2)
rows = []
with open(base + '.shp', 'rb') as f:
    for k in oo:
        f.seek(int(shx[k, 0]) * 2 + 8 + 4); bb = struct.unpack('<4d', f.read(32))
        if bb[2] < x0 or bb[0] > x1 or bb[3] < ylo or bb[1] >= yhi: continue
        npart, npt = struct.unpack('<2i', f.read(8)); f.read(4 * npart)
        pts = np.frombuffer(f.read(16 * npt), '<f8').reshape(-1, 2); best = None
        for x, y in (pts[0], pts[-1]):
            if not (ylo <= y < yhi and x0 <= x < x1): continue
            j, i = int((LAT0 - y) / d) - ra, int((x - LON0) / d) - ca
            if not (0 <= j < n and 0 <= i < m): continue
            r = root[j * m + i]; a = AREA[r]
            if a > 0 and (best is None or abs(np.log(a / dd['UPLAND_SKM'][k])) < best[0]): best = (abs(np.log(a / dd['UPLAND_SKM'][k])), r, x, y)
        if best and best[0] < np.log(1.25) and not cut[best[1]]:
            r = best[1]; rows.append([dd['UPLAND_SKM'][k], dd['DIST_UP_KM'][k], ICE[r] / CELLS[r], SLO[r] / CELLS[r], best[2], best[3]])
del root, AREA, CELLS, ICE, SLO, cut, dd, p
print('mouths', len(rows), flush=True)
rc = subprocess.run(['./route', f'ctrl_{name}.f32', str(n), str(m), f'ctrl_{name}.dx.f32', repr(float(dy)), '1', f'ctrl_{name}_me'], capture_output=True, text=True)
print('route rc', rc.returncode, rc.stdout.strip()[-200:], flush=True)
A = np.fromfile(f'ctrl_{name}_me.A', np.float32).reshape(n, m); L = np.fromfile(f'ctrl_{name}_me.L', np.float32).reshape(n, m)
for row in rows:
    j, i = int((LAT0 - row[5]) / d) - ra, int((row[4] - LON0) / d) - ca; best = None
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            jj_, ii_ = j + dj, i + di
            if 0 <= jj_ < n and 0 <= ii_ < m and A[jj_, ii_] > 0:
                e = abs(np.log(A[jj_, ii_] / row[0]))
                if best is None or e < best[0]: best = (e, jj_, ii_)
    row += [A[best[1], best[2]], L[best[1], best[2]]] if best and best[0] < np.log(1.25) else [np.nan, np.nan]
np.save(f'ctrl_{name}.npy', np.array(rows, float))
if not os.environ.get('KEEP'):
  for s in ('.f32', '.dx.f32', '_me.A', '_me.L', '_me.rec'): os.remove(f'ctrl_{name}{s}')
print('__END__')
