"""#151: do Greenland's elongated small basins come from the ice margin? Split outlets by the mouth's distance to the nearest
Natural Earth 1:10m glaciated-area vertex; fit h and basin elongation E = D/sqrt(A) per band. Bets in bets_ice.txt."""
import numpy as np, json
from hack import load, fit, D
# ice.py and elong.py run at import: take only their function definitions
exec(open('ice.py').read().split('\nr = load(')[0])
exec(open('elong.py').read().split('\ncache = {}')[0])
r = load('gr', {'NEXT_DOWN', 'MAIN_RIV', 'DIST_DN_KM', 'DIST_UP_KM', 'UPLAND_SKM'})
mr, dd = r['MAIN_RIV'], r['DIST_DN_KM']
order = np.lexsort((-dd, mr)); first = np.r_[True, mr[order][1:] != mr[order][:-1]]
head_of = dict(zip(mr[order][first].astype(np.int64), order[first]))
out = np.flatnonzero((r['NEXT_DOWN'] == 0) & (r['UPLAND_SKM'] >= 10) & (r['DIST_UP_KM'] > 0))
ox = centres('gr', out); heads = np.array([head_of[int(m)] for m in mr[out]]); hx = centres('gr', heads)
recs = rings(f'{D}/ne_glac/ne_10m_glaciated_areas.shp', (-75, -10, 59, 84))
V = np.vstack([p.vertices for rs in recs for p in rs])
def unit(ll): la, lo = np.radians(ll[:, 1]), np.radians(ll[:, 0]); return np.c_[np.cos(la)*np.cos(lo), np.cos(la)*np.sin(lo), np.sin(la)]
U = unit(V); M = unit(ox); dmin = np.empty(len(M))
for i in range(0, len(M), 64): dmin[i:i+64] = 6371 * np.arccos(np.clip((M[i:i+64] @ U.T).max(1), -1, 1))
dmin[on_ice(ox, recs)] = 0.0
head_ice = on_ice(hx, recs)
he, oe = ends('gr', heads), ends('gr', out)
Dk = np.max([gc(he[:, i], oe[:, j]) for i in (0, 1) for j in (0, 1)], axis=0)
A, L = r['UPLAND_SKM'][out], r['DIST_UP_KM'][out]; rng = np.random.default_rng(151); res = {'vertices': len(V), 'n': len(out)}
for name, s in [('d<10', dmin < 10), ('10-30', (dmin >= 10) & (dmin < 30)), ('30-60', (dmin >= 30) & (dmin < 60)), ('>=60', dmin >= 60), ('>=50', dmin >= 50)]:
    e = s & (A <= 1000) & (Dk > 0.5)
    res[name] = {**(fit(A[s], L[s], rng, 500) if s.sum() >= 20 else {'n': int(s.sum())}),
                 'median E (A10-1000)': round(float(np.median(Dk[e] / np.sqrt(A[e]))), 3) if e.sum() else None, 'n_E': int(e.sum()),
                 'head on ice %': round(100 * float(head_ice[s].mean()), 1) if s.sum() else None, 'median A': round(float(np.median(A[s])), 1) if s.sum() else None}
    print(name, res[name], flush=True)
np.save('out/icedist.npy', np.c_[A, L, Dk, dmin, head_ice]); json.dump(res, open('out/icedist.json', 'w'), indent=1, default=float)
