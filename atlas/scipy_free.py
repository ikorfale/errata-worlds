"""Distance from land in cells (two-pass chamfer), so the atlas needs only numpy."""
import numpy as np
def dist_to(mask):
    INF = 1e9; d = np.where(mask, 0.0, INF); n, m = d.shape; a, b = 1.0, 1.4142
    for y in range(n):
        for x in range(m):
            if d[y, x] == 0: continue
            v = d[y, x]
            if y: v = min(v, d[y - 1, x] + a, d[y - 1, x - 1] + b if x else INF, d[y - 1, x + 1] + b if x < m - 1 else INF)
            if x: v = min(v, d[y, x - 1] + a)
            d[y, x] = v
    for y in range(n - 1, -1, -1):
        for x in range(m - 1, -1, -1):
            v = d[y, x]
            if y < n - 1: v = min(v, d[y + 1, x] + a, d[y + 1, x - 1] + b if x else INF, d[y + 1, x + 1] + b if x < m - 1 else INF)
            if x < m - 1: v = min(v, d[y, x + 1] + a)
            d[y, x] = v
    return d
