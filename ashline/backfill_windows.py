"""One-off (2026-10-15, board #88983): add window and inputs to ticks 1-3, which ran before tick.py exported them.

Exact values that survive: tick 1 opened at config opened_at; tick 3 cut off at state.json last_tick_at.
The tick 1 and tick 2 cutoffs were not stored, so they are given as ranges: from the systemd start of the tick
service (journal, microseconds) to the second after the tick reply's created_at (the reply is posted after the cut).
A move is safely assigned if its created_at lies outside every range; input body hashes are taken today, not at tick time.
"""
import json, os, hashlib
import ashline as A, tick as T

HERE = os.path.dirname(os.path.abspath(__file__))
CUT = {1: [1791892800.537338, 1791892803.0],   # journal start 2026-10-13 12:00:00.537338; tick reply #85677 created 1791892802
       2: [1791979200.539574, 1791979206.0],   # journal start 2026-10-14 12:00:00.539574; tick reply #87187 created 1791979205
       3: [1792065600.6567235, 1792065600.6567235]}  # state.json last_tick_at
st = json.load(open(T.STATE)); posts = T.fetch(T.CFG['root'])
since = [T.CFG['opened_at']] * 2
for h in st['history'][:3]:
    until = CUT[h['tick']]
    edge = [p['seq'] for p in posts if p.get('author') not in A.SKIP_AUTHORS and A.parse(p.get('body'))
            and any(r[0] <= p['created_at'] < r[1] for r in (since, until) if r[0] != r[1])]
    assert not edge, f"tick {h['tick']}: command posts inside an uncertain cutoff range: {edge}"
    h['window'] = {'since': since, 'until': until, 'basis': 'exact' if since[0] == since[1] and until[0] == until[1] else
                   'ranges: systemd start .. tick reply created_at + 1 s; no command post falls inside a range'}
    h['inputs'] = T.inputs(posts, since[1], until[0]); h['inputs_hashed_at'] = '2026-10-15 (backfill)'
    got = {i['author'] for i in h['inputs'] if i['commands']}; want = {r['name'] for r in h['rows'] if r['seq']}
    assert got == want, (h['tick'], got, want)
    since = until
json.dump(st, open(T.STATE + '.tmp', 'w'), indent=1); os.replace(T.STATE + '.tmp', T.STATE)
T.write_site(st)
print({h['tick']: (h['window']['basis'][:5], len(h['inputs'])) for h in st['history']})
