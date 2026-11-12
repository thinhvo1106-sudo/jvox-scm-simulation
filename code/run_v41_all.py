import pandas as pd, numpy as np
from dataclasses import replace
import e2_v4 as E
def ci(df): return 1.96*df.std(ddof=1)/np.sqrt(len(df))
ALL=("NONE","A","AW","AS","ASR","CR","C","ORACLE")
out="../out/"
# base process metrics, both seed sets
rows=[];cens=[]
for s0 in (70000,90000):
    E.VS=ALL; d=E.run(E.base,1000,seed0=s0); g=d.groupby("variant")
    t=pd.DataFrame({"cost":g.cost_total.mean(),"cost_short":g.cost_short.mean(),"cost_int":g.cost_int.mean(),"otif":g.otif.mean(),"n_ep":g.n_ep.mean(),"n_cens":g.n_cens.mean(),
     "cens_share":g.n_cens.sum()/g.n_ep.sum(),"rec_incl":g.rec_mean.mean(),"rec_done":g.rec_done_mean.mean(),"lat_wks":g.lat_sum.sum()/g.n_cov.sum(),"coverage":g.n_cov.sum()/g.n_ep.sum(),
     "n_int":g.n_int.mean(),"n_false":g.n_false.mean(),"n_reviews":g.n_reviews.mean(),"n_rejected":g.n_rejected.mean(),"distortion":g.distortion.mean(),"rep_dist":g.rep_dist.mean(),
     "game_weeks":g.game_weeks.mean(),"flag_game":g.flag_game.mean(),"flag_other":g.flag_other.mean()})
    t["seed0"]=s0; rows.append(t.loc[list(ALL)].reset_index())
    x=d.pivot(index="trial",columns="variant",values="cost_total")
    print("== base",s0)
    print(t.loc[list(ALL)].round(3).to_string())
    for ref in ("A","AW","AS","ASR","CR"):
        df=x[ref]-x["C"]; print(f"  {ref}-C {df.mean():10.0f} +- {ci(df):6.0f}")
pd.concat(rows).to_csv(out+"v41_base_metrics.csv",index=False)
# E1a deterministic reviewer; E3 lag0
E.VS=("AS","ASR","CR","C")
for name,kw in (("E1a det reviewer",{"rev_prob_rule":False}),("E3 lag0",{"rep_lag":0})):
    d=E.run(replace(E.base,**kw),1000); x=d.pivot(index="trial",columns="variant",values="cost_total")
    print("==",name,{ref:(round((x[ref]-x["C"]).mean()),round(ci(x[ref]-x["C"]))) for ref in ("AS","ASR","CR")})
# E4 deterrence paired
E.VS=("C","AS"); res={}
for dp in (0.0,0.5,0.9):
    d=E.run(replace(E.base,deter_prob=dp),500); g=d.groupby("variant")
    x=d.pivot(index="trial",columns="variant",values="cost_total"); res[dp]=x["C"]
    print("== E4",dp,"game_weeks",round(g.game_weeks.mean()["C"],1),"rep_dist C",round(g.rep_dist.mean()["C"],5),"AS",round(g.rep_dist.mean()["AS"],5),"AS-C",round((x["AS"]-x["C"]).mean()),"+-",round(ci(x["AS"]-x["C"])))
for a,b in ((0.0,0.5),(0.0,0.9),(0.5,0.9)): df=res[a]-res[b]; print("   C cost",a,"minus",b,round(df.mean()),"+-",round(ci(df)))
# E6 r_int vs NONE
E.VS=("NONE","AS","C","ORACLE")
for v in (0.12,0.2,0.23,0.25,0.3,0.4):
    d=E.run(replace(E.base,r_int=v),1000); x=d.pivot(index="trial",columns="variant",values="cost_total")
    print("== E6 r_int",v,{k:round(x[k].mean()/1e3) for k in x.columns},"NONE-C",round((x["NONE"]-x["C"]).mean()),"+-",round(ci(x["NONE"]-x["C"])))
# flag sources
E.VS=("C",)
for name,kw in (("base",{}),("lag0",{"rep_lag":0}),("noise0.001",{"meas_sd":0.001}),("lag0+noise0.001",{"rep_lag":0,"meas_sd":0.001})):
    d=E.run(replace(E.base,**kw),300); print("== flags",name,round(d.flag_game.mean(),1),round(d.flag_other.mean(),1))
