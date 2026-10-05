"""Follow-up to mouths.py: are big outlet basins capped by the island? For each outlet with A>500: D (outlet to head, straight)
against R = distance from the outlet to the island's highest cell. Bet (05.10 21:35, before running): on lateral 2.0 maps,
median D/R of big outlets >= 0.7 on >= 3 of 4 seeds (their heads sit near the central divide, so length cannot grow with A)."""
import numpy as np, json, sys, os
sys.path.insert(0, "lab/worlds")  # run from the parent of lab/worlds, like the other scripts
import rivers as R, decompose as Dc
out = open("lab/worlds/out/mouths_cap.jsonl", "a")
for seed in (7, 11, 23, 42):
    for lat in (0.0, 2.0):
        h = np.load(f"lab/worlds/out/latd_{seed}_{lat}_800000.npy").astype(float)
        filled, rec_f, _ = R.flood(h)
        rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
        A, L, D = Dc.accumulate_head(rec, order, h.shape)
        outs = R.basin_outlets(A, rec, h); m = h.shape[1]
        top = np.unravel_index(np.argmax(h), h.shape)
        oj, oi = np.divmod(outs, m); Rr = np.hypot(oj - top[0], oi - top[1])
        Ab, Db, Lb = A.ravel()[outs], D.ravel()[outs], L.ravel()[outs]
        bg = Ab > 500; sm = (Ab >= 50) & (Ab <= 500)
        row = {"seed": seed, "lateral": lat, "n_big": int(bg.sum()),
               "DR_big_med": float(np.median(Db[bg] / Rr[bg])), "DR_small_med": float(np.median(Db[sm] / Rr[sm])),
               "L_big_med": float(np.median(Lb[bg])), "R_big_med": float(np.median(Rr[bg])),
               "corr_logA_logL_big": float(np.corrcoef(np.log(Ab[bg]), np.log(Lb[bg]))[0, 1])}
        row = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row.items()}
        out.write(json.dumps(row) + "\n"); out.flush(); print(row, flush=True)
