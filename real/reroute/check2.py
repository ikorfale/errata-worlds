"""#165 check 2: E = L/sqrt(A) for the same 1008 basins on my routing (route.c, epsilon priority-flood) of the 60-70N 15" window.
Mouth point from ice_touch.npy (x, y); best cell within +-1 cell whose A is within 25% of HydroRIVERS UPLAND_SKM."""
import numpy as np, json
M = json.load(open('g15.meta.json')); n, m, ra, ca = M['n'], M['m'], M['ra'], M['ca']; d = 1 / 240
A = np.fromfile('g15_me.A', np.float32).reshape(n, m); L = np.fromfile('g15_me.L', np.float32).reshape(n, m)
X = np.load('ice_touch.npy'); k = (X[:, 0] >= 10) & (X[:, 0] < 50); X = X[k]
A0, L0, ice, slo, x, y = X.T
Am, Lm = np.full(len(X), np.nan), np.full(len(X), np.nan)
for q in range(len(X)):
    j, i = int((84 - y[q]) / d) - ra, int((x[q] + 74) / d) - ca; best = None
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            jj, ii = j + dj, i + di
            if 0 <= jj < n and 0 <= ii < m and A[jj, ii] > 0:
                e = abs(np.log(A[jj, ii] / A0[q]))
                if best is None or e < best[0]: best = (e, jj, ii)
    if best and best[0] < np.log(1.25): Am[q], Lm[q] = A[best[1], best[2]], L[best[1], best[2]]
ok = np.isfinite(Am); t = ice > 0
E0 = L0 / np.sqrt(A0); Em = Lm / np.sqrt(Am)
print('matched %d of %d (touch %d, no %d)' % (ok.sum(), len(X), (ok & t).sum(), (ok & ~t).sum()))
print('L_mine/DIST_UP median: touch %.3f no %.3f' % (np.median(Lm[ok & t] / L0[ok & t]), np.median(Lm[ok & ~t] / L0[ok & ~t])))
edges = np.quantile(slo, np.linspace(0, 1, 7)); out = {'matched': int(ok.sum()), 'bins': []}
for b in range(6):
    s = ok & (slo >= edges[b]) & (slo <= edges[b + 1])
    r = {'bin': b, 'lo': round(float(edges[b]), 3), 'hi': round(float(edges[b + 1]), 3), 'n_touch': int((s & t).sum()), 'n_no': int((s & ~t).sum()),
         'E_hs_touch': round(float(np.median(E0[s & t])), 2), 'E_hs_no': round(float(np.median(E0[s & ~t])), 2),
         'E_me_touch': round(float(np.median(Em[s & t])), 2), 'E_me_no': round(float(np.median(Em[s & ~t])), 2)}
    r['ratio_hs'] = round(r['E_hs_touch'] / r['E_hs_no'], 2); r['ratio_me'] = round(r['E_me_touch'] / r['E_me_no'], 2); out['bins'].append(r); print(r)
f3 = ok & (slo <= edges[3])
for tag, g in (('touch', f3 & t), ('no', f3 & ~t)): out['flat3 ' + tag] = {'n': int(g.sum()), 'E_hs': round(float(np.median(E0[g])), 2), 'E_me': round(float(np.median(Em[g])), 2)}
out['flat3 ratio hs'] = round(out['flat3 touch']['E_hs'] / out['flat3 no']['E_hs'], 2); out['flat3 ratio me'] = round(out['flat3 touch']['E_me'] / out['flat3 no']['E_me'], 2)
rng = np.random.default_rng(76188); it, io = np.flatnonzero(f3 & t), np.flatnonzero(f3 & ~t); bs = []
for _ in range(2000): bs.append(np.median(Em[rng.choice(it, it.size)]) / np.median(Em[rng.choice(io, io.size)]))
out['flat3 ratio me ci'] = [round(float(v), 2) for v in np.percentile(bs, [2.5, 97.5])]
print({k: v for k, v in out.items() if k.startswith('flat3')})
json.dump(out, open('check2.json', 'w'), indent=1); print('__END__')
