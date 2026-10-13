"""Season-2 candidate rule 'pressure': after each tick resolves, every owned cell that a single other owner touches
on >= 2 sides and on more sides than its own owner flips to that owner (computed on the post-tick board, all at once).
Shape then matters: thin lines lose, compact blobs hold. Same turnout test as attendance.py (R^2 of score on moves)
plus the house-rule vs 'compact' (maximise own neighbours, avoid cells an enemy could pressure) head to head."""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, '..')
import ashline as A, season2 as S, evolve as E

def pressure(st):
    g = st['grid']; flips = {}
    for k, o in g.items():
        if o in (None, '#'): continue
        cnt = {}
        for m in A.nbrs(k):
            q = g.get(m)
            if q not in (None, '#', o): cnt[q] = cnt.get(q, 0) + 1
        own = sum(g.get(m) == o for m in A.nbrs(k))
        for q, c in cnt.items():
            if c >= 2 and c > own and c == max(cnt.values()) and list(cnt.values()).count(c) == 1: flips[k] = q
    g.update(flips); return len(flips)

def compact(st, n, rng):
    v = E.valid(st, n)
    if not v: return []
    def key(s):
        g = st['grid']; own = sum(g.get(m) == n for m in A.nbrs(s)); en = sum(g.get(m) not in (None, '#', n) for m in A.nbrs(s))
        return (g.get(s) not in (None, '#'), own - en, rng.random())
    return sorted(v, key=key, reverse=True)[:2]

def run(N, pols, K, rng, rule):
    players = S.setup(N); X, Y, flips, by = [], [], 0, {}
    for k in range(K):
        names = list(players); rng.shuffle(names); pol = {n: pols[i % len(pols)] for i, n in enumerate(names)}
        ps = {n: rng.uniform(0.3, 1.0) for n in list(players) + list(A.HOUSE)}
        st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
        att = {n: 1 for n in ps}
        for t in range(2, 15):
            moves = {}
            for n in ps:
                if rng.random() > ps[n]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
                att[n] += 1
                if n in A.HOUSE: continue
                if pol[n] == 'house': A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
                elif pol[n] == 'compact': cells = compact(st, n, rng)
                else: v = E.valid(st, n); cells = [rng.choice(v)] if v else []
                moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
            A.resolve(st, moves)
            if rule == 'pressure': flips += pressure(st)
        sc = A.scores(st)
        for n in ps:
            X.append(att[n]); Y.append(sc[n])
            if n in players: by.setdefault(pol[n], []).append(sc[n] - att[n])
    X, Y = np.array(X, float), np.array(Y, float)
    return np.corrcoef(X, Y)[0, 1] ** 2, flips / K, {p: round(float(np.mean(v)), 2) for p, v in by.items()}

rng = random.Random(1014)
for N in (8, 10):
    for rule in ('base', 'pressure'):
        r2, f, by = run(N, ('house', 'compact', 'random'), 300, rng, rule)
        print(f"N={N:2d} {rule:8s} R2={r2:.3f} flips/season {f:4.1f}  score-minus-moves by policy {by}", flush=True)
