"""Which erosion law keeps Hack's h near real rivers? 4 islands x variants, 0 and 400k drops."""
import numpy as np, json, sys
sys.path.insert(0, ".")
import erode as E, rivers as R
V = {"base": {}, "no_deposit": {"deposit": False}, "inertia0.3": {"inertia": 0.3},
     "evap0.06": {"evap": 0.06}, "radius1": {"radius": 1}}
out = open("out/variants.jsonl", "w")
for seed in (7, 11, 23, 42):
    for name, kw in V.items():
        rng = np.random.default_rng(seed); h = E.spectral_heightmap(256, 3.2, rng)
        args = dict(scale=60, radius=3, cap=1.0, erode_rate=0.05); args.update(kw)
        E.erode(h, 400000, rng, **args)
        f, rf, _ = R.flood(h); rec, order = R.steepest(f, rf, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
        A, L = R.accumulate(rec, order, h.shape); land = h >= 0
        row = dict(seed=seed, variant=name, land=int(land.sum()), finite=bool(np.isfinite(h).all()))
        try:  # a variant can wash the island away or blow up (no deposition crashed the 05.10 run): record, go on
            row.update(h50=round(R.hack(A, L, land, 50)[0], 4), h200=round(R.hack(A, L, land, 200)[0], 4),
                       relief=round(float(h[land].max()), 3), lake=int(((f - h) > 1e-4).sum()))
        except (TypeError, ValueError) as e:
            row["error"] = str(e)
        if seed == 7: np.save(f"out/var7_{name}.npy", h.astype(np.float32))
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
