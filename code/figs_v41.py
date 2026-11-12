"""Figures 1-3 for manuscript v4.1. Reads ../out/e2_v4_summary*.csv; Fig 2 uses the Table 6.2 values."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"axes.spines.top":False,"axes.spines.right":False})
INK="#222222"; MUT="#666666"; B="#2a6f97"; O="#c8642a"; G="#8a8a8a"; OUT="../figs_v41/"
# ---- Figure 1: five separated functions (manuscript 3.2; v4.1 code logic)
fig,ax=plt.subplots(figsize=(10,6)); ax.set_xlim(0,100); ax.set_ylim(0,72); ax.axis("off")
def box(x,y,w,h,t,fc="#f4f4f4",ec=G):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.3,rounding_size=1.2",fc=fc,ec=ec,lw=1.2))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=7.8,color=INK)
def arr(a,b,c=INK,ls="-"):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=11,color=c,lw=1.4,ls=ls))
ax.text(1,70,"Operational architecture: five separated functions",fontsize=9.5,color=INK,fontweight="bold")
xs=[1,21,41,61,81]; W_=17.5
box(7,57,26,7,"Node operations (true performance)")
names=["1 Reporting","2 Measurement\n& verification","3 Triggering","4 Approval","5 Execution"]
who=["Node (DC)\nERP self-report\n(lag 1 wk;\nmay be gamed)","SCDA\nindependent channel\n(no lag; noise)","Hybrid rule on SCDA\n4-week average\n(<0.85, or worst 10%\nand <0.90)","Human reviewer\nqueue; K cases\nper week","Intervention team\n8 weeks, handover\nfriction"]
for x,n,w in zip(xs,names,who):
    ax.text(x+W_/2,49.5,n,ha="center",va="center",fontsize=8.5,color=INK,fontweight="bold")
    box(x,32,W_,12,w,ec=B if n[0]=="2" else G,fc="#e6f0f6" if n[0]=="2" else "#f4f4f4")
arr((xs[0]+W_/2,56.7),(xs[0]+W_/2,52.6),c=O); arr((xs[1]+W_/2,56.7),(xs[1]+W_/2,52.6),c=B)
for i in range(1,4): arr((xs[i]+W_+0.6,38),(xs[i+1]-0.6,38))
ax.text(xs[0]+W_/2,53.4,"",fontsize=1)
ax.text(40,24,"Data-assurance flow: compares the two data sources;\ndoes not decide which nodes enter review",fontsize=9,color=INK,va="center")
box(14,8,24,10,"Discrepancy flag\nERP − SCDA > 0.025\n(not raised during outage)",ec=B,fc="#e6f0f6")
box(50,8,24,10,"Verification cost\nper flag (USD 250)\n[E4: may deter gaming]",ec=B,fc="#e6f0f6")
arr((xs[0]+W_/2,31.7),(21,18.5),c=O,ls="--"); arr((xs[1]+W_/2,31.7),(31,18.5),c=B,ls="--")
arr((38.6,13),(49.4,13),c=B,ls="--")
ax.text(1,4.6,"Solid arrows: operational path (SCDA data feed the trigger). Dashed arrows: data-assurance path, with no link to the trigger.",fontsize=7,color=MUT)
ax.text(1,2.2,"During an SCDA outage the trigger uses the self-reported value. The model encodes these separations as decision rules;\nit does not show that separate organisations would hold them. Not modelled: sensor ownership, audit of the SCDA, appeals, named responsibility.",fontsize=6.8,color=MUT,va="top")
fig.savefig(OUT+"fig1_five_functions.png",dpi=200,bbox_inches="tight"); plt.close(fig)
# ---- Figure 2: AS - C decomposition (waterfall)
comp=[("Lower OTIF\nshortfall cost",41985),("Lower intervention\ncost",122514),("Lower review\ncost",188),("Higher verification\ncost",-19495),("Higher fixed\ngovernance cost",-120000)]
fig,ax=plt.subplots(figsize=(8,4.4)); cum=0
for i,(n,v) in enumerate(comp):
    ax.bar(i,v,bottom=cum,color=B if v>0 else O,width=0.6)
    ax.text(i,cum+v+(6000 if v>0 else -6000),f"{v:+,}",ha="center",va="bottom" if v>0 else "top",fontsize=8.5,color=INK); cum+=v
ax.bar(len(comp),cum,color=INK,width=0.6); ax.text(len(comp),cum+6000,f"{cum:+,}",ha="center",fontsize=9,color=INK,fontweight="bold")
ax.axhline(0,color=MUT,lw=0.8); ax.set_xticks(range(len(comp)+1)); ax.set_xticklabels([c[0] for c in comp]+["Net advantage\nof C over AS"],fontsize=8)
ax.set_ylabel("USD per year (AS − C; positive favours C)"); ax.set_ylim(-20000,190000)
ax.set_title("Where C's USD 25,192 net advantage over AS comes from (dev. seeds, 1,000 trials)",fontsize=9.5,loc="left")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,_:f"{v:,.0f}"))
fig.savefig(OUT+"fig2_decomposition.png",dpi=200,bbox_inches="tight"); plt.close(fig)
# ---- Figure 3: sensitivity of AS - C (both seed sets)
dv=pd.read_csv("../out/e2_v4_summary.csv"); ho=pd.read_csv("../out/e2_v4_summary_seed90000.csv")
labs={"r_int":"Intervention recovery rate","friction":"Handover friction","meas_sd":"SCDA noise (sd)","scda_outage":"SCDA outage probability","gamer_prev":"Gaming prevalence","lam_mult":"Shock frequency multiplier","K":"Reviewer capacity K (per week)","c_verify":"Verification cost (USD)"}
fig,axs=plt.subplots(2,4,figsize=(12,6),sharey=False)
for ax,p in zip(axs.flat,labs):
    for df,c,m,dx,l in ((dv,B,"o",-0.0,"Development seeds"),(ho,O,"s",0.0,"Holdout seeds")):
        s=df[df.param==p].sort_values("value"); n=len(s); xs=np.arange(n)+(-0.12 if c==B else 0.12)
        ax.errorbar(xs,s.d_AS/1000,yerr=s.ci_AS/1000,fmt=m+"-",color=c,ms=4,lw=1,capsize=2,label=l)
    ax.axhline(0,color=INK,lw=0.8); s=df[df.param==p].sort_values("value")
    ax.set_xticks(range(len(s))); ax.set_xticklabels([f"{v:g}" for v in s.value],fontsize=7.5); ax.set_title(labs[p],fontsize=8.5,loc="left")
    ax.set_xlabel("")
for ax in axs[:,0]: ax.set_ylabel("AS − C (USD thousand/yr)")
axs[0,0].legend(fontsize=7.5,frameon=False,loc="upper right")
fig.text(0.01,0.0,"Parameter values are shown as equally spaced categories, not to scale.",fontsize=7.5,color=MUT)
fig.suptitle("Advantage of the full architecture over the strong baseline AS, by parameter (95% Monte Carlo intervals, not real-world parameter uncertainty; below zero = AS cheaper)",fontsize=10,x=0.01,ha="left")
fig.tight_layout(); fig.savefig(OUT+"fig3_sensitivity.png",dpi=200,bbox_inches="tight"); plt.close(fig)
