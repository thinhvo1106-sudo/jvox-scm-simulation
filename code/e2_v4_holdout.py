import numpy as np, pandas as pd, sys, time, json
from multiprocessing import Pool
from dataclasses import replace
from sim import P, run_trial, base_config_v41
VS=("AS","ASR","CR","C")
GRID={"r_int":[0.12,0.20,0.30,0.40,0.50,0.60],"friction":[0,0.015,0.03,0.05,0.08],
 "meas_sd":[0.004,0.01,0.02,0.04,0.08],"scda_outage":[0,0.02,0.10,0.25,0.50],
 "gamer_prev":[0,0.25,0.50,0.75,1.0],"lam_mult":[0.5,1.0,1.5,2.0,3.0],"K":[1,2,3,5,10],
 "c_verify":[0,250,500,750,1000,1500]}
base=base_config_v41()
def run(p,n,seed0=90000):
    with Pool(2) as pool:
        out=pool.map(run_trial,[(p,seed0+i,VS) for i in range(n)],chunksize=20)
    return pd.DataFrame([{**r[v],"variant":v,"trial":i} for i,(r,_) in enumerate(out) for v in VS])
if __name__=="__main__":
    n=int(sys.argv[1]); summ=[]; diag=[]
    for par,vals in GRID.items():
        for v in vals:
            t0=time.time(); d=run(replace(base,**{par:v}),n)
            x=d.pivot(index="trial",columns="variant",values="cost_total")
            row={"param":par,"value":v}
            for ref in ("AS","ASR","CR"):
                df=x[ref]-x["C"]; row[f"d_{ref}"]=df.mean(); row[f"ci_{ref}"]=1.96*df.std(ddof=1)/np.sqrt(n)
            summ.append(row)
            g=d.groupby("variant")[["otif","n_int","n_false","n_reviews","n_rejected","flag_game","flag_other","cost_total","cost_short","cost_int","distortion"]].mean()
            for var,r in g.iterrows(): diag.append({"param":par,"value":v,"variant":var,**r.to_dict()})
            print(par,v,{k:round(val/1e3,1) for k,val in row.items() if k.startswith("d_")},round(time.time()-t0),"s",flush=True)
            pd.DataFrame(summ).to_csv("../out/e2_v4_summary_seed90000.csv",index=False)
            pd.DataFrame(diag).to_csv("../out/e2_v4_diagnostics_seed90000.csv",index=False)
    json.dump({"n":n,"seed0":90000,"base":base.__dict__},open("../out/e2_v4_manifest_seed90000.json","w"),indent=1,default=str)
    print("DONE")
