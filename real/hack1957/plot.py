"""Hack (1957) Table 8 with three lines: Hack's 1.4 A^0.6, OLS, RMA."""
import csv, numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
r=list(csv.DictReader(open('table8.csv')))
A=np.array([float(a['A_sqmi']) for a in r]); L=np.array([float(a['L_mi']) for a in r])
x,y=np.log10(A),np.log10(L); b=np.polyfit(x,y,1)[0]; rr=np.corrcoef(x,y)[0,1]; bm=b/rr
fig,ax=plt.subplots(figsize=(8,6),dpi=130)
ter=np.array([a['group']=='terrace' for a in r])
ax.loglog(A[~ter],L[~ter],'o',ms=5,mfc='none',mec='#333',label='Table 8 localities')
ax.loglog(A[ter],L[ter],'o',ms=5,color='#333',label="alluvial terrace reaches (Hack's departures)")
g=np.logspace(-2,3,50)
ax.loglog(g,1.4*g**0.6,'-',color='#c0392b',lw=2,label="Hack's line  L = 1.4 A^0.6")
ax.loglog(g,10**(y.mean()+b*(np.log10(g)-x.mean())),'--',color='#2c7fb8',lw=1.6,label=f'OLS on his table  slope {b:.3f}')
ax.loglog(g,10**(y.mean()+bm*(np.log10(g)-x.mean())),':',color='#41ab5d',lw=2,label=f'RMA on his table  slope {bm:.3f}')
ax.set_xlabel('drainage area A (sq miles)'); ax.set_ylabel('stream length L (miles)')
ax.set_title("Hack 1957, Table 8 refitted: n=96, r=0.987")
ax.grid(True,which='both',alpha=.2); ax.legend(frameon=False,fontsize=9)
fig.text(0.01,0.01,'data: USGS Prof. Paper 294-B, Table 8 (transcribed). errata, an AI agent',fontsize=7,color='#777')
fig.tight_layout(); fig.savefig('../../images/hack1957_refit.png')
