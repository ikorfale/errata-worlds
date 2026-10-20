"""glitchfox #95553: my simul engine and his share hs ash (0.21) yet differ 0.80 vs 0.69 raids/season. His house ranks
raids by (touch, rng); mine by (touch - owner touch, -enemy, hash). Test: swap only the raid key in my engine.
Growth keys already agree (empty cell: margin = touch). Same seeds/counters as raid_ash.py. Usage: python3 raid_key.py [K]"""
import sys, random, hashlib
import numpy as np
import raid_diag as D, raid_ash as R
A = D.A
ORIG = D.HOUSE_MOVE

def make(raidkey):
    def hm(st, name):
        if not A.owned(st, name): return ORIG(st, name)
        best = []
        for c in range(A.N):
            for r in range(A.N):
                s = A.cell(c, r); ok, kind, _ = A.judge(st, name, s)
                if not ok: continue
                owner = st['grid'].get(s); t = A.touch(st, name, s)
                enemy = sum(st['grid'].get(n) not in (None, '#', name) for n in A.nbrs(s))
                tie = hashlib.sha256(f"{st['tick']}|{name}|{s}".encode()).hexdigest()
                if kind == 'raid':
                    k = (t - A.touch(st, owner, s), -enemy, tie) if raidkey == 'margin' else (t, tie)
                else:
                    k = (t, -enemy, tie)
                best.append(((kind == 'raid',) + k, s))
        best.sort(reverse=True)
        return [s for _, s in best[:2]]
    return hm

K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
print(f"avert houses, raid-first, 4 seats, K={K}, seed 95199 (raid_ash.py)")
print(f"{'raid key':>14} {'tick':>11} {'raids/s':>10} {'0-delay':>8} {'next tick':>9} {'hs ash':>7}")
for rk in ('margin', 'touch'):
    for v in ('base', 'timing'):
        rng = random.Random(95195 + 4); saved = D.HOUSE_MOVE; R.D.HOUSE_MOVE = make(rk)
        try: per = [R.season(4, rng, v) for _ in range(K)]
        finally: R.D.HOUSE_MOVE = saved
        d = [x for p in per for x in p[0] if x is not None]; n = max(len(d), 1)
        cnt = np.array([len(p[0]) for p in per], float); hs = sum(p[1]['house-seat'] for p in per) / K
        print(f"{rk:>14} {'simul' if v == 'base' else 'seats-first':>11} {cnt.mean():5.2f}±{cnt.std(ddof=1) / np.sqrt(K):.2f} "
              f"{100 * sum(x == 0 for x in d) / n:7.1f}% {100 * sum(x == 1 for x in d) / n:8.1f}% {hs:7.2f}", flush=True)
