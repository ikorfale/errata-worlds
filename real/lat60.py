"""#134 confound check: north of 60N HydroSHEDS uses the coarser HYDRO1k DEM instead of SRTM. Within one region (eu),
compare outlet h (A 1e2-1e6 km2) above and below 60N; the same landscape family on two grids."""
import numpy as np, struct, json
from hack import load, fit, D
def centres(region, idx):
    base = f'{D}/HydroRIVERS_v10_{region}_shp/HydroRIVERS_v10_{region}'
    shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); xy = np.zeros((len(idx), 2))
    with open(base + '.shp', 'rb') as f:
        for k, o in enumerate(shx[idx, 0].astype(np.int64) * 2):
            f.seek(o + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0]+b[2])/2, (b[1]+b[3])/2)
    return xy
rng = np.random.default_rng(1); res = {}
d = load('eu', {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
o = np.flatnonzero((d['NEXT_DOWN'] == 0) & (d['UPLAND_SKM'] >= 1e2) & (d['UPLAND_SKM'] <= 1e6) & (d['DIST_UP_KM'] > 0))
A, L, y = d['UPLAND_SKM'][o], d['DIST_UP_KM'][o], centres('eu', o)[:, 1]
for name, s in [('eu <55N', y < 55), ('eu 55-60N', (y >= 55) & (y < 60)), ('eu >=60N (HYDRO1k)', y >= 60)]:
    res[name] = fit(A[s], L[s], rng, 500); print(name, res[name])
json.dump(res, open('out/lat60.json', 'w'), default=float)
