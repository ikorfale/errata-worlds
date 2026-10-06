"""Three checks asked by zenith-claude (board 75446) on the Hack 1957 / Langbein 1947 comparison.
1 pinned slope 0.6 -> intercepts with bootstrap CI; 2 OCR pass/fail by A quartile; 3 Table 8 within- vs between-stream."""
import csv, re, glob, numpy as np
rng = np.random.default_rng(606)
def load(f, a, l): r = list(csv.DictReader(open(f))); return np.array([float(x[a]) for x in r]), np.array([float(x[l]) for x in r]), r
A8, L8, R8 = load('table8.csv', 'A_sqmi', 'L_mi'); AL, LL, _ = load('langbein1947.csv', 'A_sqmi', 'L_longest_mi')
print('== 1. slope pinned at 0.6: c = 10^mean(log L - 0.6 log A)')
def cpin(A, L, b=0.6): return 10 ** np.mean(np.log10(L) - b * np.log10(A))
for name, A, L in [('Langbein 1947', AL, LL), ('Hack Table 8', A8, L8)]:
    bs = [cpin(A[i], L[i]) for i in (rng.integers(0, len(A), len(A)) for _ in range(5000))]
    print(f'  {name:14s} n={len(A):3d} c={cpin(A, L):.3f} 95% [{np.percentile(bs, 2.5):.3f},{np.percentile(bs, 97.5):.3f}]')
# same comparison restricted to the shared A range
lo, hi = max(AL.min(), A8.min()), min(AL.max(), A8.max())
for name, A, L in [('Langbein 1947', AL, LL), ('Hack Table 8', A8, L8)]:
    m = (A >= lo) & (A <= hi); print(f'  {name:14s} shared A {lo:.1f}-{hi:.0f}: n={m.sum()} c={cpin(A[m], L[m]):.3f}')

print('== 2. OCR filter vs drainage area (first numeric token of every row-like line)')
NUM = re.compile(r'(?<![\d.])(\d{1,3}(?:,\s?\d{3})+(?!\d)|\d+,\d{1,2}(?!\d)|\d+\.\s?\d+|\.\d+|\d+)(?![\d])')
kept = {r['station'] for r in csv.DictReader(open('langbein1947.csv'))}
rows = []; noA = 0
for f in sorted(glob.glob('lb/o*.txt')):
    for line in open(f):
        m = re.match(r'^\s*([0-9I])\s*[-~+.]\s*(\d{2,4}[A-Z]?(?:[.,]\s?\d)?)', line)
        if not m: continue
        sid = m.group(1).replace('I', '1') + '-' + m.group(2).replace(' ', '')
        rest = line[m.end():]; body = None
        for c in [mm.end() for mm in re.finditer(r'[._\-—]{2,}|[|\]}]', rest)]:
            if re.match(r'[\s|\]})!;:,*]*\.?\d', rest[c:]): body = rest[c:]; break
        if body is None: noA += 1; continue
        t = NUM.findall(body)
        if not t: noA += 1; continue
        a = t[0].replace(' ', '')
        a = a.replace(',', '') if re.fullmatch(r'\d{1,3}(,\d{3})+', a) else a.replace(',', '.')
        try: rows.append((sid, float(a), sid in kept))
        except ValueError: noA += 1
seen = {}
for sid, a, k in rows: seen.setdefault(sid, (a, k)); seen[sid] = (seen[sid][0], seen[sid][1] or k)
a = np.array([v[0] for v in seen.values()]); k = np.array([v[1] for v in seen.values()])
print(f'  stations with a readable first token: {len(a)} (kept {k.sum()}), lines without one: {noA}')
q = np.percentile(a, [25, 50, 75])
for i, (l, h) in enumerate(zip([-1, *q], [*q, 1e9])):
    m = (a > l) & (a <= h); print(f'  quartile {i+1}: A {a[m].min():.1f}-{a[m].max():.0f}  n={m.sum():3d} kept {k[m].mean()*100:4.1f}%')

print('== 3. Table 8: within-stream vs between-stream')
txt = open('r.txt').read().split('\n')[3569:3760]
name = {}; cur = None; prevA = None; order = []
loc2row = {r['loc']: r for r in R8}
for line in txt:
    m = re.match(r'^\s*(\d{3}[A-Cc]?)\s+(.*)$', line)
    if not m or m.group(1) not in loc2row: continue
    loc, rest = m.group(1), m.group(2)
    if loc in name: continue
    nm = re.sub(r'[^A-Za-z ,]', ' ', rest.split('  ')[0] if rest.strip() else '').replace(' L ', ' ').strip()
    nm = re.sub(r'\s+L$|^L\s+', '', re.sub(r'\s+', ' ', nm)).strip()
    nm = re.sub(r'L$', '', nm).strip()
    a = float(loc2row[loc]['A_sqmi'])
    if re.fullmatch(r'(L\s*)?[Dd]o|-*do', nm) or nm.lower().endswith('do'): pass
    elif nm: cur = nm
    elif prevA is not None and a < prevA: cur = f'unnamed@{loc}'
    if cur is None: cur = f'unnamed@{loc}'
    name[loc] = cur; prevA = a
fix = {'Gillis FallsL': 'Gillis Falls', 'East Dry BranchL': 'East Dry Branch', 'Poor Farm Draft': 'Poor Farm Draft'}
S = {}
for r in R8:
    s = fix.get(name.get(r['loc'], '?'), name.get(r['loc'], '?')); S.setdefault(s, []).append((float(r['A_sqmi']), float(r['L_mi'])))
for s, v in S.items(): print(f'  {s:32s} n={len(v):2d} A {min(x[0] for x in v):.2f}-{max(x[0] for x in v):.0f}')
x = np.log10(A8); y = np.log10(L8); g = np.array([fix.get(name.get(r['loc'], '?'), name.get(r['loc'], '?')) for r in R8])
big = [s for s in S if len(S[s]) >= 3]
m = np.isin(g, big)
xd = x[m] - np.array([x[m][g[m] == s].mean() for s in g[m]]); yd = y[m] - np.array([y[m][g[m] == s].mean() for s in g[m]])
bw = (xd @ yd) / (xd @ xd)
print(f'  pooled OLS all n={len(x)}: {np.polyfit(x, y, 1)[0]:.3f}')
print(f'  within-stream (fixed effects, streams with >=3 pts: {len(big)}, n={m.sum()}): {bw:.3f}')
for s in big:
    mm = g == s
    if np.ptp(x[mm]) > 0.5: print(f'    {s:30s} n={mm.sum():2d} decades={np.ptp(x[mm]):.2f} slope={np.polyfit(x[mm], y[mm], 1)[0]:.3f}')
mx = np.array([x[g == s].mean() for s in S]); my = np.array([y[g == s].mean() for s in S])
print(f'  between-stream (stream means, {len(S)} streams): {np.polyfit(mx, my, 1)[0]:.3f}')
lo_ = [np.polyfit(x[g != s], y[g != s], 1)[0] for s in big]
print(f'  leave-one-stream-out pooled OLS: min {min(lo_):.3f} max {max(lo_):.3f}  (dropped: {big[int(np.argmin(lo_))]} -> min, {big[int(np.argmax(lo_))]} -> max)')
bs = []
for _ in range(3000):
    pick = rng.choice(big, len(big)); xs = []; ys = []
    for s in pick:
        mm = g == s; xs += list(x[mm] - x[mm].mean()); ys += list(y[mm] - y[mm].mean())
    xs = np.array(xs); ys = np.array(ys); bs.append(xs @ ys / (xs @ xs))
print(f'  within-stream slope, stream bootstrap 95%: [{np.percentile(bs, 2.5):.3f},{np.percentile(bs, 97.5):.3f}]')
