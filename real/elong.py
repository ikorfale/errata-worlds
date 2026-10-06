"""#146: is Greenland's extra main-stem length straight (elongated basins) or wiggly? Bets in bets_ice.txt (written first).
D = great-circle km, the largest distance between an end of the main stem's head reach and an end of the outlet reach; S = L/D; E = D/sqrt(A)."""
import numpy as np, struct, json
from hack import load, D as DD
BOX = {'Greenland': ('gr', (-75, -10, 59, 84)), 'Baffin': ('ar', (-91, -61, 61, 74)), 'Ellesmere+Devon': ('ar', (-100, -60, 74.4, 84)),
       'Iceland': ('eu', (-25, -13, 63, 67))}
def centres(region, idx):
    base = f'{DD}/HydroRIVERS_v10_{region}_shp/HydroRIVERS_v10_{region}'
    shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); xy = np.zeros((len(idx), 2))
    with open(base + '.shp', 'rb') as f:
        for k, o in enumerate(shx[idx, 0].astype(np.int64) * 2):
            f.seek(o + 12); b = struct.unpack('<4d', f.read(32)); xy[k] = ((b[0]+b[2])/2, (b[1]+b[3])/2)
    return xy
def ends(region, idx):                                   # first and last vertex of each reach polyline
    base = f'{DD}/HydroRIVERS_v10_{region}_shp/HydroRIVERS_v10_{region}'
    shx = np.fromfile(base + '.shx', dtype='>i4', offset=100).reshape(-1, 2); e = np.zeros((len(idx), 2, 2))
    with open(base + '.shp', 'rb') as f:
        for k, o in enumerate(shx[idx, 0].astype(np.int64) * 2):
            f.seek(o + 8 + 36); np_, npt = struct.unpack('<2i', f.read(8)); f.seek(4 * np_, 1)
            p = np.frombuffer(f.read(16 * npt), '<f8').reshape(-1, 2); e[k] = p[0], p[-1]
    return e
def gc(a, b):
    la1, la2 = np.radians(a[:, 1]), np.radians(b[:, 1]); dl = np.radians(b[:, 0] - a[:, 0])
    return 6371 * 2 * np.arcsin(np.sqrt(np.sin((la2-la1)/2)**2 + np.cos(la1)*np.cos(la2)*np.sin(dl/2)**2))
cache = {}; res = {}
for name, (reg, box) in BOX.items():
    if reg not in cache: cache[reg] = load(reg, {'NEXT_DOWN', 'MAIN_RIV', 'DIST_DN_KM', 'DIST_UP_KM', 'UPLAND_SKM'})
    r = cache[reg]; mr, dd = r['MAIN_RIV'], r['DIST_DN_KM']
    out = np.flatnonzero((r['NEXT_DOWN'] == 0) & (r['UPLAND_SKM'] >= 10) & (r['UPLAND_SKM'] <= 1000) & (r['DIST_UP_KM'] > 0))
    ox = centres(reg, out); k = (ox[:, 0] >= box[0]) & (ox[:, 0] <= box[1]) & (ox[:, 1] >= box[2]) & (ox[:, 1] <= box[3])
    out, ox = out[k], ox[k]
    sel = np.isin(mr, mr[out]); idx = np.flatnonzero(sel)
    order = idx[np.lexsort((-dd[idx], mr[idx]))]; first = np.r_[True, mr[order][1:] != mr[order][:-1]]
    head_of = dict(zip(mr[order][first].astype(np.int64), order[first]))
    he, oe = ends(reg, np.array([head_of[int(m)] for m in mr[out]])), ends(reg, out)
    A, L = r['UPLAND_SKM'][out], r['DIST_UP_KM'][out]
    Dk = np.max([gc(he[:, i], oe[:, j]) for i in (0, 1) for j in (0, 1)], axis=0)   # straight source-to-mouth, endpoints of the two reaches
    ok = Dk > 0.5
    S, E = L[ok] / Dk[ok], Dk[ok] / np.sqrt(A[ok])
    res[name] = {'n': int(ok.sum()), 'n_D<=0.5km': int((~ok).sum()), 'median S=L/D': round(float(np.median(S)), 3),
                 'median E=D/sqrtA': round(float(np.median(E)), 3), 'median L/sqrtA': round(float(np.median(L[ok] / np.sqrt(A[ok]))), 3),
                 'median A': round(float(np.median(A[ok])), 1),
                 'slope logD~logA': round(float(np.polyfit(np.log10(A[ok]), np.log10(Dk[ok]), 1)[0]), 3), 'slope logL~logA': round(float(np.polyfit(np.log10(A[ok]), np.log10(L[ok]), 1)[0]), 3)}
    print(name, res[name], flush=True)
json.dump(res, open('out/elong.json', 'w'), indent=1)
