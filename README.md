# J.Vox-SCM simulation — model version 4.1

Code and results for the working paper *Evaluating the Operational Feasibility of an Institutional Governance Architecture for Multi-Node Distribution Networks: Independent Data Assurance, Threshold-Based Safety Fuses, and Human-Accountable Exception Management* (manuscript v4.1, in `paper/`).

This is a simulation with **synthetic, assumed parameters**. It is not calibrated to operational data and makes no claim about any real organisation. Reproducing the results shows that the same code and seeds give the same numbers; it does not show that the numbers describe the real world.

## Repository layout

| Path | Contents |
|---|---|
| `code/sim.py` | The model (version 4.1). **Use `base_config_v41()`**: a plain `P()` keeps older v1–v3 defaults and does not reproduce the paper. |
| `code/e2_v4.py` | Base configuration and the E2 sensitivity grid, development seeds 70000–70999 |
| `code/e2_v4_holdout.py` | The same grid on holdout seeds 90000–90999 (E5) |
| `code/run_v41_all.py` | E1 (base metrics, both seed sets), E1a, E3, E4, E6, and the flag-source runs |
| `code/compare_seeds.py` | Merges the E2 and E5 summaries and reports sign agreement |
| `code/smoke_test.py` | Fails if the six headline contrasts (Table 6.1) drift by more than USD 1 |
| `code/figs_v41.py` | Figures 1–3 |
| `out/` | Result files produced by the scripts (development and holdout) |
| `figs_v41/` | Figures 1–3 as used in the manuscript |
| `paper/` | Manuscript v4.1 (Markdown, DOCX, PDF) and `build_docx.py` (formatting script) |
| `archive/sim_v4_cooldown_bug.py` | Version 4, which contained a cooldown-counter error (manuscript §4.9). Kept for audit only; do not use for results. |

## Experiments and where they are produced

| Experiment | Script | Output |
|---|---|---|
| E1 headline comparison (both seed sets), process measures | `run_v41_all.py` | `out/v41_base_metrics.csv`, `out/v41_all.log` |
| E1a deterministic reviewer | `run_v41_all.py` | `out/v41_all.log` |
| E2 one-at-a-time sensitivity, 42 settings × 1,000 trials | `e2_v4.py` | `out/e2_v4_summary.csv`, `out/e2_v4_diagnostics.csv` |
| E3 timely ERP (reporting lag 0) | `run_v41_all.py` | `out/v41_all.log` |
| E4 deterrence, 500 trials | `run_v41_all.py` | `out/v41_all.log` |
| E5 holdout replication of E2 | `e2_v4_holdout.py` | `out/e2_v4_summary_seed90000.csv`, `out/e2_v4_diagnostics_seed90000.csv` |
| E6 supplementary recovery-rate runs (r_int 0.12–0.4) | `run_v41_all.py` | `out/v41_all.log` |

Seeds: development 70000–70999, holdout 90000–90999 (E4 uses the first 500 development seeds). The manifests `out/e2_v4_manifest*.json` record the configuration.

## Environment

Python 3.13 with the packages in `requirements.txt` (NumPy 2.5.3, pandas 3.0.5, matplotlib 3.11.2). These are the versions the results were produced and checked with; other versions were not tested. The scripts start two worker processes (`multiprocessing.Pool(2)`), and runtimes below are for a 2-core machine.

## Exact execution

```bash
git clone <repository-url>
cd <repository-folder>
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd code                      # all scripts must be run from code/
python3 smoke_test.py        # ~25 s; prints PASS and exits 0 if the six contrasts match
python3 run_v41_all.py       # ~2 min; E1, E1a, E3, E4, E6
python3 e2_v4.py 1000        # ~8 min; E2 (the argument is the number of trials per setting)
python3 e2_v4_holdout.py 1000  # ~8 min; E5
python3 compare_seeds.py     # sign agreement between E2 and E5
python3 figs_v41.py          # redraws Figures 1-3 into ../figs_v41/
```

The scripts overwrite the files in `out/` and `figs_v41/`. The results are deterministic for a given seed and package versions; the shipped files in `out/` are the ones used in the manuscript.

## Expected results (smoke test)

Cost of the comparator minus cost of C, USD per year, mean over 1,000 paired trials (±95% interval of the paired differences):

| Comparison | Seeds 70000–70999 | Seeds 90000–90999 |
|---|---|---|
| AS − C | +25,192 ± 7,941 | +21,636 ± 7,917 |
| ASR − C | +44,378 ± 7,612 | +43,261 ± 7,398 |
| CR − C | +112,251 ± 8,156 | +114,378 ± 8,390 |

`run_v41_all.py` should also print E1a AS − C = +76,929 and E3 (lag 0) AS − C = −219,838. `compare_seeds.py` should report sign agreement of 41/42 against AS and 42/42 against ASR and CR.

## Configuration used in the paper

`base_config_v41()` differs from the plain `P()` defaults in six settings: `obs_review=True`, `thrB_for_B=False`, `review_cost_A=True`, `c_verify=250`, `rev_signal_sd=0.03`, `rev_prob_rule=True`. All other parameters are the defaults in `sim.py`. Every experiment script uses this function.

## Verification performed

A fresh copy of `code/` was run end to end (`smoke_test.py`, `run_v41_all.py`, `e2_v4.py 1000`, `e2_v4_holdout.py 1000`, `compare_seeds.py`, `figs_v41.py`) with an empty `out/` folder, on Python 3.13 with the package versions above. The smoke test passed; the E2 and E5 summary and diagnostics CSVs, the base-metrics CSV and the replication-comparison CSV matched the files in `out/` exactly (maximum absolute difference 0.0), the manifests were identical, and the `run_v41_all.py` log matched apart from timing lines. `SHA256SUMS` lists the checksums of the shipped files. This was run by the author's AI assistant, not by an independent human researcher.

## Notes and limits

- Break-even values are linear interpolations between grid points; intervals are normal approximations of paired differences; no multiplicity adjustment is made. Intervals describe Monte Carlo noise only, not uncertainty about the parameters.
- Reproducing these results with AI assistance (see the declaration in the manuscript) is not independent human validation.
- The figures and Appendix A of the manuscript are built from the CSV files in `out/`. Figure 2 uses the values of Table 6.2, which are entered in `figs_v41.py`.
