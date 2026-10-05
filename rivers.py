"""Rivers, lakes and Hack's law on a heightmap.

1. Priority-flood (Barnes et al. 2014) from the sea/border: fills every closed depression -> lakes = filled - h.
2. D8 flow directions on the filled surface (flats resolved by flood order: each cell drains to the cell
   that flooded it), drainage area A by accumulation, longest upstream flow length L.
3. Hack's law L = c * A^h: fit log L on log A over channel cells (A >= a_min), report h.
"""
import numpy as np, heapq, json, sys

D8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def ocean_mask(h, sea=0.0):
    """Sea = below-sea cells connected (D8) to the map edge. Inland cells below sea level are pits to fill,
    not outlets: without deposition, droplets carve channels below 0 and would otherwise become inland seas."""
    from collections import deque
    n, m = h.shape; oc = np.zeros((n, m), bool); q = deque()
    for j in range(n):
        for i in range(m):
            if (j in (0, n - 1) or i in (0, m - 1)) and h[j, i] < sea: oc[j, i] = True; q.append((j, i))
    while q:
        j, i = q.popleft()
        for dj, di in D8:
            y, x = j + dj, i + di
            if 0 <= y < n and 0 <= x < m and not oc[y, x] and h[y, x] < sea: oc[y, x] = True; q.append((y, x))
    return oc

def flood(h, sea=0.0, ocean=None):
    """ocean: optional mask of outlet cells (see ocean_mask); default = every cell below sea (old behaviour,
    kept so sweep.jsonl reproduces)."""
    n, m = h.shape
    filled = h.copy(); rec = -np.ones((n, m), np.int64); seen = np.zeros((n, m), bool); order = []
    pq = []
    for j in range(n):
        for i in range(m):
            if (ocean[j, i] if ocean is not None else h[j, i] < sea) or j in (0, n - 1) or i in (0, m - 1):
                heapq.heappush(pq, (max(h[j, i], -1e9), len(order) + j * m + i, j, i)); seen[j, i] = True
    cnt = 0
    while pq:
        z, _, j, i = heapq.heappop(pq); order.append(j * m + i)
        for dj, di in D8:
            y, x = j + dj, i + di
            if 0 <= y < n and 0 <= x < m and not seen[y, x]:
                seen[y, x] = True
                if filled[y, x] <= z: filled[y, x] = z + 1e-7  # lake surface, tiny tilt toward the outlet
                rec[y, x] = j * m + i; cnt += 1
                heapq.heappush(pq, (filled[y, x], cnt, y, x))
    return filled, rec, np.array(order)

def accumulate(rec, order, shape):
    n, m = shape; N = n * m
    A = np.ones(N); L = np.zeros(N); r = rec.ravel()
    step = np.ones(N)
    for c in order[::-1]:  # from highest (last flooded) to sea
        t = r[c]
        if t >= 0:
            A[t] += A[c]
            d = 1.0 if (abs(t - c) in (1, m)) else np.sqrt(2)
            if L[c] + d > L[t]: L[t] = L[c] + d
    return A.reshape(shape), L.reshape(shape)

def hack(A, L, land, a_min=20):
    sel = land & (A >= a_min) & (L > 0)
    x = np.log(A[sel]); y = np.log(L[sel])
    h, c = np.polyfit(x, y, 1)
    return float(h), float(np.exp(c)), int(sel.sum())

def basin_outlets(A, rec, h, sea=0.0):
    """outlet = land cell draining directly into sea/border; Hack's law on whole basins"""
    n, m = A.shape; r = rec.ravel(); out = []
    for c in range(n * m):
        j, i = divmod(c, m)
        if h[j, i] >= 0 and r[c] >= 0:
            tj, ti = divmod(r[c], m)
            if h[tj, ti] < 0: out.append(c)
    return np.array(out)

def steepest(filled, rec_flood, jitter=0.0, rng=None):
    """D8 steepest descent on the filled surface; slopes multiplied by U(1-jitter, 1+jitter) to break the
    straight-line lattice artefact on planes. Cells with no lower neighbour keep the flood receiver."""
    n, m = filled.shape; best = np.zeros((n, m)); rec = rec_flood.copy()
    pad = np.pad(filled, 1, constant_values=np.inf)
    for dj, di in D8:
        nb = pad[1 + dj:1 + dj + n, 1 + di:1 + di + m]
        s = (filled - nb) / np.hypot(dj, di)
        if jitter: s = s * rng.uniform(1 - jitter, 1 + jitter, s.shape)
        better = (s > best) & np.isfinite(nb)
        jj, ii = np.mgrid[0:n, 0:m]
        rec = np.where(better, (jj + dj) * m + (ii + di), rec); best = np.where(better, s, best)
    order = np.argsort(filled.ravel(), kind="stable")  # low to high; accumulate() walks it backwards
    return rec, order

if __name__ == "__main__":
    p = sys.argv[1]; key = sys.argv[2] if len(sys.argv) > 2 else "_h"
    h = np.load(p + key + ".npy")
    filled, rec_flood, _ = flood(h)
    # route by jittered steepest descent: flood-order receivers are not steepest descent and bias h low
    rec, order = steepest(filled, rec_flood, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
    A, L = accumulate(rec, order, h.shape)
    land = h >= 0
    lakes = (filled - h) > 1e-4
    res = {"key": key, "land_cells": int(land.sum()), "lake_cells": int((lakes & land).sum())}
    for amin in (10, 50, 200):
        hh, c, k = hack(A, L, land, amin); res[f"hack_cells_amin{amin}"] = [round(hh, 3), round(c, 2), k]
    outs = basin_outlets(A, rec, h)
    Ab = A.ravel()[outs]; Lb = L.ravel()[outs]; big = Ab >= 50
    if big.sum() > 5:
        hb, cb = np.polyfit(np.log(Ab[big]), np.log(Lb[big]), 1); res["hack_basins"] = [round(float(hb), 3), int(big.sum())]
    np.save(p + key + "_A.npy", A); np.save(p + key + "_L.npy", L); np.save(p + key + "_lake.npy", filled - h)
    print(json.dumps(res))
