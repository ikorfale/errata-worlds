"""Chart for elong.py: median straight source-to-mouth distance D by area bin, four regions on the same HYDRO1k-era grid."""
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 5.2), dpi=150)
bins = np.logspace(1, 3, 9); c = (bins[1:] * bins[:-1]) ** .5
for name, col in [('Greenland', '#c0392b'), ('Baffin', '#2c7fb8'), ('Ellesmere', '#7b6fb0'), ('Iceland', '#4d9a5b')]:
    a = np.load(f'out/elong_{name}.npy'); A, D = a[:, 0], a[:, 1]
    m = [np.median(D[(A >= lo) & (A < hi)]) if ((A >= lo) & (A < hi)).sum() >= 15 else np.nan for lo, hi in zip(bins[:-1], bins[1:])]
    b = np.polyfit(np.log10(A), np.log10(D), 1)[0]
    ax.plot(c, m, 'o-', color=col, lw=2, label=f'{name}  (slope {b:.2f}, n={len(A)})')
ax.plot(c, 1.0 * c ** .5, '--', color='#999', lw=1, label='D = √A (a round basin)')
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('basin area A, km²'); ax.set_ylabel('median straight source-to-mouth distance D, km')
ax.set_title("Greenland's small basins are long strips that widen, not lengthen", fontsize=11)
ax.legend(frameon=False, fontsize=8.5); ax.grid(alpha=.25, which='both')
fig.text(0.01, 0.01, 'HydroRIVERS v1.0 river mouths, A 10–1000 km²; errata (AI agent), lab/hack/elong.py', fontsize=7, color='#777')
fig.tight_layout(); fig.savefig('out/greenland_strips.png')
