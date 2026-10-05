"""Zenith 74830: is Hack's 0.6 the same data with a different line? Per basin (outlet A >= 1e4 km^2),
OLS slope b, Pearson r and RMA slope b/|r| of log L on log A over reaches in each A band (>= 30 reaches)."""
import numpy as np, json
from hack import load
bands = [(10, 100), (10, 300), (10, 1e4), (10, 1e7)]
res = {}
for reg in ['eu', 'af', 'na', 'sa', 'as', 'au']:
    r = load(reg, {'MAIN_RIV', 'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
    A, L, M, nd = r['UPLAND_SKM'], r['DIST_UP_KM'], r['MAIN_RIV'].astype(np.int64), r['NEXT_DOWN']
    outA = {int(m): a for m, a in zip(M[nd == 0], A[nd == 0])}
    order = np.argsort(M, kind='stable'); Ms = M[order]
    cuts = np.flatnonzero(np.diff(Ms)) + 1; starts = np.r_[0, cuts]; ends = np.r_[cuts, len(Ms)]
    st = {b: [] for b in bands}
    for s, e in zip(starts, ends):
        if outA.get(int(Ms[s]), 0) < 1e4: continue
        idx = order[s:e]; a, l = A[idx], L[idx]
        for lo, hi in bands:
            ok = (a >= lo) & (a < hi) & (l > 0)
            if ok.sum() < 30: continue
            x, y = np.log10(a[ok]), np.log10(l[ok])
            b = np.polyfit(x, y, 1)[0]; rr = np.corrcoef(x, y)[0, 1]
            st[(lo, hi)].append((b, rr, np.sign(b) * np.std(y) / np.std(x)))
    out = {}
    for (lo, hi), v in st.items():
        if not v: continue
        v = np.array(v)
        out[f'{lo:g}-{hi:g}'] = {'basins': len(v), 'ols': round(float(np.median(v[:, 0])), 3),
            'r': round(float(np.median(v[:, 1])), 3), 'rma': round(float(np.median(v[:, 2])), 3),
            'rma_iqr': [round(float(q), 3) for q in np.percentile(v[:, 2], [25, 75])]}
    res[reg] = out; print(reg, json.dumps(out), flush=True)
json.dump(res, open('out/within_rma.json', 'w'), indent=1)
