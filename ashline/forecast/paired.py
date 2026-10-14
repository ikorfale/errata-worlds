"""Paired base - border2 difference of c, same seasons (mixes.py draws are shared across rules). Promised in board #86998.
Usage: python3 paired.py K mix[,mix] N/ticks[,N/ticks] [seed]   (seed default 273 = the mixes.py draws)"""
import sys, random
import numpy as np
import mixes as M

def per_season(v, N, ticks, K, mix, seed=273):
    M.A.judge, M.A.resolve = M.R2.VARIANTS[v]
    out = []
    orig = M.np.mean
    M.np.mean = lambda x: (out.append(list(x)), orig(x))[1]   # capture d_m (first call) without copying run()
    try: M.run(N, ticks, K, mix, random.Random(seed))
    finally: M.np.mean = orig
    return np.array(out[0])

if __name__ == '__main__':
    K = int(sys.argv[1]); mixes = sys.argv[2].split(','); boards = [tuple(map(int, b.split('/'))) for b in sys.argv[3].split(',')]
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 273
    for N, ticks in boards:
        for mix in mixes:
            b = per_season('base', N, ticks, K, mix, seed); g = per_season('border2', N, ticks, K, mix, seed); d = g - b
            print(f"seed {seed} {N}x{N} {ticks:2d}t {mix}: base {b.mean():+.2f}  border2 {g.mean():+.2f}  paired diff {d.mean():+.2f}±{d.std(ddof=1)/np.sqrt(len(d)):.2f}", flush=True)
