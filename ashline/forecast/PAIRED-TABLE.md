# Paired border2 - base difference of c, full table (plan #275, zenith #87014/#87016)

200 paired seasons per cell, base and border2 on the same draws (paired.py). Raw lines: paired.txt, paired_rest.txt (seed 273),
paired_fresh6.txt (seed 20261014, pre-registered in PREREG-fresh-seed.md; the six-mix rerun is an addendum written after data).

| mix | 10x10/30, seed 273 | 12x12/45, seed 273 | 12x12/45, seed 20261014 | 12x12/45, mean of both blocks |
|-----|-------------------|--------------------|--------------------------|-------------------------------|
| hh  | +0.51±0.26 | +1.40±0.39 | +1.90±0.38 | +1.65±0.27 |
| tt  | +0.74±0.34 | +0.47±0.48 | +0.93±0.44 | +0.70±0.33 |
| cc  | +1.09±0.32 | +0.17±0.48 | +1.25±0.43 | +0.71±0.32 |
| ht  | +1.18±0.29 | +1.76±0.40 | +0.57±0.44 | +1.17±0.30 |
| hc  | +1.10±0.29 | +1.65±0.42 | +0.88±0.44 | +1.27±0.30 |
| tc  | +0.82±0.34 | +1.03±0.45 | +1.45±0.39 | +1.24±0.30 |

Reading (pre-registered rule: within 2 SE of zero on the fresh seed = the raider exception stands):
- Fresh-seed cc = +1.25±0.43, 2.9 SE above zero. The exception does not stand; seed-273 cc was a low draw.
- All 18 cells are positive. On the two-block means every 12x12 mix is >2 SE above zero; the smallest are tt and cc (~+0.7±0.3).
- Block-to-block gaps (cc 1.08, ht 1.19) are 1.7-2.0 SE of a difference: noise of the size the SEs predict, maybe a little more.
  Picking the minimum of six cells with SE ~0.45 is expected to land ~0.6 below the mean, which is what seed 273 did twice.
- Season 2 wording: "border2 raises the worth of contact over base in every tested mix and board; smallest gain ~+0.7 on 12x12."
