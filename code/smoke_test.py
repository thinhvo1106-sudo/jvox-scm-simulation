"""Smoke test: reproduces the base-configuration contrasts of Table 6.1 and fails if they drift.
Run from code/:  python3 smoke_test.py      (about 25 s; exit code 0 = pass)"""
import sys, numpy as np, e2_v4 as E
EXPECTED = {  # (seed0, comparator): (mean AS/ASR/CR minus C, USD per year) from manuscript v4.1
 (70000,"AS"):25192,(70000,"ASR"):44378,(70000,"CR"):112251,
 (90000,"AS"):21636,(90000,"ASR"):43261,(90000,"CR"):114378}
TOL = 1.0   # USD; results are deterministic given the seeds, so any larger drift means the model changed
E.VS = ("AS","ASR","CR","C"); bad = 0
for s0 in (70000, 90000):
    x = E.run(E.base, 1000, seed0=s0).pivot(index="trial", columns="variant", values="cost_total")
    for r in ("AS","ASR","CR"):
        got = (x[r]-x["C"]).mean(); exp = EXPECTED[(s0,r)]; ok = abs(got-exp) <= TOL
        bad += not ok; print(f"{s0} {r}-C  got {got:10.1f}  expected {exp:8d}  {'OK' if ok else 'FAIL'}")
print("PASS" if bad == 0 else f"FAIL ({bad} mismatches)"); sys.exit(1 if bad else 0)
