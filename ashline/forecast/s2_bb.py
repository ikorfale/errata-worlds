"""Season 2 candidate: budget + border scoring (plan #493; zenith 101532, 101556). Pre-registration: PREREG-bb.md.

Same field, budget and timing as s2_budget.py (six player seats at season 1's attendance p = 1.00, 0.92, 0.50, 0.42,
0.17, 0.08; houses on the published rule with the same budget; B=6; 12x12; 14 ticks; no expiry), border scoring
(a cell touching another player's cell scores 2). New:
  focal seat - one seat plays a different placement policy (exp, seek or seek2) while every other seat plays exp;
               rows for focal P1 and focal P3, each policy run on the same seeds (common random numbers), so the
               paired difference in the focal seat's win share is the value of the choice.
  tie rule   - fixed before the run (zenith 101556: no timing-based tie-break). Among seats tied on score:
               1) fewest own submitted moves that turned to ash, 2) most cells touching another player;
               a tie that survives both is a shared win (reported as shared, never as nobody winning).
Per row, K seasons:
  raw tied top, tied top after the tie rule, P1 strictly first (after the tie rule), house strictly first,
  not-top-attender (ties split, after the tie rule), focal seat win share (shared wins split), focal mean score, ash.
  field      - what every non-focal seat plays: exp (season 1's play) or seek (if seek pays, players will copy it).
Usage: python3 s2_bb.py [K] [seed] [--field=exp,seek] [--mix=early,late] [--focal=P1,P3] [--pol=exp,seek,seek2]"""
import sys, random
import numpy as np
import s2_choice as C
import s2_seek2 as S2
import ashline as A

P = [1.00, 0.92, 0.50, 0.42, 0.17, 0.08]
SEATS = [f'P{i + 1}' for i in range(len(P))]
T = 14


def place(st, n, pol, rng):
    if pol == 'exp': return C.policy(st, n, 'exp', rng)
    if pol == 'seek': return C.policy(st, n, 'seek', rng)
    return S2.policy(st, n, 'seek2', rng)


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
    key = lambda n: (-lost[n], bord[n])
    best = max(key(n) for n in tops); win = [n for n in tops if key(n) == best]
    out['tied'] = float(len(win) > 1); out['p1_strict'] = float(win == ['P1'])
    out['win'] = {n: (1 / len(win) if n in win else 0.0) for n in SEATS}; out['score'] = ps
    atop = max(att.values()); attenders = {n for n in SEATS if att[n] == atop}
    out['not_att'] = sum(n not in attenders for n in win) / len(win)
    out['house_first'] = float(max(sc[h] for h in A.HOUSE) > top)
    return out


def row(mix, focal, pol, B, K, seed, field='exp'):
    timing = {n: mix for n in SEATS}
    pols = {n: (pol if n == focal else field) for n in SEATS}
    R = [season(timing, pols, B, random.Random(seed * 100003 + k), random.Random(seed * 100003 + k + 7919 * 10**6)) for k in range(K)]
    # season k: same attendance and seeding draws in every row (arng); placement rng starts equal and may diverge once play differs
    f = lambda xs: (np.mean(xs), np.std(xs, ddof=1) / np.sqrt(K))
    g = lambda k: f([o[k] for o in R])
    fw = [o['win'][focal] for o in R]
    print(f'{mix:5} field {field:5} focal {focal} {pol:5}  tied raw {g("tied_raw")[0]:.3f}  tied after rule {g("tied")[0]:.3f}±{g("tied")[1]:.3f}  '
          f'P1 strictly first {g("p1_strict")[0]:.3f}±{g("p1_strict")[1]:.3f}  not-top-attender {g("not_att")[0]:.3f}  '
          f'house first {g("house_first")[0]:.3f}  focal win {f(fw)[0]:.3f}±{f(fw)[1]:.3f}  '
          f'focal score {f([o["score"][focal] for o in R])[0]:.2f}  ash {g("ash")[0]:.2f}  (K={K})', flush=True)
    return fw


if __name__ == '__main__':
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
    pos = [a for a in sys.argv[1:] if not a.startswith('--')]
    K = int(pos[0]) if pos else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2493
    pl = opt.get('pol', 'exp,seek,seek2').split(',')
    for field in opt.get('field', 'exp,seek').split(','):
      for mix in opt.get('mix', 'early,late').split(','):
        for focal in opt.get('focal', 'P1,P3').split(','):
            W = {p: np.array(row(mix, focal, p, 6, K, seed, field)) for p in pl}
            for p in pl[1:]:
                d = W[p] - W[pl[0]]
                print(f'    paired {field} {mix} {focal}: win({p}) - win({pl[0]}) = {d.mean():+.3f}±{d.std(ddof=1) / np.sqrt(K):.3f}', flush=True)
