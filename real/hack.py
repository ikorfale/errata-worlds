"""Hack's law on real rivers: HydroRIVERS v1.0 reach attributes.
L = DIST_UP_KM (reach outlet -> furthest point on the divide), A = UPLAND_SKM.
Outputs: out/<region>.json with outlet fits (independent basins), banded local
exponents on all reaches, and bootstrap CIs."""
import numpy as np, struct, json, sys, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def load(region, cols):
    p = f'{D}/HydroRIVERS_v10_{region}_shp/HydroRIVERS_v10_{region}.dbf'
    with open(p, 'rb') as f:
        h = f.read(32); n, hl, rl = struct.unpack('<IHH', h[4:12]); fs = []
        while True:
            d = f.read(32)
            if d[0] == 0x0d: break
            fs.append((d[:11].split(b'\0')[0].decode(), d[16]))
    raw = np.memmap(p, dtype=np.uint8, mode='r', offset=hl, shape=(n, rl))
    out, off = {}, 1  # byte 0 = deletion flag
    for name, w in fs:
        if name in cols:
            out[name] = raw[:, off:off+w].copy().view(f'S{w}').ravel().astype(float)
        off += w
    return out

def fit(A, L, rng, nb=1000):
    x, y = np.log10(A), np.log10(L)
    b = np.polyfit(x, y, 1)
    bs = []
    for _ in range(nb):
        i = rng.integers(0, len(x), len(x)); bs.append(np.polyfit(x[i], y[i], 1)[0])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {'h': round(b[0], 4), 'c': round(10**b[1], 4), 'ci': [round(lo, 4), round(hi, 4)], 'n': int(len(x))}

def main(region):
    rng = np.random.default_rng(1)
    r = load(region, {'HYRIV_ID', 'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM', 'ENDORHEIC', 'LENGTH_KM'})
    A, L, nd, en = r['UPLAND_SKM'], r['DIST_UP_KM'], r['NEXT_DOWN'], r['ENDORHEIC']
    ok = (A > 0) & (L > 0)
    res = {'region': region, 'reaches': int(len(A))}
    out = ok & (nd == 0)
    res['outlets_total'] = int(out.sum())
    res['outlets_endorheic'] = int((out & (en == 1)).sum())
    sel = out & (A >= 1e2) & (A <= 1e6)
    res['B1_outlets_1e2_1e6'] = fit(A[sel], L[sel], rng)
    sel2 = sel & (en == 0)
    res['outlets_exorheic_1e2_1e6'] = fit(A[sel2], L[sel2], rng)
    bands = [(1e1, 1e2), (1e2, 1e3), (1e3, 1e4), (1e4, 1e5), (1e5, 1e6), (1e4, 1e6)]
    res['outlet_bands'] = {}; res['reach_bands'] = {}
    for lo, hi in bands:
        k = f'{lo:.0e}-{hi:.0e}'
        s = out & (A >= lo) & (A < hi)
        if s.sum() >= 20: res['outlet_bands'][k] = fit(A[s], L[s], rng, 300)
        s = ok & (A >= lo) & (A < hi)
        idx = np.flatnonzero(s)
        if len(idx) > 200000: idx = rng.choice(idx, 200000, replace=False)
        if len(idx) >= 20: res['reach_bands'][k] = fit(A[idx], L[idx], rng, 200)
    # largest basins, for the record
    big = np.flatnonzero(out)[np.argsort(-A[out])[:8]]
    res['largest'] = [[int(r['HYRIV_ID'][i]), A[i], L[i]] for i in big]
    os.makedirs(os.path.join(os.path.dirname(D), 'out'), exist_ok=True)
    json.dump(res, open(os.path.join(os.path.dirname(D), 'out', f'{region}.json'), 'w'), indent=1)
    print(json.dumps(res))

if __name__ == '__main__':
    main(sys.argv[1])
