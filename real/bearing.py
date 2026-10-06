"""#151 follow-up: are Greenland's strip basins aligned with meridians (a geographic-grid artefact) or with the coast?
Bearing of the straight head-to-mouth line; share within 20 deg of N-S, against 22% for uniform directions. Bets in bets_ice.txt."""
import numpy as np, json
from hack import load
exec(open('elong.py').read().split('\ncache = {}')[0])
BOXES = {'Greenland': ('gr', (-75, -10, 59, 84)), 'Baffin': ('ar', (-91, -61, 61, 74)), 'Ellesmere+Devon': ('ar', (-100, -60, 74.4, 84))}
cache = {}; res = {}
for name, (reg, box) in BOXES.items():
    if reg not in cache: cache[reg] = load(reg, {'NEXT_DOWN', 'MAIN_RIV', 'DIST_DN_KM', 'DIST_UP_KM', 'UPLAND_SKM'})
    r = cache[reg]; mr, dd = r['MAIN_RIV'], r['DIST_DN_KM']
    out = np.flatnonzero((r['NEXT_DOWN'] == 0) & (r['UPLAND_SKM'] >= 10) & (r['UPLAND_SKM'] <= 1000) & (r['DIST_UP_KM'] > 0))
    ox = centres(reg, out); k = (ox[:, 0] >= box[0]) & (ox[:, 0] <= box[1]) & (ox[:, 1] >= box[2]) & (ox[:, 1] <= box[3]); out, ox = out[k], ox[k]
    order = np.lexsort((-dd, mr)); first = np.r_[True, mr[order][1:] != mr[order][:-1]]
    head_of = dict(zip(mr[order][first].astype(np.int64), order[first]))
    hx = centres(reg, np.array([head_of[int(m)] for m in mr[out]]))
    dy = hx[:, 1] - ox[:, 1]; dx = (hx[:, 0] - ox[:, 0]) * np.cos(np.radians((hx[:, 1] + ox[:, 1]) / 2))
    Dk = 111.2 * np.hypot(dx, dy); A = r['UPLAND_SKM'][out]; E = Dk / np.sqrt(A); ok = Dk > 0.5
    ang = np.degrees(np.arctan2(np.abs(dx), np.abs(dy)))          # 0 = N-S, 90 = E-W
    res[name] = {}
    for lab, m in [('E>1.5', ok & (E > 1.5)), ('E<=1.5', ok & (E <= 1.5))]:
        res[name][lab] = {'n': int(m.sum()), 'N-S within 20deg %': round(100 * float((ang[m] < 20).mean()), 1), 'E-W within 20deg %': round(100 * float((ang[m] > 70).mean()), 1)}
    for lo, hi in [(59, 70), (70, 76), (76, 80), (80, 84)]:
        m = ok & (ox[:, 1] >= lo) & (ox[:, 1] < hi)
        if m.sum() >= 20: res[name][f'lat {lo}-{hi}'] = {'n': int(m.sum()), 'median E': round(float(np.median(E[m])), 2), 'N-S %': round(100 * float((ang[m] < 20).mean()), 1)}
    print(name, json.dumps(res[name]), flush=True)
json.dump(res, open('out/bearing.json', 'w'), indent=1)
