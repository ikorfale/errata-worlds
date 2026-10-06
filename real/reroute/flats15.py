"""zenith 75539, done properly: flat share from the RAW 15" DEM (no strictly lower 8-neighbour, whole metres, sea = lower),
counted inside each 1' cell (4x4 block) and summed over each mouth basin of the geo_me routing.
Split at the band median; also with an area floor (A >= 50 km2) and a joint fit log L = a + h log A + b*share."""
import numpy as np, json, sys, os, tifffile, warnings
warnings.simplefilter('ignore')
sys.path.insert(0, '..'); from hack import fit
from calib import roots
TMP = os.path.expanduser('~/.tmp'); ND = 32767
M = json.load(open('geo.meta.json')); n, m = M['n'], M['m']
with tifffile.TiffFile('../data/dir/hyd_gr_dem_15s.tif') as t: dem = t.asarray(out=os.path.join(TMP, 'gr15.mm'))
FL = np.zeros((n, m), np.int16); LD = np.zeros((n, m), np.int16)
for a in range(0, n, 100):
    b = min(a + 100, n); r0, r1 = 4 * a, 4 * b
    h0, h1 = max(r0 - 1, 0), min(r1 + 1, dem.shape[0])
    z = np.asarray(dem[h0:h1, :4 * m]).astype(np.float32); land = z != ND; z[~land] = -1e9
    P = np.pad(z, 1, constant_values=np.inf)               # core = P[1:-1, 1:-1] is z; halo rows of z are discarded below
    core = P[1:-1, 1:-1]; lower = np.zeros(core.shape, bool)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            if dj or di: lower |= P[1 + dj:P.shape[0] - 1 + dj, 1 + di:P.shape[1] - 1 + di] < core
    s = r0 - h0; core_land = land[s:s + r1 - r0]; fl = core_land & ~lower[s:s + r1 - r0]
    FL[a:b] = fl.reshape(b - a, 4, m, 4).sum(axis=(1, 3)); LD[a:b] = core_land.reshape(b - a, 4, m, 4).sum(axis=(1, 3))
del dem; os.remove(os.path.join(TMP, 'gr15.mm'))
z1 = np.fromfile('geo.f32', np.float32); landr = np.isfinite(z1)
rec = np.fromfile('geo_me.rec', np.int32); A = np.fromfile('geo_me.A', np.float32); L = np.fromfile('geo_me.L', np.float32)
rt = roots(rec); idx = rt[landr]
fl = np.bincount(idx, FL.ravel()[landr], minlength=n * m); ld = np.bincount(idx, LD.ravel()[landr], minlength=n * m)
lat = M['lat0'] - (np.arange(n * m) // m + 0.5) * M['cell_deg']
o = np.flatnonzero(landr & (rec < 0) & (A >= 10) & (A <= 1e6) & (L > 0)); share = fl[o] / np.maximum(ld[o], 1)
rng = np.random.default_rng(1); out = {}
print(f'15" land flat share overall {FL.sum() / LD.sum():.3f}')
for lo, hi in ((60, 70), (70, 75), (75, 84)):
    for amin in (10, 50):
        s = (lat[o] >= lo) & (lat[o] < hi) & (A[o] >= amin); med = np.median(share[s])
        row = {}
        for tag, k in (('low', s & (share <= med)), ('high', s & (share > med))):
            r = fit(A[o][k].astype(float), L[o][k].astype(float), rng, 300); row[tag] = dict(r, mean_share=float(share[k].mean()), medA=float(np.median(A[o][k])))
            print(f'{lo}-{hi}N A>={amin:2d} {tag:4s} (mean flat {share[k].mean():.2f}, split {med:.2f}, median A {np.median(A[o][k]):5.0f}): h {r["h"]:.3f} [{r["ci"][0]:.3f}, {r["ci"][1]:.3f}] n {r["n"]}')
        X = np.c_[np.ones(s.sum()), np.log10(A[o][s]), share[s]]; beta = np.linalg.lstsq(X, np.log10(L[o][s]), rcond=None)[0]
        bs = []
        for _ in range(300):
            i = rng.integers(0, s.sum(), s.sum()); bs.append(np.linalg.lstsq(X[i], np.log10(L[o][s])[i], rcond=None)[0])
        bs = np.array(bs); row['joint'] = {'h': float(beta[1]), 'b_share': float(beta[2]), 'b_ci': np.percentile(bs[:, 2], [2.5, 97.5]).tolist()}
        print(f'   joint: h {beta[1]:.3f}, share coef {beta[2]:+.3f} [{row["joint"]["b_ci"][0]:+.3f}, {row["joint"]["b_ci"][1]:+.3f}] (log10 L per unit share)')
        out[f'{lo}-{hi} A>={amin}'] = row
json.dump(out, open('flats15.json', 'w'), indent=1); print('__END__')
