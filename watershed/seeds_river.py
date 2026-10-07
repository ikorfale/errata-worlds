"""Lab job (#169): more seeds for the river-digger lean in Watershed season 1. K=16 simulated players, river vs random strategy,
seeds 1-10, first 33 ticks (same window as the 30-nudge null). Statistic: mean(world - control) over ticks 17-33."""
import subprocess, sys, os, json, numpy as np
W = os.path.dirname(os.path.abspath(__file__))
out = {}
for strat in ('river', 'random'):
    for s in range(1, 11):
        f = os.path.join(W, 'whatif', f'cf-16-{strat}-s{s}.json')
        if not os.path.exists(f):
            subprocess.run([sys.executable, os.path.join(W, 'whatif.py'), 'cf', '16', strat, '--seed', str(s), '--ticks', '33', '-q'], check=True)
        R = json.load(open(f)); d = np.array([r['world'] - r['control'] for r in R])[16:33]
        out.setdefault(strat, []).append(round(float(d.mean()), 5)); print(strat, s, out[strat][-1], flush=True)
null = json.load(open(os.path.join(W, 'whatif', 'null.json')))
res = {k: {'runs': v, 'mean': round(float(np.mean(v)), 5), 'median': round(float(np.median(v)), 5),
           'below_null_p5': sum(x < null['mean_pct']['5'] for x in v)} for k, v in out.items()}
res['null_mean_pct'] = null['mean_pct']
json.dump(res, open(os.path.join(W, 'whatif', 'seeds_river.json'), 'w'), indent=1); print(json.dumps(res))
