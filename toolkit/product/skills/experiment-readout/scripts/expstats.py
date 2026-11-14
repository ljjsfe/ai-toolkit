#!/usr/bin/env python3
"""Zero-dependency statistics for experiment-readout. Every number the readout prints comes from here.

Usage (all output is JSON):
  expstats.py srm --counts 4800 5200 [--ratios 50 50] [--monitoring] [--checks N]
  expstats.py srm-segments --csv segments.csv [--ratios 50 50]     # header: segment,<arm>,<arm>...
  expstats.py power-prop --baseline 0.10 --mde-rel 0.05 [--alpha 0.05] [--power 0.8] [--ratio 1] [--daily N]
  expstats.py power-mean --sd 12.5 --mde-abs 0.5 [--alpha 0.05] [--power 0.8] [--ratio 1] [--daily N]
  expstats.py prop-test --control 480 5000 --treatment 540 5000 [--alpha 0.05]
  expstats.py welch --control 52.1 18.4 4980 --treatment 53.0 19.1 5011 [--alpha 0.05]   # mean sd n
  expstats.py ratio --csv units.csv [--alpha 0.05]                 # header: arm,numerator,denominator
  expstats.py holm --p 0.01 0.04 0.03 [--alpha 0.05]

`--ratio` is treatment size / control size (2 means 2:1). `--daily` is eligible units per day
entering the experiment; it adds the days needed. Method notes are in the function docstrings.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from statistics import NormalDist

Z = NormalDist()
SRM_FINAL_P = 0.01        # single final check (ai-analyst srm-check default)
SRM_MONITORING_P = 0.0005  # repeated looks while the experiment runs


# --- distributions -------------------------------------------------------------------------

def _gamma_q(a: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(a, x): series below a+1, continued fraction above."""
    if x <= 0:
        return 1.0
    log_pre = -x + a * math.log(x) - math.lgamma(a)
    if x < a + 1:
        term = total = 1.0 / a
        n = a
        for _ in range(10_000):
            n += 1
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return max(0.0, 1.0 - total * math.exp(log_pre))
    # Lentz's method for the continued fraction
    tiny = 1e-300
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return math.exp(log_pre) * h


def chi2_sf(stat: float, df: int) -> float:
    """P(X >= stat) for a chi-squared variable with df degrees of freedom."""
    return _gamma_q(df / 2.0, stat / 2.0)


def two_sided_p(z: float) -> float:
    return 2 * (1 - Z.cdf(abs(z)))


def _beta_cf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularised incomplete beta (modified Lentz)."""
    tiny = 1e-300
    c, d = 1.0, 1 - (a + b) * x / (a + 1)
    d = 1 / (tiny if abs(d) < tiny else d)
    h = d
    for m in range(1, 10_000):
        for num in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
                    -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1 + num * d
            d = 1 / (tiny if abs(d) < tiny else d)
            c = 1 + num / c
            c = tiny if abs(c) < tiny else c
            h *= d * c
        if abs(d * c - 1) < 1e-15:
            break
    return h


def _beta_inc(a: float, b: float, x: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _beta_cf(a, b, x) / a
    return 1 - front * _beta_cf(b, a, 1 - x) / b


def t_two_sided_p(t: float, df: float) -> float:
    """Two-sided p-value of Student's t: I_{df/(df+t²)}(df/2, 1/2)."""
    return _beta_inc(df / 2, 0.5, df / (df + t * t))


def t_inv(q: float, df: float) -> float:
    """Quantile of Student's t by bisection on the two-sided p (q > 0.5)."""
    target = 2 * (1 - q)
    lo, hi = 0.0, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_two_sided_p(mid, df) > target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# --- sample ratio mismatch ----------------------------------------------------------------

def srm(counts: list[float], ratios: list[float] | None = None, monitoring: bool = False,
        checks: int = 1) -> dict:
    """Chi-squared goodness of fit of observed arm counts against the designed allocation.

    The halt threshold is 0.01 for one final check, 0.0005 while monitoring, divided by
    `checks` (Bonferroni) when several periods or segments are tested.
    """
    if len(counts) < 2 or any(c < 0 for c in counts):
        raise ValueError("need two or more non-negative arm counts")
    total = sum(counts)
    if total <= 0:
        raise ValueError("total count is zero")
    ratios = ratios or [1.0] * len(counts)
    if len(ratios) != len(counts) or any(r <= 0 for r in ratios):
        raise ValueError("ratios must be positive and match the number of arms")
    shares = [r / sum(ratios) for r in ratios]
    expected = [total * s for s in shares]
    stat = sum((o - e) ** 2 / e for o, e in zip(counts, expected))
    df = len(counts) - 1
    p = chi2_sf(stat, df)
    threshold = (SRM_MONITORING_P if monitoring else SRM_FINAL_P) / max(checks, 1)
    return {
        "test": "srm_chi_squared",
        "observed": counts,
        "expected": [round(e, 2) for e in expected],
        "designed_shares": [round(s, 6) for s in shares],
        "observed_shares": [round(c / total, 6) for c in counts],
        "chi2": stat,
        "df": df,
        "p": p,
        "threshold": threshold,
        "checks": checks,
        "verdict": "HALT" if p <= threshold else "PASS",
    }


def srm_segments(rows: list[tuple[str, list[float]]], ratios: list[float] | None = None) -> dict:
    """SRM per segment, judged at the final threshold divided by the number of segments.

    Holm-adjusted p-values are reported alongside, so a single skewed segment stands out.
    """
    results = [dict(srm(c, ratios, checks=len(rows)), segment=name) for name, c in rows]
    adj = holm([r["p"] for r in results])["adjusted"]
    for r, a in zip(results, adj):
        r["p_holm"] = a
    return {"test": "srm_by_segment", "segments": results,
            "any_halt": any(r["verdict"] == "HALT" for r in results)}


# --- power and duration -------------------------------------------------------------------

def _days(n_total: float, daily: float | None) -> dict:
    if not daily:
        return {}
    if daily <= 0:
        raise ValueError("--daily must be positive")
    return {"daily": daily, "days": math.ceil(n_total / daily)}


def power_prop(baseline: float, mde_rel: float, alpha: float = 0.05, power: float = 0.8,
               ratio: float = 1.0, daily: float | None = None) -> dict:
    """Sample size for a two-sided two-proportion z-test (pooled variance under H0).

    n_c = (z_a*sqrt(p̄(1−p̄)(1+1/k)) + z_b*sqrt(p1(1−p1) + p2(1−p2)/k))² / (p2−p1)², n_t = k·n_c,
    with k = treatment/control and p̄ the allocation-weighted mean rate.
    """
    if not 0 < baseline < 1:
        raise ValueError("baseline must be in (0, 1)")
    p1, p2 = baseline, baseline * (1 + mde_rel)
    if not 0 < p2 < 1 or p1 == p2:
        raise ValueError("baseline × (1 + mde) must be in (0, 1) and differ from baseline")
    k = ratio
    za, zb = Z.inv_cdf(1 - alpha / 2), Z.inv_cdf(power)
    pbar = (p1 + k * p2) / (1 + k)
    num = za * math.sqrt(pbar * (1 - pbar) * (1 + 1 / k)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / k)
    n_c = math.ceil(num ** 2 / (p2 - p1) ** 2)
    n_t = math.ceil(k * n_c)
    out = {"test": "power_two_proportions", "baseline": p1, "treatment_rate": p2,
           "absolute_effect": p2 - p1, "alpha": alpha, "power": power, "ratio": k,
           "n_control": n_c, "n_treatment": n_t, "n_total": n_c + n_t}
    out.update(_days(n_c + n_t, daily))
    return out


def power_mean(sd: float, mde_abs: float, alpha: float = 0.05, power: float = 0.8,
               ratio: float = 1.0, daily: float | None = None) -> dict:
    """Sample size for a two-sided two-sample z-test on means with a common sd.

    n_c = (z_a + z_b)² · sd² · (1 + 1/k) / δ², n_t = k·n_c.
    """
    if sd <= 0 or mde_abs == 0:
        raise ValueError("sd must be positive and mde non-zero")
    k = ratio
    za, zb = Z.inv_cdf(1 - alpha / 2), Z.inv_cdf(power)
    n_c = math.ceil((za + zb) ** 2 * sd ** 2 * (1 + 1 / k) / mde_abs ** 2)
    n_t = math.ceil(k * n_c)
    out = {"test": "power_two_means", "sd": sd, "absolute_effect": mde_abs, "alpha": alpha,
           "power": power, "ratio": k, "n_control": n_c, "n_treatment": n_t, "n_total": n_c + n_t}
    out.update(_days(n_c + n_t, daily))
    return out


# --- effect tests -------------------------------------------------------------------------

def prop_test(xc: int, nc: int, xt: int, nt: int, alpha: float = 0.05) -> dict:
    """Two-proportion z-test: pooled standard error for p, unpooled for the interval."""
    if min(nc, nt) <= 0 or not (0 <= xc <= nc and 0 <= xt <= nt):
        raise ValueError("counts must satisfy 0 <= successes <= n, n > 0")
    pc, pt = xc / nc, xt / nt
    diff = pt - pc
    pool = (xc + xt) / (nc + nt)
    se_pool = math.sqrt(pool * (1 - pool) * (1 / nc + 1 / nt))
    se = math.sqrt(pc * (1 - pc) / nc + pt * (1 - pt) / nt)
    z = diff / se_pool if se_pool else 0.0
    zc = Z.inv_cdf(1 - alpha / 2)
    return {"test": "two_proportion_z", "rate_control": pc, "rate_treatment": pt,
            "diff": diff, "relative_lift": diff / pc if pc else None, "z": z, "p": two_sided_p(z),
            "ci": [diff - zc * se, diff + zc * se], "alpha": alpha}


def welch(mc: float, sc: float, nc: int, mt: float, st: float, nt: int, alpha: float = 0.05) -> dict:
    """Welch's t-test on a continuous metric from per-arm mean, sd and n (unequal variances)."""
    if min(nc, nt) < 2 or min(sc, st) < 0:
        raise ValueError("each arm needs n >= 2 and a non-negative sd")
    vc, vt = sc ** 2 / nc, st ** 2 / nt
    se = math.sqrt(vc + vt)
    if se == 0:
        raise ValueError("both standard deviations are zero")
    df = (vc + vt) ** 2 / (vc ** 2 / (nc - 1) + vt ** 2 / (nt - 1))
    diff = mt - mc
    t = diff / se
    tc = t_inv(1 - alpha / 2, df)
    return {"test": "welch_t", "mean_control": mc, "mean_treatment": mt, "diff": diff,
            "relative_lift": diff / mc if mc else None, "t": t, "df": df, "p": t_two_sided_p(t, df),
            "ci": [diff - tc * se, diff + tc * se], "alpha": alpha}


def _var(xs: list[float]) -> float:
    m = sum(xs) / len(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def _cov(xs: list[float], ys: list[float]) -> float:
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) - 1)


def ratio_test(arms: dict[str, tuple[list[float], list[float]]], alpha: float = 0.05) -> dict:
    """Delta-method test for a ratio metric (sum numerator / sum denominator per arm).

    Var(R) ≈ (Var(N) − 2R·Cov(N,D) + R²·Var(D)) / (mean(D)² · n). Use it whenever the analysis
    unit (session, order) differs from the randomisation unit (user); a naive per-row t-test
    understates the variance there.
    """
    if len(arms) != 2:
        raise ValueError("need exactly two arms; the first in the file is control")
    (c_name, (nc_, dc_)), (t_name, (nt_, dt_)) = list(arms.items())

    def ratio_and_var(num: list[float], den: list[float]) -> tuple[float, float]:
        if len(num) < 2 or sum(den) == 0:
            raise ValueError("each arm needs 2+ units and a non-zero denominator sum")
        r = sum(num) / sum(den)
        md = sum(den) / len(den)
        v = (_var(num) - 2 * r * _cov(num, den) + r ** 2 * _var(den)) / (md ** 2 * len(num))
        return r, v

    rc, vc = ratio_and_var(nc_, dc_)
    rt, vt = ratio_and_var(nt_, dt_)
    se = math.sqrt(vc + vt)
    diff = rt - rc
    z = diff / se if se else 0.0
    zc = Z.inv_cdf(1 - alpha / 2)
    return {"test": "ratio_delta_method", "control": c_name, "treatment": t_name,
            "ratio_control": rc, "ratio_treatment": rt, "diff": diff,
            "relative_lift": diff / rc if rc else None, "z": z, "p": two_sided_p(z),
            "ci": [diff - zc * se, diff + zc * se], "units": [len(nc_), len(nt_)], "alpha": alpha}


def holm(pvalues: list[float], alpha: float = 0.05) -> dict:
    """Holm step-down adjustment; adjusted p-values are monotone and capped at 1."""
    if not pvalues or any(not 0 <= p <= 1 for p in pvalues):
        raise ValueError("p-values must be in [0, 1]")
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running
    return {"test": "holm", "p": pvalues, "adjusted": adjusted,
            "reject": [a <= alpha for a in adjusted], "alpha": alpha}


# --- CLI ----------------------------------------------------------------------------------

def _read_rows(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("srm")
    s.add_argument("--counts", type=float, nargs="+", required=True)
    s.add_argument("--ratios", type=float, nargs="+")
    s.add_argument("--monitoring", action="store_true")
    s.add_argument("--checks", type=int, default=1)

    s = sub.add_parser("srm-segments")
    s.add_argument("--csv", required=True)
    s.add_argument("--ratios", type=float, nargs="+")

    for name, extra in (("power-prop", ("--baseline", "--mde-rel")), ("power-mean", ("--sd", "--mde-abs"))):
        s = sub.add_parser(name)
        for flag in extra:
            s.add_argument(flag, type=float, required=True)
        s.add_argument("--alpha", type=float, default=0.05)
        s.add_argument("--power", type=float, default=0.8)
        s.add_argument("--ratio", type=float, default=1.0)
        s.add_argument("--daily", type=float)

    s = sub.add_parser("prop-test")
    s.add_argument("--control", type=int, nargs=2, required=True, metavar=("SUCCESSES", "N"))
    s.add_argument("--treatment", type=int, nargs=2, required=True, metavar=("SUCCESSES", "N"))
    s.add_argument("--alpha", type=float, default=0.05)

    s = sub.add_parser("welch")
    s.add_argument("--control", type=float, nargs=3, required=True, metavar=("MEAN", "SD", "N"))
    s.add_argument("--treatment", type=float, nargs=3, required=True, metavar=("MEAN", "SD", "N"))
    s.add_argument("--alpha", type=float, default=0.05)

    s = sub.add_parser("ratio")
    s.add_argument("--csv", required=True)
    s.add_argument("--alpha", type=float, default=0.05)

    s = sub.add_parser("holm")
    s.add_argument("--p", type=float, nargs="+", required=True)
    s.add_argument("--alpha", type=float, default=0.05)

    a = ap.parse_args(argv)
    try:
        if a.cmd == "srm":
            out = srm(a.counts, a.ratios, a.monitoring, a.checks)
        elif a.cmd == "srm-segments":
            rows = _read_rows(a.csv)
            if not rows:
                raise ValueError("empty CSV")
            arms = [k for k in rows[0] if k != "segment"]
            out = srm_segments([(r["segment"], [float(r[k]) for k in arms]) for r in rows], a.ratios)
        elif a.cmd == "power-prop":
            out = power_prop(a.baseline, a.mde_rel, a.alpha, a.power, a.ratio, a.daily)
        elif a.cmd == "power-mean":
            out = power_mean(a.sd, a.mde_abs, a.alpha, a.power, a.ratio, a.daily)
        elif a.cmd == "prop-test":
            out = prop_test(*a.control, *a.treatment, alpha=a.alpha)
        elif a.cmd == "welch":
            (mc, sc, nc), (mt, st, nt) = a.control, a.treatment
            out = welch(mc, sc, int(nc), mt, st, int(nt), a.alpha)
        elif a.cmd == "ratio":
            arms: dict[str, tuple[list[float], list[float]]] = {}
            for r in _read_rows(a.csv):
                num, den = arms.setdefault(r["arm"], ([], []))
                num.append(float(r["numerator"]))
                den.append(float(r["denominator"]))
            out = ratio_test(arms, a.alpha)
        else:
            out = holm(a.p, a.alpha)
    except (ValueError, KeyError, OSError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
