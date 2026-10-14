"""Plan #273, zenith #86294: a rule judged by c must hold across fields nobody chose. Worst case of c over seat mixes.
Paired design: in each season one player seat is focal; the two other player seats play a fixed mix of policies
(h house rule, c contact-seeking, t toward = nearest-to-rival cell, never raids); house bots on house rule. The same
season (same attendance draws, same tie-break seed) is played twice, focal on contact and focal on house rule, and
c = focal margin over best rival (contact) - (house). Focal seat rotates; the two others are shuffled per season.
SE is across seasons (each season is one paired difference), so no clustering is needed.
Usage: python3 mixes.py K variant[,variant] N/ticks[,N/ticks]   e.g. python3 mixes.py 120 base,border2,both 12/14,12/45"""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, season2 as S, rank as R, rules2 as R2, stall as T

MIXES = ('hh', 'tt', 'cc', 'ht', 'hc', 'tc')

def play(players, ticks, pres, pol, seed):
    rng = random.Random(seed)
    st = A.new_state(); A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
    for t in range(ticks - 1):
        moves = {}
        for n in pres:
            if not pres[n][t]: moves[n] = {'seq': None, 'cells': [], 'superseded': []}; continue
            if n in A.HOUSE: continue
            p = pol[n]
            if p == 'c': cells = R.contact(st, n, rng)
            elif p == 't': cells = T.toward(st, n, rng)
            else: A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
            moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
        A.resolve(st, moves)
    return A.scores(st)

def run(N, ticks, K, mix, rng):
    players = S.setup(N); names = list(players); d_m, d_c = [], []
    for k in range(K):
        focal = names[k % len(names)]; others = [n for n in names if n != focal]; rng.shuffle(others)
        ps = {n: rng.uniform(0.3, 1.0) for n in names + list(A.HOUSE)}
        pres = {n: [rng.random() <= ps[n] for _ in range(ticks - 1)] for n in ps}
        seed = rng.getrandbits(32); out = {}
        for fp in 'ch':
            pol = {focal: fp, others[0]: mix[0], others[1]: mix[1]}
            sc = play(players, ticks, pres, pol, seed)
            out[fp] = (sc[focal], sc[focal] - max(v for n, v in sc.items() if n != focal))
        d_c.append(out['c'][0] - out['h'][0]); d_m.append(out['c'][1] - out['h'][1])
    se = lambda x: np.std(x, ddof=1) / np.sqrt(len(x))
    return np.mean(d_m), se(d_m), np.mean(d_c), se(d_c)

if __name__ == '__main__':
    K = int(sys.argv[1]); vs = sys.argv[2].split(','); boards = [tuple(map(int, b.split('/'))) for b in sys.argv[3].split(',')]
    for v in vs:
        A.judge, A.resolve = R2.VARIANTS[v]
        for N, ticks in boards:
            res = []
            for mix in MIXES:
                m, sm, c, sc = run(N, ticks, K, mix, random.Random(273))
                res.append((m, sm, mix))
                print(f"{v:8s} {N}x{N} {ticks:2d}t  others {mix}  c margin {m:+.2f}±{sm:.2f}  cells {c:+.2f}±{sc:.2f}", flush=True)
            m, sm, mix = min(res)
            print(f"{v:8s} {N}x{N} {ticks:2d}t  WORST mix {mix}: {m:+.2f}±{sm:.2f}  (best {max(res)[0]:+.2f}, spread {max(res)[0]-m:.2f})", flush=True)
