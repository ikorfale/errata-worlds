"""Fable's suggested test on corr_mixes.json (glitchfox #87174 caveat): stack both seed blocks into 400 per-season
6-vectors of paired deltas (border2 - base). Common delta = mean of the per-season across-mix average (no inverse);
mix heterogeneity = Hotelling T^2 on the five contrasts d_mix - d_hh, F(5, n-5); block difference = Hotelling two-sample
on the 6-vectors. Run with ~/venv/bin/python (scipy)."""
import json
import numpy as np
from scipy import stats
MIXES = ['hh', 'tt', 'cc', 'ht', 'hc', 'tc']
J = json.load(open('corr_mixes.json')); B = [np.array(J[k]).T for k in sorted(J)]   # each 200x6
for k, X in zip(sorted(J), B):
    C = np.corrcoef(X.T); off = C[~np.eye(6, dtype=bool)]
    print(f'seed {k}: between-mix correlation of per-season deltas: mean {off.mean():+.2f}, range {off.min():+.2f}..{off.max():+.2f}')
X = np.vstack(B); n = len(X)
avg = X.mean(1); print(f'\nstacked n={n}: common delta (mean of per-season 6-mix average) {avg.mean():+.2f}±{avg.std(ddof=1)/np.sqrt(n):.2f}')
print('per mix (stacked):', '  '.join(f'{m} {X[:, i].mean():+.2f}±{X[:, i].std(ddof=1)/np.sqrt(n):.2f}' for i, m in enumerate(MIXES)))
D = X[:, 1:] - X[:, [0]]; p = D.shape[1]; md = D.mean(0); S = np.cov(D.T)
T2 = n * md @ np.linalg.solve(S, md); F = (n - p) / (p * (n - 1)) * T2
print(f'mix heterogeneity: Hotelling T2={T2:.2f}, F({p},{n-p})={F:.2f}, p={stats.f.sf(F, p, n - p):.3f}')
a, b = B; na, nb = len(a), len(b); dm = a.mean(0) - b.mean(0)
Sp = ((na - 1) * np.cov(a.T) + (nb - 1) * np.cov(b.T)) / (na + nb - 2)
T2b = dm @ np.linalg.solve(Sp * (1 / na + 1 / nb), dm); q = 6; Fb = (na + nb - q - 1) / (q * (na + nb - 2)) * T2b
print(f'block difference (seed 273 vs 20261014): T2={T2b:.2f}, F({q},{na+nb-q-1})={Fb:.2f}, p={stats.f.sf(Fb, q, na + nb - q - 1):.3f}')
