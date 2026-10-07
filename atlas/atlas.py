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
RIVER_MIN = 60             # cells of drainage before a line is drawn

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
    # hachures
    gy, gx = np.gradient(h); slope = np.hypot(gx, gy)
    smax = np.percentile(slope[land], 98)
    rng = np.random.default_rng(7); sp = 1.9
    light = np.clip((gx + gy) / (np.sqrt(2) * smax), -1, 1)  # >0: facing south-east, away from a NW light
    pts = np.mgrid[0:N:sp, 0:N:sp].reshape(2, -1).T + rng.uniform(-.5, .5, (int(np.ceil(N / sp)) ** 2, 2))
    hs = []
    for y, x in pts:
        iy, ix = int(round(y)), int(round(x))
        if not (0 <= iy < N and 0 <= ix < N) or not land[iy, ix]: continue
        s = slope[iy, ix] / smax
        if s < 0.10: continue
        ux, uy = -gx[iy, ix] / slope[iy, ix], -gy[iy, ix] / slope[iy, ix]
        ln = 1.7
        x0, y0, x1, y1 = (x - ux * ln / 2 + .5) * S, (y - uy * ln / 2 + .5) * S, (x + ux * ln / 2 + .5) * S, (y + uy * ln / 2 + .5) * S
        hs.append(f'<path d="M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}" stroke-width="{(0.25 + 1.1 * min(s, 1.2)) * (1 + 0.6 * light[iy, ix]):.2f}"/>')
    el.append(f'<g stroke="{INK}" stroke-linecap="round" opacity="0.85">' + ''.join(hs) + '</g>')
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
    rv = []
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
        rv.append(f'<polyline points="{poly(xy)}" stroke-width="{min(w, 5):.2f}"/>')
    el.append(f'<g stroke="{WATER}" stroke-linecap="round" stroke-linejoin="round" fill="none">' + ''.join(rv) + '</g>')
    # claims: name at the mouth
    for n, c in meta.get('claims', {}).items():
        x, y = (c['x'] + .5) * S, (c['y'] + .5) * S
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke="{INK}" stroke-width="1"/>'
                  f'<text x="{x + 6:.1f}" y="{y - 5:.1f}" font-family="Georgia, serif" font-style="italic" font-size="13" fill="{INK}">{n}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}">' + ''.join(el) + '</svg>'
    open(out, 'w').write(svg); print(out, len(svg) // 1024, 'KB', len(hs), 'hachures', len(rv), 'river segments')

if __name__ == '__main__': main(*sys.argv[1:4])
