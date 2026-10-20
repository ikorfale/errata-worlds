"""glitchfox #95752: tick-7 snapshot in MY engine, same seeds/rows as raid_ss_slope.py (simul, avert raid-first houses,
4 neutral seats, K seasons). Snapshot = board after the tick-7 resolve. Seat cells = cells owned by P1..P4.
dist = Manhattan distance from a seat cell to the nearest house-owned cell; touched = seat cells with a 4-neighbour
owned by a house. Late raids = house raids accepted at t>7. The probe reads state only (no RNG draws).
Usage: python3 raid_touch7.py [K]"""
import sys, random
import numpy as np
import raid_ash as R
D = R.D; A = R.A; RB = R.RB; S = R.S
K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
snaps = []
_resolve = A.resolve
def season(k, rng, ticks=14):
    A.judge = S.judge_tie; A.house_move = D.HOUSE_MOVE
    names = ['P1', 'P2', 'P3', 'P4'][:k]
    st = A.new_state(); seed = {n: s for n, s in S.seeds(rng).items() if n in names}
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()})
    early = late = 0; snap = None
    for t in range(2, ticks + 1):
        moves = {n: {'seq': 0, 'cells': RB.order(st, n, rng, 'neutral'), 'superseded': []} for n in names}
        rows = A.resolve(st, moves)
        for r in rows:
            if r['result'] == 'accepted' and r['kind'] == 'raid' and r['name'] in A.HOUSE:
                if t <= 7: early += 1
                else: late += 1
        if t == 7:
            xy = lambda s: (ord(s[0]) - 65, int(s[1:]))
            seat = [s for s, v in st['grid'].items() if v in names]
            house = [xy(s) for s, v in st['grid'].items() if v in A.HOUSE]
            d = [min(abs(xy(s)[0] - h[0]) + abs(xy(s)[1] - h[1]) for h in house) for s in seat] if house else []
            tch = sum(any(st['grid'].get(n) in A.HOUSE for n in A.nbrs(s)) for s in seat)
            snap = (len(seat), np.mean(d) if d else np.nan, tch)
    return early, late, snap
rng = random.Random(95195 + 4)
per = [season(4, rng) for _ in range(K)]
E = np.array([p[0] for p in per], float); L = np.array([p[1] for p in per], float)
n_seat = np.array([p[2][0] for p in per], float); dist = np.array([p[2][1] for p in per], float); T = np.array([p[2][2] for p in per], float)
print(f"K={K}  raids {(E + L).mean():.3f}  early (t<=7) {E.mean():.3f}  late (t>7) {L.mean():.3f}")
print(f"tick-7 snapshot  seat cells {n_seat.mean():.2f}  mean dist seat->nearest house {np.nanmean(dist):.3f}  touched seat cells {T.mean():.3f}")
for y, lab in ((E + L, 'raids'), (L, 'late raids')):
    b = np.polyfit(T, y, 1); print(f"{lab} ~ touched@7: slope {b[0]:+.3f}")
for v in sorted(set(T.astype(int))):
    m = T == v
    if m.sum() >= 10: print(f"  touched {v}: n={m.sum():4d} late {L[m].mean():.3f}")
