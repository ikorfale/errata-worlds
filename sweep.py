"""Hack's exponent as erosion proceeds: seeds x droplet counts; lake cells reported separately."""
import numpy as np, json, sys
sys.path.insert(0, ".")
import erode as E, rivers as R
out = open("out/sweep.jsonl", "w")
for seed in (7, 11, 23, 42):
    rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng); done = 0
    for target in (0, 25000, 50000, 100000, 200000, 400000, 800000):
        if target > done: E.erode(h, target - done, rng, scale=60, radius=3, cap=1.0, erode_rate=0.05); done = target
        filled, rec, order = R.flood(h); A, L = R.accumulate(rec, order, h.shape)
        land = h >= 0; lake = (filled - h) > 1e-4
        row = dict(seed=seed, drops=done, order=len(order), land=int(land.sum()), lake=int((lake & land).sum()))
        row["flood"] = [round(R.hack(A, L, land, a)[0], 4) for a in (50, 200)]
        for jit in (0.0, 0.3):
            r2, o2 = R.steepest(filled, rec, jit, np.random.default_rng(1)); r2.ravel()[(h < 0).ravel()] = -1
            A2, L2 = R.accumulate(r2, o2, h.shape)
            row[f"steep{jit}"] = [round(R.hack(A2, L2, land, a)[0], 4) for a in (50, 200)]
        rec, A, L = r2, A2, L2  # basins below use jittered steepest descent
        outs = R.basin_outlets(A, rec, h); Ab, Lb = A.ravel()[outs], L.ravel()[outs]; b = Ab >= 50
        row["basins"] = [round(float(np.polyfit(np.log(Ab[b]), np.log(Lb[b]), 1)[0]), 3), int(b.sum())]
        if seed == 7: np.save(f"out/s7_{done}.npy", h.astype(np.float32))
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
