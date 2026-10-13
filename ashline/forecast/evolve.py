"""Does Ashline have a dominant strategy? (13 Oct, ashline task, before season 2 is announced.)
A policy is a weight vector over features of each valid cell; the best two cells are the move and its backup.
An evolution strategy searches for weights that beat the published house rule. If the winner is
'grow away, never touch, avoid contested cells', contact is a loss and season 2 needs a rule change, not just a
smaller board. Real resolver from ashline.py, unchanged.
Setup: N x N board, season-1 seeds scaled (season2.setup), the evolved policy sits in one of the three player
seats (rotated), the other two seats and both house bots play the house rule; players move with prob p, house
bots too (house_p = p, the season-2 proposal).
Usage: python3 evolve.py N p generations"""
import sys, os, random, json, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A
import season2 as S

FEATS = ['own_nb', 'enemy_nb', 'raid', 'margin', 'contested', 'empty_nb', 'foe_dist', 'ash_nb']


def valid(st, name):
    return [s for c in range(A.N) for r in range(A.N) for s in [A.cell(c, r)] if A.judge(st, name, s)[0]]


def features(st, name, s, vsets):
    g = st['grid']; nb = A.nbrs(s); owner = g.get(s)
    foe = [k for k, o in g.items() if o not in ('#', name)]
    c, r = A.xy(s)
    fd = min(abs(c - A.xy(k)[0]) + abs(r - A.xy(k)[1]) for k in foe) / A.N if foe else 1.0
    return np.array([
        sum(g.get(m) == name for m in nb),
        sum(g.get(m) not in (None, '#', name) for m in nb),
        float(owner not in (None, '#')),
        (A.touch(st, name, s) - A.touch(st, owner, s)) if owner not in (None, '#') else 0,
        sum(s in v for n, v in vsets.items() if n != name),
        sum(g.get(m) is None for m in nb),
        fd,
        sum(g.get(m) == '#' for m in nb)], float)


def season(players, seat, w, p, rng):
    st = A.new_state()
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
    for t in range(2, 15):
        vsets = {n: set(valid(st, n)) for n in list(players) + list(A.HOUSE)}
        moves = {}
        for n in players:
            if rng.random() > p: continue
            if n == seat:
                v = sorted(vsets[n])
                if not v: continue
                sc = [(features(st, n, s, vsets) @ w + 1e-6 * rng.random(), s) for s in v]
                cells = [s for _, s in sorted(sc, reverse=True)[:2]]
            else:
                A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
            if cells: moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
        for h in A.HOUSE:
            if rng.random() > p: moves[h] = {'seq': None, 'cells': [], 'superseded': []}
        A.resolve(st, moves)
    sc = A.scores(st); rows = [r for h in st['history'] for r in h['rows'] if r['name'] == seat]
    best_other = max(v for k, v in sc.items() if k != seat)
    return dict(margin=sc[seat] - best_other, win=sc[seat] > best_other, score=sc[seat],
                raids=sum(r['kind'] == 'raid' and r['result'] == 'accepted' for r in rows),
                coll=sum(r['result'] == 'collision' for r in rows))


def evaluate(players, w, p, k, seed):
    rng = random.Random(seed); R = []
    seats = list(players)
    for i in range(k):
        R.append(season(players, seats[i % 3], w, p, rng))
    return {key: float(np.mean([r[key] for r in R])) for key in R[0]}


if __name__ == '__main__':
    N, p, G = int(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
    K = 24; LAM = 10; SIG = 0.5
    players = S.setup(N)
    # house rule written in these features: own_nb first, then -enemy, raid margin dominates
    house_w = np.array([1.0, -0.1, 10.0, 1.0, 0, 0, 0, 0])
    rs = np.random.default_rng(20261013)
    log = []
    base = evaluate(players, house_w, p, 120, 7)
    print('house-rule seat (approx, linear):', base, flush=True)
    mean = rs.normal(0, 1, len(FEATS))
    for g in range(G):
        t0 = time.time()
        pop = [mean] + [mean + SIG * rs.normal(0, 1, len(FEATS)) for _ in range(LAM)]
        fit = [evaluate(players, w, p, K, 1000 + g) for w in pop]     # common random numbers within a generation
        order = np.argsort([-f['margin'] for f in fit])
        elite = [pop[i] for i in order[:3]]
        mean = np.mean(elite, axis=0)
        best = fit[order[0]]
        log.append({'gen': g, 'best': best, 'w': pop[order[0]].tolist(), 'mean': mean.tolist()})
        print(f"g{g:02d} margin {best['margin']:+.2f} win {best['win']:.2f} score {best['score']:.1f} raids {best['raids']:.2f} coll {best['coll']:.2f}"
              f"  w={np.round(pop[order[0]] / np.abs(pop[order[0]]).max(), 2).tolist()} ({time.time()-t0:.0f}s)", flush=True)
    final = evaluate(players, mean, p, 240, 99)                       # fresh seeds: no selection on these
    print('final mean policy on fresh seeds:', final, flush=True)
    print('weights:', dict(zip(FEATS, np.round(mean / np.abs(mean).max(), 3).tolist())), flush=True)
    json.dump({'N': N, 'p': p, 'house_seat': base, 'final': final, 'w': mean.tolist(), 'feats': FEATS, 'log': log},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'evolve_{N}_{p}.json'), 'w'), indent=1)
