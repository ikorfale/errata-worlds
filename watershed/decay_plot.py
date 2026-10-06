"""chart for decay.json: local effect of one dig vs the 20 nudged controls at the same site"""
import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
D = json.load(open('whatif/decay.json')); t = np.arange(1, D['T'] + 1)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
for a, kind, col in ((ax[0], 'river', '#1f6f9f'), (ax[1], 'random', '#b5562b')):
    for d in [d for d in D['digs'] if d['kind'] == kind]:
        a.plot(t, d['E'], color=col, lw=1.6, alpha=.85)
        a.plot(t, d['null_p95'], color='#888', lw=1, ls='--', alpha=.8)
    a.set_title(f"one dig at a {'big-river cell (A > 200)' if kind == 'river' else 'random land cell'} (4 sites)", fontsize=11)
    a.set_xlabel('hourly tick after the dig'); a.grid(alpha=.25); a.spines[['top', 'right']].set_visible(False)
ax[0].set_ylabel('local change in drainage\nmean |Δ log(1+A)| within 10 cells')
ax[0].plot([], [], color='#888', ls='--', label='95th pct of 20 invisible 1e-6 nudges, same site'); ax[0].legend(frameon=False, fontsize=9, loc='upper left')
fig.suptitle('Watershed: how long a dig stays your dig — solid: the dig, dashed: chaos alone', fontsize=12)
fig.tight_layout(); fig.savefig('whatif/decay.png', dpi=130); print('ok')
