"""#162(a) follow-up: h by latitude band and minimum mouth area, 1 km vs 500 m polar runs (outlets only, lean)."""
import numpy as np, json, sys
sys.path.insert(0, '..'); from hack import fit
R = 6371000.0; rng = np.random.default_rng(1); out = {}
for grid, name in (('polar', 'polar_me'), ('polar500', 'polar500_me')):
    M = json.load(open(f'{grid}.meta.json')); m = M['m']
    rec = np.fromfile(f'{name}.rec', np.int32); A = np.fromfile(f'{name}.A', np.float32); L = np.fromfile(f'{name}.L', np.float32)
    o = np.flatnonzero((rec < 0) & (A >= 10) & (A <= 1e6) & (L > 0)); A, L = A[o].astype(float), L[o].astype(float); del rec
    j, i = np.divmod(o, m); X = M['x0'] + i * M['S']; Y = M['y0'] - j * M['S']
    lat = 90 - 2 * np.degrees(np.arctan(np.hypot(X, Y) / (2 * R)))
    for amin in (10, 30, 100, 300):
        for lo, hi in ((60, 70), (70, 75), (75, 84), (0, 90)):
            s = (lat >= lo) & (lat < hi) & (A >= amin)
            r = fit(A[s], L[s], rng, 300) if s.sum() >= 30 else None
            key = f'{name} A>={amin} {lo}-{hi}'; out[key] = r
            print(f'{key:30s}', f'h {r["h"]:.3f} [{r["ci"][0]:.3f}, {r["ci"][1]:.3f}] c {r["c"]:.2f} n {r["n"]}' if r else 'n<30', flush=True)
json.dump(out, open('athresh.json', 'w'), default=float); print('__END__')
