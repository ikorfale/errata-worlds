"""zenith's check (#86098): split R^2(cells gained ~ moves made) at T*, the first tick on which some player has no empty
neighbour. Near 1 before and clearly lower after = the season is too short for the board; near 1 after too = raids
are too weak (a rule problem). Same move model as attendance.py (per-player turnout 0.3-1.0, house rule for all)."""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, season2 as S

def boxed(st):
    for n in set(st['grid'].values()):
        if not any(m not in st['grid'] for s in A.owned(st, n) for m in A.nbrs(s)): return True
    return False

def r2(x, y):
    x, y = np.array(x, float), np.array(y, float)
    return float('nan') if len(x) < 3 or x.std() == 0 or y.std() == 0 else np.corrcoef(x, y)[0, 1] ** 2

def run(N, ticks, K, rng):
    players = S.setup(N); pre, post, tstar = ([], []), ([], []), []
    for _ in range(K):
        ps = {n: rng.uniform(0.3, 1.0) for n in list(players) + list(A.HOUSE)}
        st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
        T = None; mv = {n: [0, 0] for n in ps}; c0 = A.scores(st); cT = None
        for t in range(2, ticks + 1):
            if T is None and boxed(st): T = t; cT = A.scores(st)
            moves = {}
            for n in ps:
                if rng.random() > ps[n]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
                mv[n][T is not None] += 1
                if n in A.HOUSE: continue
                A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
                moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
            A.resolve(st, moves)
        tstar.append(T); end = A.scores(st)
        for n in ps:
            mid = cT[n] if cT else end[n]
            pre[0].append(mv[n][0]); pre[1].append(mid - c0.get(n, 0))
            if T: post[0].append(mv[n][1]); post[1].append(end[n] - mid)
    hit = [t for t in tstar if t]
    return (len(hit) / K, (np.median(hit) if hit else None), r2(*pre), r2(*post), len(post[0]))

if __name__ == '__main__':
  rng = random.Random(86098)
  for N, ticks in ((12, 14), (8, 14), (12, 30), (12, 45)):
    f, med, a, b, n = run(N, ticks, 200, rng)
    print(f"{N}x{N} {ticks:2d} ticks  cells/(players*ticks)={N*N/(5*ticks):.2f}  seasons with T*: {f:.0%}  median T*={med}  "
          f"R2 before={a:.3f}  after={b:.3f} (n={n})", flush=True)
