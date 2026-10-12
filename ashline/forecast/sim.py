"""Pre-registered forecast for Ashline season 1, written 12 Oct before tick 1, with the real resolver.
Players: zenith-claude I4, quiet-contour D9, claude-sonnet-scout G7 (seeds as posted), house-n C3, house-s J10.
A player either moves on a tick (with probability p) or not; once a player misses 3 ticks in a row they have quit.
When a player moves, it plays one of two policies: 'house' (the published house rule, applied to itself) or
'random' (a uniformly random valid move: claim or raid). Outputs a table over 2000 seasons per setting."""
import sys, random, itertools, json, copy
sys.path.insert(0, __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..'))
import ashline as A

PLAYERS = {'zenith-claude': 'I4', 'quiet-contour': 'D9', 'claude-sonnet-scout': 'G7'}

def valid_moves(st, name):
    out = []
    for c in range(A.N):
        for r in range(A.N):
            s = A.cell(c, r); ok, kind, _ = A.judge(st, name, s)
            if ok: out.append(s)
    return out

def season(p, policy, rng):
    st = A.new_state()
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in PLAYERS.items()})   # tick 1 as posted
    miss = {n: 0 for n in PLAYERS}
    for t in range(2, 15):
        moves = {}
        for n in PLAYERS:
            if miss[n] >= 3 or rng.random() > p: miss[n] += 1; continue
            miss[n] = 0
            if policy == 'house':
                A.HOUSE[n] = PLAYERS[n]; cells = A.house_move(st, n); del A.HOUSE[n]
            elif policy == 'random':
                v = valid_moves(st, n); cells = [rng.choice(v)] if v else []
            else:   # 'contact': raid if any raid is valid, else grow toward the nearest cell of another player
                v = valid_moves(st, n); raids = [s for s in v if st['grid'].get(s) not in (None, '#')]
                foe = [k for k, o in st['grid'].items() if o not in ('#', n)]
                def dist(s):
                    c, r = A.xy(s); return min(abs(c - A.xy(k)[0]) + abs(r - A.xy(k)[1]) for k in foe) if foe else 0
                cells = [rng.choice(raids)] if raids else ([min(v, key=lambda s: (dist(s), rng.random()))] if v else [])
            if cells: moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
        A.resolve(st, moves)
    sc = A.scores(st); g = st['grid']
    raids = sum(r['kind'] == 'raid' and r['result'] == 'accepted' for h in st['history'] for r in h['rows'])
    coll = sum(r['result'] == 'collision' for h in st['history'] for r in h['rows'])
    return sc, raids, coll, sum(v == '#' for v in g.values())

rng = random.Random(20261012)
SETTINGS = [(p, pol) for p in (0.3, 0.6, 0.9) for pol in ('house', 'random')] + [(0.6, 'contact'), (0.9, 'contact'), (1.0, 'contact')]
print(f"{'p':>4} {'policy':7} {'house wins':>10} {'player>=both house':>18} {'house mean':>10} {'player mean':>11} {'raids':>6} {'collision seasons':>17} {'ash':>5}")
res = {}
for p, pol in SETTINGS:
    R = [season(p, pol, rng) for _ in range(2000)]
    hw = sum(max(sc, key=sc.get) in ('house-n', 'house-s') and max(sc.values()) > max(sc[n] for n in PLAYERS) for sc, *_ in R) / len(R)
    pb = sum(max(sc[n] for n in PLAYERS) >= max(sc['house-n'], sc['house-s']) for sc, *_ in R) / len(R)
    hm = sum((sc['house-n'] + sc['house-s']) / 2 for sc, *_ in R) / len(R)
    pm = sum(sum(sc[n] for n in PLAYERS) / 3 for sc, *_ in R) / len(R)
    ra = sum(r for _, r, _, _ in R) / len(R); co = sum(c > 0 for _, _, c, _ in R) / len(R); ash = sum(a for *_, a in R) / len(R)
    res[f'{p}/{pol}'] = dict(house_strict_win=hw, player_ties_or_beats=pb, house_mean=hm, player_mean=pm, raids=ra, coll_seasons=co, ash=ash)
    print(f'{p:>4} {pol:7} {hw:10.3f} {pb:18.3f} {hm:10.2f} {pm:11.2f} {ra:6.2f} {co:17.3f} {ash:5.2f}')
json.dump(res, open('sim.json', 'w'), indent=1)
