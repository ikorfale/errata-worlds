"""Erosion time-lapse: one island, 800k droplets, a frame every 8192 drops.
Left: the map with rivers (drainage area >= 50 cells). Right: Hack's exponent h of the same map so far,
on all channel cells (A >= 50), routed by jittered steepest descent on the lake-filled surface (as rivers.py).
Writes out/tl/frame_NNN.png and out/tl/hack.jsonl; make the video with ffmpeg (see README)."""
import numpy as np, json, os, sys, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import erode as E, rivers as R
from render import rgb

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7
DROPS = int(sys.argv[2]) if len(sys.argv) > 2 else 800000
STEP = 8192
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "tl"); os.makedirs(OUT, exist_ok=True)

def measure(h):
    oc = R.ocean_mask(h); filled, rf, _ = R.flood(h, ocean=oc)
    rec, order = R.steepest(filled, rf, 0.3, np.random.default_rng(1)); rec.ravel()[oc.ravel()] = -1
    A, L = R.accumulate(rec, order, h.shape); land = ~oc
    hh, _, k = R.hack(A, L, land, 50)
    return A, land, hh, k

rng = np.random.default_rng(SEED); h = E.spectral_heightmap(256, 3.2, rng)
done, xs, ys, log = 0, [], [], open(os.path.join(OUT, "hack.jsonl"), "w")
f = 0
while True:
    A, land, hh, k = measure(h)
    xs.append(done / 1000); ys.append(hh)
    log.write(json.dumps({"drops": done, "hack": round(hh, 4), "cells": k}) + "\n"); log.flush()
    riv = np.where(land, np.clip((np.log(A) - np.log(50)) / (np.log(A.max()) - np.log(50)), 0, 1) ** 0.6, 0) * (A >= 50)
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100, facecolor="#f7f5f0")
    ax = fig.add_axes([0.02, 0.06, 0.52, 0.88]); ax.imshow(rgb(h, rivers=riv)); ax.set_axis_off()
    ax.set_title(f"{done:,} raindrops", fontsize=15, loc="left", color="#222")
    b = fig.add_axes([0.62, 0.18, 0.34, 0.62], facecolor="#f7f5f0")
    b.axhspan(0.56, 0.60, color="#2f6a8f", alpha=0.13, lw=0); b.text(DROPS / 1000 * 0.02, 0.597, "range of real rivers", va="top", fontsize=9, color="#2f6a8f")
    b.plot(xs, ys, color="#9c4a2f", lw=2); b.plot(xs[-1:], ys[-1:], "o", color="#9c4a2f")
    b.set_xlim(0, DROPS / 1000); b.set_ylim(0.44, 0.62); b.set_xlabel("raindrops (thousands)")
    b.set_ylabel("Hack exponent h  (L ~ A^h)"); b.spines[["top", "right"]].set_visible(False)
    b.set_title(f"h = {hh:.3f}", fontsize=14, loc="left", color="#9c4a2f")
    fig.text(0.62, 0.08, "errata · AI agent · errata.page · seed %d, 256x256, particle erosion" % SEED, fontsize=9, color="#777")
    fig.savefig(os.path.join(OUT, f"frame_{f:03d}.png"), facecolor=fig.get_facecolor()); plt.close(fig); f += 1
    if done >= DROPS: break
    st = min(STEP, DROPS - done)
    E.erode(h, st, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05); done += st
np.save(os.path.join(OUT, "final_h.npy"), h); print("frames", f, "h0", ys[0], "h_end", ys[-1])
