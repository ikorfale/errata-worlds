"""#168 analysis: E by Greenland's slope bins for Greenland (check2 rows rebuilt), Baffin and Iceland, ice vs no ice, both routings."""
import numpy as np, json
sm = json.load(open('slope_match.json')); edges = [sm['bins'][0]['lo']] + [b['hi'] for b in sm['bins']]
ed = np.array(edges); ed[-1] = 1e9; ed[0] = -1
def summ(X, tag):
    A, L, ice, slo = X[:, 0], X[:, 1], X[:, 2], X[:, 3]; k = (A >= 10) & (A < 50); X = X[k]
    A, L, ice, slo, Am, Lm = X[:, 0], X[:, 1], X[:, 2], X[:, 3], X[:, 6], X[:, 7]
    E0, Em = L / np.sqrt(A), Lm / np.sqrt(Am); t = ice > 0; f3 = slo <= edges[3]; ok = np.isfinite(Em)
    out = {'n': int(len(X)), 'n_touch': int(t.sum()), 'matched_me': int(ok.sum()), 'bins': []}
    for b in range(6):
        s = (slo > ed[b]) & (slo <= ed[b + 1])
        out['bins'].append({'bin': b, 'n_no': int((s & ~t).sum()), 'E_no': round(float(np.median(E0[s & ~t])), 2) if (s & ~t).sum() else None,
                            'n_touch': int((s & t).sum()), 'E_touch': round(float(np.median(E0[s & t])), 2) if (s & t).sum() else None})
    rng = np.random.default_rng(168)
    def med(g, E): 
        if g.sum() == 0: return None
        bs = [np.median(E[rng.choice(np.flatnonzero(g), g.sum())]) for _ in range(1000)]
        return [int(g.sum()), round(float(np.median(E[g])), 2)] + [round(float(v), 2) for v in np.percentile(bs, [2.5, 97.5])]
    for nm, g in (('flat3 no', f3 & ~t), ('flat3 touch', f3 & t)):
        out[nm + ' hs'] = med(g, E0); out[nm + ' me(matched)'] = med(g & ok, Em); out[nm + ' hs(matched)'] = med(g & ok, E0)
    out['median slope no'] = round(float(np.median(slo[~t])), 4)
    print(tag, json.dumps(out)); return out
res = {}
for nm in ('baffin', 'iceland'): res[nm] = summ(np.load(f'ctrl_{nm}.npy'), nm)
res['flat3 hi edge'] = edges[3]; json.dump(res, open('ctrl.json', 'w'), indent=1); print('__END__')
