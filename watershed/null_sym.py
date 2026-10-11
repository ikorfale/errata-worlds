#!/usr/bin/env python3
"""Season-2 test, symmetric construction + planted-dig power row (theone 82727, zenith 82702/82738).

Per rain seed s, all from the un-nudged island W0 (base), same background rain rng([s, t]) for every trajectory:
  base        W0, no nudge                      (the old design's "world" under zero actions)
  world       W0 + nudge from rng([s, 999])     (new design: the world is one more nudged draw, like each member)
  base_dig    base  + one player dig at tick 1  (old design with a planted action)
  world_dig   world + the same dig              (new design with a planted action)
  members     W0 + nudge from rng([s, 1000+k]), k < K
Dig rule, declared before running: one `dig` bowl (tick.py bowl, depth 0.10 of relief) on a land cell drawn from
rng([s, 777]), applied at tick 1 before the background rain, exactly as step() applies actions. Horizon TT ticks.
Statistic: the pre-registered one, sum over ticks of the Hack exponent; p_low = (1 + #members <= x) / (K + 1).
Identity: heights always differ by the nudge itself, so an inert nudge is tested on the river network: sha256 of the
final receiver array (rsha) per trajectory; heights hashed too (sha). SLICE=a:b runs seeds [a:b] of the list.
One JSON line per seed, flushed, to null_sym.jsonl.
"""
import numpy as np, json, os, sys, time, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'worlds')]
sys.argv = sys.argv[:1]
import tick as T, erode as ER, rivers as RV
K = int(os.environ.get('K', 40)); TT = int(os.environ.get('TT', 24)); NSEED = int(os.environ.get('NSEED', 21))
W0 = np.load(os.path.join(HERE, 'world_s2.npy')); DEPTH = 0.10 * float(W0[W0 >= 0].max())
land = np.flatnonzero((~RV.ocean_mask(W0) & (W0 >= 0)).ravel())
def hack(h):
    o, r, od, A, L = T.route(h); return round(RV.hack(A, L, ~o & (h >= 0), 50)[0], 6)
def nudged(s, j):
    h = W0.copy(); h.flat[int(np.random.default_rng([s, j]).choice(land))] -= T.NUDGE * DEPTH; return h
def sha(h): return hashlib.sha256(np.ascontiguousarray(h, np.float64).tobytes()).hexdigest()[:16]
def rsha(h): return hashlib.sha256(np.ascontiguousarray(T.route(h)[1], np.int64).tobytes()).hexdigest()[:16]  # river receivers
out = os.path.join(HERE, os.environ.get('OUT', 'null_sym.jsonl'))
done = {json.loads(l)['seed'] for l in open(out)} if os.path.exists(out) else set()
a, b = map(int, os.environ.get('SLICE', f'0:{NSEED}').split(':'))
for s in ([20261005] + list(range(1, 200)))[a:b]:
    if s in done: continue
    t0 = time.time(); c = int(np.random.default_rng([s, 777]).choice(land)); dy, dx = divmod(c, W0.shape[1])
    named = {'base': W0.copy(), 'world': nudged(s, 999)}
    named['base_dig'] = named['base'].copy(); named['world_dig'] = named['world'].copy()
    T.bowl(named['base_dig'], dx, dy, -1); T.bowl(named['world_dig'], dx, dy, -1)
    E = [nudged(s, 1000 + k) for k in range(K)]
    traj = {n: [] for n in named}; me = []
    for t in range(1, TT + 1):
        for n, h in named.items(): ER.erode(h, T.BG_DROPS, np.random.default_rng([s, t]), **T.ER_KW); traj[n].append(hack(h))
        row = []
        for e in E: ER.erode(e, T.BG_DROPS, np.random.default_rng([s, t]), **T.ER_KW); row.append(hack(e))
        me.append(row)
    rec = {'seed': s, 'K': K, 'T': TT, 'dig': [dx, dy], **traj, 'members': me,
           'sha': {n: sha(h) for n, h in named.items()}, 'sha_members': [sha(e) for e in E],
           'rsha': {n: rsha(h) for n, h in named.items()}, 'rsha_members': [rsha(e) for e in E], 'sec': round(time.time() - t0)}
    with open(out, 'a') as f: f.write(json.dumps(rec) + '\n')
    print(s, rec['sec'], flush=True)
