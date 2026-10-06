#!/usr/bin/env python3
"""Chart: Hack exponent of the shared world vs its untouched control, season 1 ticks, actual and counterfactual."""
import json, os, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'whatif')
hist = json.load(open(os.path.join(HERE, 'site', 'history.json')))
runs = [('cf-0-butterfly', 'one invisible nudge (chaos only)', '#888888'), ('cf-4-random', '4 players, random digs', '#669bbc'),
        ('cf-16-random', '16 players, random digs', '#1d3557'), ('cf-4-river', '4 players, digging big rivers', '#f3a712'),
        ('cf-16-river', '16 players, digging big rivers', '#e4572e')]
fig, ax = plt.subplots(1, 2, figsize=(12, 5.4), dpi=100)
t = [r['tick'] for r in hist]
ax[0].plot(t, [r['hack_control'] for r in hist], color='k', lw=2.2, label='control = actual world (bit-identical)')
out = {}
for f, lab, c in runs:
    p = os.path.join(W, f + '.json')
    if not os.path.exists(p): continue
    R = json.load(open(p)); d = np.array([r['world'] - r['control'] for r in R])
    ax[0].plot([r['tick'] for r in R], [r['world'] for r in R], color=c, lw=1.2, label=lab)
    ax[1].plot([r['tick'] for r in R], d, color=c, lw=1.4, label=lab)
    late = d[len(d) // 2:]; out[f] = {'mean_diff_late': round(float(late.mean()), 4), 'mean_abs_late': round(float(np.abs(late).mean()), 4),
                                     'actions': sum(r['actions'] for r in R)}
ax[0].set_title("Hack's exponent h per hourly tick"); ax[0].set_xlabel('tick (hours since 5 Oct 09:00 UTC)'); ax[0].set_ylabel('h  (L ~ A^h, basins of 50+ cells)')
ax[1].axhline(0, color='k', lw=0.8); ax[1].set_title('world minus control'); ax[1].set_xlabel('tick')
ax[0].legend(fontsize=8, frameon=False, loc='lower left'); ax[1].legend(fontsize=8, frameon=False, loc='lower left')
for a in ax: a.spines[['top', 'right']].set_visible(False)
fig.suptitle('Watershed season 1: did shaping the land move Hack\'s law? (simulated players vs untouched control)', fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(W, 'watershed-hack-counterfactual.png'))
ctl = np.array([r['hack_control'] for r in hist]); print('control tick-to-tick sd', round(float(np.diff(ctl).std()), 4), 'range', ctl.min(), ctl.max())
print(json.dumps(out, indent=1))
