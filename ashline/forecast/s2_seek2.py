"""#382: a smarter border seeker. 'seek' (s2_choice.py) claims the empty cell touching the most other-player cells;
every such cell also touches its own territory, so the bordering foe sees it as a seek cell too and the two collide
into ash (border act4: ash 4.83, seeker-seeker ash 4.18 per season in s2_choice.txt).
'seek2': drop candidates that are in the argmax set of any bordering foe's seek candidates (assuming every foe seeks);
claim the best remaining one; if none remains, play the house-rule claim order (exp).
Rerun of the border rule with the same harness, seeds and seasons as s2_choice.py, seek vs seek2.
Usage: python3 s2_seek2.py [seasons]"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s2_choice as S
A = S.A

def seek_best(st, name, v=None):
    v = S.valid(st, name) if v is None else v
    cl = [s for s, k in v if k == 'claim' and S.foes(st, name, s) > 0]
    if not cl: return set(), cl
    m = max(S.foes(st, name, s) for s in cl)
    return {s for s in cl if S.foes(st, name, s) == m}, cl

_policy = S.policy
def policy(st, name, pol, rng):
    if pol != 'seek2': return _policy(st, name, 'seek' if pol == 'seek1' else pol, rng)
    v = S.valid(st, name)
    _, cl = seek_best(st, name, v)
    if cl:
        rivals = {st['grid'].get(m) for s in cl for m in A.nbrs(s)} - {None, '#', name}
        wanted = set().union(*(seek_best(st, f)[0] for f in rivals if f in st['players'])) if rivals else set()
        free = [s for s in cl if s not in wanted]
        if free:
            m = max(S.foes(st, name, s) for s in free)
            return [rng.choice([s for s in free if S.foes(st, name, s) == m])]
    return S.exp_order(st, name, v)
S.policy = policy

def run(act, mix, K, seed=94537):
    rng = random.Random(seed); R = []; diffs = []
    for _ in range(K):
        if mix == 'coin': pols = {n: (act if rng.random() < 0.5 else 'exp') for n in ('P1', 'P2', 'P3', 'P4')}
        else:
            k = {'act2': 2, 'act4': 4}[mix]; pols = {n: (act if i < k else 'exp') for i, n in enumerate(('P1', 'P2', 'P3', 'P4'))}
        o = S.season('border', pols, rng); R.append(o)
        a = [o['score'][n] for n in pols if pols[n] == act]; e = [o['score'][n] for n in pols if pols[n] == 'exp']
        if a and e: diffs.append(sum(a) / len(a) - sum(e) / len(e))
    import numpy as np
    m = lambda key: np.mean([o[key] for o in R])
    pay = (np.mean(diffs), np.std(diffs, ddof=1) / np.sqrt(len(diffs))) if len(diffs) > 1 else (float('nan'), 0)
    act_sc = np.mean([o['score'][n] for o in R for n in o['pols'] if o['pols'][n] == act])
    return f"{act:6} {mix:5} raids {m('raids'):5.2f} ash {m('ash'):5.2f} ash-aa {m('ash_aa'):5.2f} house-win {m('house_win'):4.0%} act-score {act_sc:5.2f} act-exp {pay[0]:+.2f}±{pay[1]:.2f}"

if __name__ == '__main__':
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    print(f"border rule, 12x12, 14 ticks, K={K} seasons per row, seed 94537 per row (paired across policies)")
    for mix in ('act2', 'act4', 'coin'):
        for act in ('seek1', 'seek2'):
            print(run(act, mix, K), flush=True)
