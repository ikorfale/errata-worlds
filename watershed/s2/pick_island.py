"""Season-2 island for Watershed, picked by a rule written before any candidate was generated (2026-10-07 10:22 UTC).
Same generator and parameters as season 1 (erode.py, 100k droplets, cap 1, erode rate 0.05, beta 3.2; season 1 = seed 7).
Candidates: seeds 11-20. Rule: land share 0.70-0.90, the largest basin under 15% of land, and then the most basins
of 500-5000 cells (mid-sized rivers whose divides players can actually move). Ties: lower seed. No looking at maps first."""
import sys, os, json, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.expanduser('~/repos/errata-worlds')
sys.path.insert(0, os.path.dirname(HERE)); import tick as T
rows = []
for seed in list(range(11, 21)) + [7]:
    out = os.path.join(HERE, f'seed{seed}')
    if not os.path.exists(out + '_h.npy'):
        subprocess.run([sys.executable, 'erode.py', '--seed', str(seed), '--drops', '100000', '--cap', '1', '--er', '0.05', '--out', out],
                       cwd=REPO, check=True, capture_output=True)
    h = np.load(out + '_h.npy'); oc, r, order, A, L = T.route(h)
    ocf = oc.ravel(); land = (~oc & (h >= 0)).ravel(); Af = A.ravel()
    mouth = np.array([i for i in np.flatnonzero(land) if r[i] < 0 or ocf[r[i]]])
    sizes = np.sort(Af[mouth])[::-1]; nl = int(land.sum())
    rows.append({'seed': seed, 'land_share': round(nl / land.size, 3), 'largest_share': round(float(sizes[0]) / nl, 3),
                 'mid_basins': int(((sizes >= 500) & (sizes <= 5000)).sum()), 'basins_ge_100': int((sizes >= 100).sum()),
                 'top5': [int(s) for s in sizes[:5]]})
    print(json.dumps(rows[-1]), flush=True)
ok = [x for x in rows if x['seed'] != 7 and 0.70 <= x['land_share'] <= 0.90 and x['largest_share'] < 0.15]
best = max(ok, key=lambda x: (x['mid_basins'], -x['seed'])) if ok else None
print('PICK', json.dumps(best)); json.dump({'rows': rows, 'pick': best}, open(os.path.join(HERE, 'pick.json'), 'w'), indent=1)
