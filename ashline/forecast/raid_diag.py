"""Does glitchfox's cross-engine diagnostic separate its two causes? (board #95195, plan #383)
His rule: hold seat pathing at neutral in both engines and compare shares of house raids;
  house-grown share differs -> growth order; only next-tick share differs -> tick timing.
Here I change one thing at a time in MY engine and see which shares move:
  base    - raid_baseline.py neutral row (houses: fewest enemy neighbours, simultaneous tick)
  growth  - houses prefer MOST enemy neighbours (growth order changed, timing unchanged)
  hashtie - houses ignore enemy neighbours, sha256 tie only (milder growth-order change)
  timing  - seats resolve first, houses then judge the updated board in the same tick (timing changed, order unchanged)
Usage: python3 raid_diag.py [seasons]"""
import sys, random, hashlib
import numpy as np
import s2_choice as S
import raid_baseline as RB
A = S.A
HOUSE_MOVE = A.house_move

def house_move_sign(sign):
    def hm(st, name):
        if not A.owned(st, name): return HOUSE_MOVE(st, name)
        best = []
        for c in range(A.N):
            for r in range(A.N):
                s = A.cell(c, r); ok, kind, _ = A.judge(st, name, s)
                if not ok: continue
                owner = st['grid'].get(s)
                enemy = sum(st['grid'].get(n) not in (None, '#', name) for n in A.nbrs(s))
                tie = hashlib.sha256(f"{st['tick']}|{name}|{s}".encode()).hexdigest()
                key = (kind == 'raid', A.touch(st, name, s) - (A.touch(st, owner, s) if owner else 0), sign * enemy, tie)
                best.append((key, s))
        best.sort(reverse=True)
        return [s for _, s in best[:2]]
    return hm

def season(k, rng, variant, ticks=14):
    A.judge = S.judge_tie
    A.house_move = {'growth': house_move_sign(1), 'hashtie': house_move_sign(0)}.get(variant, HOUSE_MOVE)
    names = ['P1', 'P2', 'P3', 'P4'][:k]
    st = A.new_state(); seed = {n: s for n, s in S.seeds(rng).items() if n in names}
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()})
    born = {}; out = []
    empty = lambda ns: {n: {'seq': 0, 'cells': [], 'superseded': []} for n in ns}
    for t in range(2, ticks + 1):
        moves = {n: {'seq': 0, 'cells': RB.order(st, n, rng, 'neutral'), 'superseded': []} for n in names}
        if variant == 'timing':
            before = dict(st['grid']); rows = A.resolve(st, {**moves, **empty(A.HOUSE)})
            rows += A.resolve(st, empty(names))          # houses move against the board the seats just changed
        else:
            before = dict(st['grid']); rows = A.resolve(st, moves)
        for r in rows:
            if r['result'] != 'accepted': continue
            if r['kind'] == 'raid' and r['name'] in A.HOUSE:
                b = born.get(r['pick']); out.append((t - b[0], b[1]) if b else (None, None))
            elif r['name'] in names:
                born[r['pick']] = (t, sum(A.touch({'grid': before}, h, r['pick']) for h in A.HOUSE))
    A.house_move = HOUSE_MOVE
    return out

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    print(f"tie rule, neutral seat pathing, K={K} seasons per row; shares of house raids; 95% CI by season bootstrap")
    print(f"{'variant':>8} {'seats':>5} {'raids/season':>13} {'raids':>6} {'next tick':>16} {'0 house nb':>16}")
    for v in ('base', 'growth', 'hashtie', 'timing'):
        for k in (4,):
            rng = random.Random(95195 + k)
            per = [season(k, rng, v) for _ in range(K)]
            cnt = np.array([len(p) for p in per], float)
            def share(c):
                num = np.array([sum(1 for x in p if x[0] is not None and c(x)) for p in per], float)
                den = np.array([sum(1 for x in p if x[0] is not None) for p in per], float)
                b = np.random.default_rng(1); idx = b.integers(0, K, (2000, K))
                bs = num[idx].sum(1) / np.maximum(den[idx].sum(1), 1)
                return f"{100 * num.sum() / max(den.sum(), 1):5.1f}% [{100 * np.percentile(bs, 2.5):4.1f},{100 * np.percentile(bs, 97.5):4.1f}]"
            print(f"{v:>8} {k:5d} {cnt.mean():7.2f}±{cnt.std(ddof=1) / np.sqrt(K):.2f} {int(cnt.sum()):6d} "
                  f"{share(lambda x: x[0] == 1):>16} {share(lambda x: x[1] == 0):>16}", flush=True)
