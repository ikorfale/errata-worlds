#!/usr/bin/env python3
"""No-action calibration of the season-2 nudge-ensemble test (theone 82507, zenith 82510).

With zero player actions the world is bit-identical to the control (same rain rng), so the control's rank among
the nudged members IS what the pre-registered test would report for an untouched world. For each rain seed:
control (unnudged world_s2) + K members nudged like ens_init, T ticks of background rain, Hack exponent per tick.
Seed list starts with the real season seed 20261005. One JSON line per seed, flushed, to null_calib.jsonl.
"""
import numpy as np, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'worlds'), os.path.join(HERE, '..')]
sys.argv = sys.argv[:1]
import tick as T, erode as ER, rivers as RV
K = int(os.environ.get('K', 40)); TT = int(os.environ.get('TT', 24))
W0 = np.load(os.path.join(HERE, 'world_s2.npy')); DEPTH = 0.10 * float(W0[W0 >= 0].max())
land = np.flatnonzero((~RV.ocean_mask(W0) & (W0 >= 0)).ravel())
def hack(h):
    o, r, od, A, L = T.route(h); return round(RV.hack(A, L, ~o & (h >= 0), 50)[0], 4)
out = os.path.join(HERE, os.environ.get('OUT', 'null_calib.jsonl'))
seeds = [20261005] + list(range(1, 200))
for s in seeds:
    t0 = time.time(); ctrl = W0.copy(); E = np.repeat(W0[None], K, 0)
    for k in range(K): E[k].flat[int(np.random.default_rng([s, 1000 + k]).choice(land))] -= T.NUDGE * DEPTH
    hc, he = [], []
    for t in range(1, TT + 1):
        ER.erode(ctrl, T.BG_DROPS, np.random.default_rng([s, t]), **T.ER_KW)
        for e in E: ER.erode(e, T.BG_DROPS, np.random.default_rng([s, t]), **T.ER_KW)
        hc.append(hack(ctrl)); he.append([hack(e) for e in E])
    with open(out, 'a') as f: f.write(json.dumps({'seed': s, 'K': K, 'T': TT, 'control': hc, 'members': he, 'sec': round(time.time() - t0)}) + '\n')
    print(s, round(time.time() - t0), flush=True)
