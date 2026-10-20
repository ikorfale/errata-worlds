"""glitchfox #95325: does my 'timing' variant keep house-seat collisions? Add ash cells per season and the
zero-delay share (house raids a seat claim in the same tick) to raid_diag.py's rows. (plan #384)
Same engine, seeds and variants as raid_diag.py; only counters added.
Variants: base, growth, hashtie, timing, and growth order + timing combined (glitchfox ran ignore/avert x simul/seats-first).
Usage: python3 raid_ash.py [seasons] [variant,variant]"""
import sys, random
import numpy as np
import raid_diag as D
A, RB, S = D.A, D.RB, D.S

def season(k, rng, variant, ticks=14):
    A.judge = S.judge_tie
    A.house_move = {'growth': D.house_move_sign(1), 'hashtie': D.house_move_sign(0)}.get(variant.split('+')[0], D.HOUSE_MOVE)
    names = ['P1', 'P2', 'P3', 'P4'][:k]
    st = A.new_state(); seed = {n: s for n, s in S.seeds(rng).items() if n in names}
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()})
    born = {}; delays = []; ash = {'house-seat': 0, 'seat-seat': 0, 'house-house': 0}
    empty = lambda ns: {n: {'seq': 0, 'cells': [], 'superseded': []} for n in ns}
    for t in range(2, ticks + 1):
        moves = {n: {'seq': 0, 'cells': RB.order(st, n, rng, 'neutral'), 'superseded': []} for n in names}
        if variant.endswith('timing'):
            rows = A.resolve(st, {**moves, **empty(A.HOUSE)}); rows += A.resolve(st, empty(names))
        else:
            rows = A.resolve(st, moves)
        cells = {}
        for r in rows:
            if r['result'] == 'collision': cells.setdefault(r['pick'], set()).add(r['name'] in A.HOUSE)
        for s, who in cells.items():
            ash['house-seat' if who == {True, False} else 'house-house' if who == {True} else 'seat-seat'] += 1
        for r in rows:
            if r['result'] != 'accepted': continue
            if r['kind'] == 'raid' and r['name'] in A.HOUSE:
                delays.append(t - born[r['pick']] if r['pick'] in born else None)
            elif r['name'] in names:
                born[r['pick']] = t
    A.house_move = D.HOUSE_MOVE
    return delays, ash

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    print(f"tie rule, neutral seat pathing, 4 seats, K={K} seasons per row (seed 95199 as raid_diag.py)")
    print(f"{'variant':>8} {'raids/s':>10} {'0-delay':>8} {'next tick':>9} {'ash/s':>6} {'house-seat':>10} {'seat-seat':>9} {'house-house':>11}")
    for v in (sys.argv[2].split(',') if len(sys.argv) > 2 else ('base', 'growth', 'hashtie', 'timing', 'hashtie+timing', 'growth+timing')):
        rng = random.Random(95195 + 4)
        per = [season(4, rng, v) for _ in range(K)]
        allr = [x for p in per for x in p[0]]; d = [x for x in allr if x is not None]; n = max(len(d), 1)
        a = {key: sum(p[1][key] for p in per) / K for key in per[0][1]}
        cnt = np.array([len(p[0]) for p in per], float)
        print(f"{v:>8} {cnt.mean():5.2f}±{cnt.std(ddof=1) / np.sqrt(K):.2f} {100 * sum(x == 0 for x in d) / n:7.1f}% {100 * sum(x == 1 for x in d) / n:8.1f}% "
              f"{sum(a.values()):6.2f} {a['house-seat']:10.2f} {a['seat-seat']:9.2f} {a['house-house']:11.2f}", flush=True)
