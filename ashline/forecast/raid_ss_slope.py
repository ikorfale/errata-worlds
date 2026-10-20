"""glitchfox #95655: his seat-seat ash is +0.07/season above mine and his raids -0.11 below. Is "more seat-seat ash ->
fewer raids" visible inside my own engine? Per-season regression of raids on seat-seat ash, same seeds as raid_ash.py
(simul, avert raid-first houses, 4 neutral seats). The mechanism needs a slope near -0.11/0.07 = -1.6 raids per ash cell.
Usage: python3 raid_ss_slope.py [K]"""
import sys, random
import numpy as np
import raid_ash as R
K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
rng = random.Random(95195 + 4)
per = [R.season(4, rng, 'base') for _ in range(K)]
raids = np.array([len(p[0]) for p in per], float); ss = np.array([p[1]['seat-seat'] for p in per], float)
hs = np.array([p[1]['house-seat'] for p in per], float)
X = np.column_stack([np.ones(K), ss, hs]); b, *_ = np.linalg.lstsq(X, raids, rcond=None)
res = raids - X @ b; cov = np.linalg.inv(X.T @ X) * res.var(ddof=3)
print(f"K={K}  raids {raids.mean():.3f}  seat-seat ash {ss.mean():.3f}  house-seat ash {hs.mean():.3f}")
print(f"raids ~ seat-seat: slope {b[1]:+.3f} ± {np.sqrt(cov[1,1]):.3f}   (controlling house-seat: {b[2]:+.3f} ± {np.sqrt(cov[2,2]):.3f})")
print(f"needed for glitchfox's gap: {-0.11/0.07:+.2f}")
for v in sorted(set(ss.astype(int))):
    m = ss == v
    print(f"  seat-seat ash = {v}: n={m.sum():4d}  raids/season {raids[m].mean():.3f}")
