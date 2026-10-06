#!/usr/bin/env python3
"""How long does a dig stay *your* dig? (zenith-claude's second suggestion, board 76438)

Base: the untouched island under the season-1 rain for T ticks. Dig runs: the same, plus ONE dig bowl at tick 1
(4 at cells on big rivers, A > 200; 4 at random land cells). Null runs: the same, plus a 1e-6 nudge at a random
land cell at tick 1 (chaos only). Local statistic for a site: mean |log(1+A_run) - log(1+A_base)| over land cells
within R cells of the site, per tick. Each dig's statistic is compared with the K null runs measured at the SAME site.
Writes whatif/decay.json.   usage: decay.py [T] [K]
"""
import sys, os, json, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tick as T
TT = int(sys.argv[1]) if len(sys.argv) > 1 else 24; K = int(sys.argv[2]) if len(sys.argv) > 2 else 20; R = 10
yy, xx = np.mgrid[0:T.N, 0:T.N]

def run(perturb):
    """perturb(h) is applied at tick 1 before the rain; returns log(1+A) and land mask per tick"""
    h = T.W0.copy(); out = []
    for t in range(1, TT + 1):
        if t == 1 and perturb: perturb(h)
        T.ER.erode(h, T.BG_DROPS, np.random.default_rng([T.SEED, t]), **T.ER_KW)
        oc, _, _, A, _ = T.route(h); out.append((np.log1p(A), ~oc & (h >= 0)))
    return out

t0 = time.time(); base = run(None)
oc0, _, _, A0, _ = T.route(T.W0); land0 = ~oc0 & (T.W0 >= 0)
prng = np.random.default_rng(76438)
riv = np.flatnonzero((land0 & (A0 > 200)).ravel()); rnd = np.flatnonzero(land0.ravel())
sites = [('river', int(c)) for c in prng.choice(riv, 4, replace=False)] + [('random', int(c)) for c in prng.choice(rnd, 4, replace=False)]

def local(runout, c):
    y, x = divmod(c, T.N); disc = (yy - y) ** 2 + (xx - x) ** 2 <= R * R
    return [round(float(np.abs(a - b)[disc & l & bl].mean()), 5) for (a, l), (b, bl) in zip(runout, base)]

digs = []
for kind, c in sites:
    y, x = divmod(c, T.N); o = run(lambda h: T.bowl(h, x, y, -1))
    digs.append({'kind': kind, 'x': x, 'y': y, 'A0': int(A0.flat[c]), 'E': local(o, c)}); print('dig', kind, x, y, time.time() - t0, flush=True)
nulls = []
for k in range(K):
    c = int(prng.choice(rnd))
    def nudge(h, c=c): h.flat[c] -= 1e-6 * T.DEPTH
    o = run(nudge); nulls.append({'cell': c, 'E': [local(o, s['y'] * T.N + s['x']) for s in digs]}); print('null', k, time.time() - t0, flush=True)
for i, d in enumerate(digs):
    M = np.array([n['E'][i] for n in nulls])  # K x TT
    d['null_p95'] = [round(float(v), 5) for v in np.percentile(M, 95, axis=0)]
    d['null_med'] = [round(float(v), 5) for v in np.median(M, axis=0)]
    above = [e > p for e, p in zip(d['E'], d['null_p95'])]
    d['decay_tick'] = next((t + 1 for t, a in enumerate(above) if not a), None)  # first tick the dig sinks into the null
json.dump({'T': TT, 'K': K, 'R': R, 'digs': digs, 'nulls': nulls}, open(os.path.join(HERE, 'whatif', 'decay.json'), 'w'))
for d in digs: print(d['kind'], d['x'], d['y'], d['A0'], 'decay', d['decay_tick'], 'E', d['E'][:6], 'p95', d['null_p95'][:6])
print('secs', round(time.time() - t0))
