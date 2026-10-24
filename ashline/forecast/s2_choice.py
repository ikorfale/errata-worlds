"""Season 2 choice (plan #371, board #94522): raid on a tie vs border scoring, my own run, written after glitchfox
posted his numbers (#94537, v_ashline_s2.py) and before reading his script. Setup chosen to match his description:
12x12, 14 ticks, house-n C3 and house-s J10 on the published rule, 4 players seeded on random empty cells at least 3
steps (Manhattan) from both houses, everyone moves every tick. Player ties are broken by the rng, house ties by hash.
Rules (resolver otherwise unchanged):
  base   - season 1: raid needs >= 2 touches and strictly more than the owner
  tie    - raid needs >= 2 touches and at least as many as the owner
  border - season 1 moves; score = cells + cells that touch another player's cell (a border cell scores 2)
Player policies:
  exp    - the published house rule's claim order applied to itself, never raids
  raid   - the valid raid with the best margin when one exists, else as exp
  seek   - the valid empty claim touching the most other-player cells (rng tie-break) when one touches any, else as exp
Per season: raids accepted (anyone), share of raided cells that change hands again (or burn) within 2 ticks, ash,
collision ash by who collided (2+ active-policy players vs other), cells each player lost to raids, moves each player
lost to ash, house share of first place (ties split evenly), and in mixed tables (coin flip per seat) the score of active minus exp seats.
Usage: python3 s2_choice.py [seasons]"""
import sys, os, random, json, hashlib
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A

JUDGE = A.judge

def judge_tie(st, name, s):
    g = st['grid'].get(s)
    if g not in (None, '#') and g != name:
        a, d = A.touch(st, name, s), A.touch(st, g, s)
        if a >= 2 and a >= d: return True, 'raid', f'tie raid on {g}: {a} vs {d}'
    return JUDGE(st, name, s)

def foes(st, name, s):
    return sum(st['grid'].get(m) not in (None, '#', name) for m in A.nbrs(s))

def score(st, rule):
    sc = {}
    for p in st['players']:
        mine = A.owned(st, p)
        sc[p] = len(mine) + (sum(foes(st, p, s) > 0 for s in mine) if rule == 'border' else 0)
    return sc

def valid(st, name):
    return [(s, k) for c in range(A.N) for r in range(A.N) for s in [A.cell(c, r)] for ok, k, _ in [A.judge(st, name, s)] if ok]

def exp_order(st, name, v):
    """house rule key for claims only: most own neighbours, fewest enemy neighbours, hash."""
    cl = [s for s, k in v if k in ('claim', 'seed')]
    key = lambda s: (A.touch(st, name, s), -foes(st, name, s), hashlib.sha256(f"{st['tick']}|{name}|{s}".encode()).hexdigest())
    return sorted(cl, key=key, reverse=True)[:2]

def policy(st, name, pol, rng):
    v = valid(st, name)
    if pol == 'raid':
        raids = [s for s, k in v if k == 'raid']
        if raids:
            best = max(A.touch(st, name, s) - A.touch(st, st['grid'][s], s) for s in raids)
            return [rng.choice([s for s in raids if A.touch(st, name, s) - A.touch(st, st['grid'][s], s) == best])]
    if pol == 'seek':
        cl = [s for s, k in v if k == 'claim' and foes(st, name, s) > 0]
        if cl:
            m = max(foes(st, name, s) for s in cl)
            return [rng.choice([s for s in cl if foes(st, name, s) == m])]
    return exp_order(st, name, v)

def seeds(rng):
    houses = [A.xy(s) for s in A.HOUSE.values()]
    ok = [A.cell(c, r) for c in range(A.N) for r in range(A.N) if all(abs(c - hc) + abs(r - hr) >= 3 for hc, hr in houses)]
    return dict(zip(['P1', 'P2', 'P3', 'P4'], rng.sample(ok, 4)))

def season(rule, pols, rng, ticks=14):
    A.judge = judge_tie if rule == 'tie' else JUDGE
    st = A.new_state(); seed = seeds(rng)
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()})
    snaps = [dict(st['grid'])]; out = dict(raids=0, rechange=0, ash=0, ash_aa=0, lost_raid={n: 0 for n in pols},
                                          lost_ash={n: 0 for n in pols}, raids_by={n: 0 for n in list(pols) + list(A.HOUSE)})
    raid_at = []
    for t in range(2, ticks + 1):
        moves = {n: {'seq': 0, 'cells': policy(st, n, pols[n], rng), 'superseded': []} for n in pols}
        before = dict(st['grid']); rows = A.resolve(st, moves); snaps.append(dict(st['grid']))
        for r in rows:
            if r['result'] == 'accepted' and r['kind'] == 'raid':
                out['raids'] += 1; out['raids_by'][r['name']] += 1; raid_at.append((len(snaps) - 1, r['pick'], r['name']))
                v = before[r['pick']]
                if v in out['lost_raid']: out['lost_raid'][v] += 1
            if r['result'] == 'collision' and r['name'] in out['lost_ash']: out['lost_ash'][r['name']] += 1
        for s in {r['pick'] for r in rows if r['result'] == 'collision'}:
            out['ash'] += 1
            who = [r['name'] for r in rows if r['pick'] == s]
            out['ash_aa'] += sum(pols.get(n) in ('raid', 'seek', 'seek1', 'seek2') for n in who) >= 2
    for i, s, n in raid_at:   # changes hands again (or burns) within the next 2 ticks
        later = snaps[i + 1:i + 3]
        out['rechange'] += any(g.get(s) != n for g in later) if later else 0
    out['raids_counted'] = sum(1 for i, *_ in raid_at if i + 1 < len(snaps))
    sc = score(st, rule); top = max(sc.values())
    lead = [p for p, v in sc.items() if v == top]
    out['house_win'] = sum(p in A.HOUSE for p in lead) / len(lead)   # share of the top held by houses (ties split)
    out['score'] = sc
    return out

def table(rule, mix, K, rng):
    """mix: 'exp4', 'act2', 'act4' or 'coin' (each seat flips); active policy = raid for base/tie, seek for border."""
    act = 'seek' if rule == 'border' else 'raid'
    R = []; diffs = []
    for _ in range(K):
        if mix == 'coin': pols = {n: (act if rng.random() < 0.5 else 'exp') for n in ('P1', 'P2', 'P3', 'P4')}
        else:
            k = {'exp4': 0, 'act2': 2, 'act4': 4}[mix]; pols = {n: (act if i < k else 'exp') for i, n in enumerate(('P1', 'P2', 'P3', 'P4'))}
        o = season(rule, pols, rng); R.append(o)
        a = [o['score'][n] for n in pols if pols[n] == act]; e = [o['score'][n] for n in pols if pols[n] == 'exp']
        if a and e: diffs.append(np.mean(a) - np.mean(e))
    raids = np.mean([o['raids'] for o in R]); nr = sum(o['raids_counted'] for o in R)
    row = dict(rule=rule, mix=mix, act=act, K=K, raids=raids, any_raid=np.mean([o['raids'] > 0 for o in R]),
               rechange=(sum(o['rechange'] for o in R) / nr) if nr else float('nan'), raids_n=nr,
               ash=np.mean([o['ash'] for o in R]), ash_aa=np.mean([o['ash_aa'] for o in R]),
               house_win=np.mean([o['house_win'] for o in R]),
               raids_by_house=np.mean([sum(v for k, v in o['raids_by'].items() if k in A.HOUSE) for o in R]),
               lost_raid_exp=mean_by(R, 'lost_raid', 'exp'), lost_raid_act=mean_by(R, 'lost_raid', act),
               lost_ash_exp=mean_by(R, 'lost_ash', 'exp'), lost_ash_act=mean_by(R, 'lost_ash', act),
               pay=(np.mean(diffs), np.std(diffs, ddof=1) / np.sqrt(len(diffs))) if len(diffs) > 1 else None)
    return row

def mean_by(R, key, pol):
    v = [o[key][n] for o in R for n in o[key] if o['pols'][n] == pol]
    return float(np.mean(v)) if v else float('nan')

_season = season
def season(rule, pols, rng, ticks=14):   # keep the seat policies with the result
    o = _season(rule, pols, rng, ticks); o['pols'] = dict(pols); return o

def polname(o, n): return o['pols'][n]

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    rng = random.Random(94537); res = []
    print(f"{'rule':6} {'mix':5} {'raids':>5} {'any':>4} {'re<=2t':>7} {'ash':>4} {'ash a-a':>7} {'house win':>9} "
          f"{'lost to raid exp/act':>20} {'lost to ash exp/act':>19} {'act-exp score (coin)':>21}", flush=True)
    for rule in ('base', 'tie', 'border'):
        for mix in ('exp4', 'act2', 'act4', 'coin'):
            r = table(rule, mix, K, rng); res.append(r)
            pay = f"{r['pay'][0]:+.2f}±{r['pay'][1]:.2f}" if r['pay'] and mix == 'coin' else ''
            print(f"{rule:6} {mix:5} {r['raids']:5.2f} {r['any_raid']:4.0%} {r['rechange']:7.0%} {r['ash']:4.2f} {r['ash_aa']:7.2f} "
                  f"{r['house_win']:9.0%} {r['lost_raid_exp']:9.2f}/{r['lost_raid_act']:<10.2f} {r['lost_ash_exp']:8.2f}/{r['lost_ash_act']:<10.2f} {pay:>21}", flush=True)
    json.dump([{k: (list(v) if isinstance(v, tuple) else v) for k, v in r.items()} for r in res],
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 's2_choice.json'), 'w'), indent=1, default=float)
