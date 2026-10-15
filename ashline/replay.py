"""Replay Ashline from its public history: re-resolve every tick from an empty board and compare.

Inputs are only the player moves recorded in history.json (cells in order, post seq/id); house moves,
verdicts, grid and scores are recomputed by ashline.resolve and must match what was published.
Usage: python3 replay.py [history.json path or URL]   (default: https://worlds.errata.page/ashline/history.json)
To check the inputs themselves, fetch each row's post id from the board and run ashline.parse on its body.
"""
import json, sys, urllib.request
import ashline as A

src = sys.argv[1] if len(sys.argv) > 1 else 'https://worlds.errata.page/ashline/history.json'
pub = json.load(urllib.request.urlopen(src) if src.startswith('http') else open(src))
st, bad = A.new_state(), 0
for h in pub['history']:
    moves = {r['name']: {'seq': r['seq'], 'id': r['id'], 'cells': r['cells'], 'superseded': r['superseded']}
             for r in h['rows'] if r['name'] not in A.HOUSE}
    rows = A.resolve(st, moves)
    for want, got in zip(sorted(h['rows'], key=lambda r: r['name']), sorted(rows, key=lambda r: r['name'])):
        for k in ('name', 'cells', 'pick', 'kind', 'result', 'reason'):
            if want[k] != got[k]: bad += 1; print(f"tick {h['tick']} {want['name']} {k}: published {want[k]!r}, replay {got[k]!r}")
    if len(rows) != len(h['rows']): bad += 1; print(f"tick {h['tick']}: {len(h['rows'])} rows published, {len(rows)} replayed")
    if st['history'][-1]['scores'] != h['scores']: bad += 1; print(f"tick {h['tick']} scores differ")
if st['grid'] != pub['grid']: bad += 1; print('final grid differs')
print(f"ticks {len(pub['history'])}, rows {sum(len(h['rows']) for h in pub['history'])}, mismatches {bad}")
sys.exit(1 if bad else 0)
