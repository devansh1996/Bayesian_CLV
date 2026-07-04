"""
src/priors.py
=============
Data-informed, weakly-informative priors for the BG/NBD and Gamma-Gamma models,
plus prior-predictive checks that validate them against the calibration data.

Motivation
----------
The default priors in models.py are HalfNormal(sigma=10) on every parameter.
That is badly *scaled* for this dataset:

  * BG/NBD `r` and the Beta shapes `a, b` are O(1) quantities, so sigma=10 is
    far too diffuse and lets NUTS wander into stiff regions of the posterior
    (this manifests as the sampler hitting max tree depth and taking hours).
  * Gamma-Gamma `gamma` carries *monetary* units: the population mean repeat
    spend is ~GBP 385, which forces gamma to O(few hundred). HalfNormal(sigma=10)
    places essentially all prior mass below ~40 — a severe prior/likelihood
    conflict.

The priors here keep the HalfNormal family (so they drop straight into the
existing `build_bgnbd(..., priors=)` / `build_gamma_gamma(..., priors=)` API via
the `*_sigma` keys) but set each scale from a method-of-moments read of the
calibration data. They remain weakly informative — a HalfNormal(sigma) has mean
~0.8*sigma and sd ~0.6*sigma, so an order of magnitude of spread around the
data-implied scale — while removing the gross mis-scaling. Prior-predictive
checks below confirm the implied frequency and spend distributions are
plausible.

This is empirical Bayes on the *scale* of otherwise-vague priors, a standard and
defensible choice; it is validated, not merely asserted, by the checks.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple


# HalfNormal(sigma) has mean sigma*sqrt(2/pi). To make the prior mean land on a
# target scale, use sigma = target / _HN_MEAN_FACTOR.
_HN_MEAN_FACTOR = np.sqrt(2.0 / np.pi)   # ~0.7979


def _sigma_for_mean(target_mean: float) -> float:
    """HalfNormal sigma whose prior mean equals `target_mean`."""
    return float(target_mean / _HN_MEAN_FACTOR)


def data_informed_priors(
    customers: pd.DataFrame,
    verbose: bool = True,
) -> Dict[str, Dict[str, float]]:
    """
    Derive data-scaled HalfNormal sigmas for the BG/NBD and Gamma-Gamma models.

    Parameters
    ----------
    customers : customer-level DataFrame with columns frequency, recency, T,
                monetary_value (output of aggregate_customers()).

    Returns
    -------
    dict with two sub-dicts ready to pass as `priors=`:
        {"bgnbd":       {"r_sigma", "alpha_sigma", "a_sigma", "b_sigma"},
         "gamma_gamma": {"p_sigma", "q_sigma", "gamma_sigma"}}
    """
    T    = customers["T"].clip(lower=1e-6)
    freq = customers["frequency"].astype(float)
    repeat = customers[customers["frequency"] > 0]
    mv   = repeat["monetary_value"].astype(float)

    # ── BG/NBD purchase-rate mixing distribution  lambda ~ Gamma(r, alpha) ─────
    # E[lambda] = r/alpha = mean weekly purchase rate.
    rate = (freq / T)
    mean_rate = float(rate.mean())
    # alpha ~ typical time-scale (weeks) of the rate: 1 / mean_rate.
    alpha_scale = 1.0 / max(mean_rate, 1e-6)
    # r = alpha * mean_rate ~ O(1) shape controlling heterogeneity.
    r_scale = alpha_scale * mean_rate            # = 1.0 by construction; kept explicit

    # ── BG/NBD dropout  p ~ Beta(a, b) ────────────────────────────────────────
    # Anchor E[p] = a/(a+b) to the one-time-buyer fraction (a rough churn proxy),
    # keeping a, b at O(1) so the Beta stays diffuse rather than degenerate.
    p_drop = float((freq == 0).mean())           # ~0.33 here
    a_target = 1.5                                # weakly informative, O(1)
    b_target = a_target * (1.0 - p_drop) / max(p_drop, 1e-6)

    # ── Gamma-Gamma monetary  gamma carries money units ───────────────────────
    # Population mean spend (model's own x->0 shrinkage target) = q*gamma/(q-1).
    # With q at its prior mean, back out the gamma scale that reproduces the
    # observed mean repeat spend.
    mean_spend = float(mv.mean())
    q_target = 3.0                               # typical GG across-customer shape
    gamma_target = mean_spend * (q_target - 1.0) / q_target

    priors = {
        "bgnbd": {
            "r_sigma":     round(_sigma_for_mean(r_scale), 3),
            "alpha_sigma": round(_sigma_for_mean(alpha_scale), 3),
            "a_sigma":     round(_sigma_for_mean(a_target), 3),
            "b_sigma":     round(_sigma_for_mean(b_target), 3),
        },
        "gamma_gamma": {
            "p_sigma":     2.0,                   # within-customer shape, O(1)
            "q_sigma":     round(_sigma_for_mean(q_target), 3),
            "gamma_sigma": round(_sigma_for_mean(gamma_target), 3),
        },
    }

    if verbose:
        print("Data-informed prior scales (HalfNormal sigmas)")
        print("=" * 55)
        print(f"  mean weekly purchase rate : {mean_rate:.4f}")
        print(f"  implied alpha scale (wk)  : {alpha_scale:.2f}")
        print(f"  implied r scale           : {r_scale:.2f}")
        print(f"  one-time fraction (E[p])  : {p_drop:.3f}  -> a~{a_target}, b~{b_target:.2f}")
        print(f"  mean repeat spend (GBP)   : {mean_spend:.2f}")
        print(f"  implied gamma scale (q=3) : {gamma_target:.1f}")
        print("-" * 55)
        print(f"  bgnbd       : {priors['bgnbd']}")
        print(f"  gamma_gamma : {priors['gamma_gamma']}")
        print("  (compare to the default HalfNormal(sigma=10) on every parameter)")

    return priors


# ──────────────────────────────────────────────────────────────────────────────
# PRIOR PREDICTIVE CHECKS
# ──────────────────────────────────────────────────────────────────────────────

def prior_predictive_bgnbd(
    sigmas: Dict[str, float],
    T: np.ndarray,
    n_draws: int = 2000,
    seed: int = 0,
) -> np.ndarray:
    """
    Simulate repeat-transaction counts from the BG/NBD generative process under
    the given HalfNormal prior sigmas, using the empirical distribution of T.

    Returns an array of simulated repeat-purchase counts (one per draw).
    """
    rng = np.random.default_rng(seed)
    T = np.asarray(T, dtype=float)

    # Draw population parameters (HalfNormal = |Normal(0, sigma)|).
    r     = np.abs(rng.normal(0, sigmas["r_sigma"],     n_draws))
    alpha = np.abs(rng.normal(0, sigmas["alpha_sigma"], n_draws))
    a     = np.abs(rng.normal(0, sigmas["a_sigma"],     n_draws))
    b     = np.abs(rng.normal(0, sigmas["b_sigma"],     n_draws))
    r     = np.clip(r,     1e-3, None)
    alpha = np.clip(alpha, 1e-3, None)
    a     = np.clip(a,     1e-3, None)
    b     = np.clip(b,     1e-3, None)

    # One customer-lifetime simulation per draw, using a random observed T.
    Tsamp = rng.choice(T, size=n_draws)
    lam   = rng.gamma(shape=r, scale=1.0 / alpha)     # weekly purchase rate
    p     = rng.beta(a, b)                             # dropout prob per purchase

    counts = np.zeros(n_draws, dtype=int)
    for i in range(n_draws):
        t, x = 0.0, 0
        li = max(lam[i], 1e-8)
        while True:
            t += rng.exponential(1.0 / li)            # next interpurchase gap
            if t > Tsamp[i]:
                break
            x += 1                                    # a repeat purchase occurred
            if rng.random() < p[i]:                   # customer drops out
                break
        counts[i] = x
    return counts


def prior_predictive_gamma_gamma(
    sigmas: Dict[str, float],
    n_draws: int = 5000,
    seed: int = 0,
) -> np.ndarray:
    """
    Simulate implied population mean spend (GBP) under the given GG prior sigmas,
    using the model's own shrinkage target E[M] = q*gamma/(q-1).

    Returns an array of implied mean-spend values (draws with q<=1 dropped).
    """
    rng = np.random.default_rng(seed)
    q     = np.abs(rng.normal(0, sigmas["q_sigma"],     n_draws))
    gamma = np.abs(rng.normal(0, sigmas["gamma_sigma"], n_draws))
    ok = q > 1.0
    q, gamma = q[ok], gamma[ok]
    return q * gamma / (q - 1.0)


def _summ(x: np.ndarray) -> str:
    q = np.quantile(x, [0.05, 0.5, 0.95])
    return f"mean={np.mean(x):.2f}  p05={q[0]:.2f}  median={q[1]:.2f}  p95={q[2]:.2f}"


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from pathlib import Path

    cust_path = Path("data/processed/customers.parquet")
    if not cust_path.exists():
        raise SystemExit(
            "customers.parquet not found — run `python src/data.py` first."
        )
    customers = pd.read_parquet(cust_path)

    priors = data_informed_priors(customers)

    print("\nPrior-predictive checks")
    print("=" * 55)

    # BG/NBD: simulated repeat counts vs observed.
    obs = customers["frequency"].values.astype(float)
    for label, s in [
        ("default HN(10)", {k: 10.0 for k in priors["bgnbd"]}),
        ("data-informed",  priors["bgnbd"]),
    ]:
        sim = prior_predictive_bgnbd(s, customers["T"].values, n_draws=3000)
        print(f"  BG/NBD freq [{label:14s}] {_summ(sim.astype(float))}")
    print(f"  BG/NBD freq [{'OBSERVED':14s}] {_summ(obs)}")

    # Gamma-Gamma: implied mean spend vs observed.
    obs_spend = customers.loc[customers.frequency > 0, "monetary_value"].mean()
    for label, s in [
        ("default HN(10)", {"q_sigma": 10.0, "gamma_sigma": 10.0}),
        ("data-informed",  priors["gamma_gamma"]),
    ]:
        sim = prior_predictive_gamma_gamma(s)
        print(f"  GG mean-spend [{label:12s}] {_summ(sim)}")
    print(f"  GG mean-spend [{'OBSERVED':12s}] mean={obs_spend:.2f}")

    print("\nInterpretation: the data-informed priors should bracket the observed")
    print("frequency and spend, whereas HalfNormal(10) badly misses the spend scale.")
