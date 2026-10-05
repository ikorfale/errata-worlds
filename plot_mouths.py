"""Chart for #140: outlet basins, L vs A, lateral 0 vs 2.0, seed 7 (800k drops); grey band = distance to island top."""
import numpy as np, sys, os
sys.path.insert(0, "lab/worlds")  # run from the parent of lab/worlds
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import rivers as R, decompose as Dc
fig, axs = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
for ax, lat, col in zip(axs, (0.0, 2.0), ("#4a6fa5", "#b5532b")):
    h = np.load(f"lab/worlds/out/latd_7_{lat}_800000.npy").astype(float)
    filled, rec_f, _ = R.flood(h)
    rec, order = R.steepest(filled, rec_f, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
    A, L, D = Dc.accumulate_head(rec, order, h.shape)
    outs = R.basin_outlets(A, rec, h); Ab, Lb = A.ravel()[outs], L.ravel()[outs]
    top = np.unravel_index(np.argmax(h), h.shape); oj, oi = np.divmod(outs, h.shape[1]); Rr = np.hypot(oj - top[0], oi - top[1])
    b = Ab >= 50
    ax.scatter(Ab[b], Lb[b], s=18, color=col, alpha=.8, label="river mouths")
    ax.axhspan(np.percentile(Rr[b & (Ab > 500)], 25), np.percentile(Rr[b & (Ab > 500)], 75), color="0.85", zorder=0,
               label="distance mouth → island top\n(big basins, middle half)")
    x = np.logspace(np.log10(50), np.log10(Ab.max()), 50)
    for e, ls in ((0.5, ":"), (0.6, "--")):
        ax.plot(x, Lb[b].mean() / np.exp(np.mean(np.log(Ab[b])) * e) * x**e * 0 + np.exp(np.mean(np.log(Lb[b]))) * (x / np.exp(np.mean(np.log(Ab[b]))))**e,
                ls, color="0.3", lw=1, label=f"slope {e}")
    sm, bg = b & (Ab <= 500), Ab > 500
    hs, hb = Dc.slope(Ab[sm], Lb[sm]), Dc.slope(Ab[bg], Lb[bg])
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("basin area A (cells)")
    ax.set_title(f"bank erosion {lat:g}: small mouths h={hs:.2f}, big h={hb:.2f}", fontsize=10)
    ax.grid(alpha=.3, which="both", lw=.4)
axs[0].set_ylabel("main stream length L (cells)"); axs[1].legend(fontsize=8, loc="lower right")
fig.suptitle("Why river mouths stay low: big rivers reach the island's divide and stop growing longer (seed 7, 800k drops)", fontsize=11)
fig.tight_layout(); fig.savefig("lab/worlds/out/mouths_seed7.png", dpi=130); print("ok")
