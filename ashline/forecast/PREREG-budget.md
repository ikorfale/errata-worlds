# Pre-registered: a fixed move budget for Ashline season 2 (plan #492; zenith 101532)

The turnout test (PREREG-turnout.md) found that no scoring rule or board size gets choices past turnout: under
season 1's attendance the regular wins. This test changes what turnout buys: every seat, houses included, gets B=6
moves for the 14-tick season (the seeding move counts; houses spend theirs on ticks 1-6, or 1-3 and 8-10 under expiry).

- Script: `s2_budget.py` (this commit). Command: `python3 s2_budget.py 2000 2410` (K=2000 per row, seed 2410;
  12 rows: expiry 0/1 x base/border x early/late/half).
- Field: season 1's observed attendance p = 1.00/0.92/0.50/0.42/0.17/0.08, all seats place with exp.
- Seen before writing this: smoke runs K=5 and K=40 at seed 1 (also used to find that unbudgeted houses then win
  every season, so houses got the budget too). In the K=40 smoke the primary statistic was 0.55-0.72 on early rows
  and 0.32-0.41 on late rows; base/late P1 win share 0.52.
- One structural fact found while writing it, not a result: a seat makes at most one move per tick, so "spend late"
  cannot put a budget of 6 into ticks 13-14; the latest a regular can spend 6 is ticks 9-14.

Statistics, per row:
1. Primary (as #492 was written): share of seasons where the top-scoring seat is not the top attender.
   Criterion from the turnout test: >= 0.30. **Caveat written before the full run:** the smoke shows this statistic
   passes for a reason that is not "choices decide": with a budget the three most regular seats tie on moves and
   all play exp, so the winner among them is placement luck. So passing it is necessary, not sufficient.
2. Win share by seat (ties split), tied-top share, P1 strictly first. Second criterion (added after the smoke, said
   so): on base/early the regular (p=1.00) is strictly first in at most 0.40 of seasons AND the top is tied in at
   most 0.50 of seasons. A tie-split share alone could pass through ties (three seats on 6 cells give P1 0.33
   while P1 is tied first every season), which is the same hole as the caveat on 1 (Fable round 3).
3. zenith's pile-up question: player moves per tick and ash per tick, with the share in ticks 13-14.
   Prediction (mine): on late rows the 13-14 share of moves is under 0.30 (the one-move-per-tick cap spreads late
   spending over ticks 9-14), and ash stays under 0.5 per season on every row (exp avoids contact on 12x12).
4. Expiry (zenith's guard, applied to houses too: B/2 per week, houses spend ticks 1-3 and 8-10; at most 2 carried): prediction, it changes the primary statistic by less
   than 0.05 on early rows, because the cap already prevents the end-of-season pile-up it guards against.

Decision rule: the budget goes into the season 2 draft if 1 and 2 both hold on base/early. Expiry is decided by the
cap, not by this run (Fable review): with one move per tick a late regular spends ticks 9-14, so its 13-14 share is
2/6 and the row share is bounded by 0.33; the pile-up expiry guards against cannot happen under the one-move rule.
The run only confirms the bound; expiry stays out unless the rule ever allows more than one move per tick.

Review before freezing: Fable, blocking-only. Round 1 found two: the expiry threshold was unreachable by
construction, and expiry rows did not give houses the weekly budget. Both fixed above. Round 2 found one: the late hold was re-checked every tick, so P3/P4 alternated
hold/spend; now a one-way release (per week under expiry), as the policy was written. Round 3 found one:
criterion 2 on a tie-split share passes through ties; restated on strict wins plus a tie cap, outputs added.
No round 4: the round-3 change only adds two outputs and rewords a criterion; said here rather than hidden.

## Result (run after ffba336, `s2_budget.txt`, K=2000, seed 2410)

    row (B=6)               not-top-attender  tied top  P1 strictly first  house first  13-14 move share  ash/season
    base   early            0.598±0.004       0.979     0.007              0.002        0.05              0.10
    base   late             0.503±0.005       0.922     0.063              0.004        0.21              0.08
    border early            0.621±0.009       0.390     0.171              0.136        0.05              0.10
    border late             0.533±0.010       0.366     0.248              0.139        0.21              0.08
    expiry base early       0.577±0.005       0.977     0.008              0.004        0.06              0.10
    expiry border early     0.597±0.009       0.385     0.185              0.117        0.06              0.10

- Criterion 1 passes everywhere, criterion 2 **fails** on the decision row base/early: the top is tied in 0.979 of
  seasons. With a budget and contact-free play every seat that can spend 6 moves ends on 6 cells. **A budget under
  season 1 scoring is not adopted**: it does not let choices decide, it turns the season into a draw.
- Not the pre-registered decision row, so a lead and not a result: border/early meets both criteria (tied 0.390,
  P1 strictly first 0.171), house strictly first 0.136. Budget plus border scoring is the candidate for the next
  pre-registered test.
- zenith's pile-up: late rows put 0.21-0.22 of player moves into ticks 13-14 (prediction < 0.30: right) and ash
  stays <= 0.10 per season (prediction < 0.5: right). Late spending is spread over ticks 9-14 by the one-move cap.
- Expiry changes the primary statistic by 0.021 (early base) and 0.024 (early border): prediction < 0.05, right.
  Not needed under the one-move rule.
- Found in the output, not predicted: holding moves costs the irregular seats. Under late timing P2 (p=0.92) is
  released at tick 9 with 6 moves and 6 ticks, misses about one in twelve, and its win share falls 0.310 -> 0.204
  (base) while P1's rises 0.305 -> 0.398. "late" and "half" rows are identical because seats with p <= 0.42 are
  released at tick 1 (0.42 x 14 <= 6) and P3 at tick 3 either way, so "half" differs from "late" only for seats
  whose late rule already equals early.
