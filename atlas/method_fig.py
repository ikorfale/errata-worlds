"""Three panels on one window of the season-1 final island, from atlas.py's own functions:
(1) heights and the form lines, (2) one stroke per start, run down the steepest descent to the next form line,
(3) strokes weighted by slope and light, with rivers left white. Usage: method_fig.py OUT.png"""
import sys, os, numpy as np
sys.argv_save = sys.argv[:]; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path[:0] = [HERE]
import atlas as A, re
import matplotlib.pyplot as plt
W = os.path.join(HERE, '..', 'watershed', 'state'); h = np.load(f'{W}/h.npy')
import tick as T
oc, r, order, Ar, L = T.route(h); land = ~oc & (h >= 0); relief = float(h[land].max())
near = A.blur(((Ar >= A.RIVER_MIN) & land).astype(float), 0.8) > 0.12
hs = A.hachures(h, land, near, relief)
seg = np.array([[float(v) / A.S - .5 for v in re.findall(r'[-\d.]+', s.split('stroke-width')[0])[:4]] for s in hs])
wid = np.array([float(re.search(r'stroke-width="([\d.]+)"', s).group(1)) for s in hs])
x0, y0, n = 150, 60, 48  # window, cells
inw = (seg[:, 0] > x0) & (seg[:, 0] < x0 + n) & (seg[:, 1] > y0) & (seg[:, 1] < y0 + n)
hb = A.blur(np.where(land, h, 0), 1.0); dz = relief / A.FORM
fig, ax = plt.subplots(1, 3, figsize=(15, 5.4), facecolor='#f3eddc')
win = hb[y0:y0 + n, x0:x0 + n]
for k, a in enumerate(ax):
    a.set_facecolor('#f3eddc'); a.set_xlim(x0, x0 + n); a.set_ylim(y0 + n, y0); a.set_aspect('equal'); a.set_xticks([]); a.set_yticks([])
    for s in a.spines.values(): s.set_color('#2a2622')
ax[0].imshow(np.where(land, h, np.nan), cmap='Greys', extent=(-.5, h.shape[1] - .5, h.shape[0] - .5, -.5), alpha=.55)
for a in ax[:2]: a.contour(np.arange(h.shape[1]), np.arange(h.shape[0]), np.where(land, hb, -1), levels=np.arange(dz, relief, dz), colors='#8a6a4a', linewidths=.35)
ax[1].plot(seg[inw, 0], seg[inw, 1], '.', ms=2.5, color='#e4572e')
for (a_, b_, c_, d_) in seg[inw]: ax[1].plot([a_, c_], [b_, d_], color='#2a2622', lw=.7)
for (a_, b_, c_, d_), w in zip(seg[inw], wid[inw]): ax[2].plot([a_, c_], [b_, d_], color='#2a2622', lw=w * 0.55, solid_capstyle='round')
riv = (Ar >= A.RIVER_MIN) & land; ys, xs = np.nonzero(riv[y0:y0 + n, x0:x0 + n]); ax[2].plot(xs + x0, ys + y0, 's', ms=1.1, color='#2f5f7f', alpha=.7)
titles = [f'1. heights and {A.FORM - 1} form lines\n(contours a 1/{A.FORM} of the relief apart)', '2. a start every 1.45 cells on each line,\nrun down the steepest slope to the next line',
          '3. width by slope (and by light from the NW);\nlong strokes = flat, left white; rivers kept clear']
for a, t in zip(ax, titles): a.set_title(t, fontsize=11, family='serif', color='#2a2622', loc='left')
fig.suptitle(f'How the hachures are drawn: a {n}x{n}-cell window of the Watershed island after season 1 (real output of atlas.py)', family='serif', fontsize=12, color='#2a2622', x=0.01, ha='left')
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(sys.argv[1], dpi=110, facecolor=fig.get_facecolor()); print('window strokes', inw.sum())
