#!/usr/bin/env python3
"""Season 1 replay frames + counterfactual: would agents digging have moved Hack's law?

  whatif.py frames   replay the published ticks from world0 + site/log, one PNG per tick -> whatif/frames/
  whatif.py cf K     same 33 ticks of rain, plus K simulated players each spending 5 dig/raise a day
                     (two strategies: random land cells, or cells on big rivers); hack exponent per tick -> whatif/cf-K.json
"""
import sys, os, json, glob, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tick as T
OUT = os.path.join(HERE, 'whatif')

def logs():
    for f in sorted(glob.glob(os.path.join(T.SITE, 'log', 'tick-*.json'))):
        L = json.load(open(f)); yield L, [{q: a[q] for q in ('id', 'at', 'name', 'op', 'x', 'y')} for a in L['actions']]

def frames():
    os.makedirs(os.path.join(OUT, 'frames'), exist_ok=True)
    h, ctrl, meta = T.W0.copy(), T.W0.copy(), {'tick': 0, 'claims': {}, 'used': {}}
    oc, _, _, A, _ = T.route(h); T.render(h, oc, A, -np.ones((T.N, T.N), int), meta, os.path.join(OUT, 'frames', 'f000.png'))
    for L, acts in logs():
        T.step(h, ctrl, meta, acts); oc, A, owner, area, hk, land = T.score(h, meta)
        assert T.h16(h) == L['hash'], L['tick']
        T.render(h, oc, A, owner, meta, os.path.join(OUT, 'frames', f"f{L['tick']:03d}.png"))
        print(L['tick'], hk, land, flush=True)
    np.save(os.path.join(OUT, 'h_final.npy'), h)

def cf(K, strategy):
    h, ctrl, meta = T.W0.copy(), T.W0.copy(), {'tick': 0, 'claims': {}, 'used': {}}
    prng = np.random.default_rng([7, K, strategy == 'river'])
    rows = []
    for L, acts in logs():
        t = L['tick']; oc, r, order, A, Lg = T.route(h); land = ~oc & (h >= 0)
        # 5 actions a day per player ~ one action every 4.8 ticks: each player acts with p = 5/24 per tick
        new = []
        for p in range(K):
            if strategy != 'butterfly' and prng.random() < 5 / 24:
                if strategy == 'river': cand = np.flatnonzero((land & (A > 200)).ravel())
                else: cand = np.flatnonzero(land.ravel())
                c = int(prng.choice(cand)); y, x = divmod(c, T.N)
                op = 'dig' if prng.random() < 0.7 else 'raise'
                new.append({'id': f'sim{t}-{p}', 'at': L['actions'][0]['at'] if L['actions'] else f'2026-10-05T{t%24:02d}:00:00Z',
                            'name': f'p{p}', 'op': op, 'x': x, 'y': y})
        if strategy == 'butterfly' and t == 1: h[128, 128] -= 1e-6 * T.DEPTH; new = []  # no player: one invisible nudge, chaos only
        T.step(h, ctrl, meta, acts + new); _, _, _, _, hk, land_n = T.score(h, meta)
        oc_c = T.RV.ocean_mask(ctrl); _, _, _, Ac, Lc = T.route(ctrl)
        hc = round(T.RV.hack(Ac, Lc, ~oc_c & (ctrl >= 0), 50)[0], 4)
        rows.append({'tick': t, 'world': hk, 'control': hc, 'actions': len(new), 'diff_cells': int((np.abs(h - ctrl) > 1e-9).sum())})
        print(K, strategy, rows[-1], flush=True)
    json.dump(rows, open(os.path.join(OUT, f'cf-{K}-{strategy}.json'), 'w'))

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); t0 = time.time()
    if sys.argv[1] == 'frames': frames()
    else: cf(int(sys.argv[2]), sys.argv[3])
    print('secs', round(time.time() - t0))
