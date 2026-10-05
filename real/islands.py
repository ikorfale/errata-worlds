"""#144: Hack's law on real islands. Outlet reaches (NEXT_DOWN=0) of HydroRIVERS, located by the bbox centre of their
polyline (.shp via .shx), grouped into islands by bounding box with a few carve-outs. Aisl = sum of outlet areas,
Ri = sqrt(Aisl/pi); a = A/Aisl, l = L/Ri. Bets in bets_islands.txt (written before this ran)."""
import numpy as np, struct, json, os
from hack import load, D
ISL = {  # name: region, lon0, lon1, lat0, lat1, exclude(lon,lat)->bool
 'Great Britain': ('eu', -6.4, 1.8, 49.9, 58.7, lambda x, y: (54 <= y <= 55.3) & (x < -5.3)),
 'Ireland': ('eu', -10.7, -5.4, 51.4, 55.4, lambda x, y: (y > 55.25) & (x > -6.0)),
 'Iceland': ('eu', -24.6, -13.4, 63.2, 66.6, None),
 'Corsica': ('eu', 8.5, 9.6, 41.35, 43.1, None),
 'Sardinia': ('eu', 8.1, 9.9, 38.8, 41.3, None),
 'Sicily': ('eu', 12.3, 15.65, 36.6, 38.3, None),
 'Crete': ('eu', 23.5, 26.4, 34.8, 35.7, None),
 'Tasmania': ('au', 143.8, 148.5, -43.8, -40.6, None),
 'NZ North': ('au', 172.5, 178.7, -41.8, -34.3, lambda x, y: not (y > -40.2 or (x > 174.5))),
 'NZ South': ('au', 166.3, 174.5, -47.4, -40.4, lambda x, y: (y > -40.2)),
 'New Guinea': ('au', 130.9, 150.9, -10.4, -0.3, lambda x, y: (x > 148.2) & (y > -6.4)),
 'Borneo': ('au', 108.8, 119.3, -4.2, 7.4, None),
 'Java': ('au', 105.1, 114.5, -8.8, -5.8, None),
 'Sumatra': ('au', 95.0, 106.1, -6.0, 5.9, lambda x, y: (x > 100.2) & (y > 1.2)),
}
def centres(region, idx):
    base = f'{D}/HydroRIVERS_v10_{region}_shp/HydroRIVERS_v10_{region}'
    shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2)
    off = shx[idx, 0].astype(np.int64) * 2
    xy = np.zeros((len(idx), 2))
    with open(base + '.shp', 'rb') as f:
        for k, o in enumerate(off):
            f.seek(o + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0]+b[2])/2, (b[1]+b[3])/2)
    return xy
def fit(a, l):
    if len(a) < 6: return None
    return round(float(np.polyfit(np.log10(a), np.log10(l), 1)[0]), 3)
cache, rows, pool = {}, {}, []
for name, (reg, x0, x1, y0, y1, ex) in ISL.items():
    if reg not in cache:
        r = load(reg, {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
        o = np.flatnonzero((r['NEXT_DOWN'] == 0) & (r['UPLAND_SKM'] > 0) & (r['DIST_UP_KM'] > 0))
        cache[reg] = (r['UPLAND_SKM'][o], r['DIST_UP_KM'][o], centres(reg, o))
    A, L, xy = cache[reg]
    s = (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
    if ex is not None: s &= ~np.array([bool(ex(x, y)) for x, y in xy])
    a_, L_ = A[s], L[s]; Ai = a_.sum(); Ri = np.sqrt(Ai / np.pi); a, l = a_ / Ai, L_ / Ri
    big, small = (a >= 0.01) & (a <= 0.5), (a >= 1e-4) & (a < 1e-2)
    rows[name] = {'n_out': int(s.sum()), 'Aisl_km2': round(float(Ai)), 'n_big': int(big.sum()), 'h_small': fit(a[small], l[small]),
                  'h_big': fit(a[big], l[big]), 'l_med_a>=0.05': round(float(np.median(l[a >= 0.05])), 3) if (a >= 0.05).any() else None,
                  'largest_a': round(float(a.max()), 3)}
    pool.append(np.c_[a, l]); print(name, rows[name], flush=True)
P = np.vstack(pool); a, l = P[:, 0], P[:, 1]
big, small = (a >= 0.01) & (a <= 0.5), (a >= 1e-4) & (a < 1e-2)
res = {'pooled_h_small': fit(a[small], l[small]), 'pooled_h_big': fit(a[big], l[big]), 'n_small': int(small.sum()), 'n_big': int(big.sum()),
       'median_l_a>=0.05': round(float(np.median(l[a >= 0.05])), 3), 'n_a>=0.05': int((a >= 0.05).sum())}
q = [r for r in rows.values() if r['n_big'] >= 8 and r['h_big'] is not None and r['h_small'] is not None]
res['I3'] = f"{sum(r['h_big'] < r['h_small'] for r in q)}/{len(q)} islands with >=8 big outlets have h_big < h_small"
print(res); json.dump({'islands': rows, 'pooled': res}, open('out/islands.json', 'w'), indent=1)
np.save('out/islands_pool.npy', P)
