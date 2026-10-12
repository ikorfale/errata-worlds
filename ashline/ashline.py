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
    out, fence = [], None
    for line in (body or '').splitlines():
        m = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip(): fence = None
            continue
        if m and not (m.group(1)[0] == '`' and '`' in m.group(2)): fence = m.group(1); continue
        if line.startswith('>') or '`' in line: continue
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
            got[p['author']] = {'seq': p['seq'], 'cells': cells, 'superseded': (prev['superseded'] + [prev['seq']]) if prev else []}
    return got


def new_state():
    return {'tick': 0, 'season_ticks': 14, 'grid': {}, 'players': {'house-n': 'n', 'house-s': 's'}, 'history': []}


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
        return [h] if h not in st['grid'] else [next(cell(c, r) for r in range(N) for c in range(N) if cell(c, r) not in st['grid'])]
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


def resolve(st, moves):
    """moves: {name: {'seq', 'cells', 'superseded'}}; house moves are added here. Returns verdict rows."""
    for h in HOUSE: moves.setdefault(h, {'seq': None, 'cells': house_move(st, h), 'superseded': []})
    rows, target = [], {}
    for name in sorted(moves):
        mv = moves[name]; pick, why = None, []
        for s in mv['cells']:
            ok, kind, reason = judge(st, name, s)
            if ok: pick = (s, kind, reason); break
            why.append(reason)
        rows.append({'name': name, 'seq': mv['seq'], 'cells': mv['cells'], 'superseded': mv['superseded'],
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


def scores(st):
    return {p: len(owned(st, p)) for p in sorted(st['players'], key=lambda p: (-len(owned(st, p)), p))}


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
    print('ashline: ok')


if __name__ == '__main__':
    _test()
