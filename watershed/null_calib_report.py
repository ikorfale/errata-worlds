#!/usr/bin/env python3
"""Read null_calib.jsonl: where does the untouched control rank among its nudged members?
Under exchangeability the control's rank is uniform on 0..K, so p = (r+1)/(K+1) is uniform and P(p<=0.05) ~ 0.05.
r = members whose summed exponent is <= the control's (lower = the pre-registered direction), ties counted."""
import json, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, 'null_calib.jsonl'))]
ps, ranks, ties_all, per_tick_low, mid, twins = [], [], 0, [], [], []
for d in rows:
    c = np.array(d['control']); m = np.array(d['members']); K = m.shape[1]
    cs, ms = round(c.sum(), 4), np.round(m.sum(0), 4)
    r = int((ms <= cs).sum()); ties_all += int((ms == cs).sum())
    mid.append(((ms < cs).sum() + (ms == cs).sum() / 2) / K)
    twins.append(int(np.all(np.abs(m - c[:, None]) < 1e-9, axis=0).sum()))
    ranks.append(r); ps.append((r + 1) / (K + 1))
    per_tick_low.append(np.mean([(m[t] <= c[t]).sum() / K for t in range(len(c))]))
    print(f"seed {d['seed']:>9}  K={K}  control sum {cs:.4f}  member sums {ms.min():.4f}..{ms.max():.4f}  "
          f"r={r:>2}  p={(r+1)/(K+1):.3f}  ties={(ms == cs).sum()}")
ps, ranks = np.array(ps), np.array(ranks); n = len(ps); K = rows[0]['K']
print(f"\nseeds {n}, K {K}")
print(f"p <= 0.05 in {(ps <= 0.05).sum()}/{n} seeds (expected {0.05*n:.1f} if exchangeable)")
print(f"mean rank fraction r/K = {ranks.mean()/K:.3f} (0.5 if exchangeable); median {np.median(ranks)/K:.3f}")
print(f"control at or above the member median (r >= K/2) in {(ranks >= K/2).sum()}/{n} seeds")
print(f"per-tick mean share of members <= control: {np.mean(per_tick_low):.3f}")
print(f"ties of sums with control: {ties_all}; members bit-identical to control on all ticks: {sum(twins)} ({sum(twins)/(n*K):.1%})")
print(f"mid-rank fraction (ties split): {np.mean(mid):.3f}")
h, _ = np.histogram(ranks / K, bins=5, range=(0, 1)); print("rank fraction quintiles:", h.tolist())
# one-sample KS of p against uniform (approximate: p is discrete on K+1 values)
from math import sqrt
s = np.sort(ps); D = max(np.max(np.arange(1, n+1)/n - s), np.max(s - np.arange(n)/n)); print(f"KS D={D:.3f} (5% crit ~{1.36/sqrt(n):.3f})")
