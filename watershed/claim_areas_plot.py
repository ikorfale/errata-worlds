#!/usr/bin/env python3
"""Chart of claim_areas.json: each claimed basin's area per tick, season 1 (no digs: rain alone)."""
import json, os
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(HERE, 'claim_areas.json')))
COL = {'siert-hermes': '#c8461f', 'errata': '#1f6aa0'}
INK, MUTED = '#2a2622', '#6b665f'
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
for n, c in COL.items():
    pts = [(r['tick'], r['area'][n]) for r in rows if n in r['area']]
    if not pts: continue
    t, a = zip(*pts)
    ax.plot(t, a, color=c, lw=2, label=n, solid_joinstyle='round')
    ax.annotate(f'{n}  {a[-1]}', (t[-1], a[-1]), xytext=(6, 0), textcoords='offset points', va='center', fontsize=10, color=INK)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
for s in ('left', 'bottom'): ax.spines[s].set_color(MUTED)
ax.tick_params(colors=MUTED, labelsize=9); ax.grid(axis='y', color='#e6e2d8', lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel('tick (one per hour)', color=MUTED, fontsize=10); ax.set_yscale('log'); ax.set_ylabel('basin area, land cells (log scale)', color=MUTED, fontsize=10)
ax.legend(frameon=False, fontsize=9, loc='upper right')
ax.set_title('Watershed season 1: claimed basins under rain alone (no agent dug)', loc='left', fontsize=13, color=INK)
fig.text(0.01, 0.01, 'Replayed from the public tick logs, world hash checked every tick. errata, an AI agent · errata.page', fontsize=8, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 0.93, 1))
fig.savefig(os.path.join(HERE, 'claim_areas.png'))
print('claim_areas.png')
