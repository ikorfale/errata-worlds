#!/usr/bin/env python3
"""Histogram of the untouched control's rank fraction among nudged members, one bar per rain seed (null_calib.jsonl)."""
import json, os, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
R = [json.loads(l) for l in open(os.path.join(HERE, 'null_calib.jsonl'))]
inc, mid = [], []
for r in R:
    c = round(sum(r['control']), 4); m = np.round(np.array(r['members']).sum(0), 4)  # rounded like tick.py, so ties are ties
    inc.append(((m <= c).sum()) / len(m)); mid.append(((m < c).sum() + 0.5 * (m == c).sum()) / len(m))
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
bins = np.linspace(0, 1, 11)
ax.hist(inc, bins=bins, color='#3b6ea8', edgecolor='white', linewidth=2)
ax.axhline(len(R) / 10, color='#666', lw=1.5, ls='--')
ax.text(0.01, len(R) / 10 + 0.15, f'expected per bar if exchangeable ({len(R)/10:.1f})', color='#444', fontsize=9)
ax.axvspan(0, 0.05, color='#c0392b', alpha=0.12, lw=0)
ax.text(0.055, ax.get_ylim()[1] * 0.92, 'test fires here\n(p ≤ 0.05)', color='#7a2418', fontsize=9, va='top')
ax.set_xlabel('share of nudged members with season sum ≤ untouched world (ties included)')
ax.set_ylabel('rain seeds')
ax.set_title(f'Untouched world vs {R[0]["K"]} nudged twins, {len(R)} rain seeds, {R[0]["T"]} ticks', loc='left', fontsize=11)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
ax.grid(axis='y', color='#ddd', lw=0.8); ax.set_axisbelow(True)
fig.tight_layout(); out = os.path.join(HERE, 'null_calib.png'); fig.savefig(out); print(out, len(R), 'seeds; mean inc', round(np.mean(inc), 3), 'mean mid', round(np.mean(mid), 3))
