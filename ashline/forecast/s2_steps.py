"""Season 2 rules against a strategic play the policy-blind runs never tried: an open pact of two seats.
Question (25.10, before the season-2 launch): under border scoring a cell touching another player's cell scores 2,
so two seats that agree to sit side by side can each reach 2 x 6 = 12 with 6 moves while a lone expander gets 6.
How much does a pact pay, and what does it do to everyone else?

Field and resolver are s2_frontier.py's (six seats at season 1's attendance p = 1.00 .. 0.08, houses on the
published rule with budget 6, B=6, 12x12, 14 ticks, early timing, tie rule ash -> border -> frontier).
Pact policy (both members, coordinated as two agents agreeing in public would be):
  - seeding: the first member seeds at random (as everyone does); the second seeds on an empty cell touching the
    first's cells (same tick: next to the cell the first is seeding);
  - after that: claim the valid empty cell touching the partner, most own neighbours first; the second member skips
    the cell the first picks this tick (no collisions inside the pact); with no such cell, the claim closest to the
    partner (Manhattan), then the exp order.
Rows (same seeds for every row, common random numbers): pair (P1,P2) or (P3,P4) plays pact, everyone else exp;
the paired difference against the all-exp row is the value of the pact.
Usage: python3 s2_pact.py [K] [seed] [--field=exp,seek]

s2_steps.py (copy, 25.10, zenith 102974): which step decides each season (score alone, ash, border, frontier, or a shared
win), and fields with several pacts at once (PARTNER map instead of one PAIR). With one pair it must reproduce
s2_pact.py's rows exactly (checked on the printed win shares).
Usage: python3 s2_steps.py [K] [seed]"""
import sys, random, hashlib
import numpy as np
from s2_bb import C, A, P, SEATS, T
import s2_frontier as F

PAIR = ()
PARTNER = {}
FARM_T = 7       # a farmer makes no move before this tick (houses stop after tick 6)
NOHOUSE = False  # candidate fix (Fable 25.10): houses are not foes for border score or tie key


def _foes(st, name, s):
    return sum(st['grid'].get(m) not in (None, '#', name) and not (NOHOUSE and m_owner_house(st, m)) for m in A.nbrs(s))
def m_owner_house(st, m): return st['grid'].get(m) in A.HOUSE
C.foes = _foes  # C.score and the seek policy call it through the module


def farm_pick(st, n):
    """House farmer: seed or claim on an empty cell touching a house cell, most own neighbours first."""
    v = [s for s, k in C.valid(st, n) if k in ('claim', 'seed')]
    h = lambda s: hashlib.sha256(f"{st['tick']}|{n}|{s}".encode()).hexdigest()
    hc = [s for s in v if any(st['grid'].get(x) in A.HOUSE for x in A.nbrs(s))]
    if hc: return [max(hc, key=lambda s: (A.touch(st, n, s), h(s)))]
    return C.exp_order(st, n, [(s, 'claim') for s in v])[:1] if A.owned(st, n) else []


def partner_cells(st, n):
    m = PARTNER[n]
    return m, A.owned(st, m)


def pact_pick(st, n, avoid=()):
    m, pc = partner_cells(st, n)
    v = [s for s, k in C.valid(st, n) if k in ('claim', 'seed') and s not in avoid]
    if not v: return []
    h = lambda s: hashlib.sha256(f"{st['tick']}|{n}|{s}".encode()).hexdigest()
    touch_m = [s for s in v if any(st['grid'].get(x) == m for x in A.nbrs(s))]
    if touch_m:
        return [max(touch_m, key=lambda s: (A.touch(st, n, s), h(s)))]
    if pc:
        d = lambda s: min(abs(A.xy(s)[0] - A.xy(q)[0]) + abs(A.xy(s)[1] - A.xy(q)[1]) for q in pc)
        return [min(v, key=lambda s: (d(s), h(s)))]
    return C.exp_order(st, n, [(s, 'claim') for s in v])[:1]


def season(timing, pols, B, rng, arng):
    """s2_frontier.season with the pact members' moves made jointly; every draw is taken in the same order."""
    A.judge = C.JUDGE
    st = A.new_state(); out = dict(ash=0)
    att = {n: 0 for n in SEATS}; lost = {n: 0 for n in SEATS}
    left = {n: B for n in SEATS}; hleft = {h: B for h in A.HOUSE}
    houses = [A.xy(s) for s in A.HOUSE.values()]
    for t in range(1, T + 1):
        mv = {}
        for h in A.HOUSE:
            if hleft[h] > 0: hleft[h] -= 1
            else: mv[h] = {'seq': None, 'cells': [], 'superseded': []}
        here = {}
        for n, p in zip(SEATS, P):
            u, v = arng.random(), arng.random()
            here[n] = (u < p, v)
        for n in SEATS:
            ok_here, v = here[n]
            if not ok_here: continue
            att[n] += 1
            if left[n] <= 0: continue
            pact = pols[n] == 'pact'
            if pols[n] == 'farm':
                if t < FARM_T: continue
                cells = farm_pick(st, n)  # no house cell yet (tick 1) or none free: the farmer waits (Fable 25.10)
            elif not A.owned(st, n):
                m = PARTNER[n] if pact else None
                anchor = (A.owned(st, m) or (mv[m]['cells'][:1] if m in mv and not A.owned(st, m) else [])) if pact else []
                if anchor:
                    ok = [x for a in anchor for x in A.nbrs(a) if st['grid'].get(x) is None and x not in anchor
                          and x not in mv.get(m, {}).get('cells', ())]  # not the partner's claim this tick (Fable 25.10)
                    cells = sorted(set(ok))[:1] if ok else []
                else:
                    ok = [A.cell(c, r) for c in range(A.N) for r in range(A.N)
                          if st['grid'].get(A.cell(c, r)) is None and all(abs(c - hc) + abs(r - hr) >= 3 for hc, hr in houses)]
                    ok = ok or [A.cell(c, r) for c in range(A.N) for r in range(A.N) if st['grid'].get(A.cell(c, r)) is None]
                    if not ok: continue
                    cells = [ok[int(v * len(ok))]]
            elif pact:
                m = PARTNER[n]
                avoid = mv[m]['cells'] if m in mv else ()
                cells = pact_pick(st, n, avoid)
            else:
                cells = F.place(st, n, pols[n], rng)
            if cells:
                mv[n] = {'seq': 0, 'cells': cells, 'superseded': []}; left[n] -= 1
        rows = A.resolve(st, mv)
        for r in rows:
            if r['result'] == 'collision' and r['name'] in lost: lost[r['name']] += 1
        out['ash'] += len({r['pick'] for r in rows if r['result'] == 'collision'})
    sc = C.score(st, 'border')
    ps = {n: sc.get(n, 0) for n in SEATS}
    top = max(ps.values()); tops = [n for n in SEATS if ps[n] == top]
    bord = {n: sum(C.foes(st, n, s) > 0 for s in A.owned(st, n)) for n in tops}
    front = {n: len({m for s in A.owned(st, n) for m in A.nbrs(s) if st['grid'].get(m) is None}) for n in tops}
    key = lambda n: (-lost[n], bord[n], front[n])
    best = max(key(n) for n in tops); win = [n for n in tops if key(n) == best]
    out['tied'] = float(len(win) > 1)
    if len(tops) == 1: step = 'score'
    elif len(win) > 1: step = 'shared'
    else:
        step = 'frontier'
        for i, nm in enumerate(('ash', 'border')):
            b = max(key(n)[:i + 1] for n in tops)
            if sum(key(n)[:i + 1] == b for n in tops) == 1: step = nm; break
    out['step'] = step
    out['win'] = {n: (1 / len(win) if n in win else 0.0) for n in SEATS}; out['score'] = ps
    out['pact_shared'] = float(bool(PARTNER) and len(win) == 2 and PARTNER.get(win[0]) == win[1])
    return out


def row(pairs, field, K, seed, farm=None):
    global PARTNER
    PARTNER = {a: b for x, y in pairs for a, b in ((x, y), (y, x))}
    pols = {n: ('pact' if n in PARTNER else 'farm' if n == farm else field) for n in SEATS}
    timing = {n: 'early' for n in SEATS}
    R = [season(timing, pols, 6, random.Random(seed * 100003 + k), random.Random(seed * 100003 + k + 7919 * 10**6)) for k in range(K)]
    W = np.array([[o['win'][n] for n in SEATS] for o in R])
    st = {k: np.mean([o['step'] == k for o in R]) for k in ('score', 'ash', 'border', 'frontier', 'shared')}
    lab = ' '.join('+'.join(p) for p in pairs) or '-'
    print(f"{'nohouse' if NOHOUSE else 'rules  '} field {field:4} pacts {lab:17} win " + ' '.join(f'{n} {W[:, i].mean():.3f}' for i, n in enumerate(SEATS)) +
          '  decided by: ' + ' '.join(f'{k} {v:.3f}' for k, v in st.items()) + f'  pact-shares-win {np.mean([o["pact_shared"] for o in R]):.3f}  (K={K})', flush=True)


if __name__ == '__main__':
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--'))
    pos = [a for a in sys.argv[1:] if not a.startswith('--')]
    K = int(pos[0]) if pos else 500
    seed = int(pos[1]) if len(pos) > 1 else 2510
    NOHOUSE = opt.get('nohouse', '1') == '1'
    for field in opt.get('field', 'exp').split(','):
        for pairs in ((), (('P1', 'P2'),), (('P3', 'P4'),), (('P1', 'P2'), ('P3', 'P4')), (('P1', 'P2'), ('P3', 'P4'), ('P5', 'P6'))):
            row(pairs, field, K, seed)
