"""zenith #86240: is 'border2 + cutoff cancel on 12x12/45' real or one seed's surprise? rules2.py harness (who_gains.run),
same 400-season size, five seeds per variant. Prints c (margin) per seed, the mean and the spread across seeds.
Usage: python3 seeds.py"""
import sys, os, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, rules2 as R2, who_gains as W

for v in sys.argv[1:] or ('base', 'border2', 'cutoff', 'both'):
    A.judge, A.resolve = R2.VARIANTS[v]; ms = []
    for seed in (272, 1, 2, 3, 4):
        c, m, mc, mh, sc, sm = W.run(12, 45, 400, random.Random(seed)); ms.append(m)
        print(f"{v:8s} seed {seed:3d}  margin {m:+.2f}±{sm:.2f}  cells {c:+.2f}±{sc:.2f}", flush=True)
    print(f"{v:8s} mean {np.mean(ms):+.2f}  sd across seeds {np.std(ms, ddof=1):.2f}", flush=True)
print(f"equal splits {R2.TIES['n']}, fallback used {R2.TIES['fallback']}", flush=True)
