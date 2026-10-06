"""zenith 75484: (a) which rule rejected each Langbein row, by A quartile; (b) add hillslope 1/(2*density) to L (Langbein measures to the stream source, Hack to the divide)."""
import re, glob, numpy as np
from collections import Counter
NUM = re.compile(r'(?<![\d.])(\d{1,3}(?:,\s?\d{3})+(?!\d)|\d+,\d{1,2}(?!\d)|\d+\.\s?\d+|\.\d+|\d+)(?![\d])')
def num(t):
    t = t.replace(' ', '')
    return t.replace(',', '') if re.fullmatch(r'\d{1,3}(,\d{3})+', t) else t.replace(',', '.')
rows = {}; kept = {}
for f in sorted(glob.glob('lb/o*.txt')):
    for line in open(f):
        m = re.match(r'^\s*([0-9I])\s*[-~+.]\s*(\d{2,4}[A-Z]?(?:[.,]\s?\d)?)', line)
        if not m: continue
        sid = m.group(1).replace('I', '1') + '-' + m.group(2).replace(' ', '')
        rest = line[m.end():]; body = None
        for c in [mm.end() for mm in re.finditer(r'[._\-—]{2,}|[|\]}]', rest)]:
            if re.match(r'[\s|\]})!;:,*]*\.?\d', rest[c:]): body = rest[c:]; break
        if body is None: continue
        toks = [num(t) for t in NUM.findall(body)]
        try: A = float(toks[0])
        except (ValueError, IndexError): continue
        why = []
        if len(toks) < 13: why = ['short']
        else:
            try: dens, sal, ew, ns, avg, Ll, Lp, amax, amean, amin = [float(toks[i]) for i in (1, 2, 3, 4, 5, 8, 9, 10, 11, 12)]
            except ValueError: why = ['parse']
            else:
                if not (amax >= amean >= amin and amax >= 100): why.append('alt')
                if not Lp < amax: why.append('Lpr')
                if not 0.95*min(ew, ns) <= avg <= 1.05*max(ew, ns): why.append('slope')
                if not 0.3 <= dens <= 6: why.append('dens')
                if not (Ll > 0 and 0.15 <= (sal/A)/Ll <= 0.9): why.append('Lratio')
                if not why: kept.setdefault(sid, (A, Ll, dens))
        if sid not in rows or not why: rows[sid] = (A, why)
a = np.array([v[0] for v in rows.values()]); q = np.percentile(a, [25, 50, 75])
print(f'stations {len(rows)}, kept {sum(1 for v in rows.values() if not v[1])}')
LEN = {'Lpr', 'Lratio'}
for i, (lo, hi) in enumerate(zip([-1, *q], [*q, 1e9])):
    rej = [v[1] for v in rows.values() if lo < v[0] <= hi and v[1]]
    n = sum(1 for v in rows.values() if lo < v[0] <= hi)
    c = Counter('+'.join(w) for w in rej)
    onlylen = sum(1 for w in rej if set(w) <= LEN); anylen = sum(1 for w in rej if set(w) & LEN)
    print(f'Q{i+1} A {lo:.0f}-{hi:.0f} n={n} rejected {len(rej)}: only-length {onlylen}, any-length {anylen}; {dict(c.most_common())}')
k = np.array(list(kept.values())); A, L, D = k.T
rng = np.random.default_rng(1)
def fit(A, L):
    x, y = np.log10(A), np.log10(L); s = np.polyfit(x, y, 1)[0]; c = 10**np.mean(y - 0.6*x)
    bs = [];
    for _ in range(2000):
        j = rng.integers(0, len(x), len(x)); bs.append(10**np.mean(y[j] - 0.6*x[j]))
    return s, c, np.percentile(bs, [2.5, 97.5])
for lab, LL in [('as printed (to stream source)', L), ('+ hillslope 1/(2*density)', L + 1/(2*D))]:
    s, c, ci = fit(A, LL); print(f'{lab}: n={len(A)} OLS slope {s:.3f}, pinned-0.6 c {c:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]')
print(f'median density {np.median(D):.2f} mi/sq mi -> median hillslope {np.median(1/(2*D)):.2f} mi; median L {np.median(L):.1f} mi')
