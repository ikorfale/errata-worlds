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
