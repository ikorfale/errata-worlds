"""Task #271: enclosure scoring. An empty region (4-connected, None cells) whose bordering player cells all belong
to one player counts for that player; ash ('#') and the board edge are walls. A region touching no player counts for
nobody. Question: does R2(score~moves) fall well below 0.9 (score stops being a turnout counter), and does
evolve.py then find a policy that beats the house rule? Real resolver unchanged; only A.scores is swapped.
A region counts only if its size <= CAP (env ENC_CAP, default 4): without a cap a lone player next to open
board would own the whole open board. Usage: ENC_CAP=4 python3 enclosure.py r2 | ENC_CAP=4 python3 enclosure.py evolve N p G"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import ashline as A

_plain = A.scores
CAP = int(os.environ.get('ENC_CAP', '4'))

def sealed(st):
    g = st['grid']; seen = set(); out = {}
    for c in range(A.N):
        for r in range(A.N):
            s = A.cell(c, r)
            if g.get(s) is not None or s in seen: continue
            comp, stack, owners = [], [s], set(); seen.add(s)
            while stack:
                x = stack.pop(); comp.append(x)
                for m in A.nbrs(x):
                    v = g.get(m)
                    if v is None:
                        if m not in seen: seen.add(m); stack.append(m)
                    elif v != '#': owners.add(v)
            if len(owners) == 1 and len(comp) <= CAP:
                o = owners.pop(); out[o] = out.get(o, 0) + len(comp)
    return out

def scores_enc(st):
    base = _plain(st); add = sealed(st)
    tot = {p: base[p] + add.get(p, 0) for p in base}
    return {p: tot[p] for p in sorted(tot, key=lambda p: (-tot[p], p))}

def _test():
    A.N = 4; st = {'grid': {}, 'players': {'a': 'A', 'b': 'B'}}
    for s in ['A2', 'B1']: st['grid'][s] = 'a'          # A1 sealed by a + edge
    st['grid']['D4'] = 'b'
    assert sealed(st).get('a') == 1 and 'b' not in sealed(st), sealed(st)
    st['grid'].clear(); st['grid']['A1'] = 'a'; assert sealed(st) == {}, sealed(st)  # open board is not a pocket
A_N0 = A.N
if CAP >= 1: _test()
A.N = A_N0
A.scores = scores_enc

if __name__ == '__main__':
    if sys.argv[1] == 'r2':
        import attendance  # runs its own loop with the patched scores (prints on import)
    else:
        # evolve.py with one extra feature, 'pocket': sealed cells this player would gain by taking s.
        # Output goes to enc_evolve_N_p_capC.json, never over evolve.py's own files.
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evolve.py')).read()
        extra = '''
_feat0 = features
FEATS = FEATS + ['pocket']
import enclosure as _EN
def features(st, name, s, vsets):
    g = st['grid']; before = _EN.sealed(st).get(name, 0); old = g.get(s); g[s] = name
    after = _EN.sealed(st).get(name, 0)
    if old is None: del g[s]
    else: g[s] = old
    return np.concatenate([_feat0(st, name, s, vsets), [after - before]])
'''
        src = src.replace("\nif __name__ == '__main__':", extra + "\nif __name__ == '__main__':", 1)
        src = src.replace("np.array([1.0, -0.1, 10.0, 1.0, 0, 0, 0, 0])", "np.array([1.0, -0.1, 10.0, 1.0, 0, 0, 0, 0, 0])")
        src = src.replace("f'evolve_{N}_{p}.json'", "f'enc_evolve_{N}_{p}_cap{CAP}.json'")
        assert src.count('pocket') >= 1 and 'enc_evolve_' in src and '0, 0, 0, 0, 0])' in src
        sys.argv = ['evolve.py'] + sys.argv[2:]
        exec(compile(src, 'evolve.py+pocket', 'exec'), {'__name__': '__main__', '__file__': os.path.abspath(__file__), 'CAP': CAP})
