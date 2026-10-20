"""glitchfox #95357: house-seat ash matches at 0.21 with avert houses, yet his raid rate rises 17% with seats-first
and mine stays flat. Candidate: my houses rank any legal raid above all growth (key starts with kind=='raid'), so a
raid opportunity is always taken and timing only moves WHEN it happens. Test: same avert order without raid-first
priority (own-touch margin, then fewest enemy neighbours, then hash), simultaneous vs seats-first.
Same engine, seeds and counters as raid_ash.py. Usage: python3 raid_prio.py [seasons]"""
import sys, random, hashlib
import numpy as np
import raid_diag as D, raid_ash as R
A = D.A
ORIG = D.HOUSE_MOVE

def house_move_noprio(st, name):
    if not A.owned(st, name): return ORIG(st, name)
    best = []
    for c in range(A.N):
        for r in range(A.N):
            s = A.cell(c, r); ok, kind, _ = A.judge(st, name, s)
            if not ok: continue
            owner = st['grid'].get(s)
            enemy = sum(st['grid'].get(n) not in (None, '#', name) for n in A.nbrs(s))
            tie = hashlib.sha256(f"{st['tick']}|{name}|{s}".encode()).hexdigest()
            best.append(((A.touch(st, name, s) - (A.touch(st, owner, s) if owner else 0), -enemy, tie), s))
    best.sort(reverse=True)
    return [s for _, s in best[:2]]

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    print(f"tie rule, neutral seat pathing, 4 seats, K={K} seasons per row (seed 95199 as raid_ash.py)")
    print(f"{'houses':>16} {'tick':>11} {'raids/s':>10} {'0-delay':>8} {'next tick':>9} {'house-seat ash':>14}")
    for prio in ('raid-first', 'no raid priority'):
        for v in ('base', 'timing'):
            orig = R.D.house_move_sign
            rng = random.Random(95195 + 4)
            if prio == 'raid-first':
                per = [R.season(4, rng, v) for _ in range(K)]
            else:   # R.season sets A.house_move from the variant's first part; 'base' -> D.HOUSE_MOVE, so patch that
                saved = D.HOUSE_MOVE; R.D.HOUSE_MOVE = house_move_noprio
                try: per = [R.season(4, rng, v) for _ in range(K)]
                finally: R.D.HOUSE_MOVE = saved
            d = [x for p in per for x in p[0] if x is not None]; n = max(len(d), 1)
            cnt = np.array([len(p[0]) for p in per], float)
            hs = sum(p[1]['house-seat'] for p in per) / K
            print(f"{prio:>16} {'simul' if v == 'base' else 'seats-first':>11} {cnt.mean():5.2f}±{cnt.std(ddof=1) / np.sqrt(K):.2f} "
                  f"{100 * sum(x == 0 for x in d) / n:7.1f}% {100 * sum(x == 1 for x in d) / n:8.1f}% {hs:14.2f}", flush=True)
