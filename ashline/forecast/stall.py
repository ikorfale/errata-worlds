"""zenith's checks on border1 (board #86240, #86224): does border1 pay contact by removing play?
Mixed seats: each player seat draws house rule, contact-seeking (rank.contact: raid if possible, else the valid cell
nearest a rival) or toward (same but never raids), turnout 0.3-1.0, house bots on house rule. Per rule and board:
  stuck   - share of (present player seat, tick) with no legal move at all
  empty   - empty cells left at the end of the season
  raids   - accepted raids per season (all seats)
  c       - worth of each policy vs house at equal attendance, in cells and in margin over the best rival (OLS, SE floor)
Usage: python3 stall.py K [variant ...] [--big]   (--big: 12x12/45 only)"""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, season2 as S, rank as R, rules2 as R2, who_gains as W

def toward(st, n, rng):
    v = [s for s in (A.cell(c, r) for c in range(A.N) for r in range(A.N)) if A.judge(st, n, s)[0] and st['grid'].get(s) is None]
    foe = [k for k, o in st['grid'].items() if o not in ('#', n)]
    def dist(s):
        c, r = A.xy(s); return min(abs(c - A.xy(k)[0]) + abs(r - A.xy(k)[1]) for k in foe) if foe else 0
    return [min(v, key=lambda s: (dist(s), rng.random()))] if v else []

def legal(st, n):
    return any(A.judge(st, n, A.cell(c, r))[0] for c in range(A.N) for r in range(A.N))

def run(N, ticks, K, rng):
    players = S.setup(N); rows = []; stuck = present = 0; empty = []; raids = 0
    for season in range(K):
        ps = {n: rng.uniform(0.3, 1.0) for n in list(players) + list(A.HOUSE)}
        st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
        mv = {n: 1 for n in ps}; pol = {n: rng.choice('hct') for n in players}
        for t in range(2, ticks + 1):
            moves = {}
            for n in ps:
                if rng.random() > ps[n]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
                mv[n] += 1
                if n in A.HOUSE: continue
                present += 1
                if not legal(st, n): stuck += 1
                if pol[n] == 'c': cells = R.contact(st, n, rng)
                elif pol[n] == 't': cells = toward(st, n, rng)
                else: A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
                moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
            out = A.resolve(st, moves)
            raids += sum(r['result'] == 'accepted' and r['kind'] == 'raid' for r in out)
        empty.append(N * N - len(st['grid']))
        sc = A.scores(st)
        for n in players:
            rows.append((mv[n], float(pol[n] == 'c'), float(pol[n] == 't'), sc[n], sc[n] - max(v for k, v in sc.items() if k != n), season))
    a = np.array(rows); M = np.column_stack([np.ones(len(a)), a[:, 0], a[:, 1], a[:, 2]])
    cb, cs = W.ols(M, a[:, 3]); mb, ms = W.ols(M, a[:, 4])
    paired.last = [diff(M, a[:, j], a[:, 5]) for j in (3, 4)]
    return stuck / present, np.mean(empty), np.std(empty), raids / K, cb, cs, mb, ms

def diff(M, y, g):
    """zenith #86294: contact minus toward from the same regression, SE from the covariance (plain OLS) and
    clustered by season (CR0 sandwich), since seats in one season share a board and are not independent."""
    b = np.linalg.lstsq(M, y, rcond=None)[0]; e = y - M @ b; Bi = np.linalg.inv(M.T @ M)
    V = (e @ e / (len(y) - M.shape[1])) * Bi
    meat = sum(np.outer(M[g == k].T @ e[g == k], M[g == k].T @ e[g == k]) for k in np.unique(g)); Vc = Bi @ meat @ Bi
    w = np.array([0, 0, 1, -1.0])
    return b @ w, np.sqrt(w @ V @ w), np.sqrt(w @ Vc @ w), np.sqrt(Vc[2, 2]), np.sqrt(Vc[3, 3])
paired = lambda: None

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    vs = [a for a in sys.argv[2:] if not a.startswith('--')] or ['base', 'border1']
    boards = ((12, 45),) if '--big' in sys.argv else ((12, 14), (8, 20), (12, 45))
    opt = dict(a[2:].split('=', 1) for a in sys.argv if a.startswith('--') and '=' in a)
    if 'board' in opt: boards = (tuple(int(x) for x in opt['board'].split('/')),)  # --board=10/30
    for v in vs:
        A.judge, A.resolve = R2.VARIANTS[v]
        rng = random.Random(int(opt.get('seed', 86240)))
        for N, ticks in boards:
            st, e, es, rd, cb, cs, mb, ms = run(N, ticks, K, rng)
            print(f"{v:8s} {N}x{N} {ticks:2d}t  stuck {100*st:4.1f}%  empty left {e:5.1f}±{es:4.1f} of {N*N}  raids/season {rd:4.1f}  "
                  f"contact {cb[2]:+.2f}±{cs[2]:.2f} cells {mb[2]:+.2f}±{ms[2]:.2f} margin  "
                  f"toward {cb[3]:+.2f}±{cs[3]:.2f} cells {mb[3]:+.2f}±{ms[3]:.2f} margin", flush=True)
            for name, (d, se, sec, scc, sct) in zip(('cells', 'margin'), paired.last):
                print(f"         contact-toward {name}: {d:+.2f}  SE plain {se:.2f}  SE season-clustered {sec:.2f}  (clustered SE of contact {scc:.2f}, toward {sct:.2f})", flush=True)
