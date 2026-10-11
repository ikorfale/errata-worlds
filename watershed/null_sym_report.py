#!/usr/bin/env python3
"""Report for null_sym.py rev 2 (raw floats), as declared in WATERSHED.md before its data (theone 82876, zenith-claude 82872/82878).

Primary rule = production (tick.py ens_stats): round each tick's Hack to 4 decimals, sum in tick order, inclusive rank
of the raw sum, p_low = (below + ties + 1) / (K + 1). A 6-dp row is a sensitivity check only.
Per seed:   p_low of world (new design) and base (old design) among the K members;
            q = share of the K+1 scores (world + members) whose inclusive p_low, each against the other K, lies in [0.30, 0.90];
            power: p_low of world_dig and base_dig; placement: dig cell's drainage area at tick 0, A >= 50 cells under the bowl.
Summary:    rejections (p_low <= 0.05) with exact binomial tail; band count against the exact Poisson-binomial of the q's;
            power counts against the declared bar of 4 of 21.
Usage: null_sym_report.py [null_sym.jsonl] [--dp 4|6]
"""
import json, os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE, os.path.join(HERE, '..', 'worlds')]
args = [a for a in sys.argv[1:] if not a.startswith('--')]
DP = int(sys.argv[sys.argv.index('--dp') + 1]) if '--dp' in sys.argv else 4
args = [a for a in args if a != str(DP)]
path = args[0] if args else os.path.join(HERE, 'null_sym.jsonl')
sys.argv = sys.argv[:1]

def season(xs):  # production: round per tick, accumulate in tick order
    s = 0.0
    for x in xs: s += round(x, DP)
    return s

def p_low(v, a):
    a = np.asarray(a); below = int((a < v).sum()); ties = int((a == v).sum())
    return (below + ties + 1) / (len(a) + 1)

def poibin(qs):  # exact distribution of a sum of independent Bernoulli(q)
    d = np.zeros(len(qs) + 1); d[0] = 1.0
    for q in qs: d[1:] = d[1:] * (1 - q) + d[:-1] * q; d[0] *= (1 - q)
    return d

def binom_ge(k, n, p): return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

R = [json.loads(l) for l in open(path)]
if any(r.get('hack_dp') != 'raw' for r in R): sys.exit('not a rev-2 file (hack_dp != raw): refusing to analyse')
import tick as T, rivers as RV
W0 = np.load(os.path.join(HERE, 'world_s2.npy'))
o, rec, od, A0, L0 = T.route(W0); fit0 = ~o & (W0 >= 0) & (A0 >= 50)

rows = []
for r in R:
    M = np.array(r['members'])                      # ticks x K
    ms = [season(M[:, k]) for k in range(M.shape[1])]
    sc = {n: season(r[n]) for n in ('base', 'world', 'base_dig', 'world_dig')}
    allw = [sc['world']] + ms
    ps = [p_low(allw[i], allw[:i] + allw[i + 1:]) for i in range(len(allw))]
    q = sum(0.30 <= p <= 0.90 for p in ps) / len(ps)
    dx, dy = r['dig']
    rows.append({'seed': r['seed'], 'K': len(ms), 'T': r['T'], 'dig_depth': r['dig_depth'],
                 'p_world': p_low(sc['world'], ms), 'p_base': p_low(sc['base'], ms),
                 'ties_world': int(sum(m == sc['world'] for m in ms)),
                 'q': q, 'in_band': 0.30 <= ps[0] <= 0.90,
                 'p_world_dig': p_low(sc['world_dig'], ms), 'p_base_dig': p_low(sc['base_dig'], ms),
                 'p_world_dig_hi': (int(sum(m > sc['world_dig'] for m in ms)) + int(sum(m == sc['world_dig'] for m in ms)) + 1) / (len(ms) + 1),
                 'dig_A0': int(A0[dy, dx]), 'fit_cells_under_bowl': int(fit0[max(0, dy - 3):dy + 4, max(0, dx - 3):dx + 4].sum()),
                 'inert_world': r['rsha']['world'] == r['rsha']['base'],
                 'inert_members': sum(h == r['rsha']['base'] for h in r['rsha_members'])})

n = len(rows)
print(f'{path}: {n} seeds, rule = round {DP} per tick, summed in tick order; dig depth {sorted({x["dig_depth"] for x in rows})}')
print(f'{"seed":>9} {"p_world":>7} {"ties":>4} {"q":>5} {"band":>4} {"p_base":>6} {"p_wdig":>6} {"p_bdig":>6} {"A0":>6} {"fit7x7":>6} inert(w,m)')
for x in rows:
    print(f'{x["seed"]:>9} {x["p_world"]:7.3f} {x["ties_world"]:4d} {x["q"]:5.2f} {"in" if x["in_band"] else "out":>4} {x["p_base"]:6.3f} '
          f'{x["p_world_dig"]:6.3f} {x["p_base_dig"]:6.3f} {x["dig_A0"]:6d} {x["fit_cells_under_bowl"]:6d} {x["inert_world"]!s:>5},{x["inert_members"]}')
rej = sum(x['p_world'] <= 0.05 for x in rows); rejb = sum(x['p_base'] <= 0.05 for x in rows)
print(f'\nsize, new design: {rej}/{n} seeds at p_low <= 0.05 (P(>= that | exact 5%) = {binom_ge(rej, n, 0.05):.3f}); old design: {rejb}/{n}')
d = poibin([x['q'] for x in rows]); band = sum(x['in_band'] for x in rows); exp = sum(x['q'] for x in rows)
print(f'centring: {band}/{n} in band, expected {exp:.1f}; exact P(<= {band}) = {d[:band + 1].sum():.3f}, P(>= {band}) = {d[band:].sum():.3f}')
pw = sum(x['p_world_dig'] <= 0.05 for x in rows); pb = sum(x['p_base_dig'] <= 0.05 for x in rows)
pw2 = sum(min(x['p_world_dig'], x['p_world_dig_hi']) <= 0.025 for x in rows)
print(f'power (declared bar: >= 4 of 21 in the lower tail): new design {pw}/{n} -> {"detectable" if pw >= 4 else "not detectable"}; '
      f'old design {pb}/{n}; new design two-sided at 0.025 each tail {pw2}/{n}')
print(f'placement: digs touching no fitted cell {sum(x["fit_cells_under_bowl"] == 0 for x in rows)}/{n}; '
      f'median dig-cell area {int(np.median([x["dig_A0"] for x in rows]))}')
