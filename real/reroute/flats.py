"""zenith 75539: does the share of flat cells in a basin go with a lower Hack exponent, within a latitude band?
geo_me routing of the Greenland 1' grid (metric D8). Flat = land cell with no strictly lower 8-neighbour on the whole-metre
grid (sea counts as lower). Share per mouth basin; mouths A 10-1e6 km2, split at the band's median share."""
import numpy as np, json, sys
sys.path.insert(0, '..'); from hack import fit
from calib import roots
M = json.load(open('geo.meta.json')); n, m = M['n'], M['m']
z = np.fromfile('geo.f32', np.float32).reshape(n, m); land = np.isfinite(z)
zz = np.where(land, z, -1e9); P = np.pad(zz, 1, constant_values=np.inf)
lower = np.zeros((n, m), bool)
for dj in (-1, 0, 1):
    for di in (-1, 0, 1):
        if dj or di: lower |= P[1 + dj:n + 1 + dj, 1 + di:m + 1 + di] < zz
flat = (land & ~lower).ravel(); landr = land.ravel()
rec = np.fromfile('geo_me.rec', np.int32); A = np.fromfile('geo_me.A', np.float32); L = np.fromfile('geo_me.L', np.float32)
rt = roots(rec)
cells = np.bincount(rt[landr], minlength=n * m); fl = np.bincount(rt[flat], minlength=n * m)
lat = M['lat0'] - (np.arange(n * m) // m + 0.5) * M['cell_deg']
o = np.flatnonzero(landr & (rec < 0) & (A >= 10) & (A <= 1e6) & (L > 0))
share = fl[o] / np.maximum(cells[o], 1)
rng = np.random.default_rng(1); out = {}
print(f'land flat share {flat.sum() / landr.sum():.3f}')
for lo, hi in ((60, 70), (70, 75), (75, 84)):
    s = (lat[o] >= lo) & (lat[o] < hi); med = np.median(share[s])
    for tag, k in (('low', s & (share <= med)), ('high', s & (share > med))):
        r = fit(A[o][k].astype(float), L[o][k].astype(float), rng, 300)
        out[f'{lo}-{hi} {tag}'] = dict(r, median_share=float(med), mean_share=float(share[k].mean()))
        print(f'{lo}-{hi}N {tag:4s} flats (mean {share[k].mean():.2f}, median split {med:.2f}): h {r["h"]:.3f} [{r["ci"][0]:.3f}, {r["ci"][1]:.3f}] n {r["n"]}')
    # area-matched check: A distributions of the halves differ? report median A
    print(f'   median A low {np.median(A[o][s & (share <= med)]):.0f} km2, high {np.median(A[o][s & (share > med)]):.0f} km2')
json.dump(out, open('flats.json', 'w'), indent=1); print('__END__')
