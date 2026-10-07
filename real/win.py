"""Read a row/col window from a tiled GeoTIFF without decoding the whole image (HydroSHEDS 15s DEM/DIR)."""
import numpy as np, tifffile, warnings
warnings.simplefilter('ignore')
def window(path, r0, r1, c0, c1):
    with tifffile.TiffFile(path) as t:
        p = t.pages[0]
        if not p.is_tiled: return p.asarray()[r0:r1, c0:c1].copy()
        th, tw = p.tilelength, p.tilewidth; ntx = -(-p.imagewidth // tw); fh = t.filehandle
        out = np.empty((r1 - r0, c1 - c0), p.dtype)
        for ty in range(r0 // th, (r1 - 1) // th + 1):
            for tx in range(c0 // tw, (c1 - 1) // tw + 1):
                k = ty * ntx + tx; fh.seek(p.dataoffsets[k]); seg = p.decode(fh.read(p.databytecounts[k]), k)[0].reshape(th, tw)
                y0, x0 = ty * th, tx * tw; a0, a1 = max(r0, y0), min(r1, y0 + th); b0, b1 = max(c0, x0), min(c1, x0 + tw)
                out[a0 - r0:a1 - r0, b0 - c0:b1 - c0] = seg[a0 - y0:a1 - y0, b0 - x0:b1 - x0]
        return out
