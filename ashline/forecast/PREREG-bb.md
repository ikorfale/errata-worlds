# Pre-registered: budget + border scoring for Ashline season 2 (plan #493; zenith 101532, 101556)

PREREG-budget.md found a budget alone turns the season into a draw (tied top 0.979); budget + border was a lead
(tied 0.390, P1 strictly first 0.171), not a result. This test decides it, with the tie rule written first.

- Script: `s2_bb.py` (this commit). Command: `python3 s2_bb.py 2000 2493` (K=2000 per row, seed 2493).
  Rows: field exp/seek x timing early/late x focal seat P1/P3 x focal policy exp/seek/seek2 = 24 rows; each focal
  policy reruns the same seeds, so focal differences are paired: attendance and seeding cells have their own rng stream per season
  (identical draw sequence across rows); placement draws start from the same state and diverge only once play differs.
  (Changed after the smoke, before the run: the smoke used one shared stream.)
- Field: season 1's attendance p = 1.00/0.92/0.50/0.42/0.17/0.08, B=6 for every seat and house, 12x12, 14 ticks,
  border scoring, no expiry (PREREG-budget result: not needed under one move per tick).
- **Tie rule, fixed now** (zenith 101556: nothing timing-based, since early-spend pressure hurts irregular seats):
  among seats tied on score, 1) fewest own submitted moves turned to ash, 2) most cells touching another player;
  a tie surviving both is a shared win, reported as shared.
- Seen before writing this: smoke K=20 seed 1 (field exp, early, focal P1): seek - exp focal win +0.49±0.12,
  seek2 +0.30±0.12; and K=10 seed 1 (field seek, early, focal P1, exp vs seek): -0.10±0.16. After the rng fix: K=30 seed 1 (field exp, early, focal P1) seek - exp
  +0.26±0.08. Nothing else.

Decision rule: budget + border goes into the season 2 draft only if, on **both** decision rows (early timing,
focal P1 playing what the field plays: field exp/focal exp, and field seek/focal seek), all of:
1. tied top after the tie rule <= 0.20, and raw tied top <= 0.50 (the tie rule may not be what carries it);
2. P1 (p=1.00) strictly first after the tie rule <= 0.40;
3. top seat not the top attender >= 0.30 (turnout test criterion);
4. a house strictly first <= 0.25 (written in plan #493 before this file);
and, choice matters: in field exp, |win(seek) - win(exp)| for focal P1 or P3 (early) is >= 0.05 and >= 3 SE.
If the field-exp row passes and the field-seek row fails, the verdict is "not adopted: passes only while players
ignore the scoring", because the smoke says seek pays and players copy what pays.

Predictions (mine): seek beats exp for a lone seeker in field exp by more than 0.2 win share; in field seek the
advantage of seeking is gone (|difference| < 0.1); raw tied top under 0.5 on all rows; ash under 1 per season on
every row (budget caps contact).

Review before freezing: Fable, blocking-only. Round 1 found one: one rng stream for attendance and policy, so the
focal rows were not common-random-number pairs (estimate and SE still valid). Fixed: per-season streams as above.
Round 2 found one: arng.choice consumed a board-dependent number of words, so attendance could drift out of step
after tick 2. Fixed: two uniforms per seat per tick, always drawn; the seed index uses the second.
