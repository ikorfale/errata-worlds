"""Season 2: does a seat that plays for the frontier tie step change who wins and which step decides? (zenith 102974)
s2_steps.py showed frontier settles ~37% of seasons with policies that do not know the tie rule. Here a seat plays
'front': each claim is the valid empty cell that leaves it the most open frontier (distinct empty cells orthogonally next
to its own cells, the tie_key definition), ties broken by the exp key (most own neighbours, fewest foes, hash).
Seeding is unchanged. Field, seeds and resolver are s2_steps.py's (houses not foes, K=1000, seed 2510).
Rows: all exp (baseline), P1 front, P2 front, P3 front, everyone front. Paired difference of the seat's win share.
Usage: python3 s2_front.py [K] [seed]"""
import sys, hashlib
import numpy as np
import s2_steps as S
from s2_steps import C, A, SEATS
import s2_frontier as F

_place = F.place


def frontier(st, n, extra=None):
    mine = A.owned(st, n) + ([extra] if extra else [])
    return len({m for s in mine for m in A.nbrs(s) if st['grid'].get(m) is None and m != extra})


def front_pick(st, n):
    v = [s for s, k in C.valid(st, n) if k in ('claim', 'seed')]
    if not v: return []
    h = lambda s: hashlib.sha256(f"{st['tick']}|{n}|{s}".encode()).hexdigest()
    return [max(v, key=lambda s: (frontier(st, n, s), A.touch(st, n, s), -C.foes(st, n, s), h(s)))]


def place(st, n, pol, rng):
    return front_pick(st, n) if pol == 'front' else _place(st, n, pol, rng)
F.place = place


def run(fronts, K, seed):
    S.PARTNER = {}
    pols = {n: ('front' if n in fronts else 'exp') for n in SEATS}
    import random
    R = [S.season({n: 'early' for n in SEATS}, pols, 6, random.Random(seed * 100003 + k), random.Random(seed * 100003 + k + 7919 * 10**6)) for k in range(K)]
    W = np.array([[o['win'][n] for n in SEATS] for o in R])
    st = {k: np.mean([o['step'] == k for o in R]) for k in ('score', 'ash', 'border', 'frontier', 'shared')}
    sc = np.array([[o['score'][n] for n in SEATS] for o in R]).mean(0)
    print(f"front {','.join(fronts) or '-':17} win " + ' '.join(f'{n} {W[:, i].mean():.3f}' for i, n in enumerate(SEATS)) +
          '  score ' + ' '.join(f'{x:.1f}' for x in sc) + '  decided by: ' + ' '.join(f'{k} {v:.3f}' for k, v in st.items()) + f'  (K={K})', flush=True)
    return W


if __name__ == '__main__':
    pos = sys.argv[1:]
    K = int(pos[0]) if pos else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2510
    S.NOHOUSE = True
    base = run((), K, seed)
    for f in (('P1',), ('P2',), ('P3',)):
        W = run(f, K, seed); i = SEATS.index(f[0]); d = W[:, i] - base[:, i]
        print(f'    paired {f[0]} front - exp = {d.mean():+.3f}±{d.std(ddof=1) / np.sqrt(K):.3f}', flush=True)
    run(tuple(SEATS), K, seed)
