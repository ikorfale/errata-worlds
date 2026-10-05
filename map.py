"""Final map: terrain + lakes + rivers drawn by drainage area."""
import numpy as np, sys
sys.path.insert(0, ".")
import render as R, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
p = sys.argv[1]; key = sys.argv[2] if len(sys.argv) > 2 else "_h"
import rivers as RV
h = np.load(p + key + ".npy"); filled, rf, _ = RV.flood(h); lake = filled - h
rec, order = RV.steepest(filled, rf, 0.3, np.random.default_rng(1)); rec.ravel()[(h < 0).ravel()] = -1
A, L = RV.accumulate(rec, order, h.shape)
land = h >= 0
riv = np.clip((np.log10(A) - 2.0) / 1.6, 0, 1) * land          # visible from ~100 cells upstream
riv = np.maximum(riv, ((lake > 2e-3) & land) * 1.0)
img = R.rgb(h, rivers=riv * 0.9)
fig, a = plt.subplots(figsize=(8, 8), dpi=120); a.imshow(img); a.set_axis_off()
fig.tight_layout(pad=0.2); fig.savefig(p + key + "_map.png", facecolor="white")
