"""#165 check 2: the 60-70N Greenland 15" window (same as ice_touch.py) for route.c. Sea = HydroSHEDS dir 255 -> NaN."""
import numpy as np, json, tifffile, warnings
warnings.simplefilter('ignore')
R = 6371000.0; d = 1 / 240; LAT0 = 84.0
ra, rb, ca, cb = int((84 - 72) * 240), int((84 - 59.5) * 240), int((-60 + 74) * 240), int((-15 + 74) * 240)
n, m = rb - ra, cb - ca
with tifffile.TiffFile('../data/dir/hyd_gr_dir_15s.tif') as t: sea = t.pages[0].asarray()[ra:rb, ca:cb] == 255
with tifffile.TiffFile('../data/dir/hyd_gr_dem_15s.tif') as t: z = t.pages[0].asarray()[ra:rb, ca:cb].astype(np.float32)
z[sea | (z == 32767)] = np.nan; z.tofile('g15.f32')
lat = LAT0 - (ra + np.arange(n) + 0.5) * d
(R * np.radians(d) * np.cos(np.radians(lat))).astype(np.float32).tofile('g15.dx.f32')
json.dump({'n': n, 'm': m, 'ra': ra, 'ca': ca, 'dy': R * np.radians(d)}, open('g15.meta.json', 'w')); print(n, m, R * np.radians(d))
