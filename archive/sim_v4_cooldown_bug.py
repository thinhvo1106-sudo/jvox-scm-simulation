"""
J.Vox-SCM illustrative simulation (synthetic assumptions only).

Network of N distribution centres (DCs) observed weekly. Each DC has a latent true OTIF.
Disruptions (idiosyncratic + regional) push OTIF down; OTIF recovers naturally or faster
under a management "intervention" (task force step-in).

Governance variants, all facing IDENTICAL random shocks (common random numbers):
  NONE   : no intervention ever (reference floor)
  A      : conventional discretionary management (monthly review, self-reported ERP data)
  AW     : same as A but reviewed weekly (cadence-parity control)
  B      : rank-based automatic intervention (quarterly, bottom 10%, self-reported data)
  C0     : rank-based trigger but SCDA-verified data + human review
  CR     : C's hybrid trigger + human review, but on SELF-REPORTED data (isolates SCDA value)
  C      : modified J.Vox-SCM (hybrid absolute+relative trigger, weekly, SCDA data,
           human-in-the-loop with finite reviewer capacity)
  ORACLE : intervenes the week after any true disruption starts (unattainable bound)

Every numeric input is a SYNTHETIC ASSUMPTION, not an empirical estimate.
"""
from dataclasses import dataclass, replace, asdict
import numpy as np

VARIANTS = ["NONE", "A", "AW", "AS", "ASR", "B", "C0", "CR", "C", "ORACLE"]


@dataclass(frozen=True)
class P:
    N: int = 30
    W: int = 52
    n_regions: int = 6
    # baseline performance
    base_mu: float = 0.955
    base_sd: float = 0.015
    base_lo: float = 0.90
    base_hi: float = 0.985
    eps_sd: float = 0.008
    # shocks
    lam_idio: float = 0.015
    sev_lo: float = 0.12
    sev_hi: float = 0.35
    lam_reg: float = 0.04
    reg_lo: float = 0.05
    reg_hi: float = 0.15
    lam_mult: float = 1.0
    deg_cap: float = 0.60
    # recovery dynamics
    r_nat: float = 0.12
    r_int: float = 0.40
    int_len: int = 8
    friction: float = 0.03
    friction_len: int = 3
    cooldown: int = 4
    need_deg: float = 0.05      # a DC "needs" intervention if degradation >= this
    end_deg: float = 0.03       # episode ends when degradation < this
    # reporting / gaming
    gamer_prev: float = 0.25
    gam_lo: float = 0.03
    gam_hi: float = 0.08
    thrA: float = 0.90
    thrB: float = 0.93
    rep_noise: float = 0.004
    rep_lag: int = 1
    meas_sd: float = 0.010
    scda_outage: float = 0.02
    # Model A
    A_review: int = 4
    A_win: int = 4
    A_thr: float = 0.90
    A_prob: float = 0.50
    A_delay: int = 2
    A_audit: float = 0.03
    # Model B / C0
    B_cad: int = 13
    B_frac: float = 0.10
    # Model C
    C_floor: float = 0.85
    C_rel_cap: float = 0.90
    C_ma: int = 4
    K: int = 2
    overload: float = 2.0
    acc_true: float = 0.95
    fa_normal: float = 0.10
    fa_overload: float = 0.95
    C_flag: float = 0.025
    C_clear: float = 0.92
    # economics (USD, synthetic)
    target: float = 0.95
    c_short: float = 1500.0     # per OTIF-percentage-point shortfall per DC-week
    c_int_week: float = 6000.0  # task-force cost per DC-week under intervention
    gov_A: float = 0.0
    gov_B: float = 30000.0      # annual analytics/ranking overhead
    gov_C: float = 120000.0     # annual SCDA: 80k opex + 120k setup / 3 yrs
    c_review: float = 250.0     # per human review decision
    # v2 audit switches (defaults reproduce the v1 results)
    obs_review: bool = False    # reviewer decides from OBSERVED data, not hidden degradation
    thrB_for_B: bool = True     # False => B games at the same threshold as every other variant
    review_cost_A: bool = False # charge c_review for A/AW/AS review decisions too
    # v3 audit switches
    c_verify: float = 0.0       # cost to verify ONE data-discrepancy flag / random audit (all variants that raise them)
    rev_prob_rule: bool = False # True: reviewer keeps v2 error rates (acc_true / fa_normal) even with an independent signal
    deter_prob: float = 0.0     # P(gamer stops gaming | SCDA flags a gaming week)  (C, C0 only)
    rev_signal_sd: float = -1.0 # >0: reviewer gets an INDEPENDENT noisy evidence signal (e.g. site check) = deg + N(0,sd)


def draw(p: P, seed: int):
    """All randomness for one trial, shared by every variant (common random numbers)."""
    r = np.random.default_rng(seed)
    N, W = p.N, p.W
    d = {}
    d["base"] = np.clip(r.normal(p.base_mu, p.base_sd, N), p.base_lo, p.base_hi)
    d["u_idio"] = r.random((W, N))
    d["u_sev"] = r.random((W, N))
    d["u_reg"] = r.random(W)
    d["u_reg_which"] = r.random(W)
    d["u_reg_sev"] = r.random((W, N))
    d["eps"] = r.normal(0, p.eps_sd, (W, N))
    d["u_gamer"] = r.random(N)
    d["u_gam"] = r.random(N)
    d["rep_noise"] = r.normal(0, p.rep_noise, (W, N))
    d["meas_noise"] = r.normal(0, p.meas_sd, (W, N))
    d["u_outage"] = r.random(W)
    d["u_A"] = r.random((W, N))
    d["u_audit"] = r.random((W, N))
    d["u_rev"] = r.random((W, N))
    d["rev_noise"] = r.normal(0, 1.0, (W, N))
    d["u_det"] = r.random((W, N))
    return d


def run_variant(p: P, R: dict, variant: str):
    N, W = p.N, p.W
    region_of = np.arange(N) * p.n_regions // N
    base = R["base"]
    gamer = R["u_gamer"] < p.gamer_prev
    gamer_act = gamer.copy()
    gam_amt = p.gam_lo + (p.gam_hi - p.gam_lo) * R["u_gam"]
    thr_g = p.thrB if (variant == "B" and p.thrB_for_B) else p.thrA

    deg = np.zeros(N)
    int_age = np.full(N, -1)
    cool = np.zeros(N, int)
    pending = np.full(N, -1)
    ep_active = np.zeros(N, bool)
    ep_start = np.zeros(N, int)
    ep_int = np.zeros(N, bool)
    queue = []  # list of node ids awaiting human review

    true_h = np.zeros((W, N))
    rep_h = np.zeros((W, N))
    kpi_h = np.zeros((W, N))      # the KPI the organisation "sees"
    meas_h = np.zeros((W, N))     # SCDA-feed (falls back to reported during outage)

    n_int = n_false = n_reviews = 0
    int_weeks = 0
    ep_dur, lat = [], []
    n_ep = 0
    game_weeks = flagged_game = flagged_other = 0
    otif_week = np.zeros(W)
    short_pts = 0.0
    n_rejected = 0
    deg_weeks = 0

    lam_i = min(1.0, p.lam_idio * p.lam_mult)
    lam_r = min(1.0, p.lam_reg * p.lam_mult)

    for t in range(W):
        # ---- start pending interventions
        if (pending > 0).any():
            pending[pending > 0] -= 1
        starts = np.where(pending == 0)[0]
        for i in starts:
            int_age[i] = 0
            pending[i] = -1
            n_int += 1
            if deg[i] < p.need_deg:
                n_false += 1
            if ep_active[i] and not ep_int[i]:
                lat.append(t - ep_start[i])
                ep_int[i] = True

        # ---- shocks
        shock = np.where(R["u_idio"][t] < lam_i, p.sev_lo + (p.sev_hi - p.sev_lo) * R["u_sev"][t], 0.0)
        if R["u_reg"][t] < lam_r:
            reg = int(R["u_reg_which"][t] * p.n_regions)
            m = region_of == reg
            shock = shock + np.where(m, p.reg_lo + (p.reg_hi - p.reg_lo) * R["u_reg_sev"][t], 0.0)
        deg = np.minimum(deg + shock, p.deg_cap)
        deg_weeks += int((deg >= p.need_deg).sum())
        new_ep = (deg >= p.need_deg) & (~ep_active)
        if new_ep.any():
            ep_active[new_ep] = True
            ep_start[new_ep] = t
            ep_int[new_ep] = False
            n_ep += int(new_ep.sum())

        # ---- true performance
        fr = np.where((int_age >= 0) & (int_age < p.friction_len), p.friction, 0.0)
        true = np.clip(base - deg - fr + R["eps"][t], 0.30, 1.0)
        true_h[t] = true
        otif_week[t] = true.mean()
        short_pts += np.maximum(0.0, p.target - true).sum() * 100.0
        int_weeks += int((int_age >= 0).sum())

        # ---- observation: ERP self-report (lagged, possibly inflated) and SCDA measurement
        prev = true_h[max(t - p.rep_lag, 0)]
        infl = np.where(gamer_act & (prev < thr_g), gam_amt, 0.0)
        rep = np.minimum(1.0, prev + R["rep_noise"][t] + infl)
        rep_h[t] = rep
        outage = R["u_outage"][t] < p.scda_outage
        meas = np.minimum(1.0, true + R["meas_noise"][t])
        meas_eff = rep if outage else meas
        meas_h[t] = meas_eff
        if variant in ("C0", "C"):
            kpi_h[t] = meas_eff
        else:
            kpi_h[t] = rep

        gw = infl > 0.02
        game_weeks += int(gw.sum())
        if variant in ("A", "AW", "AS", "ASR"):
            fl = R["u_audit"][t] < p.A_audit
            flagged_game += int((fl & gw).sum())
            flagged_other += int((fl & ~gw).sum())
        elif variant in ("C0", "C") and not outage:
            fl = (rep - meas) > p.C_flag
            flagged_game += int((fl & gw).sum())
            flagged_other += int((fl & ~gw).sum())
            if p.deter_prob > 0:
                gamer_act[fl & gw & (R["u_det"][t] < p.deter_prob)] = False

        elig = (int_age < 0) & (pending < 0) & (cool == 0)

        # ---- decisions (end of week t)
        if variant in ("A", "AW", "AS"):
            cad = p.A_review if variant == "A" else 1
            prob = 1.0 if variant == "AS" else p.A_prob
            dly = 0 if variant == "AS" else p.A_delay
            if (t + 1) % cad == 0 and t + 1 >= p.A_win:
                ma = rep_h[t - p.A_win + 1:t + 1].mean(axis=0)
                screened = elig & (ma < p.A_thr)
                if p.review_cost_A:
                    n_reviews += int(screened.sum())
                cand = screened & (R["u_A"][t] < prob)
                pending[cand] = 1 + dly
        elif variant == "B":
            if (t + 1) % p.B_cad == 0:
                ma = rep_h[t - p.B_cad + 1:t + 1].mean(axis=0)
                k = int(round(p.B_frac * N))
                for i in np.argsort(ma)[:k]:
                    if elig[i]:
                        pending[i] = 1
        elif variant == "ORACLE":
            cand = elig & (deg >= p.need_deg)
            pending[cand] = 1
        elif variant in ("C0", "C", "CR", "ASR"):
            src_h = meas_h if variant in ("C0", "C") else rep_h
            inq = np.zeros(N, bool)
            if queue:
                inq[queue] = True
            if variant == "C0":
                if (t + 1) % p.B_cad == 0:
                    ma = src_h[t - p.B_cad + 1:t + 1].mean(axis=0)
                    k = int(round(p.B_frac * N))
                    for i in np.argsort(ma)[:k]:
                        if elig[i] and not inq[i]:
                            queue.append(int(i))
                            inq[i] = True
            else:
                if t + 1 >= p.C_ma:
                    ma = src_h[t - p.C_ma + 1:t + 1].mean(axis=0)
                    cutoff = np.quantile(ma, p.B_frac)
                    trig = (ma < p.A_thr) if variant == "ASR" else ((ma < p.C_floor) | ((ma <= cutoff) & (ma < p.C_rel_cap)))
                    for i in np.where(trig & elig & ~inq)[0]:
                        queue.append(int(i))
                        inq[i] = True
                    # purge stale alerts for DCs that recovered
                    queue = [i for i in queue if ma[i] < p.C_clear]
            if queue:
                if variant in ("C", "CR", "ASR"):
                    ma_q = src_h[max(0, t - p.C_ma + 1):t + 1].mean(axis=0)
                else:
                    ma_q = src_h[max(0, t - p.B_cad + 1):t + 1].mean(axis=0)
                load = len(queue)
                overload = load > p.overload * p.K
                queue.sort(key=lambda i: ma_q[i])          # most severe first
                for i in queue[:p.K]:
                    n_reviews += 1
                    if p.rev_signal_sd > 0:
                        need_hat = (deg[i] + p.rev_signal_sd * R["rev_noise"][t, i]) >= p.need_deg
                        if p.rev_prob_rule:
                            pa = p.acc_true if need_hat else (p.fa_overload if overload else p.fa_normal)
                        else:
                            pa = 1.0 if need_hat else (p.fa_overload if overload else 0.0)
                    else:
                        need = (ma_q[i] < p.C_rel_cap) if p.obs_review else (deg[i] >= p.need_deg)
                        pa = (p.acc_true if need else (p.fa_overload if overload else p.fa_normal))
                    if R["u_rev"][t, i] < pa:
                        pending[i] = 1
                    else:
                        cool[i] = p.cooldown
                        n_rejected += 1
                queue = queue[p.K:]

        # ---- dynamics
        rate = np.where(int_age >= 1, p.r_int, p.r_nat)
        deg = deg * (1.0 - rate)
        done = ep_active & (deg < p.end_deg)
        if done.any():
            for i in np.where(done)[0]:
                ep_dur.append(t + 1 - ep_start[i])
            ep_active[done] = False
        # intervention ageing
        act = int_age >= 0
        int_age[act] += 1
        ended = act & (int_age >= p.int_len)
        int_age[ended] = -1
        cool[ended] = p.cooldown
        cool[(cool > 0) & ~ended] -= 1
        cool[ended] = p.cooldown

    # censor open episodes at the horizon
    ep_done_mean = float(np.mean(ep_dur)) if ep_dur else np.nan
    n_cens = int(ep_active.sum())
    for i in np.where(ep_active)[0]:
        ep_dur.append(W - ep_start[i])

    gov = {"NONE": 0.0, "A": p.gov_A, "AW": p.gov_A, "AS": p.gov_A, "ASR": p.gov_A, "B": p.gov_B, "C0": p.gov_C, "CR": p.gov_B, "C": p.gov_C, "ORACLE": 0.0}[variant]
    cost_short = short_pts * p.c_short
    cost_int = int_weeks * p.c_int_week
    cost_rev = n_reviews * p.c_review
    cost_ver = (flagged_game + flagged_other) * p.c_verify
    out = dict(
        otif=float(true_h.mean()),
        short_pts=float(short_pts),
        int_weeks=int_weeks,
        deg_weeks=deg_weeks,
        n_int=n_int,
        n_false=n_false,
        n_ep=n_ep,
        n_cov=len(lat),
        lat_sum=float(np.sum(lat)) if lat else 0.0,
        rec_mean=float(np.mean(ep_dur)) if ep_dur else np.nan,
        rec_done_mean=ep_done_mean,
        n_cens=n_cens,
        distortion=float(np.abs(kpi_h - true_h).mean()),
        rep_dist=float(np.abs(rep_h - true_h).mean()),
        game_weeks=game_weeks,
        flag_game=flagged_game,
        flag_other=flagged_other,
        n_reviews=n_reviews,
        n_rejected=n_rejected,
        cost_short=cost_short,
        cost_int=cost_int,
        cost_rev=cost_rev,
        cost_ver=cost_ver,
        cost_gov=gov,
        cost_total=cost_short + cost_int + cost_rev + cost_ver + gov,
    )
    return out, otif_week


def run_trial(args):
    p, seed, variants = args
    R = draw(p, seed)
    res = {}
    wk = {}
    for v in variants:
        res[v], wk[v] = run_variant(p, R, v)
    return res, wk
