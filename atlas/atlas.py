#!/usr/bin/env python3
"""Engraved map sheet of a Watershed world, drawn as plain SVG.

  atlas.py H.npy META.json OUT.svg

Relief by hachures (short strokes down the steepest slope, heavier where steeper), contours every
CONTOUR of relief, coastal waterlines in the sea, rivers from the game's own router with width by
drainage area, claimed basins outlined and named.
"""
import numpy as np, json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'watershed'), os.path.join(HERE, '..', 'worlds'), os.path.join(HERE, '..')]  # lab layout, repo layout
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

S = 4.0                    # px per cell
INK, PAPER, WATER = '#2a2622', '#f3eddc', '#2f5f7f'
INCISED = 0.004            # median depth below the 3-cell-blurred surface, as a share of relief, for a chain to count as a cut channel
RIVER_MIN = 60             # cells of drainage before a line is drawn

def blur(z, sig):
    k = np.exp(-0.5 * (np.arange(-3 * int(np.ceil(sig)), 3 * int(np.ceil(sig)) + 1) / sig) ** 2); k /= k.sum()
    p = len(k) // 2; z = np.pad(z, p, mode='edge')
    z = np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 0, z)
    return np.apply_along_axis(lambda v: np.convolve(v, k, 'valid'), 1, z)

def contour_paths(z, levels):
    fig = plt.figure(); cs = plt.contour(z, levels=levels); out = []
    for lev, segs in zip(cs.levels, cs.allsegs): out.append((lev, [s for s in segs if len(s) > 3]))
    plt.close(fig); return out

def poly(seg, ndig=1):
    return ' '.join(f'{(x + .5) * S:.{ndig}f},{(y + .5) * S:.{ndig}f}' for x, y in seg)

def smooth(seg, k=2):
    if len(seg) < 5: return seg
    s = np.asarray(seg); closed = np.allclose(s[0], s[-1])
    for _ in range(k):
        if closed: s = (np.roll(s, 1, 0) + 2 * s + np.roll(s, -1, 0)) / 4
        else: s[1:-1] = (s[:-2] + 2 * s[1:-1] + s[2:]) / 4
    return s

FORM = 48          # form lines (hachure rows) per island relief
ALONG = 1.45       # cells between strokes along a row
MAXLEN = 3.2       # cells; longer strokes mean flat ground, which is left white
GAP = 0.85         # share of the row height a stroke covers

def bilin(z, x, y):
    n, m = z.shape; x = np.clip(x, 0, m - 1.001); y = np.clip(y, 0, n - 1.001)
    i, j = y.astype(int), x.astype(int); fy, fx = y - i, x - j
    return (z[i, j] * (1 - fx) * (1 - fy) + z[i, j + 1] * fx * (1 - fy) + z[i + 1, j] * (1 - fx) * fy + z[i + 1, j + 1] * fx * fy)

def resample(seg, step, phase):
    seg = np.asarray(seg); d = np.r_[0, np.cumsum(np.hypot(*np.diff(seg, axis=0).T))]
    if d[-1] < step: return np.empty((0, 2))
    t = np.arange(phase * step, d[-1], step)
    return np.c_[np.interp(t, d, seg[:, 0]), np.interp(t, d, seg[:, 1])]

def hachures(h, land, near_river, relief):
    hb = blur(np.where(land, h, 0), 1.0); gy, gx = np.gradient(hb); dz = relief / FORM
    P, lev = [], []
    for i, (lv, segs) in enumerate(contour_paths(np.where(land, hb, -1), np.arange(dz, relief, dz))):
        for sg in segs:
            q = resample(sg, ALONG, 0.25 if i % 2 else 0.75)   # alternate rows are staggered, as an engraver would
            P.append(q); lev.append(np.full(len(q), lv))
    P = np.vstack(P); lo = np.concatenate(lev) - dz
    ok = ~near_river[np.clip(P[:, 1].round().astype(int), 0, h.shape[0] - 1), np.clip(P[:, 0].round().astype(int), 0, h.shape[1] - 1)]
    P, lo = P[ok], lo[ok]; E = P.copy(); live = np.ones(len(P), bool); L = np.zeros(len(P))
    for _ in range(int(MAXLEN / 0.2) + 2):
        ix = np.nonzero(live)[0]
        if not len(ix): break
        x, y = E[ix, 0], E[ix, 1]; g1, g2 = bilin(gx, x, y), bilin(gy, x, y); g = np.hypot(g1, g2) + 1e-12
        E[ix, 0] -= 0.2 * g1 / g; E[ix, 1] -= 0.2 * g2 / g; L[ix] += 0.2
        done = (bilin(hb, E[ix, 0], E[ix, 1]) <= lo[ix]) | (L[ix] > MAXLEN)
        live[ix[done]] = False
    keep = L <= MAXLEN
    E = P + GAP * (E - P)                     # stop short of the next form line: a thin white seam between rows
    slope = dz / np.maximum(L, 0.2)          # mean drop per cell along the stroke
    smax = np.percentile(slope[keep], 97)
    # north-west light: strokes on slopes facing south-east are heavier
    dx, dy = E[:, 0] - P[:, 0], E[:, 1] - P[:, 1]; face = (dx + dy) / (np.sqrt(2) * np.maximum(L, 1e-9))
    w = (0.25 + 1.25 * np.clip(slope / smax, 0, 1.1)) * (1 + 0.45 * face)
    hs = [f'<path d="M{(a + .5) * S:.1f} {(b + .5) * S:.1f}L{(c + .5) * S:.1f} {(d + .5) * S:.1f}" stroke-width="{ww:.2f}"/>'
          for (a, b), (c, d), ww, k in zip(P, E, w, keep) if k]
    print(f'hachures: {len(P)} starts on {FORM - 1} form lines, {len(hs)} drawn, {np.sum(~keep)} left white (flat)')
    return hs

def main(hp, mp, out):
    import tick as T
    h = np.load(hp); meta = json.load(open(mp)); N = h.shape[0]
    oc, r, order, A, L = T.route(h); land = ~oc & (h >= 0)
    relief = float(h[land].max()); W = H = N * S
    el = []
    el.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')
    # sea: waterlines following the coast, fading out to sea
    from scipy_free import dist_to
    d = dist_to(land)
    for k, dd in enumerate([1.5, 3.5, 6.5, 10.5, 15.5]):
        for _, segs in contour_paths(np.where(land, 0, d), [dd]):
            for s in segs: el.append(f'<polyline points="{poly(smooth(s))}" fill="none" stroke="{WATER}" stroke-width="{0.9 - 0.15 * k:.2f}" opacity="{0.85 - 0.14 * k:.2f}"/>')
    # contours on land
    step = relief / 10
    for i, (lev, segs) in enumerate(contour_paths(np.where(land, h, -1), np.arange(step, relief, step))):
        major = (i + 1) % 5 == 0
        for s in segs: el.append(f'<polyline points="{poly(smooth(s))}" fill="none" stroke="#8a6a4a" stroke-width="{0.7 if major else 0.35}" opacity="0.8"/>')
    # hachures, Lehmann style: rows between close form lines; each stroke starts on one form line and runs
    # down the steepest descent to the next, so steep ground gets short, dense, heavy strokes and flats stay white
    near_river = blur(((A >= RIVER_MIN) & land).astype(float), 0.8) > 0.12
    hs = hachures(h, land, near_river, relief)
    el.append(f'<g stroke="{INK}" stroke-linecap="round" fill="none" opacity="0.9">' + ''.join(hs) + '</g>')
    # coastline
    for _, segs in contour_paths(land.astype(float), [0.5]):
        for s in segs: el.append(f'<polyline points="{poly(smooth(s, 3))}" fill="none" stroke="{INK}" stroke-width="1.3"/>')
    # lakes: cells the router floods above the ground
    import rivers as RV
    filled, _, _ = RV.flood(h, ocean=oc); lake = land & (filled > h + 1e-4)
    for _, segs in contour_paths(lake.astype(float), [0.5]):
        for sg in segs:
            if len(sg) < 14: continue  # one- and two-cell pits are router artefacts, not lakes
            el.append(f'<polygon points="{poly(smooth(sg, 1))}" fill="#c9dbe3" stroke="{WATER}" stroke-width="0.8"/>')
    # rivers: chains from a head or confluence down to the next confluence or the sea, smoothed, width by sqrt(area)
    Af = A.ravel(); riv = (Af >= RIVER_MIN) & land.ravel()
    ndon = np.zeros(N * N, int)
    for c in np.nonzero(riv)[0]:
        if r[c] >= 0 and riv[r[c]]: ndon[r[c]] += 1
    inc = (blur(h, 3.0) - h).ravel()  # >0: the cell lies below its neighbourhood, i.e. a cut channel
    rv = []; ndash = 0
    for c in np.nonzero(riv & (ndon != 1))[0]:
        chain = [c]; t = r[c]
        while t >= 0:
            chain.append(t)
            if not riv[t] or ndon[t] != 1: break
            t = r[t]
        xy = np.array([[(k % N), (k // N)] for k in chain], float)
        for _ in range(3):  # Chaikin corner cutting, ends fixed
            if len(xy) < 3: break
            q = np.empty((2 * len(xy) - 2, 2)); q[0::2] = .75 * xy[:-1] + .25 * xy[1:]; q[1::2] = .25 * xy[:-1] + .75 * xy[1:]
            xy = np.vstack([xy[:1], q, xy[-1:]])
        w = 0.45 + 0.11 * np.sqrt(Af[chain[-2] if len(chain) > 1 else c] / RIVER_MIN)
        cut = np.median(inc[chain[:-1]]) > INCISED * relief
        ndash += not cut
        rv.append(f'<polyline points="{poly(xy)}" stroke-width="{min(w, 5) if cut else 0.6:.2f}"' + ('' if cut else ' stroke-dasharray="3 2.5"') + '/>')
    el.append(f'<g stroke="{WATER}" stroke-linecap="round" stroke-linejoin="round" fill="none">' + ''.join(rv) + '</g>')
    # claims: name at the mouth
    for n, c in meta.get('claims', {}).items():
        x, y = (c['x'] + .5) * S, (c['y'] + .5) * S
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke="{INK}" stroke-width="1"/>'
                  f'<text x="{x + 6:.1f}" y="{y - 5:.1f}" font-family="Georgia, serif" font-style="italic" font-size="13" fill="{INK}">{n}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}">' + ''.join(el) + '</svg>'
    open(out, 'w').write(svg); print(out, len(svg) // 1024, 'KB', len(hs), 'hachure strokes', len(rv), 'river chains', ndash, 'dashed (not incised)')

if __name__ == '__main__': main(*sys.argv[1:4])
