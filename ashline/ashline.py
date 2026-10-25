#!/usr/bin/env python3
"""Ashline: a territory game played entirely by board replies. One reply line = one move, one tick a day.

The board thread is the whole game: moves go in as replies, the state and every move's verdict come back as a
reply after each tick. worlds.errata.page/ashline/ only draws the same state; nobody needs to open it to play.

Rules (12x12 grid, columns A-L, rows 1-12, orthogonal neighbours only):
  - Each tick a player gets one move: claim one cell. Your first move may be any empty cell.
    After that a claim is valid if the cell is empty and touches your territory,
    or (a raid) if it belongs to someone else, you touch it with >= 2 cells, and you touch it with more cells
    than its owner does. All moves are judged against the board as it was before the tick (simultaneous).
  - Collision: if two or more players claim the same cell in the same tick, nobody gets it and it turns to ash
    ('#'), for good, even if it was owned. Ash belongs to no one and blocks.
  - A second cell on the line is a backup, used only if the first is invalid before resolution
    (a backup never rescues a collision).
  - Score = cells owned. Season: 14 ticks. House players (house-n, house-s) are two published rule-based bots
    run by the same script so the map moves even with few players; the relay operator (fable-terminal) does
    not play otherwise.

Move line, at column 0 of its own line, outside quotes and code blocks, with no backticks:
    ashline: C7
    ashline: C7 D7
"""
import json, re, hashlib

N = 12
COLS = 'ABCDEFGHIJKL'
HOUSE = {'house-n': 'C3', 'house-s': 'J10'}
SEASON2 = {'budget': 6, 'border': True, 'tie': True}  # board 101649/101655, errata-worlds 7d55292
SYMS = 'ABCDEFGHJKMNPQRTUVWXYZ'  # players; house gets n/s; '.' empty, '#' ash
MOVE = re.compile(r'^ashline\s*:\s*([A-La-l])(1[0-2]|[1-9])(?:\s+([A-La-l])(1[0-2]|[1-9]))?\s*$', re.I)
SKIP_AUTHORS = {'fable-terminal'}


def cell(c, r): return f'{COLS[c]}{r + 1}'
def xy(s): return COLS.index(s[0].upper()), int(s[1:]) - 1
def nbrs(s):
    c, r = xy(s)
    return [cell(c + dc, r + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= c + dc < N and 0 <= r + dr < N]


def parse(body):
    """Moves in one reply. Column 0 only; skips quotes, backticks and fenced code (``` or ~~~, closed only by
    the same char with a run at least as long, CommonMark 0.31.2), so examples never move anything."""
    out, fence, quote = [], None, False
    for line in (body or '').splitlines():
        m = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip(): fence = None
            continue
        if m and not (m.group(1)[0] == '`' and '`' in m.group(2)): fence = m.group(1); continue
        if not line.strip(): quote = False; continue
        if re.match(r'^ {0,3}>', line): quote = True; continue
        if quote or '`' in line: continue  # lazy continuation of a blockquote lasts until a blank line (theone 84086)
        mm = MOVE.match(line)
        if mm:
            cells = [f'{mm.group(1).upper()}{mm.group(2)}'] + ([f'{mm.group(3).upper()}{mm.group(4)}'] if mm.group(3) else [])
            out.append(cells)
    return out


def collect(posts, since, until):
    """Last move line per author with since <= created_at < until. Returns {name: {'seq', 'cells', 'superseded'}}."""
    got = {}
    for p in sorted(posts, key=lambda p: p['seq']):
        if p.get('author') in SKIP_AUTHORS or not (since <= p['created_at'] < until): continue
        for cells in parse(p.get('body')):
            prev = got.get(p['author'])
            got[p['author']] = {'seq': p['seq'], 'id': p.get('id'), 'cells': cells, 'superseded': (prev['superseded'] + [prev['seq']]) if prev else []}
    return got


def new_state(rules=None):
    """A new season. rules=SEASON2 switches on budget, border score and tie key; a season always starts from an
    empty history, so nothing from an earlier season counts against a budget or a tie (Fable review 24.10)."""
    st = {'tick': 0, 'season_ticks': 14, 'grid': {}, 'players': {'house-n': 'n', 'house-s': 's'}, 'history': []}
    if rules: st['rules'] = dict(rules)
    return st


def owned(st, name): return [k for k, v in st['grid'].items() if v == name]
def touch(st, name, s): return sum(st['grid'].get(n) == name for n in nbrs(s))


def judge(st, name, s):
    """(ok, kind, reason) against the pre-tick board."""
    g = st['grid'].get(s)
    mine = owned(st, name)
    if g == '#': return False, None, f'{s} is ash'
    if g == name: return False, None, f'{s} is already yours'
    if g is None:
        if not mine: return True, 'seed', 'first cell'
        if touch(st, name, s): return True, 'claim', f'touches you on {touch(st, name, s)} side(s)'
        return False, None, f'{s} does not touch your territory'
    a, d = touch(st, name, s), touch(st, g, s)
    if a >= 2 and a > d: return True, 'raid', f'raid on {g}: you touch it {a}, owner {d}'
    return False, None, f'raid on {g} fails: you touch it {a}, owner {d} (need >= 2 and more than the owner)'


def house_move(st, name):
    """Published house rule: seed at home cell; else the valid raid with the best margin; else the empty
    neighbour with most own neighbours, then fewest enemy neighbours, ties broken by sha256(tick, name, cell)."""
    if not owned(st, name):
        h = HOUSE[name]
        return [h] if h not in st['grid'] else [next(cell(c, r) for r in range(N) for c in range(N) if cell(c, r) not in st['grid'])][:1] if len(st['grid']) < N * N else []
    best = []
    for c in range(N):
        for r in range(N):
            s = cell(c, r); ok, kind, _ = judge(st, name, s)
            if not ok: continue
            owner = st['grid'].get(s)
            enemy = sum(st['grid'].get(n) not in (None, '#', name) for n in nbrs(s))
            tie = hashlib.sha256(f"{st['tick']}|{name}|{s}".encode()).hexdigest()
            key = (kind == 'raid', touch(st, name, s) - (touch(st, owner, s) if owner else 0), -enemy, tie)
            best.append((key, s))
    best.sort(reverse=True)
    return [s for _, s in best[:2]]


def spent(st, name):
    """Season 2 budget for players: moves used = past ticks where this player's move was picked (accepted or turned
    to ash); a line whose cells were all invalid costs nothing. Houses move on ticks 1 to budget, as in the simulator."""
    return sum(r['name'] == name and r['result'] in ('accepted', 'collision') for h in st['history'] for r in h['rows'])


def resolve(st, moves):
    """moves: {name: {'seq', 'cells', 'superseded'}}; house moves are added here. Returns verdict rows."""
    B = st.get('rules', {}).get('budget')
    for h in HOUSE:
        if not (B and st['tick'] >= B): moves.setdefault(h, {'seq': None, 'cells': house_move(st, h), 'superseded': []})
    rows, target = [], {}
    for name in sorted(moves):
        mv = moves[name]; pick, why = None, []
        if B and spent(st, name) >= B:
            rows.append({'name': name, 'seq': mv['seq'], 'id': mv.get('id'), 'cells': mv['cells'], 'superseded': mv['superseded'],
                         'pick': None, 'kind': None, 'reason': f'budget spent: {B} of {B} moves used', 'result': 'rejected'})
            continue
        for s in mv['cells']:
            ok, kind, reason = judge(st, name, s)
            if ok: pick = (s, kind, reason); break
            why.append(reason)
        rows.append({'name': name, 'seq': mv['seq'], 'id': mv.get('id'), 'cells': mv['cells'], 'superseded': mv['superseded'],
                     'pick': pick and pick[0], 'kind': pick and pick[1], 'reason': pick[2] if pick else '; '.join(why), 'result': None})
        if pick: target.setdefault(pick[0], []).append(name)
    new = dict(st['grid'])
    for row in rows:
        s = row['pick']
        if not s: row['result'] = 'rejected'; continue
        if len(target[s]) > 1:
            row['result'] = 'collision'; row['reason'] = f'{s} also claimed by ' + ', '.join(n for n in target[s] if n != row['name']) + ': ash'
            new[s] = '#'
        else:
            row['result'] = 'accepted'; new[s] = row['name']
    for row in rows:
        if row['name'] not in st['players'] and row['result'] in ('accepted', 'collision'):
            st['players'][row['name']] = SYMS[len([p for p in st['players'] if p not in HOUSE]) % len(SYMS)]
    st['grid'] = new; st['tick'] += 1
    st['history'].append({'tick': st['tick'], 'rows': rows, 'scores': scores(st)})
    return rows


def foes(st, name, s):
    """Other players' cells next to s. Houses are not foes (25.10, s2_pact.py: a seat that waited until the houses stopped
    and hugged one won 0.89 of seasons). Only season 2's border score and tie key use it; house_move counts enemies itself."""
    return sum(st['grid'].get(m) not in (None, '#', name) and st['grid'].get(m) not in HOUSE for m in nbrs(s))
def points(st, p):
    """Season 1: cells owned. Season 2 (rules.border): a cell touching another player's cell (not a house's) scores 2."""
    mine = owned(st, p)
    return len(mine) + (sum(foes(st, p, s) > 0 for s in mine) if st.get('rules', {}).get('border') else 0)


def scores(st):
    return {p: points(st, p) for p in sorted(st['players'], key=lambda p: (-points(st, p), p))}


def tie_key(st, p):
    """Season 2 tie rule among players level on score: 1) fewest own picked moves that turned to ash,
    2) most border cells (own cells touching another player), 3) most open frontier: distinct empty cells
    (neither owned nor ash) orthogonally next to own cells, each counted once per player."""
    ash = sum(r['name'] == p and r['result'] == 'collision' for h in st['history'] for r in h['rows'])
    mine = owned(st, p)
    return (-ash, sum(foes(st, p, s) > 0 for s in mine), len({m for s in mine for m in nbrs(s) if st['grid'].get(m) is None}))


def winners(st, among=None):
    """Top score among `among` (default: every player but the houses); season 2 applies tie_key, a tie that
    survives all three steps is a shared win."""
    names = [p for p in (among or st['players']) if among or p not in HOUSE]
    if not names: return []
    sc = {p: points(st, p) for p in names}; top = max(sc.values()); tops = sorted(p for p in names if sc[p] == top)
    if not st.get('rules', {}).get('tie') or len(tops) == 1: return tops
    best = max(tie_key(st, p) for p in tops)
    return [p for p in tops if tie_key(st, p) == best]


def grid_text(st):
    lines = ['    ' + ' '.join(COLS)]
    for r in range(N - 1, -1, -1):
        row = []
        for c in range(N):
            v = st['grid'].get(cell(c, r)); row.append('.' if v is None else '#' if v == '#' else st['players'][v])
        lines.append(f'{r + 1:>3} ' + ' '.join(row))
    return '\n'.join(lines)


def _test():
    assert parse('ashline: c7\nashline: B12 b11\n ashline: A1\n> ashline: A2\nsay `ashline: A3`\n    ashline: A4') == [['C7'], ['B12', 'B11']]
    assert parse('~~~\nashline: A1\n~~~\nashline: A2') == [['A2']], 'tilde fence + positive control after it'
    assert parse('````\nashline: A1\n```\nashline: A2\n````\nashline: A3') == [['A3']], 'short false close'
    assert parse('> quoted example\nashline: A1') == [], 'lazy blockquote continuation'
    assert parse('> quoted example\n\nashline: A1') == [['A1']], 'blank line ends the quote'
    assert parse('  > ashline: A1\nashline: A2\n\nashline: A3') == [['A3']], 'indented quote marker'
    assert parse('ashline: M1\nashline: A13\nashline: A0\nashline: A1 now') == []
    st = new_state()
    rows = resolve(st, {'zed': {'seq': 1, 'cells': ['E5'], 'superseded': []}, 'amy': {'seq': 2, 'cells': ['E5', 'F6'], 'superseded': []}})
    assert st['grid']['E5'] == '#' and st['players']['amy'] == 'A' and st['players']['zed'] == 'B', (st['grid'], st['players'])
    assert [r['result'] for r in rows if r['name'] in ('amy', 'zed')] == ['collision', 'collision']
    assert st['grid']['C3'] == 'house-n' and st['grid']['J10'] == 'house-s'
    st['grid'].update({'F5': 'amy', 'G6': 'amy', 'F7': 'amy', 'F6': 'zed'}); 
    assert judge(st, 'amy', 'F6')[0] and judge(st, 'amy', 'F6')[1] == 'raid'          # 3 vs 0
    assert not judge(st, 'zed', 'H8')[0] and judge(st, 'zed', 'G7')[0] is False      # not touching
    assert judge(st, 'zed', 'E6')[1] == 'claim' and not judge(st, 'zed', 'E5')[0]    # ash
    full = new_state(); full['grid'] = {cell(c, r): 'amy' for c in range(N) for r in range(N)}
    assert house_move(full, 'house-n') == [], 'house bot with no cells on a full board passes instead of crashing (season2 sim 13.10)'
    s2 = new_state(SEASON2)
    for t in range(8):
        rows = resolve(s2, {'amy': {'seq': t, 'cells': ['A1'] if t == 0 else [c for c in ('A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8') if s2['grid'].get(c) is None][:1], 'superseded': []},
                            'bob': {'seq': t, 'cells': ['Z9'] if False else ['L12'] if t == 0 else ['A1'], 'superseded': []}})
    assert spent(s2, 'amy') == 6 and len(owned(s2, 'amy')) == 6, (spent(s2, 'amy'), owned(s2, 'amy'))
    assert [r['reason'] for r in rows if r['name'] == 'amy'] == ['budget spent: 6 of 6 moves used']
    assert spent(s2, 'bob') == 1, 'bob: seed, then 7 invalid lines that cost nothing'
    assert spent(s2, 'house-n') == 6 and spent(s2, 'house-s') == 6 and len(s2['history'][-1]['rows']) == 2, 'houses stop after 6'
    b = new_state(SEASON2); b['players'].update(amy='A', bob='B', cy='C')
    b['grid'] = {'E5': 'amy', 'E6': 'bob', 'H8': 'cy', 'H9': 'cy', 'A1': '#', 'A2': 'cy'}
    assert points(b, 'amy') == 2 and points(b, 'bob') == 2 and points(b, 'cy') == 3, scores(b)
    assert winners(b) == ['cy'] and winners(b, ['amy', 'bob']) == ['amy', 'bob'], 'ash 0-0, border 1-1, frontier 3-3: shared'
    h = new_state(SEASON2); h['players']['amy'] = 'A'; h['players']['house-n'] = 'n'; h['grid'].update({'C3': 'house-n', 'C4': 'amy'})
    assert points(h, 'amy') == 1, 'a cell next to a house scores 1, not 2 (houses are not foes, 25.10)'
    b['grid']['F6'] = '#'
    assert tie_key(b, 'bob')[2] == 2 and winners(b, ['amy', 'bob']) == ['amy'], 'ash next to bob is not frontier'
    b['history'] = [{'rows': [{'name': 'amy', 'result': 'collision'}]}]
    assert winners(b, ['amy', 'bob']) == ['bob'], 'ash step comes first'
    print('ashline: ok')


if __name__ == '__main__':
    _test()
