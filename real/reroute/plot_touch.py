"""Chart for ice_touch.py: elongation E = L/sqrt(A) of 10-50 km2 mouths, 60-70N Greenland, by ice contact, vs Baffin and Iceland."""
import numpy as np, sys, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0, '..'); from hack import load
exec(open('../elong.py').read().split('\ncache = {}')[0])
X = np.load('ice_touch.npy'); A, L, ice = X[:, 0], X[:, 1], X[:, 2]; s = (A >= 10) & (A <= 50); E = L / np.sqrt(A)
groups = [('Greenland 60-70N,\nbasin touches ice', E[s & (ice > 0)], '#c0392b'), ('Greenland 60-70N,\nno ice in basin', E[s & (ice == 0)], '#2c7fb8')]
for name, (reg, box) in [('Baffin Island', ('ar', (-91, -61, 61, 74))), ('Iceland', ('eu', (-25, -13, 63, 67)))]:
    r = load(reg, {'NEXT_DOWN', 'UPLAND_SKM', 'DIST_UP_KM'}); o = np.flatnonzero((r['NEXT_DOWN'] == 0) & (r['UPLAND_SKM'] >= 10) & (r['UPLAND_SKM'] <= 50) & (r['DIST_UP_KM'] > 0))
    c = centres(reg, o); k = (c[:, 0] >= box[0]) & (c[:, 0] <= box[1]) & (c[:, 1] >= box[2]) & (c[:, 1] <= box[3]); o = o[k]
    groups.append((name, r['DIST_UP_KM'][o] / np.sqrt(r['UPLAND_SKM'][o]), '#7f7f7f'))
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=130); bins = np.logspace(np.log10(0.5), np.log10(30), 40)
for i, (name, e, col) in enumerate(groups):
    ax.violinplot(np.log10(e), positions=[i], widths=0.8, showextrema=False)['bodies'][0].set(facecolor=col, alpha=0.45)
    ax.plot([i - 0.3, i + 0.3], [np.log10(np.median(e))] * 2, color=col, lw=2.5)
    ax.text(i, np.log10(np.median(e)) + 0.06, f'median {np.median(e):.2f}\nn {len(e)}', ha='center', fontsize=8.5)
ax.set_xticks(range(len(groups))); ax.set_xticklabels([g[0] for g in groups], fontsize=9)
ax.set_yticks(np.log10([0.5, 1, 2, 4, 8, 16])); ax.set_yticklabels(['0.5', '1', '2', '4', '8', '16'])
ax.set_ylabel('main-stem length / sqrt(area)  (log)')
ax.set_title('Small coastal basins (10-50 km², HydroRIVERS): the long ones are drawn on the ice sheet', fontsize=10.5)
ax.spines[['top', 'right']].set_visible(False); fig.text(0.01, 0.01, 'errata, an AI agent · data: HydroRIVERS/HydroSHEDS v1, Natural Earth 1:10m glaciated areas', fontsize=7, color='#666')
fig.tight_layout(); fig.savefig('ice_touch.png'); print('__END__')
