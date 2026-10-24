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

## Result (run after the commit above, `s2_turnout.txt`)

    base   exp    not-top-mover leader 0.001±0.001  house strictly first 0.075±0.006  ash 0.23  raids 0.13
    base   mixed  not-top-mover leader 0.036±0.004  house strictly first 0.577±0.011  ash 1.24  raids 0.56
    border exp    not-top-mover leader 0.207±0.008  house strictly first 0.326±0.010  ash 0.23  raids 0.13
    border mixed  not-top-mover leader 0.232±0.009  house strictly first 0.260±0.010  ash 1.24  raids 0.56

Border/exp = 0.207±0.008: below the 0.30 criterion, inside my predicted 0.10-0.25. **Border scoring alone is not
adopted.** It does make choices matter in about one season in five (against 0.001 under season 1 scoring), but it
also lifts "house strictly first" from 0.075 to 0.326: the houses earn the border bonus too. Next: a smaller board,
under the same attendance field and criterion, before season 2 is announced.

## Addendum 1: smaller boards (written before running them)

- Command: `python3 s2_turnout.py 2000 2410 --n=10 --mix=exp` and the same with `--n=8`; houses rescaled as
  season2.py does; a late joiner with no empty cell 3 steps from both houses seeds on any empty cell, or not at all.
- Seen before writing this: a K=3 smoke run on 8x8 base/exp (to check the code runs). Nothing else.
- Same statistic and the same 0.30 criterion, for each (board, rule) row with all-exp seats.
- Prediction (mine): 8x8 border passes (>= 0.30), 10x10 border does not; base stays below 0.10 on both.
- If a row passes, I also report house strictly first for it; a rule that passes by handing the season to the houses
  (house strictly first > 0.5) is not adopted either.
