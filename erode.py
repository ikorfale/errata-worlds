"""Worlds carved by rain: spectral-noise heightmap + vectorised droplet hydraulic erosion.

Droplet model after the classic particle scheme (inertia, carrying capacity ~ slope*speed*water,
erosion/deposition shared bilinearly over the four cell corners). Droplets run in batches so numpy does
the work; droplets inside one batch do not see each other's changes (a small, stated approximation).
"""
import numpy as np, argparse, time, json

def spectral_heightmap(n, beta, rng, shape="island"):
    kx = np.fft.fftfreq(n)[:, None]; ky = np.fft.fftfreq(n)[None, :]
    k = np.sqrt(kx**2 + ky**2); k[0, 0] = 1
    amp = k ** (-beta / 2); amp[0, 0] = 0
    ph = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    h = np.real(np.fft.ifft2(amp * ph))
    h = (h - h.min()) / (h.max() - h.min())
    if shape == "plane":  # tilted plane draining to the sea along the bottom edge
        yy = np.mgrid[0:n, 0:n][0] / (n - 1)
        return (h * 0.6 + 0.7 * (1 - yy) - 0.3).astype(np.float64)
    # island-ish falloff so water has somewhere to go: lower the borders
    y, x = np.mgrid[0:n, 0:n] / (n - 1) - 0.5
    r = np.sqrt(x**2 + y**2) / 0.5
    h = h * 0.75 + 0.45 * (1 - np.clip(r, 0, 1.2) ** 2) - 0.32
    return h.astype(np.float64)

def bilinear(h, x, y):
    n = h.shape[0]
    i = x.astype(int); j = y.astype(int)
    u = x - i; v = y - j
    h00 = h[j, i]; h10 = h[j, i + 1]; h01 = h[j + 1, i]; h11 = h[j + 1, i + 1]
    gx = (h10 - h00) * (1 - v) + (h11 - h01) * v
    gy = (h01 - h00) * (1 - u) + (h11 - h10) * u
    hh = h00 * (1 - u) * (1 - v) + h10 * u * (1 - v) + h01 * (1 - u) * v + h11 * u * v
    return hh, gx, gy, i, j, u, v

def spread(h, i, j, u, v, amt):
    """add amt (per droplet) to the four corners with bilinear weights"""
    np.add.at(h, (j, i), amt * (1 - u) * (1 - v))
    np.add.at(h, (j, i + 1), amt * u * (1 - v))
    np.add.at(h, (j + 1, i), amt * (1 - u) * v)
    np.add.at(h, (j + 1, i + 1), amt * u * v)

def brush(r):
    o = [(a, b) for a in range(-r, r + 1) for b in range(-r, r + 1) if a * a + b * b <= r * r]
    oy = np.array([a for a, _ in o]); ox = np.array([b for _, b in o])
    w = np.maximum(0, r + 0.5 - np.hypot(oy, ox)); return oy, ox, w / w.sum()

def erode_brush(h, i, j, amt, B):
    """remove amt (>0) per droplet spread over a disc around cell (i, j)"""
    oy, ox, w = B; n = h.shape[0]
    jj = j[:, None] + oy[None, :]; ii = i[:, None] + ox[None, :]
    ok = (jj >= 0) & (jj < n) & (ii >= 0) & (ii < n)
    ww = np.where(ok, w[None, :], 0); ww = ww / ww.sum(1, keepdims=True)  # renormalise inside the map
    np.add.at(h, (np.clip(jj, 0, n - 1).ravel(), np.clip(ii, 0, n - 1).ravel()), -(amt[:, None] * ww).ravel())

def erode(h, drops, rng, batch=4096, steps=64, inertia=0.05, cap=4.0, min_slope=0.01,
          erode_rate=0.3, deposit_rate=0.3, evap=0.02, gravity=4.0, scale=1.0, radius=3, sea=0.0, snap=None, snap_every=0):
    n = h.shape[0]; done = 0; frames = []; B = brush(radius); life = 0
    while done < drops:
        m = min(batch, drops - done)
        x = rng.uniform(1, n - 2, m); y = rng.uniform(1, n - 2, m)
        dx = np.zeros(m); dy = np.zeros(m); speed = np.ones(m); water = np.ones(m); sed = np.zeros(m)
        alive = np.ones(m, bool)
        for _ in range(steps):
            idx = np.nonzero(alive)[0]
            if idx.size == 0: break
            hh, gx, gy, i, j, u, v = bilinear(h, x[idx], y[idx])
            ndx = dx[idx] * inertia - gx * (1 - inertia)
            ndy = dy[idx] * inertia - gy * (1 - inertia)
            L = np.hypot(ndx, ndy)
            ok = L > 1e-12
            ndx = np.where(ok, ndx / np.where(ok, L, 1), 0); ndy = np.where(ok, ndy / np.where(ok, L, 1), 0)
            nx = x[idx] + ndx; ny = y[idx] + ndy
            inb = ok & (nx >= 0) & (nx < n - 1.001) & (ny >= 0) & (ny < n - 1.001)
            # droplets that leave the map: drop their sediment where they are and die
            out = ~inb
            if out.any():
                spread(h, i[out], j[out], u[out], v[out], sed[idx[out]] * 0)  # sediment carried off-map is lost
                alive[idx[out]] = False
            k = idx[inb]; i, j, u, v, hh = i[inb], j[inb], u[inb], v[inb], hh[inb]
            ndx, ndy, nx, ny = ndx[inb], ndy[inb], nx[inb], ny[inb]
            nh = bilinear(h, nx, ny)[0]
            # reaching the sea (base level): drop the whole load as a delta and stop
            wet = nh < sea
            if wet.any():
                spread(h, i[wet], j[wet], u[wet], v[wet], sed[k[wet]] / scale)
                alive[k[wet]] = False
                dry = ~wet; k = k[dry]; i, j, u, v, hh = i[dry], j[dry], u[dry], v[dry], hh[dry]
                ndx, ndy, nx, ny, nh = ndx[dry], ndy[dry], nx[dry], ny[dry], nh[dry]
            dh = (nh - hh) * scale
            c = np.maximum(-dh, min_slope) * speed[k] * water[k] * cap
            depo = (sed[k] > c) | (dh > 0)
            amt = np.where(dh > 0, np.minimum(dh, sed[k]), (sed[k] - c) * deposit_rate)
            amt = np.where(depo, amt, -np.minimum((c - sed[k]) * erode_rate, -dh))
            dep = np.where(amt > 0, amt, 0); ero = np.where(amt < 0, -amt, 0)
            spread(h, i, j, u, v, dep / scale)
            if radius > 0: erode_brush(h, i, j, ero / scale, B)
            else: spread(h, i, j, u, v, -ero / scale)
            life += k.size
            sed[k] -= amt
            speed[k] = np.sqrt(np.maximum(speed[k] ** 2 - dh * gravity, 0))
            water[k] *= (1 - evap)
            x[k], y[k], dx[k], dy[k] = nx, ny, ndx, ndy
        done += m
        if snap_every and (done // batch) % snap_every == 0 and snap is not None:
            frames.append(h.copy())
    erode.mean_life = life / max(drops, 1)
    return frames

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=256); ap.add_argument("--drops", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=7); ap.add_argument("--beta", type=float, default=3.2)
    ap.add_argument("--scale", type=float, default=60.0, help="height units per map unit when computing slopes")
    ap.add_argument("--radius", type=int, default=3); ap.add_argument("--cap", type=float, default=4.0); ap.add_argument("--er", type=float, default=0.3); ap.add_argument("--out", default="out/w"); ap.add_argument("--snap_every", type=int, default=0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    h0 = spectral_heightmap(a.n, a.beta, rng); h = h0.copy()
    t = time.time()
    frames = erode(h, a.drops, rng, scale=a.scale, radius=a.radius, cap=a.cap, erode_rate=a.er, snap=True, snap_every=a.snap_every)
    el = time.time() - t
    np.save(a.out + "_h0.npy", h0); np.save(a.out + "_h.npy", h)
    if frames: np.save(a.out + "_frames.npy", np.array(frames, dtype=np.float32))
    d = h - h0
    info = dict(cap=a.cap, er=a.er, n=a.n, drops=a.drops, seed=a.seed, beta=a.beta, scale=a.scale, seconds=round(el, 1),
                eroded_max=float(-d.min()), deposited_max=float(d.max()), mean_change=float(np.abs(d).mean()),
                net=float(d.sum()), frames=len(frames), mean_life=round(erode.mean_life, 1))
    json.dump(info, open(a.out + "_info.json", "w"), indent=1); print(json.dumps(info))
