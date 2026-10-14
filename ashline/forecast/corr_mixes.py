"""Are the six mixes' paired deltas correlated within a block (they share random.Random(seed))? glitchfox #87174 caveat.
Saves per-season deltas, prints the between-mix correlation matrix and a Q test with the full covariance (GLS)."""
import json, sys
import numpy as np
from paired import per_season
MIXES = ['hh', 'tt', 'cc', 'ht', 'hc', 'tc']; N, T, K = 12, 45, int(sys.argv[1]) if len(sys.argv) > 1 else 200
out = {}
for seed in (273, 20261014):
    D = []
    for mix in MIXES:
        d = per_season('border2', N, T, K, mix, seed) - per_season('base', N, T, K, mix, seed); D.append(d)
        print(f'seed {seed} {mix}: {d.mean():+.2f}±{d.std(ddof=1)/np.sqrt(len(d)):.2f} n={len(d)}', flush=True)
    out[seed] = [list(map(float, d)) for d in D]
json.dump(out, open('corr_mixes.json', 'w'))
for seed, D in out.items():
    D = np.array(D); C = np.corrcoef(D); off = C[~np.eye(6, dtype=bool)]
    print(f'\nseed {seed}: between-mix correlation of per-season deltas, mean {off.mean():+.3f}, range {off.min():+.3f}..{off.max():+.3f}')
    print(np.array2string(C, precision=2))
# pooled per mix (two blocks independent), then GLS common mean and Q with full covariance
means, covs = [], []
for seed, D in out.items():
    D = np.array(D); n = D.shape[1]; means.append(D.mean(1)); covs.append(np.cov(D) / n)
V = np.linalg.inv(np.linalg.inv(covs[0]) + np.linalg.inv(covs[1]))
m = V @ (np.linalg.inv(covs[0]) @ means[0] + np.linalg.inv(covs[1]) @ means[1])
W = np.linalg.inv(V); one = np.ones(6); mu = one @ W @ m / (one @ W @ one); se = (one @ W @ one) ** -0.5
Q = (m - mu) @ W @ (m - mu)
from math import exp, lgamma
def chi2_sf(x, k):  # regularized upper gamma, series
    a = k / 2; x = x / 2; s = t = 1 / a; i = 1
    while t > 1e-12: t *= x / (a + i); s += t; i += 1
    return 1 - exp(-x + a * np.log(x) - lgamma(a)) * s
print('\npooled per mix (GLS):', ' '.join(f'{k} {v:+.2f}' for k, v in zip(MIXES, m)))
print(f'common delta {mu:+.2f}±{se:.2f}; Q={Q:.2f} df=5 p={chi2_sf(Q, 5):.3f} (full covariance)')
print('naive (independent) common delta for comparison: see glitchfox #87174 +1.19±0.12, Q=6.94 p=0.22')
