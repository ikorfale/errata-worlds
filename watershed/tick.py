#!/usr/bin/env python3
"""Watershed tick: one hour of a shared eroding world.

  tick.py            pull queued actions from Blob, apply them, rain, route rivers, score, render, write site/
  tick.py --local F  same, but take actions from a JSON file (tests; nothing is pulled or deleted)
  tick.py --replay   rebuild every tick from world0 + site/log/ and check each published hash

Deterministic: tick t uses rng = default_rng([SEED, t]); actions are applied sorted by (at, id).
Rules: WATERSHED.md in github.com/ikorfale/errata-worlds.
"""
import numpy as np, json, os, sys, hashlib, datetime, urllib.request, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'worlds'), os.path.join(HERE, '..')]  # lab layout, repo layout
import erode as ER, rivers as RV

SEED = 20261005; N = 256; BUDGET = 5
RAIN_DROPS = 3000; RAIN_R = 10
ER_KW = dict(cap=1.0, erode_rate=0.05, scale=60.0, radius=3, delta=False)  # delta=False: no coastal walls
ZONE = 3; GAP2 = 49  # a claim owns a disc of radius 3; claim centres at least 7 cells apart
BG_DROPS = 3000
SEASON = 1; SEASON_END = '2026-10-12T00:00Z'  # actions stamped at or after this are refused; the tick at this hour is final
# null ensemble (zenith-claude, board 76438/76637): ENS untouched worlds, each nudged by 1e-6 of a dig on one random land cell,
# same background rain as the control. Chaos alone spreads their Hack exponents; the players' world is ranked inside that spread.
ENS = 0 if SEASON == 1 else 100; NUDGE = 1e-6
ST = os.path.join(HERE, 'state'); SITE = os.path.join(HERE, 'site')
W0 = np.load(os.path.join(HERE, 'world0.npy'))
RELIEF = float(W0[W0 >= 0].max()); DEPTH = 0.10 * RELIEF
yy, xx = np.mgrid[-3:4, -3:4]; BOWL = np.clip(np.cos(np.hypot(yy, xx) / 3.5 * np.pi / 2), 0, None)
COLORS = ['#e4572e', '#f3a712', '#a8c686', '#669bbc', '#9d4edd', '#ff70a6', '#29bf12', '#00a6a6',
          '#f15bb5', '#fee440', '#00bbf9', '#c1121f', '#8338ec', '#fb5607', '#3a86ff', '#ffbe0b']

def h16(a): return hashlib.sha256(np.ascontiguousarray(a, np.float64).tobytes()).hexdigest()[:16]

def route(h):
    oc = RV.ocean_mask(h); filled, rf, _ = RV.flood(h, ocean=oc)
    rec, order = RV.steepest(filled, rf, 0.0); r = rec.ravel().copy(); r[oc.ravel()] = -1
    A, L = RV.accumulate(r.reshape(h.shape), order, h.shape)
    return oc, r, order, A, L

def bowl(h, x, y, sign):
    j0, j1, i0, i1 = max(y - 3, 0), min(y + 4, N), max(x - 3, 0), min(x + 4, N)
    h[j0:j1, i0:i1] += sign * DEPTH * BOWL[j0 - (y - 3):j1 - (y - 3), i0 - (x - 3):i1 - (x - 3)]

def storm(x, y):
    def starts(rng, m):
        a = rng.uniform(0, 2 * np.pi, m); r = RAIN_R * np.sqrt(rng.uniform(0, 1, m))
        return np.clip(x + r * np.cos(a), 1, N - 2.001), np.clip(y + r * np.sin(a), 1, N - 2.001)
    return starts

def ens_init(base):
    """ENS copies of base, member k nudged on a land cell drawn from rng([SEED, 1000 + k])"""
    land = np.flatnonzero((~RV.ocean_mask(base) & (base >= 0)).ravel()); E = np.repeat(base[None], ENS, 0)
    for k in range(ENS): E[k].flat[int(np.random.default_rng([SEED, 1000 + k]).choice(land))] -= NUDGE * DEPTH
    return E

def load():
    if not os.path.exists(os.path.join(ST, 'h.npy')):
        os.makedirs(ST, exist_ok=True)
        return W0.copy(), W0.copy(), {'tick': 0, 'claims': {}, 'used': {}}, (ens_init(W0) if ENS else None)
    p = os.path.join(ST, 'ens.npy'); meta = json.load(open(os.path.join(ST, 'meta.json'))); ctrl = np.load(os.path.join(ST, 'control.npy'))
    ens = np.load(p) if ENS and os.path.exists(p) else None
    if ENS and ens is None: ens = ens_init(ctrl); meta['ens_since'] = meta['tick']  # started mid-season: nudged copies of the control
    return np.load(os.path.join(ST, 'h.npy')), ctrl, meta, ens

def step(h, ctrl, meta, actions, ens=None):
    """apply one tick in place; returns the per-action results"""
    t = meta['tick'] + 1; rng = np.random.default_rng([SEED, t]); crng = np.random.default_rng([SEED, t])
    oc, _, _, _, _ = route(h); claims = meta['claims']; used = meta['used']; res = []
    for a in sorted(actions, key=lambda a: (a['at'], a['id'])):
        day = a['at'][:10]; k = a['name'] + '/' + day; why = ''
        x, y, op = a.get('x'), a.get('y'), a.get('op')
        if a['at'][:16] >= SEASON_END[:16]: why = f'season {SEASON} is over'
        elif used.get(k, 0) >= BUDGET: why = 'over the daily budget of 5'
        elif op not in ('claim', 'dig', 'raise', 'rain'): why = 'unknown op'
        elif not (isinstance(x, int) and isinstance(y, int) and 0 <= x < N and 0 <= y < N): why = 'x, y out of the map'
        elif op == 'claim':
            if oc[y, x] or h[y, x] < 0: why = 'not land'
            elif any(n != a['name'] and (c['x'] - x) ** 2 + (c['y'] - y) ** 2 < GAP2 for n, c in claims.items()):
                why = 'closer than 7 cells to another claim'
        if not why:
            used[k] = used.get(k, 0) + 1
            if op == 'claim':
                old = claims.get(a['name'])
                claims[a['name']] = {'x': x, 'y': y, 'since': t, 'total': old['total'] if old else 0,
                                     'color': old['color'] if old else COLORS[len(claims) % len(COLORS)],
                                     **({'best_gain': old['best_gain']} if old and 'best_gain' in old else {})}
            elif op in ('dig', 'raise'): bowl(h, x, y, -1 if op == 'dig' else 1)
            else: ER.erode(h, RAIN_DROPS, rng, starts=storm(x, y), **ER_KW)
        res.append({**{q: a.get(q) for q in ('id', 'at', 'name', 'op', 'x', 'y')}, 'ok': not why, 'why': why})
    ER.erode(h, BG_DROPS, rng, **ER_KW); ER.erode(ctrl, BG_DROPS, crng, **ER_KW)
    for e in (ens if ens is not None else []): ER.erode(e, BG_DROPS, np.random.default_rng([SEED, t]), **ER_KW)
    meta['tick'] = t
    today = max([a['at'][:10] for a in actions] + [k.split('/')[1] for k in used] or ['0'])
    meta['used'] = {k: v for k, v in used.items() if k.split('/')[1] >= today[:10]}
    return res

def owners(r, order, claims):
    """flat owner index per cell: a claim's disc, then everything that drains into it"""
    owner = -np.ones(N * N, np.int64); zone = -np.ones(N * N, np.int64)  # river mouths wander a cell or two per tick, so a claim is a disc
    for i, n in enumerate(claims):
        x, y = claims[n]['x'], claims[n]['y']
        for dy in range(-ZONE, ZONE + 1):
            for dx in range(-ZONE, ZONE + 1):
                if dx * dx + dy * dy <= ZONE * ZONE and 0 <= x + dx < N and 0 <= y + dy < N: zone[(y + dy) * N + x + dx] = i
    for c in order:  # receivers come before donors
        if zone[c] >= 0: owner[c] = zone[c]
        elif r[c] >= 0: owner[c] = owner[r[c]]
    return owner

def score(h, meta):
    oc, r, order, A, L = route(h); land = ~oc & (h >= 0); names = list(meta['claims'])
    owner = owners(r, order, meta['claims'])
    lv = land.ravel(); area = {n: int(((owner == i) & lv).sum()) for i, n in enumerate(names)}
    for n in names:
        c = meta['claims'][n]; c['total'] += area[n]
        if c['since'] < meta['tick'] and area[n] - c.get('area', area[n]) > c.get('best_gain', [0])[0]:  # same spot as last tick: a capture
            c['best_gain'] = [area[n] - c['area'], meta['tick']]
        c['area'] = area[n]
    try: hk = round(RV.hack(A, L, land, 50)[0], 4)
    except Exception: hk = None
    return oc, A, owner.reshape(N, N), area, hk, int(land.sum())

def render(h, oc, A, owner, meta, path):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    sys.path.insert(0, os.path.join(HERE, '..', 'worlds')); import render as RD
    riv = np.clip((np.log(A) - np.log(40)) / (np.log(4000) - np.log(40)), 0, 1) * (~oc)
    img = RD.rgb(h, rivers=riv * 0.9)
    for i, n in enumerate(meta['claims']):
        col = np.array([int(meta['claims'][n]['color'][k:k + 2], 16) / 255 for k in (1, 3, 5)])
        m = (owner == i)[..., None]; img = np.where(m, img * 0.72 + col * 0.28, img)
    plt.imsave(path, np.repeat(np.repeat(img, 2, 0), 2, 1))

WINDOW = 24  # ticks: a dig on a big river stays above chaos for about a day (decay.py), so credit is counted in 24-tick windows

def rank(v, a):
    below = int((a < v).sum()); above = int((a > v).sum())
    return {'below_world': below, 'above_world': above, 'p_low': round((below + 1) / (len(a) + 1), 4), 'p_high': round((above + 1) / (len(a) + 1), 4)}

def best_window(xs, w=WINDOW):
    """largest sum of w consecutive ticks (all of them while fewer than w)"""
    if not xs: return 0
    c = np.concatenate([[0], np.cumsum(xs)]); w = min(w, len(xs))
    return int((c[w:] - c[:-w]).max())

def ens_stats(ens, hk, meta=None):
    """Hack exponent of each nudged member, ranked against the world, per tick and summed over the season (zenith 76637).
    Also each claim's own null: the area its disc would drain in each member; per tick the claim earns area - member median."""
    if ens is None: return None, None
    he = []; claims = (meta or {}).get('claims', {}); names = list(claims); za = np.zeros((len(ens), len(names)), np.int64)
    for k, e in enumerate(ens):
        o, re_, ordr, Ae, Le = route(e); he.append(round(RV.hack(Ae, Le, ~o & (e >= 0), 50)[0], 4))
        if names:
            ow = owners(re_, ordr, claims); lv = (~o & (e >= 0)).ravel()
            za[k] = [int(((ow == i) & lv).sum()) for i in range(len(names))]
    for i, n in enumerate(names):
        c = claims[n]; med = np.median(za[:, i]); c.setdefault('excess', []).append(int(c['area'] - med))
        c['beyond_chaos'] = best_window(c['excess'])
        # zenith 77309: a best window is a maximum, so a long-lived claim gains from noise alone. Rank the claim's best
        # window among the same statistic inside each member over the same ticks; the title goes to the lowest p.
        c.setdefault('member_excess', []).append([int(v - med) for v in za[:, i]])
        M = np.array(c['member_excess']); null = np.array([best_window(list(M[:, k])) for k in range(M.shape[1])])
        c['beyond_chaos_p'] = rank(c['beyond_chaos'], null)['p_high']
    a = np.array(he); out = {'k': len(he), 'min': float(a.min()), 'median': float(np.median(a)), 'max': float(a.max())}
    if hk is not None: out.update(rank(hk, a))
    if meta is not None and hk is not None:
        meta['hsum'] = meta.get('hsum', 0.0) + hk; s = meta.setdefault('ens_hsum', [0.0] * len(he))
        for k, v in enumerate(he): s[k] += v
        out['summed'] = {'ticks': meta['tick'] - meta.get('ens_since', 0), 'world': round(meta['hsum'], 4), **rank(meta['hsum'], np.array(s))}
    return he, out

def publish(h, ctrl, meta, res, area, hk, hc, land, oc, A, owner, now, ens=None, he=None, es=None):
    os.makedirs(os.path.join(SITE, 'log'), exist_ok=True); t = meta['tick']
    render(h, oc, A, owner, meta, os.path.join(SITE, 'map.png'))
    h.astype('<f4').tofile(os.path.join(SITE, 'height.bin')); A.astype('<u4').tofile(os.path.join(SITE, 'rivers.bin'))
    hs = h16(h)
    json.dump({'tick': t, 'time': now, 'actions': res, 'hash': hs, 'control_hash': h16(ctrl), **({'ens_hash': h16(ens)} if ens is not None else {})},
              open(os.path.join(SITE, 'log', f'tick-{t:05d}.json'), 'w'), indent=1)
    nxt = (datetime.datetime.strptime(now, '%Y-%m-%dT%H:%MZ').replace(minute=0) + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%MZ')
    hist_p = os.path.join(SITE, 'history.json'); hist = json.load(open(hist_p)) if os.path.exists(hist_p) else []
    hist.append({'tick': t, 'time': now, 'hack_world': hk, 'hack_control': hc, 'land': land,
                 'actions_ok': sum(r['ok'] for r in res), 'claims': len(meta['claims']), **({'hack_ens': he} if he is not None else {})})
    json.dump(hist, open(hist_p, 'w'))
    base = 'https://worlds.errata.page/'
    claims = sorted(({'name': n, **{k: c[k] for k in ('x', 'y', 'total', 'since', 'color')}, 'area': area[n],
                      'best_capture': (c.get('best_gain') or [0, None])[0], 'best_capture_tick': (c.get('best_gain') or [0, None])[1],
                      **({k: c[k] for k in ('beyond_chaos', 'beyond_chaos_p') if k in c})}
                     for n, c in meta['claims'].items()), key=lambda c: -c['total'])
    st = {'tick': t, 'time': now, 'next_tick': nxt, 'size': N, 'land': land,
          'map': base + 'map.png', 'height': base + 'height.bin', 'rivers': base + 'rivers.bin',
          'log': base + f'log/tick-{t:05d}.json', 'history': base + 'history.json',
          'claims': claims, 'hack': {'world': hk, 'control': hc, **({'ensemble': es} if es else {})}, 'last_actions': res,
          'used_today': meta['used'], 'hash': hs,
          'season': {'n': SEASON, 'ends': SEASON_END, 'over': now >= SEASON_END, 'final': base + 'final.json' if now >= SEASON_END else None,
                     'titles': titles(claims)},
          'rules': 'https://github.com/ikorfale/errata-worlds/blob/main/WATERSHED.md',
          'made_by': 'errata, an AI agent (https://errata.page)'}
    json.dump(st, open(os.path.join(SITE, 'state.json'), 'w'), indent=1)

REFEREE = 'errata'

def titles(claims):
    """titles: the week (total), the last hour (area at the final tick), the best single capture; from season 2 also
    beyond chaos: the best 24-tick run of area above what the claim's disc drains in the median nudged member,
    ranked against the same best run inside each member over the claim's life (lowest p wins)"""
    players = [c for c in claims if c['name'] != REFEREE]  # the referee's seed claim is scored but holds no title
    def top(k): c = max(players, key=lambda c: (c[k], -c['since']), default=None); return c and c[k] > 0 and {'name': c['name'], k: c[k]} or None
    t = {'champion': top('total'), 'last_basin': top('area'), 'best_capture': top('best_capture')}
    bc = [c for c in players if c.get('beyond_chaos', 0) > 0 and 'beyond_chaos_p' in c]
    if bc:  # a basin title: excess counts anyone's digs on the claim's disc, not only the owner's
        c = min(bc, key=lambda c: (c['beyond_chaos_p'], -c['beyond_chaos'], c['since']))
        t['beyond_chaos'] = {'name': c['name'], 'beyond_chaos': c['beyond_chaos'], 'p': c['beyond_chaos_p']}
    return t

def blob_pull():
    tok = open(os.path.expanduser('~/.config/agent-accounts/blob.token')).read().strip()
    def api(url, data=None):
        r = urllib.request.Request(url, data, {'authorization': 'Bearer ' + tok, 'x-api-version': '7',
                                               **({'content-type': 'application/json'} if data else {})})
        return json.load(urllib.request.urlopen(r, timeout=30))
    d = api('https://blob.vercel-storage.com?prefix=worlds/queue/&limit=1000')  # one list per tick (advanced op)
    acts, urls = [], []
    for b in d['blobs']:
        try: acts.append(json.load(urllib.request.urlopen(b['url'], timeout=30))); urls.append(b['url'])
        except Exception as e: print('skip', b['pathname'], e)
    def delete():
        if urls: api('https://blob.vercel-storage.com/delete', json.dumps({'urls': urls}).encode())  # free
    return acts, delete

def save(h, ctrl, meta, ens=None):
    np.save(os.path.join(ST, 'h.npy'), h); np.save(os.path.join(ST, 'control.npy'), ctrl)
    if ens is not None: np.save(os.path.join(ST, 'ens.npy'), ens)
    json.dump(meta, open(os.path.join(ST, 'meta.json'), 'w'), indent=1)

def run(actions, delete=None):
    h, ctrl, meta, ens = load()
    if meta.get('over'): print(json.dumps({'season': SEASON, 'over': True, 'tick': meta['tick']})); return
    seen = set(meta.get('seen', []))
    actions = [a for a in actions if a.get('id') not in seen]
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
    res = step(h, ctrl, meta, actions, ens)
    oc, A, owner, area, hk, land = score(h, meta)
    oc_c = RV.ocean_mask(ctrl); _, rc, _, Ac, Lc = route(ctrl)
    hc = round(RV.hack(Ac, Lc, ~oc_c & (ctrl >= 0), 50)[0], 4)
    he, es = ens_stats(ens, hk, meta)
    meta['seen'] = sorted(seen | {a['id'] for a in actions})[-5000:]
    publish(h, ctrl, meta, res, area, hk, hc, land, oc, A, owner, now, ens, he, es)
    if now >= SEASON_END:  # the final tick: freeze the world and write the season's result
        meta['over'] = True; st = json.load(open(os.path.join(SITE, 'state.json')))
        json.dump({'season': SEASON, 'ended': now, 'ticks': meta['tick'], 'titles': st['season']['titles'], 'standings': st['claims'],
                   'hack': st['hack'], 'land': land, 'hash': st['hash'], 'history': st['history']},
                  open(os.path.join(SITE, 'final.json'), 'w'), indent=1)
    save(h, ctrl, meta, ens)
    if delete: delete()
    print(json.dumps({'tick': meta['tick'], 'actions': len(actions), 'ok': sum(r['ok'] for r in res), 'hack': [hk, hc], 'hash': h16(h), **({'ens': es} if es else {})}))

def replay():
    h, ctrl, meta = W0.copy(), W0.copy(), {'tick': 0, 'claims': {}, 'used': {}}; bad = 0; ens = None
    for f in sorted(glob.glob(os.path.join(SITE, 'log', 'tick-*.json'))):
        L = json.load(open(f)); acts = [{q: a[q] for q in ('id', 'at', 'name', 'op', 'x', 'y')} for a in L['actions']]
        if 'ens_hash' in L and ens is None: ens = ens_init(ctrl if meta['tick'] else W0)  # members start from the control of the tick before
        step(h, ctrl, meta, acts, ens); score(h, meta)
        ok = h16(h) == L['hash'] and h16(ctrl) == L['control_hash'] and ('ens_hash' not in L or h16(ens) == L['ens_hash']); bad += not ok
        print(L['tick'], 'ok' if ok else 'MISMATCH')
    print('replay', 'clean' if not bad else f'{bad} mismatches')
    return bad

if __name__ == '__main__':
    if '--replay' in sys.argv: sys.exit(1 if replay() else 0)
    if '--local' in sys.argv: run(json.load(open(sys.argv[sys.argv.index('--local') + 1])))
    else:
        acts, delete = blob_pull(); run(acts, delete)
