"""#133: Hack's h of complete coastal/sink basins (A 10-1e4 km2, basin never touches the window edge) at 3s vs 15s,
and the L ratio of the same mouths matched across resolutions."""
import numpy as np, json, sys
sys.path.insert(0, '..'); from hack import fit
M = json.load(open('meta.json')); rng = np.random.default_rng(133); out = {}
def outlets(k):
    g = M[k]; n, m = g['n'], g['m']
    d = np.fromfile(f'{k}.u8', np.uint8); rec = np.fromfile(f'{k}.rec', np.int32); e = np.fromfile(f'{k}.edge', np.uint8)
    A = np.fromfile(f'{k}.A', np.float32); L = np.fromfile(f'{k}.L', np.float32)
    o = np.flatnonzero((d != 255) & (rec < 0) & (e == 0) & (A >= 10) & (A <= 1e4) & (L > 0)); j, i = np.divmod(o, m)
    lat = g['lat_top'] - (j + 0.5) * g['cd']; lon = g['lon_left'] + (i + 0.5) * g['cd']
    return A[o].astype(float), L[o].astype(float), lat, lon
allA = {'3s': [], '15s': []}; pairs = []
for w in ('corsica', 'catalonia'):
    S = {r: outlets(f'{w}_{r}') for r in ('3s', '15s')}
    for r in S: allA[r].append(S[r])
    A3, L3, la3, lo3 = S['3s']
    for a, l, la, lo in zip(*S['15s']):  # same mouth: within 1.5 15s-cells (~550 m) and area within 25%
        c = np.flatnonzero((np.abs(la3 - la) < 1.5 / 240) & (np.abs(lo3 - lo) < 1.5 / 240) & (np.abs(A3 / a - 1) < 0.25))
        if len(c): b = c[np.argmin(np.abs(A3[c] / a - 1))]; pairs.append((w, a, l, A3[b], L3[b]))
for r in allA:
    A = np.concatenate([s[0] for s in allA[r]]); L = np.concatenate([s[1] for s in allA[r]])
    out[f'all_{r}'] = fit(A, L, rng, 500); print(r, 'all mouths', out[f'all_{r}'])
P = np.array([p[1:] for p in pairs]); a15, l15, a3, l3 = P.T
out['matched_n'] = len(P); out['match_15s'] = fit(a15, l15, rng, 500); out['match_3s'] = fit(a3, l3, rng, 500)
print('matched', len(P), '\n 15s', out['match_15s'], '\n 3s ', out['match_3s'])
ratio = l3 / l15; out['ratio_bands'] = {}
for lo, hi in ((10, 30), (30, 100), (100, 1000), (1000, 1e4)):
    s = (a15 >= lo) & (a15 < hi)
    if s.sum(): out['ratio_bands'][f'{lo:g}-{hi:g}'] = {'n': int(s.sum()), 'median_L3/L15': round(float(np.median(ratio[s])), 3)}
print('L3/L15 by area band', out['ratio_bands'])
json.dump(out, open('res.json', 'w'), indent=1, default=float); print('__END__')
# paired bootstrap of h(3s) - h(15s) on the matched mouths
x15, x3, y15, y3 = np.log10(a15), np.log10(a3), np.log10(l15), np.log10(l3); dh = []
for _ in range(2000):
    i = rng.integers(0, len(P), len(P)); dh.append(np.polyfit(x3[i], y3[i], 1)[0] - np.polyfit(x15[i], y15[i], 1)[0])
out['paired_dh'] = {'est': round(float(np.polyfit(x3, y3, 1)[0] - np.polyfit(x15, y15, 1)[0]), 4), 'ci': [round(float(v), 4) for v in np.percentile(dh, [2.5, 97.5])]}
r = np.log(ratio); out['logratio_vs_logA_slope'] = round(float(np.polyfit(x15, r / np.log(10), 1)[0]), 4)
print('paired dh', out['paired_dh'], 'slope of log10(L3/L15) on log10 A', out['logratio_vs_logA_slope'])
json.dump(out, open('res.json', 'w'), indent=1, default=float); print('__END2__')
