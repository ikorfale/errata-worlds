"""Where do house raids come from? (board #95129, glitchfox: raids ~ 0.27 per expander, set by expander pathing)
Tie rule (raid needs >= 2 touches and >= the owner's; glitchfox's setting) and base rules, houses fixed, 0/1/2/4 expander seats on the published house claim order (exp_order), never raiding.
Per season: accepted raids (by houses / by seats), and 'contacts': cells an expander claimed that touch >= 2 house
cells at the moment of the claim (the cells a house can then raid). Same engine and seeds() as s2_choice.py.
Usage: python3 raid_attrib.py [seasons]"""
import sys, random
import numpy as np
import s2_choice as S
A = S.A

def season(k, rng, rule='tie', ticks=14):
    A.judge = S.judge_tie if rule == 'tie' else S.JUDGE
    names = ['P1', 'P2', 'P3', 'P4'][:k]
    st = A.new_state(); seed = {n: s for n, s in S.seeds(rng).items() if n in names}
    A.resolve(st, {n: {'seq': 0, 'cells': [s], 'superseded': []} for n, s in seed.items()})
    raids_h = raids_p = contacts = 0; born = {}; ages = []
    for t in range(2, ticks + 1):
        moves = {n: {'seq': 0, 'cells': S.policy(st, n, 'exp', rng), 'superseded': []} for n in names}
        before = dict(st['grid']); rows = A.resolve(st, moves)
        for r in rows:
            if r['result'] != 'accepted': continue
            if r['kind'] == 'raid':
                if r['name'] in A.HOUSE:
                    raids_h += 1; b = born.get(r['pick']); ages.append((t - b[0], b[1]) if b else (None, None))
                else: raids_p += 1
            elif r['name'] in names:
                ht = sum(A.touch({'grid': before}, h, r['pick']) for h in A.HOUSE)
                born[r['pick']] = (t, ht); contacts += ht >= 2
    AGES.extend(ages)
    return raids_h, raids_p, contacts

AGES = []

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    rng = random.Random(95129)
    for rule in ('tie',):
     print(rule)
     print(f"{'seats':>5} {'house raids':>12} {'seat raids':>10} {'contacts':>9} {'raids/contact':>13}   (K={K})")
     for k in (0, 1, 2, 4):
        AGES.clear()
        R = np.array([season(k, rng, rule) for _ in range(K)], float)
        m = R.mean(0); se = R.std(0, ddof=1) / np.sqrt(K)
        print(f"{k:5d} {m[0]:7.2f}±{se[0]:.2f} {m[1]:10.2f} {m[2]:5.2f}±{se[2]:.2f} {(m[0] / m[2] if m[2] else float('nan')):13.2f}", flush=True)
        from collections import Counter
        print('raided cell: (ticks since the seat claimed it, house neighbours when claimed) ->', sorted(Counter(AGES).items(), key=lambda x: -x[1])[:10])
