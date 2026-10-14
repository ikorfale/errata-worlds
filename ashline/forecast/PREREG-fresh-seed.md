# Pre-registration: fresh-seed rerun of 12x12/45 cc (zenith #87014/#87016)

Written and committed before the run (14.10.2026 ~10:45 UTC).

- Question: is the near-zero paired border2 - base difference on 12x12/45 against a cc field (+0.17±0.48, seed 273)
  a real raider exception, or the minimum of six cells picking up noise?
- Run: `python3 paired.py 200 cc 12/45 20261014` — new seed block 20261014, 200 paired seasons, base and border2 on the same draws.
- Reading: if the paired diff stays within 2 SE of zero, the raider exception stands. If it is above 2 SE (as the other
  long-board cells were, +1.1..+1.8), the seed-273 cell was the low tail, and the worst-case claim gets reworded.
- Same commit: the three missing mixes (tt, hc, tc) on the seed-273 draws for 10x10/30 and 12x12/45, completing the table.

## Addendum, 14.10 ~10:50 UTC (written after seeing data, so not pre-registered in the strict sense)

Seen before this addendum: fresh-seed 12x12/45 cc = +1.25±0.43; seed-273 12x12/45 tt = +0.47±0.48 (a second low cell).
Rather than rerun whichever cell looks low, rerun all six 12x12/45 mixes on seed 20261014 (cc again included, same draws,
so it must reproduce +1.25). Report both blocks side by side and the per-mix mean of the two independent blocks.
