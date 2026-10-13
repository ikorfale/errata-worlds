"""How much of an Ashline score is turnout? Each player gets its own move probability (uniform 0.3-1.0),
everyone plays the house rule (or random valid moves); regress final score on moves attempted. Answers the
evolve.py null result: if R^2 is near 1, strategy has nothing left to explain."""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '..')
import ashline as A, season2 as S, evolve as E

def run(N, pol, K, rng):
    players = S.setup(N); X, Y = [], []
    for _ in range(K):
        ps = {n: rng.uniform(0.3, 1.0) for n in list(players) + list(A.HOUSE)}
        st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
        att = {n: 1 for n in ps}
        for t in range(2, 15):
            moves = {}
            for n in ps:
                if rng.random() > ps[n]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
                att[n] += 1
                if n in A.HOUSE: continue
                if pol == 'house':
                    A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
                else:
                    v = E.valid(st, n); cells = [rng.choice(v)] if v else []
                moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
            A.resolve(st, moves)
        sc = A.scores(st)
        for n in ps: X.append(att[n]); Y.append(sc[n])
    X, Y = np.array(X, float), np.array(Y, float)
    r = np.corrcoef(X, Y)[0, 1]; resid = Y - X
    return r * r, resid.mean(), resid.std(), np.mean(np.abs(resid) <= 1)

rng = random.Random(1013)
for N in (8, 12):
    for pol in ('house', 'random'):
        r2, m, s, w1 = run(N, pol, 300, rng)
        print(f"N={N:2d} {pol:6s} R2(score~moves)={r2:.3f}  score-moves mean {m:+.2f} sd {s:.2f}  |score-moves|<=1 in {w1:.0%}", flush=True)
