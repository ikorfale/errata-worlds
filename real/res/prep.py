"""#133: cut the same windows from HydroSHEDS DIR 3s (tile n40e000) and 15s (eu) and run dirflow on both."""
import numpy as np, subprocess, json
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
import sys
WIN = {'corsica': (43.2, 40.0, 8.0, 10.0), 'catalonia': (43.5, 41.0, 0.5, 3.5), 'liguria': (44.6, 43.4, 6.5, 9.99)}
if len(sys.argv) > 1: WIN = {k: WIN[k] for k in sys.argv[1:]}   # lat_top, lat_bot, lon_left, lon_right
SRC = {'3s': ('../data/dir/n40e000_dir.tif', 50.0, 0.0, 1 / 1200), '15s': ('../data/dir/hyd_eu_dir_15s.tif', 84.0, -25.0, 1 / 240)}
meta = {}
for res, (p, top, left, cd) in SRC.items():
    im = Image.open(p)
    for w, (lt, lb, ll, lr) in WIN.items():
        j0, j1 = round((top - lt) / cd), round((top - lb) / cd); i0, i1 = round((ll - left) / cd), round((lr - left) / cd)
        a = np.asarray(im.crop((i0, j0, i1, j1)), np.uint8); a.tofile(f'{w}_{res}.u8'); n, m = a.shape
        out = subprocess.run(['./dirflow', f'{w}_{res}.u8', str(n), str(m), str(lt), repr(cd), f'{w}_{res}'], capture_output=True, text=True).stdout
        meta[f'{w}_{res}'] = {'n': n, 'm': m, 'lat_top': lt, 'lon_left': ll, 'cd': cd}; print(w, res, a.shape, out.strip(), flush=True)
    im.close()
old = json.load(open('meta.json')) if __import__('os').path.exists('meta.json') else {}
old.update(meta); json.dump(old, open('meta.json', 'w'), indent=1)
