"""Chart for #161: same Greenland DEM, three routings, against HydroRIVERS."""
import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
r = json.load(open('reroute.json')); hl = json.load(open('../out/hlat.json'))
x = [0, 1, 2]; lab = ['60–70°N', '70–75°N', '75–84°N']; B = ['60-70N', '70-75N', '75-84N']
S = [('HydroRIVERS (HydroSHEDS routing)', '#eb6834', 'o', [hl[f'gr {b}']['h'] for b in B], None),
     ('my routing, lat/long grid, square cells', '#2a78d6', 's', [r[f'geo_sq {b}']['h']['h'] for b in B], [r[f'geo_sq {b}']['meridian_pct'] for b in B]),
     ('my routing, metric polar grid', '#1baf7a', '^', [r[f'polar_me {b}']['h']['h'] for b in B], [r[f'polar_me {b}']['meridian_pct'] for b in B])]
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False})
fig, ax = plt.subplots(1, 2, figsize=(12, 5.2), facecolor='#fcfcfb')
for a in ax: a.set_facecolor('#fcfcfb'); a.grid(axis='y', color='#e4e3dc', lw=0.8); a.set_xticks(x, lab); a.tick_params(colors='#55544e')
for name, c, m, h, mer in S:
    ax[0].plot(x, h, color=c, lw=2, marker=m, ms=8, label=name)
    ax[0].annotate(f'{h[-1]:.2f}', (2, h[-1]), xytext=(8, 0), textcoords='offset points', va='center', color='#2b2a26')
    if mer: ax[1].plot(x, mer, color=c, lw=2, marker=m, ms=8); ax[1].annotate(f'{mer[-1]:.0f}%', (2, mer[-1]), xytext=(8, 0), textcoords='offset points', va='center', color='#2b2a26')
ax[1].axhline(22.2, color='#8a8980', lw=1, ls='--'); ax[1].text(0, 24, 'random directions (22%)', color='#55544e', fontsize=10)
ax[0].set_title("Hack's exponent h of river mouths", loc='left', color='#2b2a26'); ax[0].set_ylim(0.2, 0.7)
ax[1].set_title('flow steps within 20° of a meridian', loc='left', color='#2b2a26'); ax[1].set_ylim(0, 100)
ax[0].legend(frameon=False, loc='lower left', fontsize=10)
fig.suptitle("Greenland: one elevation model, routed two ways. The north–south lean, and the fall of h toward the pole, come from the grid.", x=0.02, ha='left', color='#2b2a26', fontsize=13)
fig.text(0.02, 0.01, 'HydroSHEDS gr 15" DEM (HYDRO1k-based). Outlets ≥10 km². My absolute h levels are uncalibrated; compare routings, not levels. errata · github.com/ikorfale/errata-worlds', fontsize=9, color='#55544e')
fig.tight_layout(rect=(0, 0.04, 1, 0.94)); fig.savefig('greenland_reroute.png', dpi=110)
