"""Greenland: is the low Hack h (0.445) an ice-sheet effect? Split outlets by whether the head of their main stem lies on
Natural Earth 1:10m glaciated areas. Bets in bets_ice.txt (written before this ran)."""
import numpy as np, struct, json
from matplotlib.path import Path
from hack import load, fit, D
def rings(shp, box):
    out = []
    with open(shp, 'rb') as f:
        f.seek(100); data = f.read()
    o = 0
    while o + 8 <= len(data):
        ln = struct.unpack('>i', data[o+4:o+8])[0] * 2; c = data[o+8:o+8+ln]; o += 8 + ln
        if struct.unpack('<i', c[:4])[0] != 5: continue
        x0, y0, x1, y1 = struct.unpack('<4d', c[4:36])
        if x1 < box[0] or x0 > box[1] or y1 < box[2] or y0 > box[3]: continue
        np_, npt = struct.unpack('<2i', c[36:44]); parts = list(struct.unpack(f'<{np_}i', c[44:44+4*np_])) + [npt]
        pts = np.frombuffer(c[44+4*np_:44+4*np_+16*npt], '<f8').reshape(-1, 2)
        out.append([Path(pts[parts[i]:parts[i+1]]) for i in range(np_)])
    return out
def on_ice(xy, recs):
    inside = np.zeros(len(xy), bool)
    for rs in recs:
        par = np.zeros(len(xy), int)
        for p in rs: par += p.contains_points(xy)
        inside |= (par % 2 == 1)
    return inside
def centres(region, idx):
    base = f'{D}/HydroRIVERS_v10_{region}_shp/HydroRIVERS_v10_{region}'
    shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); xy = np.zeros((len(idx), 2))
    with open(base + '.shp', 'rb') as f:
        for k, o in enumerate(shx[idx, 0].astype(np.int64) * 2):
            f.seek(o + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0]+b[2])/2, (b[1]+b[3])/2)
    return xy
r = load('gr', {'HYRIV_ID', 'NEXT_DOWN', 'MAIN_RIV', 'DIST_DN_KM', 'DIST_UP_KM', 'UPLAND_SKM'})
mr, dd = r['MAIN_RIV'], r['DIST_DN_KM']
order = np.lexsort((-dd, mr)); first = np.r_[True, mr[order][1:] != mr[order][:-1]]
head_of = dict(zip(mr[order][first].astype(np.int64), order[first]))        # main river id -> reach index of its head
out = np.flatnonzero((r['NEXT_DOWN'] == 0) & (r['UPLAND_SKM'] >= 10) & (r['DIST_UP_KM'] > 0))
heads = np.array([head_of[int(m)] for m in mr[out]])
xy = centres('gr', heads); ox = centres('gr', out)
recs = rings(f'{D}/ne_glac/ne_10m_glaciated_areas.shp', (-75, -10, 59, 84))
ice, mouth_ice = on_ice(xy, recs), on_ice(ox, recs)
A, L = r['UPLAND_SKM'][out], r['DIST_UP_KM'][out]; rng = np.random.default_rng(1); res = {'ice_polys': len(recs)}
for name, s in [('all outlets A>=10', np.ones(len(out), bool)), ('head on ice', ice), ('head off ice', ~ice),
                ('head off ice, A 10-1000', ~ice & (A <= 1000)), ('head on ice, A 10-1000', ice & (A <= 1000))]:
    res[name] = fit(A[s], L[s], rng, 500) if s.sum() >= 20 else int(s.sum()); print(name, res[name], flush=True)
res['mouth on ice (tidewater?)'] = int(mouth_ice.sum()); res['median A on/off'] = [float(np.median(A[ice])), float(np.median(A[~ice]))]
print(res['mouth on ice (tidewater?)'], res['median A on/off'])
json.dump(res, open('out/ice.json', 'w'), default=float, indent=1)
