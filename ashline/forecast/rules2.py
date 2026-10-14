"""Season 2 rule candidates (board #86225, plan #272). Does contact pay under a changed rule? Same harness as
who_gains.py: mixed seats (coin flip between house rule and contact-seeking), turnout 0.3-1.0; c = what
contact-seeking is worth at equal attendance, in cells and in margin over the best rival. A rule qualifies for
season 2 only if c >= 0 on margin.
Variants (resolver otherwise unchanged):
  base     - season 1 rules
  border2  - zenith: an empty cell touching cells of two or more other owners cannot be taken by a plain claim
  border1  - stricter: an empty cell touching any other owner cannot be taken by a plain claim
  cutoff   - after the tick, cells of a raided owner that are no longer connected to that owner's largest
             component and touch the raided cell go to the raider
  both     - border2 + cutoff
Usage: python3 rules2.py [variant ...]"""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, who_gains as W

JUDGE, RESOLVE = A.judge, A.resolve

def judge_border(k):
    def j(st, name, s):
        ok, kind, reason = JUDGE(st, name, s)
        if ok and kind == 'claim':
            others = {st['grid'].get(m) for m in A.nbrs(s)} - {None, '#', name}
            if len(others) >= k: return False, None, f'{s} is a border cell'
        return ok, kind, reason
    return j

def comps(cells):
    cells, out = set(cells), []
    while cells:
        stack = [min(cells)]; cells.discard(stack[0]); c = set(stack)  # min(), not set.pop(): pop order follows PYTHONHASHSEED (#86304)
        while stack:
            for m in A.nbrs(stack.pop()):
                if m in cells: cells.discard(m); c.add(m); stack.append(m)
        out.append(c)
    return out

def resolve_cutoff(st, moves):
    before = dict(st['grid']); rows = RESOLVE(st, moves)
    for r in rows:
        if r['result'] == 'accepted' and r['kind'] == 'raid':
            s = r['pick']; victim = before[s]; cs = comps(A.owned(st, victim))
            if len(cs) < 2: continue
            main = max(cs, key=lambda c: (len(c), [-ord(ch) for ch in min(c)]))  # tie: the part holding the alphabetically first cell stays
            for c in cs:
                if c is not main and any(m in c for m in A.nbrs(s)):
                    for k in c: st['grid'][k] = r['name']
    if st['history']: st['history'][-1]['scores'] = A.scores(st)
    return rows

VARIANTS = {'base': (JUDGE, RESOLVE), 'border2': (judge_border(2), RESOLVE), 'border1': (judge_border(1), RESOLVE),
            'cutoff': (JUDGE, resolve_cutoff), 'both': (judge_border(2), resolve_cutoff)}

if __name__ == '__main__':
    for v in sys.argv[1:] or list(VARIANTS):
        A.judge, A.resolve = VARIANTS[v]
        rng = random.Random(272)
        for N, ticks in ((12, 14), (8, 20), (12, 45)):
            c, m, mc, mh, sc, sm = W.run(N, ticks, 400, rng)
            print(f"{v:8s} {N}x{N} {ticks:2d} ticks  contact worth {c:+.2f}±{sc:.2f} cells, {m:+.2f}±{sm:.2f} margin  (mean cells: contact {mc:.1f}, house {mh:.1f})", flush=True)
