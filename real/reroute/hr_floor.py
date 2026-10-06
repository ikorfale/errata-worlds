"""Is Greenland's 60-70N HydroRIVERS deficit a small-basin effect? h of HydroRIVERS mouths for A floors 10, 50, 200 km2,
in the calibration windows and in Greenland 60-70N (mouth = reach end point; window test on the reach bbox centre as in calib.py)."""
import numpy as np, struct, sys, json
sys.path.insert(0, '..'); from hack import fit, load, D
from calib import WIN
W = {k: (v[1], v[3]) for k, v in WIN.items()}; W['greenland60-70'] = ('gr', (-75.0, -10.0, 60.0, 70.0))
W['arctic-canada60-70'] = ('ar', (-180.0, -50.0, 60.0, 70.0)); W['eu60-70'] = ('eu', (-10.0, 40.0, 60.0, 70.0))
W['eu55-60'] = ('eu', (-10.0, 40.0, 55.0, 60.0)); W['na55-60'] = ('na', (-100.0, -50.0, 55.0, 60.0))
rng = np.random.default_rng(1); out = {}
for name, (reg, I) in W.items():
    dd = load(reg, {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
    oo = np.flatnonzero((dd['NEXT_DOWN'] == 0) & (dd['UPLAND_SKM'] >= 10) & (dd['UPLAND_SKM'] <= 1e6) & (dd['DIST_UP_KM'] > 0))
    base = f'{D}/HydroRIVERS_v10_{reg}_shp/HydroRIVERS_v10_{reg}'; shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); xy = np.zeros((len(oo), 2))
    with open(base + '.shp', 'rb') as f:
        for k, off in enumerate(shx[oo, 0].astype(np.int64) * 2):
            f.seek(off + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    s = (xy[:, 0] >= I[0]) & (xy[:, 0] <= I[1]) & (xy[:, 1] >= I[2]) & (xy[:, 1] <= I[3]); A, L = dd['UPLAND_SKM'][oo][s], dd['DIST_UP_KM'][oo][s]
    line = []
    for amin in (10, 50, 200):
        k = A >= amin; r = fit(A[k], L[k], rng, 300) if k.sum() >= 30 else None; out[f'{name} A>={amin}'] = r
        line.append(f'A>={amin:3d}: {r["h"]:.3f} [{r["ci"][0]:.3f},{r["ci"][1]:.3f}] n {r["n"]}' if r else f'A>={amin}: n<30')
    print(f'{name:15s} ' + ' | '.join(line), flush=True)
json.dump(out, open('hr_floor.json', 'w'), indent=1, default=float); print('__END__')
