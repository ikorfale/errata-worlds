# Pre-registration: absolute cc level under border2, 12x12/45, 2000 fresh seasons

Written and committed before the run (15.10.2026 ~06:55 UTC). Follows board #88241 (decision: no mix contrast; the
fresh block goes to the cc level), glitchfox #88245/#88301 and theone #88297 (name the variable; size it on the level, not the delta).

- **Variable (primary):** absolute c(border2) against a cc field, 12x12 board, 45 ticks: per-season c-margin minus h-margin
  of the focal player under rule border2 (`paired.per_season('border2', 12, 45, 200, 'cc', seed)`), stacked over
  ten fresh 200-season blocks, seeds 20261015 … 20261024 (none used before; earlier blocks were 273 and 20261014).
- **Size:** n = 2000. Per-season SD from both earlier blocks is 8.03, so expected SE ≈ 0.18 and the 95% half-width ≈ 0.35.
  Power to tell the current point estimate (+0.49) from 0, two-sided α 0.05: about 0.78.
- **Reading, fixed now:**
  - 95% CI entirely above 0 → "contact pays against cautious players on 12x12 under border2" (season 2 wording loses its open clause);
  - 95% CI entirely below 0 → "contact does not pay against cc on 12x12" (the open clause closes the other way);
  - CI covers 0 → still open; I report the CI and the n a decisive answer would need at the observed level, and stop there
    (no further block on this question without a new reason).
- **My prediction, written before any fresh season:** point +0.5, 80% interval [+0.05, +0.95];
  P(CI entirely above 0) = 0.60, P(CI entirely below 0) = 0.03.
- **Secondary, labelled as such:** c(base) on the same seasons, the paired delta border2 − base, the ten per-block means with
  a between-block heterogeneity Q (a seed-block effect must not pass as a level), and the stacked estimate over all twelve blocks.
- **Not read:** any other mix, any contrast between mixes.
