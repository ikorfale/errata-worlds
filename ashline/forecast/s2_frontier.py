"""Season 2: a third tie-break step, open frontier (zenith 101621), on the budget + border field of s2_bb.py.
Pre-registration: PREREG-frontier.md. Everything is s2_bb.py's season() (copied below, one change) except the tie key:
  frozen   - s2_bb.py's rule: 1) fewest own moves turned to ash, 2) most cells touching another player
  frontier - the same, then 3) most distinct empty cells orthogonally next to the seat's own cells at season end
Both rules are scored on the same seasons (same seeds as s2_bb.py), so --rule=frozen must reproduce s2_bb.txt.
Placement policies do not know the tie rule: this measures the tie rule on unchanged play, not how players would
adapt to it (zenith: it may reward spreading thin).
Usage: python3 s2_frontier.py [K] [seed] [--rule=frozen|frontier]"""
import sys, random
import numpy as np
from s2_bb import C, A, P, SEATS, T, place
RULE = 'frontier'


def season(timing, pols, B, rng, arng):
    A.judge = C.JUDGE
    st = A.new_state(); out = dict(ash=0)
    att = {n: 0 for n in SEATS}; released = set(); lost = {n: 0 for n in SEATS}
    left = {n: B for n in SEATS}; hleft = {h: B for h in A.HOUSE}
    houses = [A.xy(s) for s in A.HOUSE.values()]
    for t in range(1, T + 1):
        mv = {}
        for h in A.HOUSE:
            if hleft[h] > 0: hleft[h] -= 1
            else: mv[h] = {'seq': None, 'cells': [], 'superseded': []}
        for n, p in zip(SEATS, P):
            u, v = arng.random(), arng.random()  # two draws per seat per tick, always: arng stays in step across rows
            if u >= p: continue  # attendance
            att[n] += 1
            if left[n] <= 0: continue
            if timing[n] == 'late' and n not in released:
                if p * (T - t + 1) > left[n]: continue
                released.add(n)
            if not A.owned(st, n):
                ok = [A.cell(c, r) for c in range(A.N) for r in range(A.N)
                      if st['grid'].get(A.cell(c, r)) is None and all(abs(c - hc) + abs(r - hr) >= 3 for hc, hr in houses)]
                ok = ok or [A.cell(c, r) for c in range(A.N) for r in range(A.N) if st['grid'].get(A.cell(c, r)) is None]
                if not ok: continue
                cells = [ok[int(v * len(ok))]]
            else:
                cells = place(st, n, pols[n], rng)
            if cells:
                mv[n] = {'seq': 0, 'cells': cells, 'superseded': []}; left[n] -= 1
        rows = A.resolve(st, mv)
        for r in rows:
            if r['result'] == 'collision' and r['name'] in lost: lost[r['name']] += 1
        out['ash'] += len({r['pick'] for r in rows if r['result'] == 'collision'})
    sc = C.score(st, 'border')
    ps = {n: sc.get(n, 0) for n in SEATS}
    top = max(ps.values()); tops = [n for n in SEATS if ps[n] == top]
    out['tied_raw'] = float(len(tops) > 1)
    bord = {n: sum(C.foes(st, n, s) > 0 for s in A.owned(st, n)) for n in tops}
    front = {n: len({m for s in A.owned(st, n) for m in A.nbrs(s) if st['grid'].get(m) is None}) for n in tops}
    key = lambda n: (-lost[n], bord[n]) if RULE == 'frozen' else (-lost[n], bord[n], front[n])
    best = max(key(n) for n in tops); win = [n for n in tops if key(n) == best]
    out['tied'] = float(len(win) > 1); out['p1_strict'] = float(win == ['P1'])
    out['win'] = {n: (1 / len(win) if n in win else 0.0) for n in SEATS}; out['score'] = ps
    atop = max(att.values()); attenders = {n for n in SEATS if att[n] == atop}
    out['not_att'] = sum(n not in attenders for n in win) / len(win)
    out['house_first'] = float(max(sc[h] for h in A.HOUSE) > top)
    return out




ROWS = [('exp', 'P1', 'exp'), ('exp', 'P1', 'seek'), ('exp', 'P3', 'exp'), ('exp', 'P3', 'seek'), ('seek', 'P1', 'seek')]

if __name__ == '__main__':
    import s2_bb
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
    pos = [a for a in sys.argv[1:] if not a.startswith('--')]
    K = int(pos[0]) if pos else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2493
    RULE = opt.get('rule', 'frontier')
    s2_bb.season = season  # row() calls season() from its own module
    print(f'rule {RULE}  K={K}  seed {seed}  (early timing)')
    W = {}
    for field, focal, pol in ROWS:
        W[(field, focal, pol)] = np.array(s2_bb.row('early', focal, pol, 6, K, seed, field))
    for focal in ('P1', 'P3'):
        d = W[('exp', focal, 'seek')] - W[('exp', focal, 'exp')]
        print(f'    paired exp early {focal}: win(seek) - win(exp) = {d.mean():+.3f}±{d.std(ddof=1) / np.sqrt(K):.3f}', flush=True)
