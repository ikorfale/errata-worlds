"""glitchfox #95933: two numbers to localise the early-raid gap. Same engine, seeds and stream as raid_touch7.py,
aligned snapshot SNAP=8 (resolves incl. seed placement = his t7). Counts early (t<=SNAP) house raids at touched@SNAP=0,
and splits early raids by the victim cell's owner just before that resolve (house / seat / none).
Probe reads state only (no RNG draws). Usage: python3 raid_early_split.py [K] [SNAP]"""
import sys, random
import numpy as np
import raid_ash as R
D = R.D; A = R.A; RB = R.RB; S = R.S
K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
SNAP = int(sys.argv[2]) if len(sys.argv) > 2 else 8
def season(k, rng, ticks=14):
    A.judge = S.judge_tie; A.house_move = D.HOUSE_MOVE
    names = ['P1', 'P2', 'P3', 'P4'][:k]
    st = A.new_state(); seed = {n: s for n, s in S.seeds(rng).items() if n in names}
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()})
    early = {'house': 0, 'seat': 0, 'none': 0}; late = 0; tch = None; retaken = 0; early_cells = []
    for t in range(2, ticks + 1):
        before = dict(st['grid'])
        moves = {n: {'seq': 0, 'cells': RB.order(st, n, rng, 'neutral'), 'superseded': []} for n in names}
        rows = A.resolve(st, moves)
        for r in rows:
            if r['result'] == 'accepted' and r['kind'] == 'raid' and r['name'] in A.HOUSE:
                if t <= SNAP:
                    o = before.get(r['pick']); early['house' if o in A.HOUSE else 'seat' if o in names else 'none'] += 1
                    early_cells.append(r['pick'])
                else: late += 1
        if t == SNAP:
            seat = [s for s, v in st['grid'].items() if v in names]
            tch = sum(any(st['grid'].get(n) in A.HOUSE for n in A.nbrs(s)) for s in seat)
            retaken = sum(st['grid'].get(c) not in A.HOUSE for c in early_cells)
    return early, late, tch, retaken, len(early_cells)
rng = random.Random(95195 + 4)
per = [season(4, rng) for _ in range(K)]
T = np.array([p[2] for p in per]); E = np.array([sum(p[0].values()) for p in per], float)
tot = {k: sum(p[0][k] for p in per) for k in ('house', 'seat', 'none')}
print(f"K={K} SNAP={SNAP}  early raids/season {E.mean():.3f}  touched@SNAP {T.mean():.3f}")
m = T == 0
print(f"touched=0: n={m.sum()}  early raids mean {E[m].mean():.3f}  seasons with >=1 early raid {(E[m] > 0).sum()}")
print(f"seasons with any early raid: {(E > 0).sum()}, of which touched=0 at SNAP: {((E > 0) & m).sum()}")
print(f"early raid victims (owner before resolve): house {tot['house']}  seat {tot['seat']}  none {tot['none']}  (total {sum(tot.values())})")
print(f"early-raided cells no longer house-owned at SNAP: {sum(p[3] for p in per)} of {sum(p[4] for p in per)}")
