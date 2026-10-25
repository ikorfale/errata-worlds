"""Season 2 port check (plan #494, board 101655): the live engine (ashline.py with SEASON2 rules: budget, border
score, tie key) must name the same winners as the simulator s2_frontier.py on the same seasons.
Runs s2_frontier's season() with st['rules'] = SEASON2 switched on inside the live resolver, keeps each final board,
and compares per season: every seat's score (sim C.score border vs live points) and the winner set (sim tie key vs
live winners()). Also counts budget rejections the live resolver issued to seats (should be 0: the sim never
submits past the budget) and to houses (expected after tick 6, they change nothing).
Usage: python3 s2_live_check.py [K] [seed]"""
import sys, random
import s2_bb, s2_frontier as F
from s2_bb import A, SEATS

pos = [a for a in sys.argv[1:] if not a.startswith('--')]
K = int(pos[0]) if pos else 500
seed = int(pos[1]) if len(pos) > 1 else 2493
_new, _res = A.new_state, A.resolve
last = {}
def new_state():
    st = _new(); st['rules'] = dict(A.SEASON2); last['st'] = st; return st
A.new_state = new_state
F.RULE = 'frontier'
# 25.10: the live engine no longer counts houses as foes; the simulator gets the same rule here (s2_pact.py --nohouse=1)
if '--old-foes' not in sys.argv:
    C = s2_bb.C
    C.foes = lambda st, name, s: sum(st['grid'].get(m) not in (None, '#', name) and st['grid'].get(m) not in A.HOUSE for m in A.nbrs(s))
n = bad_score = bad_win = seat_budget = house_budget = shared = 0
for field in ('exp', 'seek'):
    for k in range(K):
        pols = {s: field for s in SEATS}; timing = {s: 'early' for s in SEATS}
        out = F.season(timing, pols, 6, random.Random(seed * 100003 + k), random.Random(seed * 100003 + k + 7919 * 10**6))
        st = last['st']; n += 1
        live = {s: A.points(st, s) for s in SEATS}
        bad_score += live != out['score']
        sim_win = sorted(s for s in SEATS if out['win'][s] > 0)
        lw = A.winners(st, SEATS)
        bad_win += lw != sim_win; shared += len(lw) > 1
        for h in st['history']:
            for r in h['rows']:
                if r['reason'].startswith('budget spent'):
                    if r['name'] in A.HOUSE: house_budget += 1
                    else: seat_budget += 1
print(f'seasons {n} (fields exp, seek; K={K} each; seed {seed})  score mismatches {bad_score}  winner mismatches {bad_win}  '
      f'shared wins {shared}  budget rejections: seats {seat_budget}, houses {house_budget}')
