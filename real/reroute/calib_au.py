"""Calibration control (zenith 75533): the same router and grid recipe as the Greenland run (1' lat/long block means of the
HydroSHEDS 15" DEM, whole metres, metric D8) on eastern Australia (SRTM, 140-154E, 10.5-44S), against HydroRIVERS outlets
in the same window. Outlets: land cells draining to sea (must touch a sea cell; frame outlets excluded), A 10-1e6 km2."""
import numpy as np, tifffile, os, json, subprocess, sys, struct
sys.path.insert(0, '..'); from hack import fit, load, D
R = 6371000.0; TMP = os.path.expanduser('~/.tmp'); ND = 32767; W = (140.0, 154.0, -44.0, -10.5)
with tifffile.TiffFile('../data/dir/hyd_au_dem_15s.tif') as t:
    tie = t.pages[0].tags['ModelTiepointTag'].value; d = t.pages[0].tags['ModelPixelScaleTag'].value[0]
    dem = t.asarray(out=os.path.join(TMP, 'au_dem.mm'))
lon0, lat0 = tie[3], tie[4]
c0, c1 = int(round((W[0] - lon0) / d)), int(round((W[1] - lon0) / d)); r0, r1 = int(round((lat0 - W[3]) / d)), int(round((lat0 - W[2]) / d))
c1 -= (c1 - c0) % 4; r1 -= (r1 - r0) % 4
blk = np.asarray(dem[r0:r1, c0:c1]).astype(np.float32); blk[blk == ND] = np.nan
n, m = (r1 - r0) // 4, (c1 - c0) // 4
import warnings; warnings.simplefilter('ignore')
g = np.round(np.nanmean(blk.reshape(n, 4, m, 4), axis=(1, 3))).astype(np.float32); del blk
lat = lat0 - (r0 + (np.arange(n) + 0.5) * 4) * d; dy = R * np.radians(4 * d); dx = (R * np.radians(4 * d) * np.cos(np.radians(lat))).astype(np.float32)
g.tofile('au.f32'); dx.tofile('au.dx.f32'); os.remove(os.path.join(TMP, 'au_dem.mm'))
print(subprocess.run(['./route', 'au.f32', str(n), str(m), 'au.dx.f32', str(dy), '1', 'au_me'], capture_output=True, text=True).stdout.strip())
rec = np.fromfile('au_me.rec', np.int32); A = np.fromfile('au_me.A', np.float32); L = np.fromfile('au_me.L', np.float32)
sea = np.isnan(g); land = ~sea; touch = np.zeros_like(sea)
for dj in (-1, 0, 1):
    for di in (-1, 0, 1):
        touch |= np.roll(np.roll(sea, dj, 0), di, 1)
frame = np.zeros_like(sea); frame[0] = frame[-1] = True; frame[:, 0] = frame[:, -1] = True
o = np.flatnonzero((land & touch & ~frame).ravel() & (rec < 0) & (A >= 10) & (A <= 1e6) & (L > 0))
rng = np.random.default_rng(1); mine = fit(A[o].astype(float), L[o].astype(float), rng, 300)
# HydroRIVERS outlets in the same window
dd = load('au', {'NEXT_DOWN', 'DIST_UP_KM', 'UPLAND_SKM'})
oo = np.flatnonzero((dd['NEXT_DOWN'] == 0) & (dd['UPLAND_SKM'] >= 10) & (dd['UPLAND_SKM'] <= 1e6) & (dd['DIST_UP_KM'] > 0))
base = f'{D}/HydroRIVERS_v10_au_shp/HydroRIVERS_v10_au'
shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); xy = np.zeros((len(oo), 2))
with open(base + '.shp', 'rb') as f:
    for k, off in enumerate(shx[oo, 0].astype(np.int64) * 2):
        f.seek(off + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
s = (xy[:, 0] >= W[0] + 0.1) & (xy[:, 0] <= W[1]) & (xy[:, 1] >= W[2]) & (xy[:, 1] <= W[3])
hr = fit(dd['UPLAND_SKM'][oo][s], dd['DIST_UP_KM'][oo][s], rng, 300)
res = {'window': W, 'mine_metric_1min': mine, 'hydrorivers': hr}
print('mine (1\' metric):', mine); print('HydroRIVERS     :', hr)
json.dump(res, open('calib_au.json', 'w'), default=float); print('__END__')
