"""Season 2 on smaller boards (#256: forced contact). Does a smaller board shrink the pact's edge (lone seats meet
rivals anyway and score border points too) and change which step decides seasons?
Field, seeds, resolver, houses-not-foes, 14 ticks, B=6: s2_steps.py / s2_front_pact.py. Only the board changes:
N=12 houses C3,J10 (the live rule); N=10 C3,H8; N=8 C3,F6 (each house two cells in from its corner, as on 12x12).
Rows per board: A all exp | B pact P1+P2 | C P3 front. Pact value = B-A (pair share), front value = C-A (P3 share).
Usage: python3 s2_board.py [K] [seed]"""
import sys
import numpy as np
import s2_steps as S
from s2_steps import A, SEATS
import s2_front_pact as FP

HOUSES = {12: ('C3', 'J10'), 10: ('C3', 'H8'), 8: ('C3', 'F6')}

if __name__ == '__main__':
    pos = sys.argv[1:]
    K = int(pos[0]) if pos else 1000
    seed = int(pos[1]) if len(pos) > 1 else 2510
    S.NOHOUSE = True
    i = {n: SEATS.index(n) for n in SEATS}
    for N in (12, 10, 8):
        A.N = N; A.HOUSE = dict(zip(('house-n', 'house-s'), HOUSES[N]))
        print(f'--- board {N}x{N}, houses {A.HOUSE}', flush=True)
        a = FP.run('A', (), (), K, seed); b = FP.run('B', (('P1', 'P2'),), (), K, seed); c = FP.run('C', (), ('P3',), K, seed)
        FP.paired('P1+P2 pact value (B-A), win share', b[0], a[0], [i['P1'], i['P2']], K)
        FP.paired('P3 front value (C-A), win share', c[0], a[0], [i['P3']], K)
