"""#161 step 1: where does Greenland's north-south lean come from? On the HydroSHEDS gr 15" DEM, by latitude band:
 (a) terrain: true gradient direction at the DEM's native ~1 km scale (E-W difference over ~1 km of columns, N-S over 2 rows);
     share within 20 deg of a meridian vs within 20 deg of a parallel (isotropic terrain: 22% each);
 (b) D8 on the raw DEM as if cells were square: N+S codes / E+W codes;
 (c) D8 with true metric distances (E-W step 463*cos(lat) m): same ratio, and the share of flat cells (no lower neighbour);
 (d) HydroSHEDS's own D8 codes on the same cells.
Low memory: memmaps, 200-row chunks."""
import numpy as np, tifffile, os
TMP = os.path.expanduser('~/.tmp'); ND = 32767
def mm(p, name):
    with tifffile.TiffFile(p) as t:
        tie = t.pages[0].tags['ModelTiepointTag'].value; sc = t.pages[0].tags['ModelPixelScaleTag'].value
        return t.asarray(out=os.path.join(TMP, name)), tie[4], sc[1]
dem, lat0, d = mm('data/dir/hyd_gr_dem_15s.tif', 'gr_dem.mm'); dr, _, _ = mm('data/dir/hyd_gr_dir_15s.tif', 'gr_dir.mm')
DY = 6371000 * np.radians(d)          # m per row
# D8 neighbours (dj, di) and ESRI codes
NB = [(0, 1, 1), (1, 1, 2), (1, 0, 4), (1, -1, 8), (0, -1, 16), (-1, -1, 32), (-1, 0, 64), (-1, 1, 128)]
NS, EW = {4, 64}, {1, 16}
for lo, hi in ((60, 65), (65, 70), (70, 75), (75, 80), (80, 84)):
    r0, r1 = max(1, int(round((lat0 - hi) / d))), min(dem.shape[0] - 1, int(round((lat0 - lo) / d)))
    acc = dict(gn=0, ge=0, gt=0, sq=np.zeros(256), me=np.zeros(256), hs=np.zeros(256), flat=0, land=0)
    for a in range(r0, r1, 200):
        b = min(a + 200, r1)
        Z = np.asarray(dem[a - 1:b + 1]).astype(np.float32); Z[Z == ND] = np.nan
        lat = lat0 - (np.arange(a, b) + 0.5) * d; coslat = np.cos(np.radians(lat))[:, None]
        z = Z[1:-1, 1:-1]; ok = ~np.isnan(z)
        # (b),(c): drops to the 8 neighbours
        best_sq = np.full(z.shape, 0.0, np.float32); code_sq = np.zeros(z.shape, np.uint8)
        best_me = np.full(z.shape, 0.0, np.float32); code_me = np.zeros(z.shape, np.uint8)
        for dj, di, c in NB:
            nb = Z[1 + dj:Z.shape[0] - 1 + dj, 1 + di:Z.shape[1] - 1 + di]
            drop = np.nan_to_num(z - nb, nan=-1e9)
            sq = drop / (1.0 if dj == 0 or di == 0 else np.sqrt(2))
            me = drop / np.sqrt((dj * DY) ** 2 + (di * DY * coslat) ** 2)
            m = sq > best_sq; best_sq[m] = sq[m]; code_sq[m] = c
            m = me > best_me; best_me[m] = me[m]; code_me[m] = c
        hs = np.asarray(dr[a:b, 1:-1])
        sel = ok & (hs >= 1) & (hs <= 128)
        acc['land'] += sel.sum(); acc['flat'] += (sel & (code_me == 0)).sum()
        acc['sq'] += np.bincount(code_sq[sel & (code_sq > 0)], minlength=256)
        acc['me'] += np.bincount(code_me[sel & (code_me > 0)], minlength=256)
        acc['hs'] += np.bincount(hs[sel], minlength=256)
        # (a) terrain gradient at ~1 km: E-W over k columns each side, k = round(500 / (463 cos lat))
        for row in range(z.shape[0]):
            k = max(1, int(round(500 / (DY * coslat[row, 0])))); zr = Z[row + 1]
            if zr.size <= 2 * k + 2: continue
            gx = (zr[2 * k:] - zr[:-2 * k]) / (2 * k * DY * coslat[row, 0])
            up = Z[row]; dn = Z[row + 2]
            gy = (up[k:-k] - dn[k:-k]) / (2 * DY)
            g = ~np.isnan(gx) & ~np.isnan(gy) & ((gx != 0) | (gy != 0))
            ang = np.degrees(np.arctan2(np.abs(gx[g]), np.abs(gy[g])))   # 0 = gradient along a meridian
            acc['gn'] += (ang < 20).sum(); acc['ge'] += (ang > 70).sum(); acc['gt'] += g.sum()
    rat = lambda h: (h[4] + h[64]) / max(1, h[1] + h[16])
    print(f'{lo}-{hi}N land {acc["land"]:>10,} | terrain grad: N-S {acc["gn"]/acc["gt"]*100:4.1f}% E-W {acc["ge"]/acc["gt"]*100:4.1f}% '
          f'| NS:EW square D8 {rat(acc["sq"]):5.2f}  metric D8 {rat(acc["me"]):5.2f} (flat {acc["flat"]/acc["land"]*100:4.1f}%)  HydroSHEDS {rat(acc["hs"]):5.2f}', flush=True)
for n in ('gr_dem.mm', 'gr_dir.mm'): os.remove(os.path.join(TMP, n))
print('__END__')
