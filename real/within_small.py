"""Zenith's check (74799): within-basin Hack h restricted to small reaches, plus a band ladder.
Per basin (outlet A >= 1e4 km^2): OLS log L on log A over reaches in each A band (>= 30 reaches in band).
Also a pooled per-region fit with basin fixed effects (demeaned within basin) on 10-300 km^2."""
import numpy as np, json
from hack import load
bands = [(10, 300), (10, 100), (100, 1e3), (1e3, 1e4), (1e4, 1e7)]
res = {}
for reg in ['eu', 'af', 'na', 'sa', 'as', 'au']:
    r = load(reg, {'MAIN_RIV', 'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
    A, L, M, nd = r['UPLAND_SKM'], r['DIST_UP_KM'], r['MAIN_RIV'].astype(np.int64), r['NEXT_DOWN']
    outA = {int(m): a for m, a in zip(M[nd == 0], A[nd == 0])}
    order = np.argsort(M, kind='stable'); Ms = M[order]
    cuts = np.flatnonzero(np.diff(Ms)) + 1; starts = np.r_[0, cuts]; ends = np.r_[cuts, len(Ms)]
    hb = {b: [] for b in bands}; px, py = [], []
    for s, e in zip(starts, ends):
        m = int(Ms[s])
        if outA.get(m, 0) < 1e4: continue
        idx = order[s:e]; a, l = A[idx], L[idx]
        for lo, hi in bands:
            ok = (a >= lo) & (a < hi) & (l > 0)
            if ok.sum() < 30: continue
            x, y = np.log10(a[ok]), np.log10(l[ok])
            hb[(lo, hi)].append(np.polyfit(x, y, 1)[0])
            if (lo, hi) == (10, 300): px.append(x - x.mean()); py.append(y - y.mean())
    px, py = np.concatenate(px), np.concatenate(py)
    out = {f'{lo:g}-{hi:g}': {'basins': len(v), 'median_h': round(float(np.median(v)), 4),
           'iqr': [round(float(q), 3) for q in np.percentile(v, [25, 75])]} for (lo, hi), v in hb.items() if v}
    out['pooled_fe_10-300'] = {'h': round(float((px @ py) / (px @ px)), 4), 'n': int(len(px))}
    res[reg] = out; print(reg, json.dumps(out), flush=True)
json.dump(res, open('out/within_small.json', 'w'), indent=1)
