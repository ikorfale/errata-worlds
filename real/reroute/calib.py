"""Calibration spread (zenith 75539): is my method offset (h of my router minus h of HydroRIVERS) the same everywhere?
Same recipe as calib_au.py (1' lat/long block means of the HydroSHEDS 15" DEM, whole metres, metric D8), but:
- route an OUTER window, count outlets only inside an INNER window (both sides), so big rivers are whole;
- drop my outlets whose basin touches the frame of the outer window (truncated basins).
Outlets: land cells draining to sea (touching a sea cell), A 10-1e6 km2. usage: python3 calib.py [name ...]"""
import numpy as np, tifffile, os, json, subprocess, sys, struct, warnings
sys.path.insert(0, '..'); from hack import fit, load, D
warnings.simplefilter('ignore')
R = 6371000.0; TMP = os.path.expanduser('~/.tmp'); ND = 32767
# name: (DEM region, HydroRIVERS region, outer (lon0, lon1, lat0, lat1), inner)
WIN = {
    'au':      ('au', 'au', (139.5, 154.0, -44.5, -10.0), (140.0, 154.0, -44.0, -10.5)),
    'norway':  ('eu', 'eu', (4.0, 13.5, 57.5, 62.0),       (4.5, 12.5, 57.8, 60.0)),
    'chile':   ('sa', 'sa', (-76.0, -67.5, -56.5, -39.0),  (-76.0, -71.0, -56.0, -41.0)),
    'denmark': ('eu', 'eu', (7.0, 14.0, 53.5, 58.0),       (8.0, 13.0, 54.3, 57.8)),
}

def roots(rec):
    """basin id (outlet index) of every cell by pointer doubling over the receiver array."""
    p = np.where(rec >= 0, rec, np.arange(len(rec), dtype=np.int64)).astype(np.int64)
    while True:
        q = p[p]
        if np.array_equal(q, p): return p
        p = q

def run(name):
    dreg, hreg, O, I = WIN[name]
    with tifffile.TiffFile(f'../data/dir/hyd_{dreg}_dem_15s.tif') as t:
        tie = t.pages[0].tags['ModelTiepointTag'].value; d = t.pages[0].tags['ModelPixelScaleTag'].value[0]
        dem = t.asarray(out=os.path.join(TMP, f'{name}_dem.mm'))
    lon0, lat0 = tie[3], tie[4]
    c0, c1 = int(round((O[0] - lon0) / d)), int(round((O[1] - lon0) / d)); r0, r1 = int(round((lat0 - O[3]) / d)), int(round((lat0 - O[2]) / d))
    c0, r0 = max(c0, 0), max(r0, 0); c1 = min(c1, dem.shape[1]); r1 = min(r1, dem.shape[0])
    c1 -= (c1 - c0) % 4; r1 -= (r1 - r0) % 4
    blk = np.asarray(dem[r0:r1, c0:c1]).astype(np.float32); blk[blk == ND] = np.nan
    del dem; os.remove(os.path.join(TMP, f'{name}_dem.mm'))
    n, m = (r1 - r0) // 4, (c1 - c0) // 4
    g = np.round(np.nanmean(blk.reshape(n, 4, m, 4), axis=(1, 3))).astype(np.float32); del blk
    lat = lat0 - (r0 + (np.arange(n) + 0.5) * 4) * d; lon = lon0 + (c0 + (np.arange(m) + 0.5) * 4) * d
    dy = R * np.radians(4 * d); dx = (R * np.radians(4 * d) * np.cos(np.radians(lat))).astype(np.float32)
    pre = f'{name}_me'; g.tofile(f'{name}.f32'); dx.tofile(f'{name}.dx.f32')
    print(subprocess.run(['./route', f'{name}.f32', str(n), str(m), f'{name}.dx.f32', str(dy), '1', pre], capture_output=True, text=True).stdout.strip())
    rec = np.fromfile(pre + '.rec', np.int32); A = np.fromfile(pre + '.A', np.float32); L = np.fromfile(pre + '.L', np.float32)
    for e in ('.rec', '.A', '.L'): os.remove(pre + e)
    os.remove(f'{name}.f32'); os.remove(f'{name}.dx.f32')
    sea = np.isnan(g); land = ~sea; touch = np.zeros_like(sea)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            touch |= np.roll(np.roll(sea, dj, 0), di, 1)
    frame = np.zeros_like(sea); frame[0] = frame[-1] = True; frame[:, 0] = frame[:, -1] = True
    rt = roots(rec); cut = np.zeros(n * m, bool); cut[np.unique(rt[(frame & land).ravel()])] = True
    LAT, LON = np.meshgrid(lat, lon, indexing='ij')
    inner = ((LON >= I[0]) & (LON <= I[1]) & (LAT >= I[2]) & (LAT <= I[3])).ravel()
    cand = (land & touch & ~frame).ravel() & (rec < 0) & (A >= 10) & (A <= 1e6) & (L > 0) & inner
    o = np.flatnonzero(cand & ~cut)
    rng = np.random.default_rng(1); mine = fit(A[o].astype(float), L[o].astype(float), rng, 300)
    dd = load(hreg, {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
    oo = np.flatnonzero((dd['NEXT_DOWN'] == 0) & (dd['UPLAND_SKM'] >= 10) & (dd['UPLAND_SKM'] <= 1e6) & (dd['DIST_UP_KM'] > 0))
    base = f'{D}/HydroRIVERS_v10_{hreg}_shp/HydroRIVERS_v10_{hreg}'
    shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); xy = np.zeros((len(oo), 2))
    with open(base + '.shp', 'rb') as f:
        for k, off in enumerate(shx[oo, 0].astype(np.int64) * 2):
            f.seek(off + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    s = (xy[:, 0] >= I[0]) & (xy[:, 0] <= I[1]) & (xy[:, 1] >= I[2]) & (xy[:, 1] <= I[3])
    hr = fit(dd['UPLAND_SKM'][oo][s], dd['DIST_UP_KM'][oo][s], rng, 300)
    k1 = A[o] >= 50; k2 = dd['UPLAND_SKM'][oo][s] >= 50
    m50 = fit(A[o][k1].astype(float), L[o][k1].astype(float), rng, 300); h50 = fit(dd['UPLAND_SKM'][oo][s][k2], dd['DIST_UP_KM'][oo][s][k2], rng, 300)
    res = {'A>=50': {'mine': m50, 'hydrorivers': h50, 'offset': round(m50['h'] - h50['h'], 4)}, 'name': name, 'outer': O, 'inner': I, 'grid': [n, m], 'dropped_truncated': int((cand & cut).sum()),
           'mine_metric_1min': mine, 'hydrorivers': hr, 'offset': round(mine['h'] - hr['h'], 4)}
    print(json.dumps(res)); return res

if __name__ == '__main__':
    names = sys.argv[1:] or list(WIN)
    out = {}
    if os.path.exists('calib.json'): out = json.load(open('calib.json'))
    for nm in names: out[nm] = run(nm)
    json.dump(out, open('calib.json', 'w'), indent=1, default=float)
    for nm, r in out.items(): print(f"{nm:8s} mine {r['mine_metric_1min']['h']:.3f} (n {r['mine_metric_1min']['n']})  HR {r['hydrorivers']['h']:.3f} (n {r['hydrorivers']['n']})  offset {r['offset']:+.3f} | A>=50 mine {r['A>=50']['mine']['h']:.3f} HR {r['A>=50']['hydrorivers']['h']:.3f} offset {r['A>=50']['offset']:+.3f}")
    print('__END__')
