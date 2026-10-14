# Enclosure scoring for season 2? (task #271, 14.10)

Rule tested: an empty 4-connected region of <= 4 cells bordered by one player only counts for that player (enclosure.py).

| 8x8, move p 0.9 / attendance U(0.3,1) | result |
|---|---|
| R2(score~moves), house rule / random | 0.965 / 0.818 (plain 0.965 / 0.850): the house rule makes no pockets |
| evolve + 'pocket' feature vs house seat, fresh seeds | margin +2.9, win 65% (house seat -1.45, 11%) |
| all seats evolved policy: R2, pocket cells/player, rival-touch rate | 0.78, 1.84, 16.6% |
| same weights, pocket weight 0 | 0.87, 0.83, 9.7% |
| plain scoring, same moves | 0.96, 0, 9.7% |
| single-owner regions at tick 14 | sizes 1-4 only (377/236/142/100): cap does not bind at game end |

Reviewed by a second model (Fable 5.1), which changed the reading:
- The R2 drop is NOT skill evidence: identical policies in all seats means everything moves don't explain is luck;
  half the drop arrives with pocket weight 0. Needed: mixed seats (evolved/house/random) with shared attendance
  schedules, rotated over starting cells, score ~ moves + policy + seat, partial R2 of policy.
- Pockets are nearly uncounterable: judge() requires touching own territory, so only a zero-cell seed (any empty
  cell, pocket included) or a 1-move spoil from an adjacent rival breaks one.
- Predicted degenerate human line: a raid-proof corner fort (C2,C1,C3,B3,A3 seals A1,A2,B1,B2) plus an edge comb,
  ~1.8 points per move with no contact. Not yet tested. Contact rate here went UP (9.7% -> 16.6%), but the linear
  policy never found the fort.
Status: not adopted. Next: scripted corner fort vs evolved and house (seat rotation), and a 'spoil' feature.

## 12x12 (the season-1 board), same test
- evolve + pocket vs house seat, fresh seeds: margin +5.2, win 74% (house seat -1.3, 4%). Top weight: foe_dist (stay far
  from rivals), then margin, pocket. Raids 0, collisions 0.
- all seats evolved policy (K=100): R2 0.89, pocket cells/player 1.93, **first-choice cell touching a rival: 0.0%**.
**Verdict on #271: rejected for season 2.** On the season-1 board, enclosure scoring rewards farming pockets far from
everyone: the opposite of the contact the season-2 rule is meant to create.
