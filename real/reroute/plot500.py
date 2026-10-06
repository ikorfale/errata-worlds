"""#162: h by latitude band at mouths A >= 100 km2: my metric routing (1 km, 500 m), HydroRIVERS Greenland, HydroRIVERS Arctic Canada."""
import json, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
a = json.load(open('athresh.json')); hr = json.load(open('../out/hlat_amin.json'))
B = ['60-70', '70-75', '75-84']; x = range(3)
S = [('my metric routing, 500 m', [a[f'polar500_me A>=100 {b}'] for b in B], '#1f6f8b', 'o'),
     ('my metric routing, 1 km', [a[f'polar_me A>=100 {b}'] for b in B], '#7fb3c8', 's'),
     ('HydroRIVERS, Arctic Canada', [hr[f'ar A>=100 {b}N'] for b in B], '#5a8f3a', '^'),
     ('HydroRIVERS, Greenland', [hr[f'gr A>=100 {b}N'] for b in B], '#b5432f', 'D')]
fig, ax = plt.subplots(figsize=(8, 5), dpi=130)
for k, (lab, rs, col, mk) in enumerate(S):
    xs = [i + (k - 1.5) * 0.08 for i in x]; h = [r['h'] for r in rs]
    ax.errorbar(xs, h, yerr=[[r['h'] - r['ci'][0] for r in rs], [r['ci'][1] - r['h'] for r in rs]], color=col, marker=mk, lw=1.6, capsize=3, label=lab)
ax.set_xticks(list(x)); ax.set_xticklabels([f'{b}°N' for b in B]); ax.set_ylabel("Hack's exponent h (mouths ≥ 100 km²)")
ax.set_title("Greenland: a mild fall of h toward the pole is real; the deep one is routing", fontsize=11)
ax.grid(alpha=.3); ax.legend(frameon=False, fontsize=9); ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout(); fig.savefig('../../images/greenland-amin100.png'); print('__END__')
