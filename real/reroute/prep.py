"""#161: two grids from the HydroSHEDS gr 15" DEM (integer metres, as HydroSHEDS used it).
 geo:   1' x 1' lat/long (4x4 block mean, rounded to whole metres), true dx = R cos(lat) dlon per row.
 polar: 1 km polar stereographic (north pole, lon0 -45), bilinear from the 15" grid, rounded to whole metres.
Writes <name>.f32, <name>.dx.f32, <name>.meta.json (n, m, dy, and per-row lat for geo / x0,y0 for polar)."""
import numpy as np, tifffile, os, json
R = 6371000.0; TMP = os.path.expanduser('~/.tmp'); ND = 32767
with tifffile.TiffFile('../data/dir/hyd_gr_dem_15s.tif') as t:
    tie = t.pages[0].tags['ModelTiepointTag'].value; d = t.pages[0].tags['ModelPixelScaleTag'].value[0]
    dem = t.asarray(out=os.path.join(TMP, 'gr_dem2.mm'))
lon0, lat0 = tie[3], tie[4]; n15, m15 = dem.shape
# geo 1'
n, m = n15 // 4, m15 // 4; g = np.full((n, m), np.nan, np.float32)
for a in range(0, n, 100):
    b = min(a + 100, n); blk = np.asarray(dem[4 * a:4 * b, :4 * m]).astype(np.float32).reshape(b - a, 4, m, 4)
    blk[blk == ND] = np.nan; g[a:b] = np.round(np.nanmean(blk, axis=(1, 3))) if True else 0
lat = lat0 - (np.arange(n) + 0.5) * 4 * d
g.tofile('geo.f32'); (R * np.radians(4 * d) * np.cos(np.radians(lat))).astype(np.float32).tofile('geo.dx.f32')
json.dump({'n': n, 'm': m, 'dy': R * np.radians(4 * d), 'lat0': lat0, 'lon0': lon0, 'cell_deg': 4 * d}, open('geo.meta.json', 'w'))
print('geo', n, m, int(np.isfinite(g).sum()), 'land cells', flush=True); del g
# polar 1 km: grid covering Greenland's land cells
def fwd(lat, lon):
    r = 2 * R * np.tan(np.pi / 4 - np.radians(lat) / 2); a = np.radians(lon + 45)
    return r * np.sin(a), -r * np.cos(a)
LA, LO = np.meshgrid(lat0 - (np.arange(0, n15, 40) + .5) * d, lon0 + (np.arange(0, m15, 40) + .5) * d, indexing='ij')
sub = np.asarray(dem[::40, ::40]) != ND; X, Y = fwd(LA[sub], LO[sub])
x0, x1, y0, y1 = X.min() - 20e3, X.max() + 20e3, Y.min() - 20e3, Y.max() + 20e3; S = 1000.0
xs = np.arange(x0, x1, S); ys = np.arange(y1, y0, -S); P = np.full((len(ys), len(xs)), np.nan, np.float32)
for r0 in range(0, len(ys), 100):
    yy, xx = np.meshgrid(ys[r0:r0 + 100], xs, indexing='ij'); rho = np.hypot(xx, yy)
    la = 90 - 2 * np.degrees(np.arctan(rho / (2 * R))); lo = -45 + np.degrees(np.arctan2(xx, -yy))
    fi = (lat0 - la) / d - 0.5; fj = (lo - lon0) / d - 0.5
    i0 = np.floor(fi).astype(int); j0 = np.floor(fj).astype(int); wi = fi - i0; wj = fj - j0
    ok = (i0 >= 0) & (j0 >= 0) & (i0 < n15 - 1) & (j0 < m15 - 1)
    v = np.full(la.shape, np.nan, np.float32); I, J = i0[ok], j0[ok]
    q = [np.asarray(dem[I + a, J + b], np.float32) for a in (0, 1) for b in (0, 1)]
    if any(len(x) for x in q):
        q = [np.where(x == ND, np.nan, x) for x in q]; a_, b_ = wi[ok], wj[ok]
        v[ok] = (q[0] * (1 - a_) * (1 - b_) + q[1] * (1 - a_) * b_ + q[2] * a_ * (1 - b_) + q[3] * a_ * b_)
    P[r0:r0 + 100] = np.round(v)
P.tofile('polar.f32'); np.full(len(ys), S, np.float32).tofile('polar.dx.f32')
json.dump({'n': len(ys), 'm': len(xs), 'dy': S, 'x0': float(xs[0]), 'y0': float(ys[0]), 'S': S}, open('polar.meta.json', 'w'))
print('polar', len(ys), len(xs), int(np.isfinite(P).sum()), 'land cells', flush=True)
os.remove(os.path.join(TMP, 'gr_dem2.mm')); print('__END__')
