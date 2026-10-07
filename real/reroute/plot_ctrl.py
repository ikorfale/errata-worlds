"""Chart for #168: median E (main-stem length / sqrt(area)) of flat 10-50 km2 basins, ice-sheet surface vs flat land elsewhere."""
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
rows = [('Greenland, touches ice', 333, 6.30, None), ('Greenland, no ice', 173, 2.34, None),
        ('Baffin, no ice', 754, 2.23, (2.17, 2.27)), ('Iceland, no ice', 62, 2.35, (2.18, 2.62))]
fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150); fig.patch.set_facecolor('white')
for k, (nm, n, e, ci) in enumerate(rows[::-1]):
    c = '#c0392b' if 'touches' in nm else '#8c96a0'
    ax.barh(k, e, height=0.55, color=c, edgecolor='white', linewidth=2)
    if ci: ax.plot(ci, [k, k], color='#333', lw=1.5)
    ax.text(max(e, ci[1] if ci else e) + 0.1, k, f'{e:.2f}   n={n}', va='center', fontsize=10, color='#222')
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=10.5)
ax.set_xlim(0, 7.4); ax.set_xlabel('median elongation E = main-stem length / √area', fontsize=10, color='#444')
for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
ax.tick_params(axis='y', length=0); ax.grid(axis='x', color='#e6e6e6'); ax.set_axisbelow(True)
ax.set_title('Flat basins grow long only on the ice sheet', loc='left', fontsize=13, fontweight='bold')
fig.text(0.01, 0.01, '10-50 km² HydroRIVERS mouths, 60-70°N, three flattest slope bins (slope ≤ 0.058). Baffin\'s flattest no-ice basins are 5x flatter than\n'
         'Greenland\'s ice basins and still ordinary. Bars: HydroSHEDS routing; whiskers: 95% bootstrap CI. errata.page · github.com/ikorfale/errata-worlds',
         fontsize=7.5, color='#666')
plt.tight_layout(rect=(0, 0.07, 1, 1)); plt.savefig(__import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'out', 'ice-flat-controls.png')); print('ok')
