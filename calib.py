"""Calibration curve (zenith 74799): how much erosion brings sim rivers to real h ~ 0.54?
Real targets from HydroRIVERS (lab/hack): outlets 0.533-0.553 (6 regions), within-basin median 0.53-0.55.
Same worlds and erosion law as decompose.py; finer drop checkpoints. Writes out/calib.jsonl."""
import numpy as np, json, sys
sys.path.insert(0, "lab/worlds")
import erode as E
from decompose import measure
out = open("lab/worlds/out/calib.jsonl", "w")
for shape in ("island", "plane"):
    for seed in (7, 11, 23, 42):
        rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng, shape); done = 0
        for target in (0, 25000, 50000, 100000, 200000, 400000, 800000):
            if target > done: E.erode(h, target - done, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05); done = target
            row = {"shape": shape, "seed": seed, "drops": done, **measure(h)}
            out.write(json.dumps(row) + "\n"); out.flush(); print(row["shape"], seed, done, row["h"], row["h_out"], flush=True)
