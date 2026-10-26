"""Season 2: defection inside a pact (zenith 103064). A pact pair finishes level on score, so frontier mostly picks
between the two members; each has a reason to grow side by side and then spread out for frontier against its partner.
A defector plays its last k moves as 'front' (s2_front.py's pick: most open frontier), still skipping the cell its
partner claims this tick. "Last k moves", not "last k ticks": with budget 6 and early timing a full-attendance seat
spends its 6 moves on ticks 1-6, so the end of its season is its last moves, whatever the tick.
Field, seeds, resolver, houses-not-foes: s2_steps.py (K=1000, seed 2510, common random numbers in every row).
Per pair (P1+P2, P3+P4): no pact; pact; first member defects k=1,2,3; second member defects k=1,2,3; both defect k=1,2,3.
Reported: defector's win share and its gain over the honest pact, defector's share of the pair's wins, pair's joint
share, the pair's gain over no pact, and the defector's mean score (does spreading out cost border points?).
Two defect picks. raw: the most-frontier cell anywhere (s2_front.py's pick); a second model pointed out it mostly
takes open-side cells that touch nobody, so each raw defect move scores 1 instead of 2 and the defector falls off
the top score before the tie key is read. level: the most-frontier cell among those that still touch another player
(score 2), falling back to the pact pick when there is none: spreading out while staying level, zenith's intent.
Usage: python3 s2_defect.py [K] [seed]"""
import sys, random
import numpy as np
import s2_steps as S
from s2_steps import C, SEATS
import s2_front as F2

DEFECT = {}  # seat -> k: play the last k moves as front
MODE = 'raw'  # raw: most frontier anywhere; level: most frontier among cells that still score 2
_pact_pick = S.pact_pick


def pact_pick(st, n, avoid=(), left=None):
    if n in DEFECT and left is not None and left <= DEFECT[n]:
        v = [s for s, k in C.valid(st, n) if k in ('claim', 'seed') and s not in avoid]
        if MODE == 'level':  # stay level on score: only cells that still touch another player (score 2) (Fable 26.10)
            v = [s for s in v if C.foes(st, n, s) > 0]
            if not v: return _pact_pick(st, n, avoid, left)
        if not v: return []
        return [max(v, key=lambda s: (F2.frontier(st, n, s), S.A.touch(st, n, s), -C.foes(st, n, s),
                                      F2.hashlib.sha256(f"{st['tick']}|{n}|{s}".encode()).hexdigest()))]
    return _pact_pick(st, n, avoid, left)
S.pact_pick = pact_pick


def run(label, pair, defect, K, seed):
    S.PARTNER = {a: b for a, b in ((pair[0], pair[1]), (pair[1], pair[0]))} if pair else {}
    DEFECT.clear(); DEFECT.update(defect)
    pols = {n: ('pact' if n in S.PARTNER else 'exp') for n in SEATS}
    R = [S.season({n: 'early' for n in SEATS}, pols, 6, random.Random(seed * 100003 + k), random.Random(seed * 100003 + k + 7919 * 10**6)) for k in range(K)]
    W = np.array([[o['win'][n] for n in SEATS] for o in R]); Sc = np.array([[o['score'][n] for n in SEATS] for o in R])
    st = {k: np.mean([o['step'] == k for o in R]) for k in ('score', 'ash', 'border', 'frontier', 'shared')}
    print(f"{label:16} win " + ' '.join(f'{n} {W[:, i].mean():.3f}' for i, n in enumerate(SEATS)) +
          '  score ' + ' '.join(f'{x:.2f}' for x in Sc.mean(0)) + '  decided: ' + ' '.join(f'{k} {v:.3f}' for k, v in st.items()), flush=True)
    return W, Sc


def pd(a, b, idx, K):
    d = a[:, idx].sum(1) - b[:, idx].sum(1)
    return f'{d.mean():+.3f}±{d.std(ddof=1) / np.sqrt(K):.3f}'


if __name__ == '__main__':
    pos = sys.argv[1:]
    K = int(pos[0]) if pos else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2510
    S.NOHOUSE = True
    i = {n: SEATS.index(n) for n in SEATS}
    N = run('no pact', (), {}, K, seed)
    for pair in (('P1', 'P2'), ('P3', 'P4')):
        a, b = pair; pi = [i[a], i[b]]
        H = run(f'pact {a}+{b}', pair, {}, K, seed)
        print(f'    honest pact: pair gain over no pact {pd(H[0], N[0], pi, K)}', flush=True)
        for MODE, who, k in [(m, w, k) for m in ('raw', 'level') for w in ((a,), (b,), (a, b)) for k in (1, 2, 3)]:
            D = run(f'{MODE} {"+".join(who)} k={k}', pair, {w: k for w in who}, K, seed)
            pw = D[0][:, pi].sum(1).mean()
            line = f'    pair joint share {pw:.3f} (honest {H[0][:, pi].sum(1).mean():.3f}), pair gain over no pact {pd(D[0], N[0], pi, K)}'
            for w in who:
                line += (f'; {w}: share {D[0][:, i[w]].mean():.3f}, gain over honest {pd(D[0], H[0], [i[w]], K)},'
                         f' share of pair wins {D[0][:, i[w]].mean() / pw:.3f}, score {D[1][:, i[w]].mean():.2f} (honest {H[1][:, i[w]].mean():.2f})')
            print(line, flush=True)
