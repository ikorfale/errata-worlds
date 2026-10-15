"""glitchfox #87999: size a pre-registered season-2 contrast from the ACTUAL per-season covariance of paired deltas
(corr_mixes.json, both seed blocks stacked, n=400), not from inferred correlation blocks.
n = ((z_{1-a/2} + z_{1-b}) * sqrt(w' S w) / Delta)^2, two-sided a=0.05, power 0.80.
Also prints the observed value of each contrast on this block (post hoc, NOT a test). Run with ~/venv/bin/python."""
import json
import numpy as np
from scipy import stats
MIXES = ['hh', 'tt', 'cc', 'ht', 'hc', 'tc']
J = json.load(open('corr_mixes.json')); X = np.vstack([np.array(J[k]).T for k in sorted(J)]); n = len(X)
S = np.cov(X.T)
print(f'n={n} seasons; per-season SD by mix:', '  '.join(f'{m} {np.sqrt(S[i, i]):.2f}' for i, m in enumerate(MIXES)))
za, zb = stats.norm.ppf(0.975), stats.norm.ppf(0.80)
C = {
    'mean(tt,cc) - mean(hh,ht,hc,tc)  [glitchfox]': {'tt': .5, 'cc': .5, 'hh': -.25, 'ht': -.25, 'hc': -.25, 'tc': -.25},
    'mean(tt,cc,tc) - mean(hh,ht,hc)  [no-h vs with-h]': {'tt': 1/3, 'cc': 1/3, 'tc': 1/3, 'hh': -1/3, 'ht': -1/3, 'hc': -1/3},
}
for name, wd in C.items():
    w = np.array([wd[m] for m in MIXES]); sd = np.sqrt(w @ S @ w); est = (X @ w).mean()
    print(f'\n{name}\n  per-season SD sqrt(w\'Sw) = {sd:.2f}; observed (post hoc) {est:+.2f}±{sd/np.sqrt(n):.2f}')
    for d in (0.4, 0.5, 0.63, 0.7):
        print(f'  80% power at Delta={d}: n = {int(np.ceil(((za + zb) * sd / d) ** 2))} seasons')
