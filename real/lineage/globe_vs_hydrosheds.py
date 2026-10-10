"""#227 (theone 82466): what is the lineage of the HydroSHEDS Greenland 15" DEM? Compare it cell by cell with GLOBE tile B
(NOAA, public), whose source/lineage map splits Greenland into DTED (2, 3), Zwally/NSIDC/JPL satellite altimetry (12),
an altimetry-DCW blend (13) and DCW contours (14). HydroSHEDS above 60N is exact 2x2 blocks of a 30" lattice, so each
30" GLOBE cell is compared with the top-left 15" cell of its block (after finding the lattice offset)."""
import numpy as np, tifffile, os, json
G = '../data/globe/'; N, R, C = 90.0, 4800, 10800; W = -90.0; d = 1 / 120
gz = np.memmap(G + 'b10g', '<i2', 'r', shape=(R, C)); gs = np.memmap(G + 'b10s', 'u1', 'r', shape=(R, C))
with tifffile.TiffFile('../data/dir/hyd_gr_dem_15s.tif') as t:
    p = t.pages[0]; tie = p.tags['ModelTiepointTag'].value; sc = p.tags['ModelPixelScaleTag'].value
    hz = t.asarray(out='memmap')
lon0, lat0, e = tie[3], tie[4], sc[0]; print('hydrosheds gr', hz.shape, 'lon0', lon0, 'lat0', lat0, 'step', e * 3600, 'arcsec', hz.dtype)
# GLOBE row/col of the hydrosheds origin
gr0 = (N - lat0) / d; gc0 = (lon0 - W) / d; print('origin in GLOBE cells', gr0, gc0)
res = {}
for off in [(0, 0), (0, 1), (1, 0), (1, 1)]:   # which 15" cell of each 2x2 block aligns best
    r0 = int(round(gr0)); c0 = int(round(gc0)); nr = min(hz.shape[0] // 2 - 1, R - r0); nc = min(hz.shape[1] // 2 - 1, C - c0)
    h = np.asarray(hz[off[0]:off[0] + 2 * nr:2, off[1]:off[1] + 2 * nc:2]).astype(np.int32)
    g = np.asarray(gz[r0:r0 + nr, c0:c0 + nc]).astype(np.int32); s = np.asarray(gs[r0:r0 + nr, c0:c0 + nc])
    out = {}
    for code in (2, 3, 12, 13, 14):
        m = (s == code) & (h > -1000) & (h < 10000) & (g > -500)
        if m.sum() < 100: continue
        dz = h[m] - g[m]
        out[code] = dict(n=int(m.sum()), exact=round(float((dz == 0).mean()), 4), within5=round(float((abs(dz) <= 5).mean()), 4),
                         med_abs=float(np.median(abs(dz))), mean=round(float(dz.mean()), 1))
    res[str(off)] = out; print(off, json.dumps(out), flush=True)
json.dump(res, open('globe_vs_hydrosheds.json', 'w'), indent=1)
