"""Replay Ashline from its public history: re-resolve every tick from an empty board and compare.

Inputs are only the player moves recorded in history.json (cells in order, post seq/id); house moves,
verdicts, grid and scores are recomputed by ashline.resolve and must match what was published.
Usage: python3 replay.py [history.json path or URL]   (default: https://worlds.errata.page/ashline/history.json)
Since 2026-10-15 each tick also records its window (since/until; ticks 1-2 as ranges, see backfill_windows.py) and
inputs: every reply in the window with id, seq, created_at, body sha256 and parsed commands; since tick 5 also code:
sha256 of ashline.py and tick.py as run, the repo commit and a dirty flag. The replay checks that the
moves follow from those inputs; to check the inputs, fetch each id, hash the body and run ashline.parse on it.
"""
import json, sys, urllib.request, hashlib
import ashline as A

src = sys.argv[1] if len(sys.argv) > 1 else 'https://worlds.errata.page/ashline/history.json'
pub = json.load(urllib.request.urlopen(src) if src.startswith('http') else open(src))
st, bad = A.new_state(pub.get('rules')), 0
for h in pub['history']:
    moves = {r['name']: {'seq': r['seq'], 'id': r['id'], 'cells': r['cells'], 'superseded': r['superseded']}
             for r in h['rows'] if r['name'] not in A.HOUSE}
    if 'inputs' in h:  # the moves must follow from the recorded inputs by the last-line-per-author rule of ashline.collect
        fromin = {}
        for i in sorted(h['inputs'], key=lambda i: i['seq']):
            for c in i['commands']:
                prev = fromin.get(i['author'])
                fromin[i['author']] = {'seq': i['seq'], 'cells': c, 'superseded': (prev['superseded'] + [prev['seq']]) if prev else []}
        for n in set(fromin) | set(moves):
            a, b = fromin.get(n), moves.get(n)
            if not a or not b or (a['seq'], a['cells'], a['superseded']) != (b['seq'], b['cells'], b['superseded']):
                bad += 1; print(f"tick {h['tick']} {n}: inputs give {a}, history row has {b}")
    if 'code' in h:  # since tick 5: the code that resolved this tick; compare with the ashline.py this replay imports
        mine = hashlib.sha256(open(A.__file__, 'rb').read()).hexdigest()
        if mine != h['code']['ashline.py']: print(f"note: tick {h['tick']} was resolved by ashline.py {h['code']['ashline.py'][:12]} (commit {h['code']['commit'][:7]}), this replay runs {mine[:12]}")
    rows = A.resolve(st, moves)
    for want, got in zip(sorted(h['rows'], key=lambda r: r['name']), sorted(rows, key=lambda r: r['name'])):
        for k in ('name', 'cells', 'pick', 'kind', 'result', 'reason'):
            if want[k] != got[k]: bad += 1; print(f"tick {h['tick']} {want['name']} {k}: published {want[k]!r}, replay {got[k]!r}")
    if len(rows) != len(h['rows']): bad += 1; print(f"tick {h['tick']}: {len(h['rows'])} rows published, {len(rows)} replayed")
    if st['history'][-1]['scores'] != h['scores']: bad += 1; print(f"tick {h['tick']} scores differ")
if st['grid'] != pub['grid']: bad += 1; print('final grid differs')
print(f"ticks {len(pub['history'])}, rows {sum(len(h['rows']) for h in pub['history'])}, mismatches {bad}")
sys.exit(1 if bad else 0)
