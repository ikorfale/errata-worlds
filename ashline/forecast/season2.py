"""Season 2 design check for Ashline, 13 Oct (task #256), before anything is announced.
Question: on which board size does contact (two owners touching) happen early enough to matter in a 14-tick season,
and does contact produce raids, or only collisions and ash? The real resolver from ashline.py is used unchanged;
only the board size N and the seeds change. Seeds are the season-1 seeds scaled to the smaller board:
players I4, D9, G7 and house bots C3, J10 mapped by round(x * (N-1) / 11).
Policies as in sim.py: 'house' (everyone plays the published house rule), 'random' (uniform valid move),
'contact' (raid if possible, else grow toward the nearest other player). p = chance a player moves on a tick.
Usage: python3 season2.py [seasons_per_setting]"""
import sys, os, random, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A

SEEDS1 = {'zenith-claude': 'I4', 'quiet-contour': 'D9', 'claude-sonnet-scout': 'G7'}
HOUSE1 = {'house-n': 'C3', 'house-s': 'J10'}


def scale(s, n):
    c, r = A.xy(s)  # uses N-independent COLS
    return A.COLS[round(c * (n - 1) / 11)] + str(round(r * (n - 1) / 11) + 1)


def setup(n):
    A.N = n
    A.HOUSE.clear(); A.HOUSE.update({h: scale(s, n) for h, s in HOUSE1.items()})
    players = {p: scale(s, n) for p, s in SEEDS1.items()}
    assert len(set(players.values()) | set(A.HOUSE.values())) == 5, (n, players, A.HOUSE)
    return players


def valid_moves(st, name):
    return [s for c in range(A.N) for r in range(A.N) for s in [A.cell(c, r)] if A.judge(st, name, s)[0]]


def contact(st):
    g = st['grid']
    return any(o not in (None, '#') and g.get(m) not in (None, '#', o) for k, o in g.items() for m in A.nbrs(k))


def season(players, p, policy, rng, house_p=1.0):
    st = A.new_state()
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in players.items()})
    first = None
    for t in range(2, 15):
        moves = {}
        for n in players:
            if rng.random() > p: continue
            if policy == 'house':
                A.HOUSE[n] = players[n]; cells = A.house_move(st, n); del A.HOUSE[n]
            else:
                v = valid_moves(st, n)
                if policy == 'random': cells = [rng.choice(v)] if v else []
                else:
                    raids = [s for s in v if st['grid'].get(s) not in (None, '#')]
                    foe = [k for k, o in st['grid'].items() if o not in ('#', n)]
                    def dist(s):
                        c, r = A.xy(s); return min(abs(c - A.xy(k)[0]) + abs(r - A.xy(k)[1]) for k in foe) if foe else 0
                    cells = [rng.choice(raids)] if raids else ([min(v, key=lambda s: (dist(s), rng.random()))] if v else [])
            if cells: moves[n] = {'seq': 0, 'cells': cells, 'superseded': []}
        for h in A.HOUSE:
            if rng.random() > house_p: moves[h] = {'seq': None, 'cells': [], 'superseded': []}   # house sits this tick out
        A.resolve(st, moves)
        if first is None and contact(st): first = t
    sc = A.scores(st); rows = [r for h in st['history'] for r in h['rows']]
    return dict(first=first,
                raids=sum(r['kind'] == 'raid' and r['result'] == 'accepted' for r in rows),
                coll=sum(r['result'] == 'collision' for r in rows) // 2,
                ash=sum(v == '#' for v in st['grid'].values()),
                fill=len(st['grid']) / A.N ** 2,
                house_win=max(sc, key=sc.get) in A.HOUSE and max(sc.values()) > max(sc[n] for n in players),
                stalled=sum(1 for h in st['history'][1:] for r in h['rows'] if r['name'] in A.HOUSE and r['result'] == 'rejected'))


if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    rng = random.Random(20261013); out = {}
    print(f"{'N':>3} {'p':>4} {'policy':7} {'contact%':>8} {'1st tick':>8} {'raids':>6} {'coll':>5} {'ash':>5} {'fill':>5} {'house win':>9}")
    for n in (tuple(int(x) for x in sys.argv[2].split(",")) if len(sys.argv) > 2 else (6, 7, 8, 10, 12)):
        players = setup(n)
        for p in (0.6, 0.9):
            for pol in ('house', 'random', 'contact'):
                t0 = time.time(); R = [season(players, p, pol, rng) for _ in range(K)]
                c = [r['first'] for r in R if r['first']]
                row = dict(contact=len(c) / K, first_med=sorted(c)[len(c) // 2] if c else None,
                           raids=sum(r['raids'] for r in R) / K, coll=sum(r['coll'] for r in R) / K,
                           ash=sum(r['ash'] for r in R) / K, fill=sum(r['fill'] for r in R) / K,
                           house_win=sum(r['house_win'] for r in R) / K, seeds=dict(players, **A.HOUSE))
                out[f'{n}/{p}/{pol}'] = row
                print(f"{n:>3} {p:>4} {pol:7} {row['contact']:8.2f} {str(row['first_med']):>8} {row['raids']:6.2f} {row['coll']:5.2f} "
                      f"{row['ash']:5.2f} {row['fill']:5.2f} {row['house_win']:9.2f}  ({time.time() - t0:.0f}s)", flush=True)
    if len(sys.argv) > 3 and sys.argv[3] == 'house-matched':   # variant: house bots skip ticks at the players' rate
        print('variant: house bots move with the same p as players')
        for n in (8, 12):
            players = setup(n)
            for p in (0.6, 0.9):
                R = [season(players, p, 'random', rng, house_p=p) for _ in range(K)]
                c = [r['first'] for r in R if r['first']]
                print(f"{n:>3} {p:>4} random  contact {len(c)/K:.2f} first {sorted(c)[len(c)//2] if c else None} raids {sum(r['raids'] for r in R)/K:.2f} "
                      f"coll {sum(r['coll'] for r in R)/K:.2f} fill {sum(r['fill'] for r in R)/K:.2f} house_win {sum(r['house_win'] for r in R)/K:.2f}", flush=True)
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'season2.json' if len(sys.argv) < 3 else f'season2_{sys.argv[2]}.json'), 'w'), indent=1)
