# Pre-registered: does border scoring let choices, not turnout, decide a season with season 1's real attendance?

Written after a Fable review (24.10) pointed out that every earlier season-2 table (s2_choice, s2_seek2, rest point)
set attendance to 1 for all seats, while season 1 was decided by attendance: after 12 ticks, 0 raids, 0 collisions,
0 rejected moves, and the top score equalled the most moves.

- Script: `s2_turnout.py` (this commit). Command: `python3 s2_turnout.py 2000 2410` (K=2000 per row, seed 2410).
- Field: six seats with season 1's observed attendance (12, 11, 6, 5, 2, 1 moves of 12 -> p 1.00/0.92/0.50/0.42/0.17/0.08).
- Seen before writing this: one smoke run, K=20, seed 1 (to check the script runs): not-top-mover leader base/exp 0.00,
  base/mixed 0.05, border/exp 0.18, border/mixed 0.15. Nothing else.
- Primary statistic: share of seasons where the top-scoring player seat is not a top mover among player seats.
- Adoption criterion for season 2 (from the review): border scoring is adopted only if border/exp >= 0.30.
  Below that, attendance still decides most seasons and border alone is not enough; I say so in the season 2 post
  and test a smaller board next, before announcing anything.
- Prediction (mine): border/exp lands between 0.10 and 0.25, so border alone fails the criterion.
- Also reported, not tested: house strictly first, ash and raids per season, and the mixed rows (two regulars seek).
