"""Step 02: rolling 500-day daily backtests of the static Gaussian, variance-matched Student-t and historical models (Kupiec, Christoffersen, Acerbi-Szekely Z2). Adds sol_results.json["backtest"]."""
import numpy as np, pandas as pd, json
from scipy import stats
import os
HERE=os.path.dirname(os.path.abspath(__file__)); r=pd.read_csv(f"{HERE}/data/daily_returns.csv",index_col=0,parse_dates=True); W=pd.read_csv(f"{HERE}/data/weights.csv",index_col=0); PJ=json.load(open(f"{HERE}/ports.json")); WIN=PJ["WINDOW"]
DF_GRID=np.array([3,3.5,4,4.5,5,6,7,8,10,12,15,20,30,50])
def backtest(x, a_v=0.99, a_e=0.975, win=500):
    n=len(x); T=n-win; rec={k:{"exc":np.zeros(T,int),"es":np.zeros(T)} for k in ("gauss","t","hist")}; dfs=[]
    for j,i in enumerate(range(win,n)):
        h=x[i-win:i]; L=-x[i]; m,s=h.mean(),h.std(ddof=1)
        # gaussian
        zv,ze=stats.norm.ppf(a_v),stats.norm.ppf(a_e); vG=s*zv-m; vGe=s*ze-m; eG=s*stats.norm.pdf(ze)/(1-a_e)-m
        # standardised t: fit df on z=(h-m)/s with unit variance scaling
        z=(h-m)/s
        # variance-matched Student-t: scale c = sqrt((df-2)/df) so that Var(z)=1; df chosen by profile likelihood on a grid
        best=None
        for dfc in DF_GRID:
            cc=np.sqrt((dfc-2)/dfc); ll_=stats.t.logpdf(z,dfc,0,cc).sum()
            if best is None or ll_>best[0]: best=(ll_,dfc,cc)
        _,df_,c=best; dfs.append(df_)
        qv,qe=stats.t.ppf(a_v,df_),stats.t.ppf(a_e,df_)
        vT=s*c*qv-m; vTe=s*c*qe-m; eT=s*c*(stats.t.pdf(qe,df_)*(df_+qe**2)/((df_-1)*(1-a_e)))-m
        hl=-h; vH=np.quantile(hl,a_v); vHe=np.quantile(hl,a_e); eH=hl[hl>=vHe].mean()
        for k,v,ve,e in (("gauss",vG,vGe,eG),("t",vT,vTe,eT),("hist",vH,vHe,eH)):
            rec[k]["exc"][j]=int(L>v); rec[k]["es"][j]=(L/e)*int(L>ve) if e>0 else 0.0
    out={}
    for k in rec:
        xk=rec[k]["exc"]; N1=int(xk.sum()); p=1-a_v; ph=N1/T
        lr=-2*((T-N1)*np.log(1-p)+N1*np.log(p)-(T-N1)*np.log(1-ph)-N1*np.log(ph)) if 0<N1<T else np.nan
        n00=n01=n10=n11=0
        for a_,b_ in zip(xk[:-1],xk[1:]):
            if a_==0 and b_==0:n00+=1
            elif a_==0 and b_==1:n01+=1
            elif a_==1 and b_==0:n10+=1
            else:n11+=1
        p01=n01/(n00+n01) if n00+n01 else 0; p11=n11/(n10+n11) if n10+n11 else 0; p1=(n01+n11)/(T-1)
        def ll(pa,pb):
            v=0.0
            if n00:v+=n00*np.log(1-pa)
            if n01:v+=n01*np.log(pa)
            if n10:v+=n10*np.log(1-pb)
            if n11 and pb>0:v+=n11*np.log(pb)
            return v
        lri=-2*(ll(p1,p1)-ll(p01,p11)) if 0<p01<1 else np.nan
        z2=float(rec[k]["es"].sum()/(T*(1-a_e))-1)
        out[k]=dict(T=int(T),exceedances=N1,expected=float(T*p),rate=float(ph),kupiec_LR=float(lr) if lr==lr else None,kupiec_p=float(1-stats.chi2.cdf(lr,1)) if lr==lr else None,
                    christoffersen_LR=float(lri) if lri==lri else None,christoffersen_p=float(1-stats.chi2.cdf(lri,1)) if lri==lri else None,AS_Z2=z2)
    out["t_df_median"]=float(np.median(dfs)); out["t_df_min"]=float(np.min(dfs))
    return out
res=json.load(open(f"{HERE}/sol_results.json")); res["backtest"]={}
for name in ["Balanced (US)","EEA representative","Egypt insurer","Egypt insurer (real)","Saudi insurer"]:
    cols=[c for c in W.columns if W.loc[name,c]!=0]; a0,a1=WIN[name]; R=r.loc[a0:a1,cols].dropna(); x=R.values@W.loc[name,cols].values; res["backtest"][name]=backtest(x)
    print(name,{k:(v["exceedances"],round(v["AS_Z2"],2),round(v["kupiec_p"],3) if v["kupiec_p"] is not None else None) for k,v in res["backtest"][name].items() if isinstance(v,dict)}, "df med",round(res["backtest"][name]["t_df_median"],1))
json.dump(res,open(f"{HERE}/sol_results.json","w"),indent=2,default=float); print("saved")
