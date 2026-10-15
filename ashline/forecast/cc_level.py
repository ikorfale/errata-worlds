"""Pre-registered run (PREREG-cc-level.md): absolute cc c(border2) level, 12x12/45, ten fresh 200-season blocks.
Writes cc_level.json (per-season base and border2 per seed) and prints per-block and stacked results."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paired import per_season
N, T, K = 12, 45, 200
SEEDS = list(range(20261015, 20261025))
out_path = sys.argv[1] if len(sys.argv) > 1 else 'cc_level.json'
out = json.load(open(out_path)) if os.path.exists(out_path) else {}
se = lambda x: x.std(ddof=1) / np.sqrt(len(x))
for s in SEEDS:
    if str(s) not in out:
        b = per_season('base', N, T, K, 'cc', s); g = per_season('border2', N, T, K, 'cc', s)
        out[str(s)] = {'base': list(map(float, b)), 'border2': list(map(float, g))}
        json.dump(out, open(out_path, 'w'))
    b, g = (np.array(out[str(s)][k]) for k in ('base', 'border2'))
    print(f'seed {s}: c(border2) {g.mean():+.2f}±{se(g):.2f}  c(base) {b.mean():+.2f}±{se(b):.2f}  delta {(g - b).mean():+.2f}±{se(g - b):.2f}', flush=True)
G = np.concatenate([out[str(s)]['border2'] for s in SEEDS]); B = np.concatenate([out[str(s)]['base'] for s in SEEDS])
m, e = G.mean(), se(G)
print(f'\nPRIMARY n={len(G)}: c(border2) cc = {m:+.3f} ± {e:.3f}  95% CI [{m - 1.96 * e:+.2f}, {m + 1.96 * e:+.2f}]  per-season SD {G.std(ddof=1):.2f}')
bm = np.array([np.mean(out[str(s)]['border2']) for s in SEEDS]); bs = np.array([se(np.array(out[str(s)]['border2'])) for s in SEEDS])
w = 1 / bs ** 2; mw = (w * bm).sum() / w.sum(); Q = (w * (bm - mw) ** 2).sum()
from math import lgamma, exp
def chi2_sf(x, k, steps=20000):   # survival function by numeric integration of the chi-square density
    h = x / steps; f = lambda t: exp((k / 2 - 1) * np.log(t) - t / 2 - (k / 2) * np.log(2) - lgamma(k / 2)) if t > 0 else 0.0
    return 1 - sum((f(i * h) + f((i + 1) * h)) / 2 * h for i in range(steps))
print(f'secondary: between-block Q = {Q:.2f} on {len(SEEDS) - 1} df, p = {chi2_sf(Q, len(SEEDS) - 1):.3f}')
print(f'secondary: c(base) cc = {B.mean():+.3f} ± {se(B):.3f}   delta = {(G - B).mean():+.3f} ± {se(G - B):.3f}')
old = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'abs_levels.json')))
A12 = np.concatenate([G] + [np.array(old[f'{s}/cc']['border2']) for s in (273, 20261014)])
print(f'secondary: all twelve blocks n={len(A12)}: c(border2) cc = {A12.mean():+.3f} ± {se(A12):.3f}')
