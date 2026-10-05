"""Within-basin Hack fits (Hack 1957 style): for each large basin, OLS of log L on log A over all its reaches."""
import numpy as np, json, sys
from hack import load
res = {}
for reg in ['eu', 'af', 'na', 'sa', 'as', 'au']:
    r = load(reg, {'MAIN_RIV', 'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
    A, L, M, nd = r['UPLAND_SKM'], r['DIST_UP_KM'], r['MAIN_RIV'].astype(np.int64), r['NEXT_DOWN']
    outA = {int(m): a for m, a, n in zip(M[nd == 0], A[nd == 0], nd[nd == 0])}
    order = np.argsort(M, kind='stable'); Ms = M[order]
    cuts = np.flatnonzero(np.diff(Ms)) + 1; starts = np.r_[0, cuts]; ends = np.r_[cuts, len(Ms)]
    hs = {}
    for s, e in zip(starts, ends):
        m = int(Ms[s]); a_out = outA.get(m, 0)
        if a_out < 1e4: continue
        idx = order[s:e]; ok = (A[idx] >= 10) & (L[idx] > 0)
        x, y = np.log10(A[idx][ok]), np.log10(L[idx][ok])
        if len(x) < 50: continue
        hs[m] = (np.polyfit(x, y, 1)[0], a_out, len(x))
    h = np.array([v[0] for v in hs.values()]); a = np.array([v[1] for v in hs.values()])
    res[reg] = {'basins': len(h), 'median_h': round(float(np.median(h)), 4), 'iqr': [round(float(v), 4) for v in np.percentile(h, [25, 75])],
                'area_weighted_mean': round(float(np.average(h, weights=a)), 4),
                'largest3': sorted([[round(v[1]), round(v[0], 3)] for v in hs.values()], reverse=True)[:3]}
    print(reg, res[reg], flush=True)
json.dump(res, open('out/within.json', 'w'), indent=1)
