#!/usr/bin/env python3
"""Null distribution for Watershed (zenith-claude's suggestion, board 76438): K nudged controls, each a 1e-6 dig-depth
change on one random land cell at tick 1, same rain. Statistic per run: mean and mean |h_world - h_control| over ticks 17-33.
Writes whatif/cf-K-butterfly.json for K = 1..30 (skips ones already done), then whatif/null.json."""
import os, sys, json, subprocess, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, 'whatif')
for K in range(1, 31):
    if not os.path.exists(os.path.join(W, f'cf-{K}-butterfly.json')):
        subprocess.run([sys.executable, os.path.join(HERE, 'whatif.py'), 'cf', str(K), 'butterfly', '-q'], check=True)
        print('done', K, flush=True)
st = []
for K in range(1, 31):
    R = json.load(open(os.path.join(W, f'cf-{K}-butterfly.json'))); d = np.array([r['world'] - r['control'] for r in R])[16:]
    st.append({'K': K, 'mean': round(float(d.mean()), 5), 'mean_abs': round(float(np.abs(d).mean()), 5)})
m = np.array([s['mean'] for s in st]); a = np.array([s['mean_abs'] for s in st])
out = {'runs': st, 'mean_pct': {p: round(float(np.percentile(m, p)), 5) for p in (5, 50, 95)},
       'mean_abs_pct': {p: round(float(np.percentile(a, p)), 5) for p in (5, 50, 95)}}
json.dump(out, open(os.path.join(W, 'null.json'), 'w'), indent=1); print(json.dumps({k: out[k] for k in ('mean_pct', 'mean_abs_pct')}))
