"""Smoke test of the season-2 scoring path with a small ensemble (ENS=4) in a scratch dir: 3 ticks, two claims, some digs."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tick as T
d = tempfile.mkdtemp(dir=os.path.expanduser('~')); T.ST = os.path.join(d, 'state'); T.SITE = os.path.join(d, 'site'); os.makedirs(T.ST)
T.ENS = 4; T.SEASON = 2; T.SEASON_END = '2099-01-01T00:00Z'
import numpy as np
land = np.argwhere((T.W0 > 0.2 * T.RELIEF)); (y1, x1), (y2, x2) = land[0], land[-1]
for t in range(1, 4):
    acts = [{'id': f'a{t}', 'at': f'2026-10-13T0{t}:00:00Z', 'name': 'p1', 'op': 'claim' if t == 1 else 'dig', 'x': int(x1), 'y': int(y1)},
            {'id': f'b{t}', 'at': f'2026-10-13T0{t}:00:01Z', 'name': 'p2', 'op': 'claim', 'x': int(x2), 'y': int(y2)}]
    json.dump(acts, open(os.path.join(d, 'a.json'), 'w')); T.run(acts)
st = json.load(open(os.path.join(T.SITE, 'state.json')))
print(json.dumps({'ens': st['hack']['ensemble'], 'claims': [{k: c.get(k) for k in ('name', 'area', 'total', 'beyond_chaos', 'beyond_chaos_p')} for c in st['claims']], 'titles': st['season']['titles']}))
import shutil; shutil.rmtree(d)

# theone 82273: ties belong to both tails
from tick import rank as _rank
import numpy as _np
assert _rank(0, _np.zeros(100))['p_low'] == 1 and _rank(0, _np.zeros(100))['p_high'] == 1
r = _rank(0, _np.ones(100)); assert r['p_low'] == round(1 / 101, 4) and r['p_high'] == 1
r = _rank(5, _np.array([4] + [5] * 99)); assert r['p_low'] == 1 and r['ties'] == 99
r = _rank(0.5, _np.arange(100) + 0.0); assert r['p_low'] == round(2 / 101, 4) and r['p_high'] == round(100 / 101, 4)
print('rank ties: ok')
