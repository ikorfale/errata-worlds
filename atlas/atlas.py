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

def sheet(body, W, H, N, meta, claimed):
    """the map inside a margin: double neatline with cell ticks, north arrow, title block, legend and scale bar below"""
    M, B = 56, 190; SW, SH = W + 2 * M, H + M + B
    f = 'font-family="Georgia, serif" fill="' + INK + '"'
    o = [f'<rect width="{SW}" height="{SH}" fill="{PAPER}"/>', f'<g transform="translate({M},{M})">{body}</g>',
         f'<rect x="{M}" y="{M}" width="{W}" height="{H}" fill="none" stroke="{INK}" stroke-width="0.8"/>',
         f'<rect x="{M - 7}" y="{M - 7}" width="{W + 14}" height="{H + 14}" fill="none" stroke="{INK}" stroke-width="2.2"/>']
    for k in range(0, N + 1, 32):  # cell coordinates as players give them, x along the top, y down the left
        p = k * S
        o.append(f'<line x1="{M + p}" y1="{M - 7}" x2="{M + p}" y2="{M - 13}" stroke="{INK}"/><text x="{M + p}" y="{M - 17}" text-anchor="middle" font-size="9" {f}>{k}</text>')
        o.append(f'<line x1="{M - 7}" y1="{M + p}" x2="{M - 13}" y2="{M + p}" stroke="{INK}"/><text x="{M - 16}" y="{M + p + 3}" text-anchor="end" font-size="9" {f}>{k}</text>')
    ax, ay = M + W - 34, M + 40  # north arrow, half-filled needle
    o.append(f'<path d="M{ax},{ay - 26} L{ax + 7},{ay + 8} L{ax},{ay + 2} Z" fill="{INK}"/><path d="M{ax},{ay - 26} L{ax - 7},{ay + 8} L{ax},{ay + 2} Z" fill="{PAPER}" stroke="{INK}" stroke-width="0.8"/>'
             f'<text x="{ax}" y="{ay - 31}" text-anchor="middle" font-size="12" {f}>N</text>')
    y0 = M + H + 24
    tick = meta.get('tick', 0)
    o.append(f'<text x="{M}" y="{y0 + 30}" font-size="30" letter-spacing="7" {f}>THE WATERSHED ISLAND</text>'
             f'<text x="{M}" y="{y0 + 54}" font-size="13" font-style="italic" {f}>the world of the game Watershed after {tick} ticks of rain, drawn from its own heights and river router</text>'
             f'<text x="{M}" y="{y0 + 74}" font-size="11" {f}>' + ' · '.join(f'{n}: {a} cells' + (f', claimed at tick {sn}' if sn else '') for n, a, sn in claimed) + '</text>'
             f'<text x="{M}" y="{y0 + 150}" font-size="10" font-style="italic" {f}>Drawn by code (atlas.py, errata-worlds) by errata, an AI agent · errata.page · relief in hachures after Lehmann, contours every tenth of the relief</text>')
    lx, ly = M + W - 330, y0 + 4  # legend
    rows = [(f'<line x1="0" y1="0" x2="26" y2="0" stroke="{WATER}" stroke-width="2.4" stroke-linecap="round"/>', 'river in a cut channel, width by drainage'),
            (f'<line x1="0" y1="0" x2="26" y2="0" stroke="{WATER}" stroke-width="0.6" stroke-dasharray="3 2.5"/>', 'stream without a fixed bed'),
            (f'<rect x="2" y="-5" width="22" height="10" fill="#c9dbe3" stroke="{WATER}" stroke-width="0.8"/>', 'lake'),
            (f'<line x1="0" y1="0" x2="26" y2="0" stroke="#8a6a4a" stroke-width="0.7"/>', 'contour, every fifth heavier'),
            ('<g stroke="' + INK + '" stroke-width="1.1">' + ''.join(f'<line x1="{3 + 4 * i}" y1="-5" x2="{3 + 4 * i}" y2="5"/>' for i in range(6)) + '</g>', 'hachures: denser and heavier = steeper'),
            (f'<rect x="2" y="-5" width="22" height="10" fill="#e4572e" fill-opacity="0.10" stroke="{INK}" stroke-width="0.9" stroke-dasharray="7 2.5 1.2 2.5"/>', 'claimed basin, mouth circled')]
    for i, (sym, txt) in enumerate(rows):
        o.append(f'<g transform="translate({lx},{ly + 18 * i})">{sym}<text x="36" y="4" font-size="11" {f}>{txt}</text></g>')
    sx, sy = M, y0 + 112  # scale bar in cells, alternating blocks
    for i in range(4):
        o.append(f'<rect x="{sx + i * 16 * S}" y="{sy}" width="{16 * S}" height="5" fill="{INK if i % 2 == 0 else PAPER}" stroke="{INK}" stroke-width="0.8"/>'
                 f'<text x="{sx + i * 16 * S}" y="{sy - 4}" text-anchor="middle" font-size="9" {f}>{16 * i}</text>')
    o.append(f'<text x="{sx + 64 * S}" y="{sy - 4}" text-anchor="middle" font-size="9" {f}>64 cells</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SW:.0f} {SH:.0f}" width="{SW:.0f}" height="{SH:.0f}">' + ''.join(o) + '</svg>'

def main(hp, mp, out):
    import tick as T
    h = np.load(hp); meta = json.load(open(mp)); N = h.shape[0]
    oc, r, order, A, L = T.route(h); land = ~oc & (h >= 0)
    relief = float(h[land].max()); W = H = N * S
    el = []; claimed = []
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
    # claimed basins: the claim's disc and every cell that drains into it (the game's scoring rule), outlined with the old dash-dot boundary sign
    own = T.owners(r, order, meta.get('claims', {})).reshape(N, N)  # the game's own rule: the claim's disc and all that drains into it
    for i, (n, c) in enumerate(meta.get('claims', {}).items()):
        b = (own == i) & land
        ys, xs = np.nonzero(b)
        for _, segs in contour_paths(b.astype(float), [0.5]):
            for sg in segs:
                el.append(f'<polygon points="{poly(smooth(sg, 1))}" fill="{c.get("color", INK)}" fill-opacity="0.10" stroke="{INK}" stroke-width="0.9" stroke-dasharray="7 2.5 1.2 2.5"/>')
        x, y = (c['x'] + .5) * S, (c['y'] + .5) * S
        el.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke="{INK}" stroke-width="1"/>')
        # name in spaced capitals at the basin's centre of mass, or beside the mouth if the basin is small
        big = b.sum() >= 150
        left = x > 0.7 * W  # near the east edge the label goes on the west side of the mouth
        tx, ty = ((xs.mean() + .5) * S, (ys.mean() + .5) * S) if big else ((x - 8, y - 6) if left else (x + 8, y - 6))
        anc = 'middle' if big else ('end' if left else 'start')
        el.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anc}" font-family="Georgia, serif" font-size="11" letter-spacing="2.5" fill="{INK}" stroke="{PAPER}" stroke-width="3" paint-order="stroke">{n.upper()}</text>'
                  f'<text x="{tx:.1f}" y="{ty + 12:.1f}" text-anchor="{anc}" font-family="Georgia, serif" font-style="italic" font-size="9" fill="{INK}" stroke="{PAPER}" stroke-width="3" paint-order="stroke">basin, {int(b.sum())} cells</text>')
        claimed.append((n, int(b.sum()), c.get('since')))
    svg = sheet(''.join(el), W, H, N, meta, claimed)
    open(out, 'w').write(svg); print(out, len(svg) // 1024, 'KB', len(hs), 'hachure strokes', len(rv), 'river chains', ndash, 'dashed (not incised)')

if __name__ == '__main__': main(*sys.argv[1:4])
