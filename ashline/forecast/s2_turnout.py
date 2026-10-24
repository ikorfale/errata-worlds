"""Season 2 under real turnout (plan #256; Fable review 24.10: every earlier season-2 table set attendance to 1 for
all seats, so none tested the effect that decided season 1). Pre-registration: PREREG-turnout.md, committed first.

Field: six player seats whose attendance is season 1's observed field after 12 ticks: moves 12, 11, 6, 5, 2, 1 of 12,
i.e. p = 1.00, 0.92, 0.50, 0.42, 0.17, 0.08 per tick. A seat plays only on ticks it attends; it seeds on its first
attended tick on a random empty cell at least 3 steps (Manhattan) from both houses. Houses play every tick on the
published rule. 12x12, 14 ticks (tick 1 included: seats that attend tick 1 seed then).
Policies (s2_choice.py): exp for every seat (what season 1's players did: 0 raids, 0 collisions), and a variant
where the two regulars play seek (mixed).
Rules: base (season 1 scoring) and border (a cell touching another player's cell scores 2).
Per row, K seasons:
  primary  - share of seasons where the top-scoring player seat is not a top-mover among player seats
             (ties split: a tied top counts as the fraction of top seats that are not top movers)
  also     - house strictly first (top house score > every player seat), ash per season, raids per season
Board size: --n=N rescales the board and the two house cells as season2.py does (default 12).
Usage: python3 s2_turnout.py [K] [seed] [--n=N] [--rules=base,border] [--mix=exp,mixed]"""
import sys, random
import numpy as np
import s2_choice as C
import ashline as A

P = [1.00, 0.92, 0.50, 0.42, 0.17, 0.08]
SEATS = [f'P{i + 1}' for i in range(len(P))]


def season(rule, pols, rng, ticks=14):
    A.judge = C.JUDGE
    st = A.new_state(); moves_made = {n: 0 for n in SEATS}; out = dict(raids=0, ash=0)
    houses = [A.xy(s) for s in A.HOUSE.values()]
    for t in range(1, ticks + 1):
        mv = {}
        for n, p in zip(SEATS, P):
            if rng.random() >= p: continue
            if not A.owned(st, n):
                ok = [A.cell(c, r) for c in range(A.N) for r in range(A.N)
                      if st['grid'].get(A.cell(c, r)) is None and all(abs(c - hc) + abs(r - hr) >= 3 for hc, hr in houses)]
                ok = ok or [A.cell(c, r) for c in range(A.N) for r in range(A.N) if st['grid'].get(A.cell(c, r)) is None]
                if not ok: continue  # a late joiner on a full board cannot seed
                cells = [rng.choice(ok)]
            else:
                cells = C.policy(st, n, pols[n], rng)
            if cells: mv[n] = {'seq': 0, 'cells': cells, 'superseded': []}
        rows = A.resolve(st, mv)
        for r in rows:
            if r['name'] in moves_made and r['result'] == 'accepted': moves_made[r['name']] += 1
            if r['result'] == 'accepted' and r['kind'] == 'raid': out['raids'] += 1
        out['ash'] += len({r['pick'] for r in rows if r['result'] == 'collision'})
    sc = C.score(st, rule)
    ps = {n: sc.get(n, 0) for n in SEATS}
    top = max(ps.values()); tops = [n for n in SEATS if ps[n] == top]
    mtop = max(moves_made.values()); movers = {n for n in SEATS if moves_made[n] == mtop}
    out['not_mover'] = sum(n not in movers for n in tops) / len(tops)
    out['house_first'] = float(max(sc[h] for h in A.HOUSE) > top)
    return out


def row(rule, mix, K, seed):
    rng = random.Random(seed)
    pols = {n: ('seek' if mix == 'mixed' and i < 2 else 'exp') for i, n in enumerate(SEATS)}
    R = [season(rule, pols, rng) for _ in range(K)]
    f = lambda k: (np.mean([o[k] for o in R]), np.std([o[k] for o in R], ddof=1) / np.sqrt(K))
    (nm, nms), (hf, hfs), (ash, _), (rd, _) = f('not_mover'), f('house_first'), f('ash'), f('raids')
    print(f'{rule:6} {mix:6} not-top-mover leader {nm:.3f}±{nms:.3f}  house strictly first {hf:.3f}±{hfs:.3f}  '
          f'ash {ash:.2f}  raids {rd:.2f}  (K={K})', flush=True)


if __name__ == '__main__':
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
    pos = [a for a in sys.argv[1:] if not a.startswith('--')]
    K = int(pos[0]) if len(pos) > 0 else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2410
    n = int(opt.get('n', 12))
    if n != 12:
        import season2
        A.N = n; A.HOUSE.update({h: season2.scale(s, n) for h, s in season2.HOUSE1.items()})
        print(f'board {n}x{n}, houses {A.HOUSE}', flush=True)
    for rule in opt.get('rules', 'base,border').split(','):
        for mix in opt.get('mix', 'exp,mixed').split(','):
            row(rule, mix, K, seed)
