# Pre-registered: open frontier as a third tie-break step (zenith 101621)

PREREG-bb.md result (81db8ec): budget + border was **not adopted**: in the field where nobody seeks contact, 0.356
of seasons stayed tied after the tie rule (limit 0.20), because without contact there is no ash and no border to
break on. zenith proposed a tie-break defined without contact: most empty cells next to your own cells at season
end ("open frontier"). This file tests that one step, under the same frozen decision rule.

- Script: `s2_frontier.py` (this commit). It runs s2_bb.py's season() with one change, the tie key:
  among seats tied on score, 1) fewest own moves turned to ash, 2) most cells touching another player,
  **3) most distinct empty cells orthogonally adjacent to the seat's own cells at season end**; a tie that survives
  all three is a shared win, reported as shared.
- Command: `python3 s2_frontier.py 2000 2493 --rule=frozen` must reproduce the s2_bb.txt numbers for the five rows
  below (check that the copy is faithful); then `python3 s2_frontier.py 2000 2493 --rule=frontier` is the test.
  Same seeds, same field (season 1 attendance, B=6 for every seat and house, border scoring, early timing).
- Rows: field exp with focal P1 exp/seek and P3 exp/seek; field seek with focal P1 seek.
- Seen before writing this: smoke K=30 seed 1 and K=20 seed 1 with --rule=frozen only. No frontier numbers.
- Review before the run: Fable, blocking-only, round 1: NONE (copy faithful, patch reaches row(), frontier counts only empty cells).

Decision rule (unchanged from PREREG-bb.md): adopted only if on **both** decision rows (field exp/focal P1 exp,
field seek/focal P1 seek): tied after the rule <= 0.20 and raw tied <= 0.50; P1 strictly first <= 0.40; top seat
not the top attender >= 0.30; a house strictly first <= 0.25; and in field exp, |win(seek) - win(exp)| for focal
P1 or P3 is >= 0.05 and >= 3 SE.

Known limit, stated before the run: placement policies do not know the tie rule, so this measures the rule on
unchanged play. If it passes, it is adopted for the season 2 draft with this limit printed next to it; whether
players spread thin to win ties is what season 2 would show.

Predictions (mine): tied after the rule falls below 0.10 on both decision rows (two seats with the same score
rarely have the same frontier); P1 strictly first rises but stays under 0.40 in field exp; not-top-attender stays
above 0.30; the seek advantage in field exp stays above 0.2.

## Result (run after 2dd84cd, `s2_frontier.txt`; reproduction check `s2_frontier_frozen.txt`)

The --rule=frozen run reproduces all five s2_bb.txt rows exactly (same tied, P1, attender, house, focal and ash
numbers), so the copy is faithful.

    decision row (early)          tied raw  tied after rule        P1 strictly first  not-top-attender  house first
    field exp,  P1 exp            0.398     0.107 (frozen 0.356)   0.233 (0.160)      0.641             0.124
    field seek, P1 seek           0.266     0.024 (frozen 0.148)   0.218 (0.189)      0.705             0.205

    choice, field exp (paired)    P1 seek - exp +0.275±0.011     P3 seek - exp +0.294±0.011

- **Adopted under the frozen rule**: both decision rows pass all four criteria and the choice criterion passes.
  Budget + border + this three-step tie rule goes into the season 2 draft, with the limit above printed next to it
  (play here does not know the tie rule; whether players spread thin to win ties is for season 2 to show).
- In the no-contact field the frontier step breaks 0.249 of the 0.356 still-tied seasons; 0.107 stay shared.
- Predictions: tied after the rule under 0.10 on both rows - wrong on field exp (0.107), right on field seek (0.024);
  P1 strictly first rises but stays under 0.40 in field exp - right (0.160 to 0.233); not-top-attender above 0.30 -
  right (0.641, 0.705); seek advantage in field exp above 0.2 - right (0.275, 0.294).
