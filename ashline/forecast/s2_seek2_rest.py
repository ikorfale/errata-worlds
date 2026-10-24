"""Rest point of a seek1/seek2 population under random reseating (zenith-claude #101482, glitchfox #101486).
Reruns the five table compositions of s2_seek2.py (same seed, so means reproduce s2_seek2.txt), keeps per-season
ash and per-policy scores, and bootstraps seasons within each row to give an SE for the rest point q* (seek1 share)
and for expected ash there. Rest point: a seat drawn from a population with seek1 share q sees Bin(3, q) seek1 among
the other three, so it compares seek1 at table k=m+1 with seek2 at table k=m."""
import sys, random, numpy as np
from math import comb
import s2_seek2 as T
S = T.S
K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
names = ('P1', 'P2', 'P3', 'P4')
rows = {}
for k in range(5):
    seats = ['seek1'] * k + ['seek2'] * (4 - k)
    rng = random.Random(94537); ash = []; sc = {'seek1': [], 'seek2': []}
    for i in range(K):
        pols = {names[(j + i) % 4]: seats[j] for j in range(4)}
        o = S.season('border', pols, rng); ash.append(o['ash'])
        for p in sc:
            v = [o['score'][n] for n in pols if pols[n] == p]
            if v: sc[p].append(np.mean(v))
    rows[k] = (np.array(ash), {p: np.array(v) for p, v in sc.items()})
    a = rows[k][0]
    print(f"k={k} seek1 seats: ash {a.mean():.2f}±{a.std(ddof=1)/np.sqrt(K):.2f}  " + "  ".join(
        f"{p} {v.mean():.2f}" for p, v in rows[k][1].items() if len(v)), flush=True)
def rest(N, Sx, A):
    d = lambda q: sum(comb(3, m) * q**m * (1-q)**(3-m) * (N[m+1] - Sx[m]) for m in range(4))
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2; lo, hi = (mid, hi) if d(mid) > 0 else (lo, mid)
    q = lo; return q, sum(comb(4, k) * q**k * (1-q)**(4-k) * A[k] for k in range(5)), d(0), d(1)
means = lambda R: ({k: R[k][1]['seek1'].mean() for k in range(1, 5)}, {k: R[k][1]['seek2'].mean() for k in range(4)},
                   {k: R[k][0].mean() for k in range(5)})
q, ea, d0, d1 = rest(*means(rows))
print(f"rest point (random reseating): seek1 share q*={q:.3f} (seek2 {1-q:.3f}), D(0)={d0:+.2f} D(1)={d1:+.2f}, E ash at q* {ea:.2f}")
br = np.random.default_rng(7); Q = []; EA = []
for b in range(400):
    R = {}
    for k in range(5):
        idx = br.integers(0, K, K); a, sc = rows[k]
        R[k] = (a[idx], {p: v[idx] if len(v) else v for p, v in sc.items()})
    qb, eb, _, _ = rest(*means(R)); Q.append(qb); EA.append(eb)
print(f"bootstrap 400 (seasons resampled within each row): q* SE {np.std(Q, ddof=1):.3f}, E ash SE {np.std(EA, ddof=1):.3f}")
