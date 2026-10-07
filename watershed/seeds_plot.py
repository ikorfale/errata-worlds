import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
d = json.load(open('whatif/seeds_river.json')); n = json.load(open('whatif/null.json'))
nm = [r['mean'] for r in n['runs']]
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
for i, (lab, key, c) in enumerate([('30 nudges\n(chaos only)', None, '#9a9a9a'), ('random diggers\n10 seeds', 'random', '#669bbc'), ('river diggers\n10 seeds', 'river', '#e4572e')]):
    v = np.array(nm if key is None else d[key]['runs']) * 1000
    ax.scatter(np.full(len(v), i) + np.random.default_rng(i).uniform(-.12, .12, len(v)), v, s=28, color=c, alpha=.85, zorder=3)
    ax.hlines(np.median(v), i - .25, i + .25, color='#222', lw=2, zorder=4)
ax.axhline(n['mean_pct']['50'] * 1000, color='#9a9a9a', ls=':', lw=1)
ax.set_xticks(range(3), ['30 nudges\n(chaos only)', 'random diggers\n10 seeds', 'river diggers\n10 seeds'])
ax.set_ylabel("Hack exponent, world − control\n(mean of ticks 17–33, ×1000)")
ax.set_title('Watershed: river-digging is not different from random digging (p = 0.37)', fontsize=11, loc='left')
ax.text(2.45, n['mean_pct']['50'] * 1000, 'null median', fontsize=8, color='#777', va='bottom', ha='right')
for s in ('top', 'right'): ax.spines[s].set_visible(False)
fig.text(0.01, 0.01, '16 simulated players, 5 actions/day; bar = median. errata (AI agent) · errata.page', fontsize=7, color='#777')
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig('whatif/seeds_river.png')
