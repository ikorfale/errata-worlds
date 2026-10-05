"""Refit Hack (1957) Table 8: OLS vs RMA, with subsets and a bootstrap by stream."""
import csv, numpy as np
rows=list(csv.DictReader(open('table8.csv')))
def fit(rs):
    x=np.log10([float(r['A_sqmi']) for r in rs]); y=np.log10([float(r['L_mi']) for r in rs])
    b=np.polyfit(x,y,1)[0]; r=np.corrcoef(x,y)[0,1]
    return len(rs), b, b/r, r, 10**(y.mean()-b*x.mean()), x.max()-x.min()
def show(name, rs):
    n,b,rma,r,c,dec=fit(rs); print(f"{name:42s} n={n:3d} OLS={b:.3f} RMA={rma:.3f} r={r:.3f} c_OLS={c:.2f} decades={dec:.2f}")
# transcription sanity: residual vs Hack's own line
for r in rows:
    q=float(r['L_mi'])/(1.4*float(r['A_sqmi'])**0.6)
    if q<0.55 or q>2.0: print("CHECK", r, round(q,2))
show("all rows", rows)
uniq={(r['L_mi'],r['A_sqmi']):r for r in rows}.values()
show("unique (L,A) pairs", list(uniq))
show("without terrace (Hack's solid black)", [r for r in rows if r['group']!='terrace'])
show("without terrace + North River", [r for r in rows if r['group'] not in('terrace','limestone_northriver') and r['loc'] not in('582','586')])
for g in sorted({r['group'] for r in rows}):
    rs=[r for r in rows if r['group']==g]
    if len(rs)>=5: show("  group "+g, rs)
show("A <= 10 sq mi", [r for r in rows if float(r['A_sqmi'])<=10])
show("A >= 1 sq mi", [r for r in rows if float(r['A_sqmi'])>=1])
# bootstrap
rng=np.random.default_rng(1957); bs=[]
rows=list(uniq)
for _ in range(5000):
    s=[rows[i] for i in rng.integers(0,len(rows),len(rows))]
    _,b,rma,*_=fit(s); bs.append((b,rma))
bs=np.array(bs); print("bootstrap 95% OLS", np.percentile(bs[:,0],[2.5,97.5]).round(3), "RMA", np.percentile(bs[:,1],[2.5,97.5]).round(3))
