"""Follow-up to rank.py (board #86221): when play reverses the attendance order, who gains? Mixed seats (each
player seat flips a coin between house rule and contact-seeking, house bots on house rule), per-player turnout
0.3-1.0. Fit cells = a + b*moves + c*contact by least squares; c is what contact-seeking is worth in cells at equal
attendance. Also: mean cells lost to raids by contact vs house seats, and win share (strictly most cells) per move."""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, season2 as S, rank as R

def run(N, ticks, K, rng):
    players = S.setup(N); X = []; rows = []
    for _ in range(K):
        ps = {n: rng.uniform(0.3, 1.0) for n in list(players) + list(A.HOUSE)}
        st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
        mv = {n: 1 for n in ps}; pol = {n: rng.random() < 0.5 for n in players}
        for t in range(2, ticks + 1):
            moves = {}
            for n in ps:
                if rng.random() > ps[n]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
                mv[n] += 1
                if n in A.HOUSE: continue
                if pol[n]: cells = R.contact(st, n, rng)
                else: A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
                moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
            A.resolve(st, moves)
        sc = A.scores(st)
        for n in players:
            best_other = max(v for k, v in sc.items() if k != n)
            rows.append((mv[n], float(pol[n]), sc[n], sc[n] - best_other))
    a = np.array(rows); M = np.column_stack([np.ones(len(a)), a[:, 0], a[:, 1]])
    cells = np.linalg.lstsq(M, a[:, 2], rcond=None)[0]; marg = np.linalg.lstsq(M, a[:, 3], rcond=None)[0]
    return cells[2], marg[2], a[a[:, 1] == 1, 2].mean(), a[a[:, 1] == 0, 2].mean()

if __name__ == '__main__':
    rng = random.Random(86221)
    for N, ticks in ((12, 14), (8, 14), (8, 20), (12, 45)):
        c, m, mc, mh = run(N, ticks, 200, rng)
        print(f"{N}x{N} {ticks:2d} ticks  contact-seeking worth {c:+.2f} cells and {m:+.2f} margin at equal attendance  "
              f"(raw mean cells: contact {mc:.1f}, house {mh:.1f})", flush=True)
