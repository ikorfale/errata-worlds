#!/usr/bin/env python3
"""Season-1 final numbers from the live state, for the final post (#119). Prints only; run after the final tick.
What it reports: ticks, accepted actions by op, whether world == control (byte compare), Hack exponent of world and
control (final, mean, range over the season), claims with totals and best capture, and the real-river reference."""
import json, os, numpy as np, collections, glob
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, 'state'); SITE = os.path.join(HERE, 'site')
hist = json.load(open(os.path.join(SITE, 'history.json'))); st = json.load(open(os.path.join(SITE, 'state.json')))
ops = collections.Counter(); names = collections.Counter()
for f in sorted(glob.glob(os.path.join(SITE, 'log', 'tick-*.json'))):
    for a in json.load(open(f)).get('actions', []):
        if a.get('ok'): ops[a['op']] += 1; names[a['name']] += 1
same = open(os.path.join(S, 'h.npy'), 'rb').read() == open(os.path.join(S, 'control.npy'), 'rb').read()
hw = np.array([r['hack_world'] for r in hist]); hc = np.array([r['hack_control'] for r in hist])
print(f"ticks {hist[0]['tick']}..{hist[-1]['tick']} ({len(hist)} rows), last {hist[-1]['time']}, final.json: {os.path.exists(os.path.join(SITE, 'final.json'))}")
print(f"accepted actions by op: {dict(ops)}; by player: {dict(names)}")
print(f"world == control byte for byte: {same}; ticks where Hack differs: {int((hw != hc).sum())}")
print(f"Hack world: final {hw[-1]:.4f}, mean {hw.mean():.4f}, range {hw.min():.4f}..{hw.max():.4f}; control final {hc[-1]:.4f}")
print("reference: real rivers h ~0.54 (my 05.10 measurement; the page said 0.56-0.60 until 11.10)")
for c in sorted(st['claims'], key=lambda c: -c['total']):
    print(f"claim {c['name']:<14} at ({c['x']},{c['y']}) since tick {c['since']}: total {c['total']}, area now {c['area']}, best capture {c['best_capture']} at tick {c['best_capture_tick']}")
