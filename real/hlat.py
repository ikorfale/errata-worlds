"""#159: outlet h by latitude band inside Greenland (gr) and the North American Arctic (ar).
If the north-south lean of the lat/long D8 grid (dircodes2.py) shapes basins, h should fall with latitude in both."""
import numpy as np, json
from hack import load, fit
import struct
from hack import D
def centres(region, idx):
    base = f'{D}/HydroRIVERS_v10_{region}_shp/HydroRIVERS_v10_{region}'
    shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); xy = np.zeros((len(idx), 2))
    with open(base + '.shp', 'rb') as f:
        for k, o in enumerate(shx[idx, 0].astype(np.int64) * 2):
            f.seek(o + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0]+b[2])/2, (b[1]+b[3])/2)
    return xy
rng = np.random.default_rng(1); res = {}
for reg in ('gr', 'ar'):
    d = load(reg, {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
    o = np.flatnonzero((d['NEXT_DOWN'] == 0) & (d['UPLAND_SKM'] >= 10) & (d['UPLAND_SKM'] <= 1e6) & (d['DIST_UP_KM'] > 0))
    A, L, y = d['UPLAND_SKM'][o], d['DIST_UP_KM'][o], centres(reg, o)[:, 1]
    for lo, hi in ((60, 70), (70, 75), (75, 84)):
        s = (y >= lo) & (y < hi)
        if s.sum() < 30: continue
        r = fit(A[s], L[s], rng, 500); res[f'{reg} {lo}-{hi}N'] = r; print(reg, lo, hi, r, flush=True)
json.dump(res, open('out/hlat.json', 'w'), default=float)
print('__END__')
