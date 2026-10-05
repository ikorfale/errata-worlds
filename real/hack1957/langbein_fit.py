import csv, numpy as np
r=list(csv.DictReader(open('langbein1947.csv')))
A=np.array([float(a['A_sqmi']) for a in r]); L=np.array([float(a['L_longest_mi']) for a in r])
def show(name,m):
    x,y=np.log10(A[m]),np.log10(L[m]); b=np.polyfit(x,y,1)[0]; rr=np.corrcoef(x,y)[0,1]
    rng=np.random.default_rng(1947); bs=[]
    for _ in range(5000):
        i=rng.integers(0,m.sum(),m.sum()); bb=np.polyfit(x[i],y[i],1)[0]; bs.append((bb,bb/np.corrcoef(x[i],y[i])[0,1]))
    bs=np.array(bs); lo=np.percentile(bs,2.5,axis=0); hi=np.percentile(bs,97.5,axis=0)
    print(f"{name:34s} n={m.sum():3d} A {A[m].min():.1f}-{A[m].max():.0f} OLS={b:.3f} [{lo[0]:.3f},{hi[0]:.3f}] RMA={b/rr:.3f} [{lo[1]:.3f},{hi[1]:.3f}] r={rr:.3f} c={10**(y.mean()-b*x.mean()):.2f}")
q=L/(1.4*A**0.6)
show("all kept rows", np.ones(len(A),bool))
show("drop |log ratio to Hack line|>0.35", np.abs(np.log10(q))<=0.35)
show("A <= 100 sq mi", A<=100)
show("A > 100 sq mi", A>100)
