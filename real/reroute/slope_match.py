import numpy as np, json
X = np.load('ice_touch.npy')
A, L, ice, slo = X[:, 0], X[:, 1], X[:, 2], X[:, 3]
E = L / np.sqrt(A); k = (A >= 10) & (A < 50)
touch = k & (ice > 0); no = k & (ice == 0)
print('n touch', touch.sum(), 'no', no.sum(), 'median slope touch %.3f no %.3f' % (np.median(slo[touch]), np.median(slo[no])))
edges = np.quantile(slo[k], np.linspace(0, 1, 7)); out = []
for i in range(6):
    b = (slo >= edges[i]) & (slo <= edges[i + 1])
    t, n = touch & b, no & b
    r = dict(bin=i, lo=round(float(edges[i]), 3), hi=round(float(edges[i + 1]), 3), n_touch=int(t.sum()), n_no=int(n.sum()),
             E_touch=round(float(np.median(E[t])), 2) if t.sum() else None, E_no=round(float(np.median(E[n])), 2) if n.sum() else None)
    if t.sum() and n.sum(): r['ratio'] = round(r['E_touch'] / r['E_no'], 2)
    out.append(r); print(r)
# regression log E ~ log slope + touch
y = np.log(E[k]); x1 = np.log(slo[k] + 1e-4); x2 = (ice[k] > 0).astype(float)
M = np.c_[np.ones(k.sum()), x1, x2]; beta, *_ = np.linalg.lstsq(M, y, rcond=None)
rng = np.random.default_rng(1); bs = []
idx = np.arange(k.sum())
for _ in range(2000):
    s = rng.choice(idx, idx.size); bs.append(np.linalg.lstsq(M[s], y[s], rcond=None)[0][2])
lo, hi = np.percentile(bs, [2.5, 97.5])
print('log E = a + b log slope + c touch: b %.3f c %.3f [%.3f, %.3f] -> touch factor %.2f [%.2f, %.2f]' % (beta[1], beta[2], lo, hi, np.exp(beta[2]), np.exp(lo), np.exp(hi)))
json.dump(dict(bins=out, c=float(beta[2]), ci=[float(lo), float(hi)]), open('slope_match.json', 'w'), indent=1)
print('__END__')
