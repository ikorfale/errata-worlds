"""Neutral-pathing baseline for house raids (plan #383, board #95160/#95170, glitchfox v_ashraid_claim.py).
Three expander pathings, never raiding, tie rule, houses fixed, 1/2/4 seats, same engine and seeds() as s2_choice.py:
  avert   - the published house claim order: most own neighbours, FEWEST enemy neighbours, hash (raid_attrib.py)
  neutral - most own neighbours, enemy neighbours ignored, rng tie-break
  toward  - most own neighbours, MOST enemy neighbours, rng tie-break (hugs others, glitchfox-like)
Per raided cell: ticks between the seat's claim and the raid, and house neighbours at the moment of the claim.
Shares reported: next tick, claimed with 0 house neighbours (the house grew into it), claimed with >= 2.
Usage: python3 raid_baseline.py [seasons]"""
import sys, random, hashlib
import numpy as np
import s2_choice as S
A = S.A

def order(st, name, rng, mode):
    cl = [s for s, k in S.valid(st, name) if k in ('claim', 'seed')]
    sign = {'neutral': 0, 'toward': 1}[mode]
    key = lambda s: (A.touch(st, name, s), sign * S.foes(st, name, s), rng.random())
    return sorted(cl, key=key, reverse=True)[:2]

def season(k, rng, mode, ticks=14):
    A.judge = S.judge_tie
    names = ['P1', 'P2', 'P3', 'P4'][:k]
    st = A.new_state(); seed = {n: s for n, s in S.seeds(rng).items() if n in names}
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()})
    born = {}; out = []
    for t in range(2, ticks + 1):
        pick = (lambda n: S.policy(st, n, 'exp', rng)) if mode == 'avert' else (lambda n: order(st, n, rng, mode))
        moves = {n: {'seq': 0, 'cells': pick(n), 'superseded': []} for n in names}
        before = dict(st['grid']); rows = A.resolve(st, moves)
        for r in rows:
            if r['result'] != 'accepted': continue
            if r['kind'] == 'raid' and r['name'] in A.HOUSE:
                b = born.get(r['pick']); out.append((t - b[0], b[1]) if b else (None, None))
            elif r['name'] in names:
                born[r['pick']] = (t, sum(A.touch({'grid': before}, h, r['pick']) for h in A.HOUSE))
    return out

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    print(f"tie rule, K={K} seasons per row; shares of house raids (raided cell attributed to the seat claim it took over)")
    print(f"{'pathing':>8} {'seats':>5} {'raids/season':>13} {'raids':>6} {'next tick':>9} {'0 house nb':>10} {'>=2 house nb':>12}")
    for mode in ('avert', 'neutral', 'toward'):
        for k in (1, 2, 4):
            rng = random.Random(95170 + k)
            per = [season(k, rng, mode) for _ in range(K)]
            R = [x for p in per for x in p if x[0] is not None]; n = len(R)
            cnt = np.array([len(p) for p in per], float)
            f = lambda c: f"{100 * sum(map(c, R)) / n:5.1f}%" if n else '   -'
            print(f"{mode:>8} {k:5d} {cnt.mean():7.2f}±{cnt.std(ddof=1) / np.sqrt(K):.2f} {n:6d} {f(lambda x: x[0] == 1):>9} "
                  f"{f(lambda x: x[1] == 0):>10} {f(lambda x: x[1] >= 2):>12}", flush=True)
