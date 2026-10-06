"""Chart for #151: direction of strip-shaped basins (E > 1.5) relative to the meridian, Greenland vs Baffin vs Ellesmere."""
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
bins = np.arange(0, 91, 10); fig, ax = plt.subplots(figsize=(10, 5.6), dpi=130)
cols = {'Greenland': '#b2182b', 'Baffin': '#2166ac', 'Ellesmere': '#878787'}
w = 2.8
for k, (name, c) in enumerate(cols.items()):
    a = np.load(f'out/bearing_{name}.npy'); s = a[a[:, 1] > 1.5, 0]
    h = np.histogram(s, bins)[0] / len(s) * 100
    ax.bar(bins[:-1] + 5 + (k - 1) * w, h, width=w, color=c, label=f'{name} (n={len(s)})')
ax.axhline(100 / 9, color='k', lw=0.8, ls='--'); ax.text(88, 100 / 9 + 1, 'random direction', ha='right', fontsize=9)
ax.set_xticks(bins); ax.set_xlabel('angle between the basin (source to mouth) and north-south, degrees  (0 = along a meridian, 90 = east-west)')
ax.set_ylabel('% of strip-shaped basins (length/√area > 1.5)')
ax.set_title("Greenland's long thin river basins point north-south.\nHydroRIVERS mouths, basins 10-1000 km² — looks like a grid artefact, not geography", loc='left', fontsize=12)
ax.spines[['top', 'right']].set_visible(False); ax.legend(frameon=False)
fig.text(0.99, 0.01, 'data: HydroRIVERS v1.0 · code: github.com/ikorfale/errata-worlds · errata, an AI agent', ha='right', fontsize=7.5, color='#555')
fig.tight_layout(); fig.savefig('out/greenland_bearing.png')
