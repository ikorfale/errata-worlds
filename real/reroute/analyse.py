"""#161: h of river mouths (A 10-1e6 km2) and flow-step bearings by latitude band, for three routings of one DEM."""
import numpy as np, json, sys
sys.path.insert(0, '..'); from hack import fit
R = 6371000.0; rng = np.random.default_rng(1); out = {}
BANDS = ((60, 70), (70, 75), (75, 84), (0, 90))
for name, grid in (('geo_sq', 'geo'), ('geo_me', 'geo'), ('polar_me', 'polar')):
    M = json.load(open(f'{grid}.meta.json')); n, m = M['n'], M['m']
    z = np.fromfile(f'{grid}.f32', np.float32).reshape(n, m); land = np.isfinite(z).ravel()
    rec = np.fromfile(f'{name}.rec', np.int32); A = np.fromfile(f'{name}.A', np.float32); L = np.fromfile(f'{name}.L', np.float32)
    jj, ii = np.divmod(np.arange(n * m), m)
    if grid == 'geo':
        lat = M['lat0'] - (jj + 0.5) * M['cell_deg']; dx = R * np.radians(M['cell_deg']) * np.cos(np.radians(lat))
    else:
        X = M['x0'] + ii * M['S']; Y = M['y0'] - jj * M['S']; lat = 90 - 2 * np.degrees(np.arctan(np.hypot(X, Y) / (2 * R)))
    flow = land & (rec >= 0); c = np.flatnonzero(flow); t = rec[c]
    dj, di = t // m - c // m, t % m - c % m
    if grid == 'geo':
        e, nn = di * dx[c], -dj * M['dy']; ang = np.degrees(np.arctan2(np.abs(e), np.abs(nn)))   # 0 = along a meridian
    else:
        sx, sy = di * M['S'], -dj * M['S']; rx, ry = -X[c], -Y[c]; rr = np.hypot(rx, ry)
        cosang = np.abs(sx * rx + sy * ry) / (np.hypot(sx, sy) * rr); ang = np.degrees(np.arccos(np.clip(cosang, 0, 1)))
    o = np.flatnonzero(land & (rec < 0) & (A >= 10) & (A <= 1e6) & (L > 0))
    for lo, hi in BANDS:
        s = (lat[o] >= lo) & (lat[o] < hi); sb = (lat[c] >= lo) & (lat[c] < hi)
        r = fit(A[o][s].astype(float), L[o][s].astype(float), rng, 300) if s.sum() >= 30 else None
        mer, par = (ang[sb] < 20).mean() * 100, (ang[sb] > 70).mean() * 100
        key = f'{name} {lo}-{hi}N' if hi < 90 else f'{name} ALL'
        out[key] = {'h': r, 'meridian_pct': mer, 'parallel_pct': par}
        print(f'{key:22s} h {r["h"]:.3f} [{r["ci"][0]:.3f}, {r["ci"][1]:.3f}] n {r["n"]:5d} | flow steps along meridian {mer:4.1f}%  along parallel {par:4.1f}%' if r else key, flush=True)
json.dump(out, open('reroute.json', 'w'), default=float); print('__END__')
