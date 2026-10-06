"""#159: D8 code shares by latitude band on the gr / ar 15s direction grids. Low memory: decode to an on-disk memmap.
Codes: 1 E, 2 SE, 4 S, 8 SW, 16 W, 32 NW, 64 N, 128 NE; 0 outlet, 255 no data."""
import numpy as np, tifffile, os, sys
TMP = os.path.expanduser('~/.tmp')
for name in sys.argv[1:]:
    p = f'data/dir/hyd_{name}_dir_15s.tif' if name != 'au' else 'data/hyd_au_dir_15s.tif'
    with tifffile.TiffFile(p) as t:
        tags = t.pages[0].tags
        tie = tags['ModelTiepointTag'].value; scale = tags['ModelPixelScaleTag'].value
        a = t.asarray(out=os.path.join(TMP, f'dir_{name}.mm'))
    lat0, dlat = tie[4], scale[1]
    print(f'{name}: shape {a.shape}, top lat {lat0:.3f}, cell {dlat*3600:.1f}"', flush=True)
    bands = [(60, 65), (65, 70), (70, 75), (75, 80), (80, 84)] if lat0 > 60 else [(-15, -10), (-25, -15), (-35, -25), (-45, -35)]
    tot = np.zeros(256, np.int64)
    for lo, hi in bands:
        r0 = max(0, int(round((lat0 - hi) / dlat))); r1 = min(a.shape[0], int(round((lat0 - lo) / dlat)))
        if r1 <= r0: continue
        h = np.zeros(256, np.int64)
        for r in range(r0, r1, 500):
            h += np.bincount(np.asarray(a[r:min(r + 500, r1)]).ravel(), minlength=256)
        tot += h
        land = sum(h[k] for k in (1, 2, 4, 8, 16, 32, 64, 128))
        if land < 1000: continue
        s = {k: h[k] / land * 100 for k in (1, 2, 4, 8, 16, 32, 64, 128)}
        ns, ew = s[4] + s[64], s[1] + s[16]
        print(f'  {lo}-{hi}N land {land:>10,}  N/S {ns:5.1f}%  E/W {ew:5.1f}%  diag {100-ns-ew:5.1f}%  NS:EW {ns/ew:5.2f}', flush=True)
    land = sum(tot[k] for k in (1, 2, 4, 8, 16, 32, 64, 128))
    s = {k: tot[k] / land * 100 for k in (1, 2, 4, 8, 16, 32, 64, 128)}
    print(f'  ALL land {land:,}  ' + ' '.join(f'{k}:{v:.1f}' for k, v in s.items()) + f"  NS:EW {(s[4]+s[64])/(s[1]+s[16]):.2f}", flush=True)
    del a; os.remove(os.path.join(TMP, f'dir_{name}.mm'))
print('__END__')
