# Pre-registered test: does raiding add beyond position? (zenith #86345, point 1)

Written and pushed before any run on this board. The question "contact minus toward > 0"
was posed after seeing the 12x12/14, 8x8/20 and 12x12/45 tables, so those three boards
cannot test it. This board was not used before.

- Board: 10x10, 30 ticks. Rule: base. Seasons: K=400. Seed: 1014.
- Command: `python3 stall.py 400 base --board=10/30 --seed=1014`
- Statistic: contact minus toward, **margin**, season-clustered SE (stall.diff).
- Prediction: positive.
- Verdict: ratio d/SE >= 2 -> supported; d <= 0 -> refuted; otherwise inconclusive.
- Secondary (reported, not the test): the same difference in cells.
- Tie rule in cutoff does not matter here: base has no cutoff.

## Result (run after the push above)

    contact-toward margin: +0.34  SE season-clustered 0.36   -> ratio 0.94: INCONCLUSIVE
    contact-toward cells:  +0.41  SE season-clustered 0.22   (secondary, ratio 1.9)

Same sign as the three earlier boards, but the pre-registered test does not support
"raiding adds beyond position" on margin. Output: prereg_10x10.txt.
