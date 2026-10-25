"""Judge the three season-1 forecasts (README, pre-registered 12 Oct) from the public state after tick 14.
Run: python3 forecast/season1_verdict.py [state.json]. Refuses to judge before the last tick."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ashline as a

st = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'state.json'))
N = st['season_ticks']
assert st['tick'] == N, f"judge exactly at the last tick: state is at tick {st['tick']} of {N}"
rows = [dict(r, tick=t['tick']) for t in st['history'] if t['tick'] <= N for r in t['rows']]
sc = a.scores(st)
top = max(sc.values())
tops = sorted(p for p, v in sc.items() if v == top)
raids = sum(r['kind'] == 'raid' and r['result'] == 'accepted' for r in rows)
ash = len({(r['tick'], r['pick']) for r in rows if r['result'] == 'collision'})  # one collision = one cell, however many claimants
HOUSES = ('house-n', 'house-s')
house_best = max(sc[h] for h in HOUSES)
player_best = max(v for p, v in sc.items() if p not in HOUSES)
# Binding reading (thread post before tick 14): the one the 95% was computed with, sim.py line 52 in 8e15640
# (12 Oct, before tick 1): a house holds the top score and every player is below it; the houses may tie each other.
# The README words "strictly first" also allow a narrower reading (one house alone on top); printed, not scored.
narrow = sum(sc[h] == top for h in HOUSES) == 1 and len(tops) == 1
print(f'forecast 1, narrow reading (one house alone on top, not scored): {"YES" if narrow else "NO"}')
results = [
    ('A house bot finishes above every player (sim.py:52 reading)', 0.95, house_best > player_best),
    ('Accepted raids over the season <= 2', 0.80, raids <= 2),
    ('At least one collision (ash)', 0.30, ash >= 1),
]
print('final scores:', ', '.join(f'{p} {v}' for p, v in sorted(sc.items(), key=lambda x: -x[1])))
print(f'top {top}: {", ".join(tops)}; accepted raids {raids}; ash {ash}; rows {len(rows)}')
b = []
for q, p, y in results:
    b.append((p - y) ** 2)
    print(f'{q}: said {p:.2f}, outcome {"YES" if y else "NO"}, Brier {(p - y) ** 2:.4f}')
print(f'mean Brier {sum(b) / len(b):.4f}. Three events cannot show forecasting skill: this is a record of these forecasts, not a skill score; 0.25 is what saying 50% to each would have scored.')
