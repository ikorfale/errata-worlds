"""Absolute c(base) and c(border2) with their own SEs next to each paired delta (zenith #87420).
Same seasons as corr_mixes.py: 12x12/45, K=200, seeds 273 and 20261014; the two blocks are independent, so pooled SE = sqrt(se1^2+se2^2)/2."""
import json
import numpy as np
from paired import per_season
MIXES = ['hh', 'tt', 'cc', 'ht', 'hc', 'tc']; N, T, K = 12, 45, 200
se = lambda x: x.std(ddof=1) / np.sqrt(len(x))
out = {}
for seed in (273, 20261014):
    for mix in MIXES:
        b = per_season('base', N, T, K, mix, seed); g = per_season('border2', N, T, K, mix, seed); d = g - b
        out[f'{seed}/{mix}'] = {'base': list(map(float, b)), 'border2': list(map(float, g))}
        print(f'seed {seed} {mix}: c(base) {b.mean():+.2f}±{se(b):.2f}  c(border2) {g.mean():+.2f}±{se(g):.2f}  delta {d.mean():+.2f}±{se(d):.2f}  corr(b,g) {np.corrcoef(b, g)[0, 1]:+.2f}', flush=True)
json.dump(out, open('abs_levels.json', 'w'))
print('\npooled over both blocks (independent):')
for mix in MIXES:
    r = []
    for key in ('base', 'border2'):
        xs = [np.array(out[f'{s}/{mix}'][key]) for s in (273, 20261014)]
        r.append((np.mean([x.mean() for x in xs]), np.sqrt(sum(se(x) ** 2 for x in xs)) / 2))
    ds = [np.array(out[f'{s}/{mix}']['border2']) - np.array(out[f'{s}/{mix}']['base']) for s in (273, 20261014)]
    dm, dse = np.mean([d.mean() for d in ds]), np.sqrt(sum(se(d) ** 2 for d in ds)) / 2
    print(f'{mix}: c(base) {r[0][0]:+.2f}±{r[0][1]:.2f}  c(border2) {r[1][0]:+.2f}±{r[1][1]:.2f}  delta {dm:+.2f}±{dse:.2f}')
