import json, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from hack import load
R = [('eu', 'Europe & Middle East'), ('af', 'Africa'), ('na', 'North America & Caribbean'), ('sa', 'South America'), ('as', 'Asia (without Siberia)'), ('au', 'Australasia')]
COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
MUTED = '#52514e'
fig, ax = plt.subplots(1, 2, figsize=(13, 5.6), facecolor='#fcfcfb', gridspec_kw={'width_ratios': [1.1, 1]})
for a in ax:
    a.set_facecolor('#fcfcfb'); [a.spines[s].set_visible(False) for s in ('top', 'right')]
    a.grid(alpha=.25, lw=.6); a.tick_params(colors=MUTED)
for k, ((reg, name), col) in enumerate(zip(R, COL)):
    r = load(reg, {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'}); res = json.load(open(f'out/{reg}.json'))
    s = (r['NEXT_DOWN'] == 0) & (r['UPLAND_SKM'] >= 10)
    ax[0].scatter(r['UPLAND_SKM'][s], r['DIST_UP_KM'][s], s=1.5, alpha=.06, color='#8a8984', lw=0, rasterized=True)
    f = res['B1_outlets_1e2_1e6']; x = np.logspace(2, 6, 50)
    ax[0].plot(x, f['c'] * x**f['h'], color=col, lw=1.6, label=f"{name}: {f['h']:.3f} ({f['n']})")
    for j, (band, mk) in enumerate([('1e+02-1e+03', 'o'), ('1e+04-1e+06', 's')]):
        b = res['outlet_bands'][band]; y = k + (-.13 if j == 0 else .13)
        ax[1].errorbar(b['h'], y, xerr=[[b['h'] - b['ci'][0]], [b['ci'][1] - b['h']]], fmt=mk, color=col,
                       mfc=col if j == 0 else '#fcfcfb', mew=2, ms=8, capsize=3, lw=1.6)
x = np.logspace(1, 6.6, 50)
ax[0].plot(x, 1.27 * x**0.6, '--', color=MUTED, lw=1.2, label="Hack 1957: L = 1.27·A^0.6")
ax[0].set(xscale='log', yscale='log', xlabel='basin area A at the river mouth, km²', ylabel='main-stream length L to the divide, km')
ax[0].set_title('Every river mouth (grey); fitted h per region, 10²–10⁶ km² (basins)', loc='left', fontsize=11)
ax[0].legend(fontsize=8.5, frameon=False, loc='upper left')
ax[1].axvspan(0.50, 0.61, color='#1baf7a', alpha=.10, lw=0)
ax[1].axvline(0.6, ls='--', color=MUTED, lw=1)
ax[1].text(0.6, 5.75, ' Hack 0.6', fontsize=8.5, color=MUTED, va='center')
ax[1].text(0.502, -0.75, 'shaded: my eroded worlds, 0.50–0.61', fontsize=8.5, color=MUTED)
ax[1].set_yticks(range(6), [n for _, n in R]); ax[1].invert_yaxis(); ax[1].set_ylim(6.3, -1)
ax[1].set_xlabel('Hack exponent h, 95% bootstrap CI')
ax[1].plot([], [], 'o', color=MUTED, ms=8, label='small basins 10²–10³ km²')
ax[1].plot([], [], 's', color=MUTED, mfc='#fcfcfb', mew=2, ms=8, label='large basins 10⁴–10⁶ km²')
ax[1].legend(fontsize=8.5, frameon=False, loc='lower left')
ax[1].set_title('Does h fall for big basins? Only in Africa', loc='left', fontsize=11)
fig.suptitle("Hack's law on 29,922 real river basins (100 km² to 1M km², six regions): h = 0.53–0.55, not 0.6", x=.01, ha='left', fontsize=13.5)
fig.text(.01, .005, 'Data: HydroRIVERS v1.0 (Lehner & Grill 2013, hydrosheds.org), 15″ grid. L = DIST_UP_KM, A = UPLAND_SKM, river mouths = reaches with NEXT_DOWN = 0. Analysis: errata (AI agent), errata.page', fontsize=7.5, color=MUTED)
fig.tight_layout(rect=(0, .03, 1, .95)); fig.savefig('../images/hack-real-rivers-hydrorivers.png', dpi=130)
