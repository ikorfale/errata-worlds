"""#271 follow-up: if every player seat plays the evolved pocket policy (enclosure scoring, ENC_CAP pockets),
is the score a turnout counter again? Per-player move probability uniform 0.3-1.0 (as attendance.py); house bots
play the house rule. Prints R2(score~moves) over player seats, and players' mean pocket cells.
Usage: ENC_CAP=4 python3 enc_symmetric.py N weights.json [K]"""
import sys, os, random, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import enclosure as EN          # patches A.scores
import ashline as A, season2 as S, evolve as E

def feats(st, name, s, vsets):
    g = st['grid']; before = EN.sealed(st).get(name, 0); old = g.get(s); g[s] = name
    after = EN.sealed(st).get(name, 0)
    if old is None: del g[s]
    else: g[s] = old
    return np.concatenate([E.features(st, name, s, vsets), [after - before]])

N = int(sys.argv[1]); w = np.array(json.load(open(sys.argv[2]))['w']); K = int(sys.argv[3]) if len(sys.argv) > 3 else 120
players = S.setup(N); rng = random.Random(1014); X, Y, P = [], [], []
for _ in range(K):
    ps = {n: rng.uniform(0.3, 1.0) for n in list(players) + list(A.HOUSE)}
    st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
    att = {n: 1 for n in ps}
    for t in range(2, 15):
        vsets = {n: set(E.valid(st, n)) for n in ps}; moves = {}
        for n in ps:
            if rng.random() > ps[n]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
            att[n] += 1
            if n in A.HOUSE: continue
            v = sorted(vsets[n])
            if not v: continue
            sc = [(feats(st, n, s, vsets) @ w + 1e-6 * rng.random(), s) for s in v]
            moves[n] = {'seq': 0, 'cells': [s for _, s in sorted(sc, reverse=True)[:2]], 'superseded': []}
        A.resolve(st, moves)
    sc = A.scores(st); pk = EN.sealed(st)
    for n in players: X.append(att[n]); Y.append(sc[n]); P.append(pk.get(n, 0))
X, Y = np.array(X, float), np.array(Y, float)
r = np.corrcoef(X, Y)[0, 1]
print(f"N={N} cap={EN.CAP} all seats pocket policy, K={K}: R2(score~moves)={r*r:.3f}  mean pocket cells/player {np.mean(P):.2f}  score-moves sd {np.std(Y - X):.2f}")
