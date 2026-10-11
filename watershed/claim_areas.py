#!/usr/bin/env python3
"""Replay season 1 from the tick logs (world only, no ensemble) and record each claim's basin area per tick.
Checks the world hash at every tick against the log. Writes claim_areas.json; prints a summary.
Question: with nobody digging, how much does a claimed basin change under rain alone?"""
import json, os, glob, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tick as T

h, ctrl, meta = T.W0.copy(), T.W0.copy(), {'tick': 0, 'claims': {}, 'used': {}}
rows, bad, t0 = [], 0, time.time()
for f in sorted(glob.glob(os.path.join(T.SITE, 'log', 'tick-*.json'))):
    L = json.load(open(f)); acts = [{q: a[q] for q in ('id', 'at', 'name', 'op', 'x', 'y')} for a in L['actions']]
    T.step(h, ctrl, meta, acts); _, _, _, area, hk, land = T.score(h, meta)
    ok = T.h16(h) == L['hash']; bad += not ok
    rows.append({'tick': meta['tick'], 'ok': ok, 'area': area, 'hack': hk, 'land': land})
json.dump(rows, open(os.path.join(HERE, 'claim_areas.json'), 'w'))
print(f"{len(rows)} ticks replayed in {time.time() - t0:.0f} s, hash mismatches: {bad}")
for n in meta['claims']:
    a = np.array([r['area'].get(n, 0) for r in rows if n in r['area']])
    d = np.abs(np.diff(a))
    print(f"{n}: first {a[0]}, last {a[-1]}, min {a.min()}, max {a.max()}, median {int(np.median(a))}, "
          f"ticks with a change {int((d > 0).sum())}/{len(d)}, largest one-tick jump {int(d.max())}")
