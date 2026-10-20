"""glitchfox #95856: seed-7 trace in MY engine, same setup as raid_touch7.py (simul, avert raid-first houses,
4 neutral seats). Prints, per resolve, every pick with kind/result, and seat cells after it. Then over K seasons
of the raid_touch7 stream: mean seat cells and loss counts per resolve index. Coordinates as (col,row), 0-based.
Usage: python3 trace_seed7.py [K]"""
import sys, random
import numpy as np
import raid_ash as R
D = R.D; A = R.A; RB = R.RB; S = R.S
K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
names = ['P1', 'P2', 'P3', 'P4']
def season(rng, ticks=14, show=False):
    A.judge = S.judge_tie; A.house_move = D.HOUSE_MOVE
    st = A.new_state(); seed = {n: s for n, s in S.seeds(rng).items() if n in names}
    out = []
    for t in range(1, ticks + 1):
        if t == 1: moves = {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()}
        else: moves = {n: {'seq': 0, 'cells': RB.order(st, n, rng, 'neutral'), 'superseded': []} for n in names}
        rows = A.resolve(st, moves)
        seats = sum(v in names for v in st['grid'].values())
        out.append((seats, sum(r['result'] == 'collision' for r in rows if r['name'] in names),
                    sum(r['result'] == 'rejected' for r in rows if r['name'] in names),
                    sum(r['result'] == 'accepted' and r['kind'] == 'raid' and r['name'] in A.HOUSE for r in rows)))
        if show:
            picks = '  '.join(f"{r['name'].replace('house-','')}->{A.xy(r['pick']) if r['pick'] else None}:{r['kind']}/{r['result']}" for r in rows)
            print(f"resolve {t} (st.tick {st['tick']}): seats={seats}  {picks}")
    return out
print("== first season, random.Random(7) ==")
season(random.Random(7), ticks=8, show=True)
rng = random.Random(95195 + 4)
P = np.array([season(rng) for _ in range(K)], float)   # K x ticks x 4
print(f"\n== K={K}, raid_touch7 stream: mean per resolve index (resolve 1 = seed placement) ==")
for t in range(P.shape[1]):
    print(f"resolve {t+1:2d}: seats {P[:,t,0].mean():6.2f}  seat collisions {P[:,t,1].mean():.3f}  seat rejects {P[:,t,2].mean():.3f}  house raids {P[:,t,3].mean():.3f}")
