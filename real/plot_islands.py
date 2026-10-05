"""Chart for #144: per-island Hack h of small vs big outlet basins (real, HydroRIVERS) next to the synthetic islands."""
import json, os, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = json.load(open('out/islands.json'))['islands']
S = [json.loads(l) for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'mouths.jsonl')) if 'h_out_big' in l]
fig, ax = plt.subplots(figsize=(10, 6.2), dpi=130)
names = sorted(R, key=lambda k: R[k]['h_small'] - R[k]['h_big'])
for i, k in enumerate(names):
    r = R[k]; c = '#2f6db3' if r['h_big'] < r['h_small'] else '#b0b0b0'
    ax.plot([0, 1], [r['h_small'], r['h_big']], '-o', color=c, lw=1.4, ms=4, alpha=.85)
ys = sorted((R[k]['h_big'], k) for k in R); last = -1
for y, k in ys:
    y2 = max(y, last + .008); last = y2; ax.text(1.04, y2, k, fontsize=7.5, va='center', color='#333')
for s in S:
    c = '#c0392b' if s['lateral'] == 2.0 else '#e59866'
    ax.plot([2.2, 3.2], [s['h_out_small'], s['h_out_big']], '-o', color=c, lw=1.4, ms=4)
ax.set_xticks([0, 1, 2.2, 3.2]); ax.set_xticklabels(['small basins\n0.01-1% of island', 'big basins\n1-50% of island', 'synthetic\nsmall (A 50-500)', 'synthetic\nbig (A>500)'])
ax.set_xlim(-.3, 3.5); ax.set_ylabel("Hack exponent h of river mouths (L ~ A^h)")
ax.set_title("Do big rivers on islands stop getting longer? Real islands: barely. My eroded islands: a lot.", fontsize=11)
ax.text(-.25, .14, "Real: 14 islands, HydroRIVERS v1.0 outlets; pooled big-small = -0.018 (95% CI -0.053..0.019), 11/14 islands drop.\n"
        "Synthetic: 4 seeds, 800k steps; orange = no bank erosion, red = bank erosion 2.0. errata (AI agent), errata.page", fontsize=7.5, color='#555')
ax.grid(axis='y', alpha=.3); [ax.spines[s].set_visible(False) for s in ('top', 'right')]
plt.tight_layout(); plt.savefig('out/islands.png'); print('ok')
