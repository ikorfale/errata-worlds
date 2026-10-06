"""#162(a): analyse.py for one polar run, memory-lean (lat/angle only for the cells needed). usage: analyse500.py grid run out.json"""
import numpy as np, json, sys
sys.path.insert(0, '..'); from hack import fit
R = 6371000.0; rng = np.random.default_rng(1); out = {}; grid, name, outf = sys.argv[1:4]
BANDS = ((60, 70), (70, 75), (75, 84), (0, 90))
M = json.load(open(f'{grid}.meta.json')); n, m = M['n'], M['m']
land = np.isfinite(np.fromfile(f'{grid}.f32', np.float32))
rec = np.fromfile(f'{name}.rec', np.int32); A = np.fromfile(f'{name}.A', np.float32); L = np.fromfile(f'{name}.L', np.float32)
def xy(idx):
    j, i = np.divmod(idx, m); return M['x0'] + i * M['S'], M['y0'] - j * M['S']
def latof(X, Y): return 90 - 2 * np.degrees(np.arctan(np.hypot(X, Y) / (2 * R)))
c = np.flatnonzero(land & (rec >= 0)); t = rec[c].astype(np.int64)
dj, di = t // m - c // m, t % m - c % m; X, Y = xy(c); latc = latof(X, Y).astype(np.float32)
sx, sy = di * M['S'], -dj * M['S']; cosang = np.abs(sx * -X + sy * -Y) / (np.hypot(sx, sy) * np.hypot(X, Y))
ang = np.degrees(np.arccos(np.clip(cosang, 0, 1))).astype(np.float32); del X, Y, sx, sy, cosang, t, dj, di
o = np.flatnonzero(land & (rec < 0) & (A >= 10) & (A <= 1e6) & (L > 0)); lato = latof(*xy(o))
for lo, hi in BANDS:
    s = (lato >= lo) & (lato < hi); sb = (latc >= lo) & (latc < hi)
    r = fit(A[o][s].astype(float), L[o][s].astype(float), rng, 300) if s.sum() >= 30 else None
    mer, par = (ang[sb] < 20).mean() * 100, (ang[sb] > 70).mean() * 100
    key = f'{name} {lo}-{hi}N' if hi < 90 else f'{name} ALL'
    out[key] = {'h': r, 'meridian_pct': mer, 'parallel_pct': par}
    print(f'{key:22s} h {r["h"]:.3f} [{r["ci"][0]:.3f}, {r["ci"][1]:.3f}] n {r["n"]:5d} | flow steps along meridian {mer:4.1f}%  along parallel {par:4.1f}%' if r else key, flush=True)
json.dump(out, open(outf, 'w'), default=float); print('__END__')
