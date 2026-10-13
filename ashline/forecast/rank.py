"""zenith's check (#86198): does play change who finishes ahead? R^2 of own score on own moves cannot see who lost a
raided cell, so compare orders instead. Per season (house rule for all, per-player turnout 0.3-1.0 as attendance.py):
 - discordant: among pairs of players with different move counts, share where the one with fewer moves finishes
   strictly ahead in cells;
 - flat: share of such pairs that finish level in cells (attendance did not separate them either);
 - top differs: seasons where the cell leader is not (one of) the move leaders.
Also the median number of ticks after T* (first boxed-in tick) among seasons that reach it, zenith's caution on 0.682."""
import sys, os, random, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, season2 as S, split as SP

def contact(st, n, rng):
    v = [s for s in (A.cell(c, r) for c in range(A.N) for r in range(A.N)) if A.judge(st, n, s)[0]]
    raids = [s for s in v if st['grid'].get(s) not in (None, '#')]
    foe = [k for k, o in st['grid'].items() if o not in ('#', n)]
    def dist(s):
        c, r = A.xy(s); return min(abs(c - A.xy(k)[0]) + abs(r - A.xy(k)[1]) for k in foe) if foe else 0
    return [rng.choice(raids)] if raids else ([min(v, key=lambda s: (dist(s), rng.random()))] if v else [])

def run(N, ticks, K, rng, mixed=False):
    players = S.setup(N); disc = flat = pairs = 0; top = 0; after = []; turn = []
    for _ in range(K):
        ps = {n: rng.uniform(0.3, 1.0) for n in list(players) + list(A.HOUSE)}
        st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
        mv = {n: 1 for n in ps}; T = None
        pol = {n: (mixed and rng.random() < 0.5) for n in players}
        for t in range(2, ticks + 1):
            if T is None and SP.boxed(st): T = t
            moves = {}
            for n in ps:
                if rng.random() > ps[n]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
                mv[n] += 1
                if n in A.HOUSE: continue
                if pol[n]: cells = contact(st, n, rng)
                else: A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
                moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
            A.resolve(st, moves)
        if T: after.append(ticks - T + 1)
        sc = A.scores(st); turn.append(np.mean([(mv[n] - 1) / (ticks - 1) for n in ps]))
        for a, b in itertools.combinations(ps, 2):
            if mv[a] == mv[b]: continue
            hi, lo = (a, b) if mv[a] > mv[b] else (b, a); pairs += 1
            disc += sc[lo] > sc[hi]; flat += sc[lo] == sc[hi]
        best = max(sc.values()); mm = max(mv.values())
        top += not any(sc[n] == best and mv[n] == mm for n in ps)
    return disc / pairs, flat / pairs, top / K, (np.median(after) if after else None), len(after) / K, np.mean(turn)

if __name__ == '__main__':
    rng = random.Random(86198)
    for mixed in (False, True):
      print('players: house rule' if not mixed else 'players: each seat flips a coin between house rule and contact-seeking (raid if possible, else grow toward nearest rival)')
      for N, ticks in ((12, 14), (8, 14), (8, 20), (12, 30), (12, 45)):
        d, f, t, med, reach, tu = run(N, ticks, 200, rng, mixed)
        print(f"  {N}x{N} {ticks:2d} ticks  land/expected moves={N*N/(5*(ticks-1)*tu+5):.2f}  discordant pairs {d:.1%}  level {f:.1%}  "
              f"leader not a move leader {t:.0%}  reach T* {reach:.0%}  median ticks after T* {med}", flush=True)
