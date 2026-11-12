"""Merges the development (seed 70000) and holdout (seed 90000) E2 summaries into one table and
reports sign agreement. Run from code/ after e2_v4.py and e2_v4_holdout.py. Writes ../out/v41_replication_compare.csv."""
import pandas as pd
a = pd.read_csv("../out/e2_v4_summary.csv"); b = pd.read_csv("../out/e2_v4_summary_seed90000.csv")
m = a.merge(b, on=["param", "value"], suffixes=("_70k", "_90k"))
m = m[["param","value"]+[f"{k}_{r}_{s}" for r in ("AS","ASR","CR") for k in ("d","ci") for s in ("70k","90k")]]
cols = ["param","value","d_AS_70k","ci_AS_70k","d_ASR_70k","ci_ASR_70k","d_CR_70k","ci_CR_70k","d_AS_90k","ci_AS_90k","d_ASR_90k","ci_ASR_90k","d_CR_90k","ci_CR_90k"]
m = m[cols]; m.to_csv("../out/v41_replication_compare.csv", index=False)
for r in ("AS","ASR","CR"):
    print(r, "sign agreement", int(((m[f"d_{r}_70k"] > 0) == (m[f"d_{r}_90k"] > 0)).sum()), "of", len(m))
