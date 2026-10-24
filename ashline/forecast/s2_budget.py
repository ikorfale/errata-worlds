"""Season 2 with a fixed move budget (plan #492; zenith 101532). Pre-registration: PREREG-budget.md, committed first.

Field and placement as s2_turnout.py: six player seats with season 1's observed attendance p = 1.00, 0.92, 0.50,
0.42, 0.17, 0.08 per tick; every seat places with exp (what season 1's players did); houses play every tick on the
published rule; 12x12, 14 ticks. New: each player seat and each house has a budget of B moves for the season (the seeding move
counts; houses spend early: they move on ticks 1..B and pass after). A seat that attends a tick spends one move only if its timing policy says so; a submitted move costs one
unit of budget whether it is accepted or turns to ash.
Timing policies:
  early  - spend on every attended tick until the budget is gone
  late   - hold until the expected attended ticks left (p * ticks left, this one included) are <= budget left,
           then spend on every attended tick (one-way; under expiry once per week): as late as a seat can go without expecting to lose moves
Mixes: all-early, all-late, half (the three most regular seats late, the rest early).
Expiry variant (zenith's guard): the budget comes as B/2 per week (ticks 1-7, 8-14); at most 2 unspent moves carry
into week 2; houses get the same weekly budget (they spend ticks 1-3 and 8-10). Policies apply within the moves available.
Per row, K seasons:
  primary  - share of seasons where the top-scoring player seat is not a top attender (ticks present) among seats
             (ties split as in s2_turnout.py)
  also     - house strictly first, ash per season, player moves per tick and ash per tick (means over seasons,
             ticks 1-14, with the share falling in ticks 13-14), win share by seat (ties split),
             share of seasons with a tied top, P1 strictly first
Usage: python3 s2_budget.py [K] [seed] [--B=6] [--rules=base,border] [--mix=early,late,half] [--expiry=0,1]"""
import sys, random
import numpy as np
import s2_choice as C
import ashline as A

P = [1.00, 0.92, 0.50, 0.42, 0.17, 0.08]
SEATS = [f'P{i + 1}' for i in range(len(P))]
T = 14


def season(rule, timing, B, expiry, rng):
    A.judge = C.JUDGE
    st = A.new_state(); out = dict(raids=0, ash=0, ash_t=[0] * T, mv_t=[0] * T)
    out['win'] = [0.0] * len(SEATS)
    att = {n: 0 for n in SEATS}; released = set()
    left = {n: (B // 2 if expiry else B) for n in SEATS}
    hleft = {h: (B // 2 if expiry else B) for h in A.HOUSE}
    houses = [A.xy(s) for s in A.HOUSE.values()]
    for t in range(1, T + 1):
        if expiry and t == 8:
            for n in SEATS: left[n] = min(left[n], 2) + (B - B // 2)
            for h in A.HOUSE: hleft[h] = min(hleft[h], 2) + (B - B // 2)
        mv = {}
        for h in A.HOUSE:
            if hleft[h] > 0: hleft[h] -= 1
            else: mv[h] = {'seq': None, 'cells': [], 'superseded': []}
        for n, p in zip(SEATS, P):
            if rng.random() >= p: continue
            att[n] += 1
            if left[n] <= 0: continue
            if timing[n] == 'late' and (n, t <= 7 and expiry) not in released:
                end = 7 if expiry and t <= 7 else T
                if p * (end - t + 1) > left[n]: continue
                released.add((n, t <= 7 and expiry))  # one-way: once released, spend on every attended tick
            if not A.owned(st, n):
                ok = [A.cell(c, r) for c in range(A.N) for r in range(A.N)
                      if st['grid'].get(A.cell(c, r)) is None and all(abs(c - hc) + abs(r - hr) >= 3 for hc, hr in houses)]
                ok = ok or [A.cell(c, r) for c in range(A.N) for r in range(A.N) if st['grid'].get(A.cell(c, r)) is None]
                if not ok: continue
                cells = [rng.choice(ok)]
            else:
                cells = C.policy(st, n, 'exp', rng)
            if cells:
                mv[n] = {'seq': 0, 'cells': cells, 'superseded': []}; left[n] -= 1
        out['mv_t'][t - 1] = sum(1 for n in mv if n in SEATS and mv[n]['cells'])
        rows = A.resolve(st, mv)
        for r in rows:
            if r['result'] == 'accepted' and r['kind'] == 'raid': out['raids'] += 1
        a = len({r['pick'] for r in rows if r['result'] == 'collision'})
        out['ash'] += a; out['ash_t'][t - 1] += a
    sc = C.score(st, rule)
    ps = {n: sc.get(n, 0) for n in SEATS}
    top = max(ps.values()); tops = [n for n in SEATS if ps[n] == top]
    atop = max(att.values()); attenders = {n for n in SEATS if att[n] == atop}
    for n in tops: out['win'][SEATS.index(n)] = 1 / len(tops)
    out['tied'] = float(len(tops) > 1); out['p1_strict'] = float(tops == ['P1'])
    out['not_att'] = sum(n not in attenders for n in tops) / len(tops)
    out['house_first'] = float(max(sc[h] for h in A.HOUSE) > top)
    return out


def row(rule, mix, B, expiry, K, seed):
    rng = random.Random(seed)
    timing = {n: ('late' if mix == 'late' or (mix == 'half' and i < 3) else 'early') for i, n in enumerate(SEATS)}
    R = [season(rule, timing, B, expiry, rng) for _ in range(K)]
    f = lambda k: (np.mean([o[k] for o in R]), np.std([o[k] for o in R], ddof=1) / np.sqrt(K))
    (nm, nms), (hf, hfs), (ash, ashs) = f('not_att'), f('house_first'), f('ash')
    (td, tds), (p1, p1s) = f('tied'), f('p1_strict')
    at = np.mean([o['ash_t'] for o in R], axis=0)
    print(f'B={B} expiry={expiry} {rule:6} {mix:5} not-top-attender leader {nm:.3f}±{nms:.3f}  house strictly first '
          f'{hf:.3f}±{hfs:.3f}  ash {ash:.2f}±{ashs:.2f}  (K={K})', flush=True)
    mt = np.mean([o['mv_t'] for o in R], axis=0); w = np.mean([o['win'] for o in R], axis=0)
    print('    player moves per tick ' + ' '.join(f'{x:.2f}' for x in mt) + f'   share in ticks 13-14 {mt[12:].sum() / mt.sum():.2f}', flush=True)
    print(f'    tied top {td:.3f}±{tds:.3f}  P1 strictly first {p1:.3f}±{p1s:.3f}', flush=True)
    print('    win share by seat (p ' + '/'.join(f'{p:.2f}' for p in P) + ') ' + ' '.join(f'{x:.3f}' for x in w), flush=True)
    print('    ash per tick ' + ' '.join(f'{x:.2f}' for x in at) + f'   share in ticks 13-14 {at[12:].sum() / max(at.sum(), 1e-9):.2f}', flush=True)


if __name__ == '__main__':
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
    pos = [a for a in sys.argv[1:] if not a.startswith('--')]
    K = int(pos[0]) if len(pos) > 0 else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2410
    B = int(opt.get('B', 6))
    for ex in [int(x) for x in opt.get('expiry', '0,1').split(',')]:
        for rule in opt.get('rules', 'base,border').split(','):
            for mix in opt.get('mix', 'early,late,half').split(','):
                row(rule, mix, B, ex, K, seed)
