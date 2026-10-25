"""Season 2: front against a pact (zenith 103045). A pact pair grows side by side and fills in rather than spreads;
a 'front' seat plays for the open-frontier tie key (s2_front.py). If front beats a pact at no score cost, the pact
is worth less once the tie rule is known, and the #102971 reading of what pacts are worth changes.
Field, seeds, resolver, houses-not-foes: s2_steps.py (K=1000, seed 2510, common random numbers in every row).
Rows: A all exp | B pact P1+P2 | C P3 front | D pact P1+P2 and P3 front | E pact P3+P4 | F P1 front | G pact P3+P4 and P1 front.
Pact value, rule unknown = B-A; rule known (a front seat in the field) = D-C (pair share). Front vs pact = D-B (front seat).
Usage: python3 s2_front_pact.py [K] [seed]"""
import sys, random
import numpy as np
import s2_steps as S
from s2_steps import SEATS
import s2_front  # noqa: F401  patches s2_frontier.place with the 'front' policy


def run(label, pairs, fronts, K, seed):
    S.PARTNER = {a: b for x, y in pairs for a, b in ((x, y), (y, x))}
    pols = {n: ('pact' if n in S.PARTNER else 'front' if n in fronts else 'exp') for n in SEATS}
    R = [S.season({n: 'early' for n in SEATS}, pols, 6, random.Random(seed * 100003 + k), random.Random(seed * 100003 + k + 7919 * 10**6)) for k in range(K)]
    W = np.array([[o['win'][n] for n in SEATS] for o in R]); Sc = np.array([[o['score'][n] for n in SEATS] for o in R])
    st = {k: np.mean([o['step'] == k for o in R]) for k in ('score', 'ash', 'border', 'frontier', 'shared')}
    print(f"{label} pact {'+'.join(p for x in pairs for p in x) or '-':5} front {','.join(fronts) or '-':3} win " + ' '.join(f'{n} {W[:, i].mean():.3f}' for i, n in enumerate(SEATS)) +
          '  score ' + ' '.join(f'{x:.1f}' for x in Sc.mean(0)) + '  decided: ' + ' '.join(f'{k} {v:.3f}' for k, v in st.items()), flush=True)
    return W, Sc


def paired(txt, a, b, idx, K):
    d = a[:, idx].sum(1) - b[:, idx].sum(1)
    print(f'    {txt} = {d.mean():+.3f}±{d.std(ddof=1) / np.sqrt(K):.3f}', flush=True)


if __name__ == '__main__':
    pos = sys.argv[1:]
    K = int(pos[0]) if pos else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2510
    S.NOHOUSE = True
    i = {n: SEATS.index(n) for n in SEATS}
    A = run('A', (), (), K, seed)
    for pair, f in ((('P1', 'P2'), 'P3'), (('P3', 'P4'), 'P1')):
        B = run('B', (pair,), (), K, seed); C = run('C', (), (f,), K, seed); D = run('D', (pair,), (f,), K, seed)
        pi = [i[n] for n in pair]
        paired(f'{"+".join(pair)} pact value, no front seat (B-A), win share', B[0], A[0], pi, K)
        paired(f'{"+".join(pair)} pact value, {f} plays front (D-C), win share', D[0], C[0], pi, K)
        paired(f'{f} front value, no pact (C-A), win share', C[0], A[0], [i[f]], K)
        paired(f'{f} front value against the pact (D-B), win share', D[0], B[0], [i[f]], K)
        paired(f'{f} score cost of front against the pact (D-B), points', D[1], B[1], [i[f]], K)
