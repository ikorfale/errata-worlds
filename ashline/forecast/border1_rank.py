"""border1 (rules2.py) through rank.py: does the order of finish leave attendance more often than under season 1 rules?"""
import random, rules2 as R2, rank, ashline as A
A.judge = R2.VARIANTS['border1'][0]
rng = random.Random(2721)
for N, ticks in ((8, 20), (12, 45)):
    d, f, t, med, reach, tu = rank.run(N, ticks, 200, rng, True)
    print(f"border1 mixed {N}x{N} {ticks} ticks  discordant pairs {d:.1%}  level {f:.1%}  leader not a move leader {t:.0%}", flush=True)
