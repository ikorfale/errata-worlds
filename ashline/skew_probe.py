"""Real seq/created_at skew on the board feed (glitchfox #108826): walk /v1/activity back N pages, find pairs where
seq order and created_at disagree; the largest such disagreement is a lower bound on commit skew."""
import json, subprocess, sys
import os
WORK = os.environ.get('ERRATA_WORK', os.path.expanduser('~/work'))
pages = int(sys.argv[1]) if len(sys.argv) > 1 else 150
rows, before = {}, None
for _ in range(pages):
    q = '/v1/activity?limit=30' + (f'&before={before}' if before else '')
    d = json.loads(subprocess.run([f'{WORK}/get.sh', q], capture_output=True, text=True, timeout=60).stdout)
    for p in d.get('items', []): rows[p['seq']] = p['created_at']
    before = d.get('next_before')
    if not before: break
json.dump(rows, open('skew_probe_rows.json','w')); s = sorted(rows); print('posts', len(rows), 'seq', s[0], '..', s[-1], 'example created_at', repr(rows[s[-1]]))
# running max of created_at over lower seqs: inversion = a lower seq created later than a higher seq
run_max, run_seq, inv, worst = None, None, 0, (0, None, None)
for q in s:
    t = rows[q]
    if run_max is not None and t < run_max:
        inv += 1; gap = run_max - t
        if gap > worst[0]: worst = (gap, run_seq, q)
    if run_max is None or t > run_max: run_max, run_seq = t, q
print('seqs created before some lower seq:', inv, 'of', len(s))
print('largest inversion (s):', worst[0], 'lower seq', worst[1], rows.get(worst[1]), 'higher seq', worst[2], rows.get(worst[2]))
gaps = sorted(rows[b] - rows[a] for a, b in zip(s, s[1:]) if rows[b] < rows[a])
print('adjacent-pair inversions:', len(gaps), 'sizes (s):', [round(g, 3) for g in gaps[:12]])

ties = sum(1 for a, b in zip(s, s[1:]) if rows[a] == rows[b])
print('adjacent seqs with the same created_at second:', ties)
print('seq holes in range:', (s[-1] - s[0] + 1) - len(s))
print('integer seconds:', all(isinstance(rows[q], int) for q in s))
