"""glitchfox #95553: in my simul engine, after a house-seat collision, is the cell '#' at end of tick, or does a
claim land on it? Same engine, seeds and variant as raid_ash.py base; resolve wrapped to read the grid after the tick
and at season end. Also prints one collision tick in full. Usage: python3 raid_dump.py [seasons]"""
import sys, random
import raid_ash as R
A = R.A
ORIG = A.resolve
log = {'hs': 0, 'end_tick': {}, 'end_season': {}, 'example': None}
live = []

def resolve(st, moves):
    before = dict(st['grid'])
    rows = ORIG(st, moves)
    cells = {}
    for r in rows:
        if r['result'] == 'collision': cells.setdefault(r['pick'], []).append(r['name'])
    for s, who in cells.items():
        if {n in A.HOUSE for n in who} == {True, False}:
            log['hs'] += 1; v = st['grid'].get(s)
            k = '#' if v == '#' else 'empty' if v is None else 'house' if v in A.HOUSE else 'seat'
            log['end_tick'][k] = log['end_tick'].get(k, 0) + 1
            live.append((st, s))
            if log['example'] is None:
                log['example'] = (st['tick'], s, before.get(s), [(r['name'], r['cells'], r['pick'], r['kind'], r['result']) for r in rows])
    return rows

A.resolve = resolve
K = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
rng = random.Random(95195 + 4)
for _ in range(K):
    live.clear(); R.season(4, rng, 'base')
    for st, s in live:
        v = st['grid'].get(s); k = '#' if v == '#' else 'other'
        log['end_season'][k] = log['end_season'].get(k, 0) + 1
print(f"K={K} seasons, avert houses, simul, seed 95199 (raid_ash.py base)")
print(f"house-seat collisions: {log['hs']} ({log['hs'] / K:.2f}/season)")
print("cell at end of the collision tick:", log['end_tick'])
print("same cell at end of season:", log['end_season'])
t, s, b, rows = log['example']
print(f"first example: tick {t}, cell {s}, before={b!r}")
for r in rows: print("  ", r)
