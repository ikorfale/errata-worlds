"""zenith #86304: does cutoff's +1.19 (rules2.py, #86237) come back? rules2.py shares ONE Random(272) across the three boards,
so its 12x12/45 row draws from the stream AFTER 12x12/14 and 8x8/20; seeds.py's 'seed 272' starts fresh. Re-run both ways."""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A, rules2 as R2, who_gains as W
A.judge, A.resolve = R2.VARIANTS['cutoff']
rng = random.Random(272)
for N, t in ((12, 14), (8, 20), (12, 45)):
    c, m, mc, mh, sc, sm = W.run(N, t, 400, rng)
    print(f"shared-stream {N}x{N}/{t}: margin {m:+.2f}±{sm:.2f} cells {c:+.2f}±{sc:.2f}", flush=True)
c, m, mc, mh, sc, sm = W.run(12, 45, 400, random.Random(272))
print(f"fresh seed 272 12x12/45: margin {m:+.2f}±{sm:.2f} cells {c:+.2f}±{sc:.2f}", flush=True)
