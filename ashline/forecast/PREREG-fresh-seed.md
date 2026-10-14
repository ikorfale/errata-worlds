# Pre-registration: fresh-seed rerun of 12x12/45 cc (zenith #87014/#87016)

Written and committed before the run (14.10.2026 ~10:45 UTC).

- Question: is the near-zero paired border2 - base difference on 12x12/45 against a cc field (+0.17±0.48, seed 273)
  a real raider exception, or the minimum of six cells picking up noise?
- Run: `python3 paired.py 200 cc 12/45 20261014` — new seed block 20261014, 200 paired seasons, base and border2 on the same draws.
- Reading: if the paired diff stays within 2 SE of zero, the raider exception stands. If it is above 2 SE (as the other
  long-board cells were, +1.1..+1.8), the seed-273 cell was the low tail, and the worst-case claim gets reworded.
- Same commit: the three missing mixes (tt, hc, tc) on the seed-273 draws for 10x10/30 and 12x12/45, completing the table.
