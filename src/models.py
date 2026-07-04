"""
src/models.py
=============
Bayesian CLV models built in PyMC:

    1. Standard BG/NBD          — build_bgnbd()
    2. Hierarchical BG/NBD      — build_hierarchical_bgnbd()
    3. Gamma-Gamma monetary     — build_gamma_gamma()

Prediction utilities:
    predict_conditional_transactions()
    predict_monetary_value()
    compute_clv_posterior()
    compute_p_alive()

Sampling & I/O helpers:
    fit_model()
    load_trace()

Typical notebook workflow
-------------------------
    from src.data import load_processed
    from src.models import build_bgnbd, fit_model, predict_conditional_transactions

    _, _, customers, _ = load_processed()

    model = build_bgnbd(customers)
    trace = fit_model(model, save_name="bgnbd_standard")

    preds = predict_conditional_transactions(trace, customers, t_future=13.0)

References
----------
    Fader, Hardie, Lee (2005) — "Counting Your Customers the Easy Way:
        An Alternative to the Pareto/NBD Model"
    Fader & Hardie (2013)     — "The Gamma-Gamma Model of Monetary Value"
"""

import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
import arviz as az
from scipy.special import gammaln, betaln
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

TRACES_DIR = Path("outputs/traces")


# ──────────────────────────────────────────────────────────────────────────────
# 1. STANDARD BG/NBD
# ──────────────────────────────────────────────────────────────────────────────

def build_bgnbd(
    data: pd.DataFrame,
    priors: Optional[Dict[str, Any]] = None,
) -> pm.Model:
    """
    Build a standard (pooled) BG/NBD model in PyMC.

    The BG/NBD model (Fader, Hardie & Lee 2005) assumes:
        - Each customer makes purchases at a Poisson rate λ while active.
        - λ is drawn from a Gamma(r, α) population distribution.
        - After each purchase, the customer may "die" (churn) with
          probability p drawn from a Beta(a, b) population distribution.

    All four population parameters (r, α, a, b) are estimated from data.
    The individual λ and p values are analytically integrated out, so the
    model has only 4 parameters regardless of how many customers there are.

    Parameters
    ----------
    data   : customer-level DataFrame with columns: frequency, recency, T
             (output of aggregate_customers())
    priors : optional dict to override default HalfNormal sigma values, e.g.
             {"r_sigma": 5, "alpha_sigma": 5, "a_sigma": 5, "b_sigma": 5}

    Returns
    -------
    pm.Model — PyMC model object (not yet sampled; call fit_model() on it)
    """
    p = priors or {}

    # Extract arrays — PyMC needs plain numpy arrays, not pandas Series
    x   = data["frequency"].values.astype(float)   # repeat purchases
    t_x = data["recency"].values.astype(float)      # weeks first → last purchase
    T   = data["T"].values.astype(float)            # weeks first purchase → cal end

    with pm.Model() as model:

        # ── Population-level priors ──────────────────────────────────────────
        # HalfNormal keeps all four parameters strictly positive.
        # Default sigma=10 is weakly informative — it allows a wide range of
        # values without strongly pulling toward any particular value.
        r     = pm.HalfNormal("r",     sigma=p.get("r_sigma",     10))
        alpha = pm.HalfNormal("alpha", sigma=p.get("alpha_sigma", 10))
        a     = pm.HalfNormal("a",     sigma=p.get("a_sigma",     10))
        b     = pm.HalfNormal("b",     sigma=p.get("b_sigma",     10))

        # ── BG/NBD log-likelihood (Fader et al. 2005, Eq. 7) ─────────────────
        #
        # The likelihood has two components:
        #
        #   A_1 : customer made x purchases and is STILL ALIVE at T
        #   A_2 : customer made x purchases and CHURNED after their last one
        #
        # We use logaddexp(ln_A1, ln_A2) for numerical stability — it computes
        # log(A1 + A2) without ever computing the raw probabilities, which
        # could underflow to zero for customers with many purchases.

        # ln(A_1) — alive term
        ln_A_1 = (
              pt.gammaln(r + x)
            - pt.gammaln(r)
            + r     * pm.math.log(alpha)
            - (r + x) * pm.math.log(alpha + T)
            + pt.gammaln(a + b)
            + pt.gammaln(b + x)
            - pt.gammaln(b)
            - pt.gammaln(a + b + x)
        )

        # ln(A_2) — dead term, only defined for customers with x > 0
        # (a customer with zero repeat purchases cannot have churned after
        #  a repeat purchase, so this term doesn't exist for them)
        delta = pm.math.switch(
            pm.math.gt(x, 0),
            (
                  pt.gammaln(r + x)
                - pt.gammaln(r)
                + r     * pm.math.log(alpha)
                - (r + x) * pm.math.log(alpha + t_x)
                + pt.gammaln(a + 1 + b + x - 1)
                - pt.gammaln(a + b + x)
                + pm.math.log(a)
                - pm.math.log(b + x - 1)
            ),
            -np.inf,   # log(0) — no dead term for x=0 customers
        )

        log_likelihood = pm.math.logaddexp(ln_A_1, delta)

        # pm.Potential adds the log-likelihood to the model without creating
        # an observed random variable. We use it here because the BG/NBD
        # likelihood is a custom expression, not one of PyMC's built-in
        # distribution families.
        pm.Potential("obs", log_likelihood.sum())

    return model


# ──────────────────────────────────────────────────────────────────────────────
# 2. HIERARCHICAL BG/NBD  (per country segment)
# ──────────────────────────────────────────────────────────────────────────────

def build_hierarchical_bgnbd(
    data: pd.DataFrame,
    segment_col: str = "country_segment",
) -> pm.Model:
    """
    Build a hierarchical BG/NBD model with per-country-segment parameters.

    Extends the standard BG/NBD by allowing each country segment to have
    its own (r, α, a, b), while sharing information across segments through
    a common set of hyperpriors. This is the "partial pooling" approach:
    segments with few customers borrow strength from the global population.

    Non-centered parameterization
    ------------------------------
    Instead of sampling segment parameters directly (r_seg ~ HalfNormal(μ, σ)),
    we sample standardised offsets (z ~ Normal(0,1)) and reconstruct:

        r_seg = softplus(μ_r + σ_r * z_r)

    This avoids "funnel geometry" — a pathology where the sampler gets stuck
    when μ and σ are sampled jointly and σ is small. Non-centered
    parameterization is best practice for hierarchical models in PyMC.

    Parameters
    ----------
    data        : customer-level DataFrame (output of collapse_countries())
    segment_col : column name for country segment labels

    Returns
    -------
    pm.Model — PyMC model object
    """
    segments = data[segment_col].unique()
    n_seg    = len(segments)

    # Map each customer to a segment index (0, 1, 2, ...)
    seg_idx = pd.Categorical(data[segment_col], categories=segments).codes

    x   = data["frequency"].values.astype(float)
    t_x = data["recency"].values.astype(float)
    T   = data["T"].values.astype(float)

    with pm.Model(coords={"segment": segments}) as model:

        # ── Hyperpriors (population-level, shared across all segments) ────────
        mu_r     = pm.HalfNormal("mu_r",     sigma=10)
        sigma_r  = pm.HalfNormal("sigma_r",  sigma=5)
        mu_alpha = pm.HalfNormal("mu_alpha", sigma=10)
        sigma_alpha = pm.HalfNormal("sigma_alpha", sigma=5)
        mu_a     = pm.HalfNormal("mu_a",     sigma=10)
        sigma_a  = pm.HalfNormal("sigma_a",  sigma=5)
        mu_b     = pm.HalfNormal("mu_b",     sigma=10)
        sigma_b  = pm.HalfNormal("sigma_b",  sigma=5)

        # ── Non-centered offsets (one per segment) ────────────────────────────
        z_r     = pm.Normal("z_r",     0, 1, dims="segment")
        z_alpha = pm.Normal("z_alpha", 0, 1, dims="segment")
        z_a     = pm.Normal("z_a",     0, 1, dims="segment")
        z_b     = pm.Normal("z_b",     0, 1, dims="segment")

        # ── Segment-level parameters (positive via softplus) ──────────────────
        # softplus(x) = log(1 + exp(x)) ≈ max(0, x) — smooth, always positive
        r     = pm.Deterministic("r",     pt.softplus(mu_r     + sigma_r     * z_r),     dims="segment")
        alpha = pm.Deterministic("alpha", pt.softplus(mu_alpha + sigma_alpha * z_alpha), dims="segment")
        a     = pm.Deterministic("a",     pt.softplus(mu_a     + sigma_a     * z_a),     dims="segment")
        b     = pm.Deterministic("b",     pt.softplus(mu_b     + sigma_b     * z_b),     dims="segment")

        # ── Index into per-segment parameters for each customer ───────────────
        # seg_idx maps each customer row to their segment's parameter vector
        r_i     = r[seg_idx]
        alpha_i = alpha[seg_idx]
        a_i     = a[seg_idx]
        b_i     = b[seg_idx]

        # ── BG/NBD log-likelihood (same formula, now with per-customer params) ─
        ln_A_1 = (
              pt.gammaln(r_i + x)
            - pt.gammaln(r_i)
            + r_i   * pm.math.log(alpha_i)
            - (r_i + x) * pm.math.log(alpha_i + T)
            + pt.gammaln(a_i + b_i)
            + pt.gammaln(b_i + x)
            - pt.gammaln(b_i)
            - pt.gammaln(a_i + b_i + x)
        )

        delta = pm.math.switch(
            pm.math.gt(x, 0),
            (
                  pt.gammaln(r_i + x)
                - pt.gammaln(r_i)
                + r_i   * pm.math.log(alpha_i)
                - (r_i + x) * pm.math.log(alpha_i + t_x)
                + pt.gammaln(a_i + 1 + b_i + x - 1)
                - pt.gammaln(a_i + b_i + x)
                + pm.math.log(a_i)
                - pm.math.log(b_i + x - 1)
            ),
            -np.inf,
        )

        log_likelihood = pm.math.logaddexp(ln_A_1, delta)
        pm.Potential("obs", log_likelihood.sum())

    return model


# ──────────────────────────────────────────────────────────────────────────────
# 3. GAMMA-GAMMA MONETARY MODEL
# ──────────────────────────────────────────────────────────────────────────────

def build_gamma_gamma(
    data: pd.DataFrame,
    priors: Optional[Dict[str, Any]] = None,
) -> pm.Model:
    """
    Build the Gamma-Gamma model for monetary value (Fader & Hardie 2013).

    The Gamma-Gamma model assumes:
        - Each customer has a latent average transaction value ν ~ Gamma(p, γ)
        - Individual transaction amounts are drawn from Gamma(p, ν)
        - The observed average spend per customer m̄ is a sufficient statistic

    Importantly, this model is only fit on REPEAT purchasers (frequency > 0)
    because:
        1. You need at least one observation to estimate average spend.
        2. First-purchase spend may differ systematically from repeat spend
           (promotional discounts, trial behaviour, etc.).

    Parameters
    ----------
    data   : customer-level DataFrame with columns: frequency, monetary_value
    priors : optional dict to override default prior sigmas

    Returns
    -------
    pm.Model — PyMC model object
    """
    p_cfg = priors or {}

    # Filter to repeat purchasers only
    repeat = data[data["frequency"] > 0].copy()

    if len(repeat) == 0:
        raise ValueError("No repeat purchasers found. Check your data.")

    x = repeat["frequency"].values.astype(float)      # number of repeat purchases
    m = repeat["monetary_value"].values.astype(float)  # mean spend per repeat purchase

    print(f"  Gamma-Gamma fitting on {len(repeat):,} repeat purchasers")
    print(f"  Mean monetary value: £{m.mean():.2f}  |  Median: £{np.median(m):.2f}")

    with pm.Model() as model:

        # ── Population parameters ─────────────────────────────────────────────
        p_param = pm.HalfNormal("p",     sigma=p_cfg.get("p_sigma",     10))
        q       = pm.HalfNormal("q",     sigma=p_cfg.get("q_sigma",     10))
        gamma   = pm.HalfNormal("gamma", sigma=p_cfg.get("gamma_sigma", 10))

        # ── Gamma-Gamma log-likelihood (Fader & Hardie 2013, Eq. 4) ──────────
        #
        # The joint density of (x, m̄) integrates out the latent spend rate ν,
        # yielding a closed-form expression. Taking the log:
        #
        #   log L = log Γ(p·x + q)  − log Γ(p·x)  − log Γ(q)
        #         + q · log(γ)
        #         + (p·x − 1) · log(m̄)
        #         + (p·x)     · log(x)
        #         − (p·x + q) · log(x·m̄ + γ)
        log_lik = (
              pt.gammaln(p_param * x + q)
            - pt.gammaln(p_param * x)
            - pt.gammaln(q)
            + q           * pm.math.log(gamma)
            + (p_param * x - 1) * pm.math.log(m)
            + (p_param * x)     * pm.math.log(x)
            - (p_param * x + q) * pm.math.log(x * m + gamma)
        )

        pm.Potential("obs", log_lik.sum())

    return model


# ──────────────────────────────────────────────────────────────────────────────
# 4. P(ALIVE) COMPUTATION
# ──────────────────────────────────────────────────────────────────────────────

def compute_p_alive(
    r: float,
    alpha: float,
    a: float,
    b: float,
    x: np.ndarray,
    t_x: np.ndarray,
    T: np.ndarray,
) -> np.ndarray:
    """
    Compute P(alive at T | x, t_x, T) for each customer.

    Uses Fader, Hardie & Lee (2005) Eq. 11:

        P(alive) = A_alive / (A_alive + A_dead)

    where A_alive is the probability of the observed purchase pattern if
    the customer is still active, and A_dead is the probability if they
    churned after their last purchase.

    Parameters
    ----------
    r, alpha, a, b : scalar BG/NBD parameters (single posterior draw)
    x, t_x, T      : customer-level arrays

    Returns
    -------
    np.ndarray of shape (n_customers,) — P(alive) in [0, 1]
    """
    # Log-probability that customer is alive at T
    log_alive = -(r + x) * np.log(alpha + T) + betaln(a, b + x)

    # Log-probability that customer churned after their last purchase
    # Only defined for customers with at least one repeat (x > 0)
    log_dead = np.full_like(x, -np.inf, dtype=float)
    mask = x > 0
    if mask.any():
        log_dead[mask] = (
            -(r + x[mask]) * np.log(alpha + t_x[mask])
            + np.log(a)
            - np.log(np.maximum(b + x[mask] - 1, 1e-10))
            + betaln(a + 1, b + x[mask] - 1)
        )

    # P(alive) = exp(log_alive) / (exp(log_alive) + exp(log_dead))
    #          = 1 / (1 + exp(log_dead - log_alive))  — numerically stable
    log_total = np.logaddexp(log_alive, log_dead)
    p_alive   = np.exp(log_alive - log_total)

    return np.clip(p_alive, 0.0, 1.0)


# ──────────────────────────────────────────────────────────────────────────────
# 5. PREDICTION: CONDITIONAL EXPECTED TRANSACTIONS
# ──────────────────────────────────────────────────────────────────────────────

def predict_conditional_transactions(
    trace: az.InferenceData,
    data: pd.DataFrame,
    t_future: float,
    n_samples: int = 1000,
    hierarchical: bool = False,
    segment_col: str = "country_segment",
) -> np.ndarray:
    """
    Compute E[X(t_future) | x, t_x, T] for each customer using posterior samples.

    For each posterior draw of (r, α, a, b), computes:

        E[transactions] = P(alive) × (r + x) / (α + T) × t_future

    This is the BG/NBD conditional expectation — it multiplies the
    probability of still being active by the expected rate if active.

    Parameters
    ----------
    trace       : ArviZ InferenceData from a fitted BG/NBD model
    data        : customer-level DataFrame
    t_future    : prediction horizon in same time units as T (e.g. 13.0 weeks)
    n_samples   : how many posterior draws to use (more = more accurate CI)
    hierarchical: if True, uses per-segment posterior parameters
    segment_col : segment column name (only used when hierarchical=True)

    Returns
    -------
    np.ndarray of shape (n_samples, n_customers)
        Each row is one posterior draw; each column is one customer.
        Use .mean(axis=0) for point predictions, quantiles for intervals.
    """
    posterior = trace.posterior

    x   = data["frequency"].values.astype(float)
    t_x = data["recency"].values.astype(float)
    T   = data["T"].values.astype(float)

    predictions = np.zeros((n_samples, len(data)))

    if hierarchical:
        # Per-customer parameters — index into segment dimension
        segments = data[segment_col].values
        seg_cats = pd.Categorical(segments, categories=posterior.coords["segment"].values)
        seg_idx  = seg_cats.codes

        # Flatten posterior chains: (chains, draws, segments) → (total_draws, segments)
        n_seg      = posterior.sizes["segment"]
        r_post     = posterior["r"].values.reshape(-1, n_seg)[:n_samples]
        alpha_post = posterior["alpha"].values.reshape(-1, n_seg)[:n_samples]
        a_post     = posterior["a"].values.reshape(-1, n_seg)[:n_samples]
        b_post     = posterior["b"].values.reshape(-1, n_seg)[:n_samples]

        for s in range(n_samples):
            r_s     = r_post[s][seg_idx]
            alpha_s = alpha_post[s][seg_idx]
            a_s     = a_post[s][seg_idx]
            b_s     = b_post[s][seg_idx]

            p_alive = _compute_p_alive_vectorized(r_s, alpha_s, a_s, b_s, x, t_x, T)
            predictions[s] = p_alive * (r_s + x) / (alpha_s + T) * t_future

    else:
        # Standard model — scalar parameters per draw
        r_flat     = posterior["r"].values.flatten()[:n_samples]
        alpha_flat = posterior["alpha"].values.flatten()[:n_samples]
        a_flat     = posterior["a"].values.flatten()[:n_samples]
        b_flat     = posterior["b"].values.flatten()[:n_samples]

        for s in range(n_samples):
            p_alive = compute_p_alive(
                r_flat[s], alpha_flat[s], a_flat[s], b_flat[s], x, t_x, T
            )
            predictions[s] = p_alive * (r_flat[s] + x) / (alpha_flat[s] + T) * t_future

    return predictions


def _compute_p_alive_vectorized(
    r: np.ndarray,
    alpha: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    x: np.ndarray,
    t_x: np.ndarray,
    T: np.ndarray,
) -> np.ndarray:
    """
    Vectorised P(alive) for the hierarchical model where r, alpha, a, b
    are arrays (one value per customer, not scalars).
    """
    log_alive = -(r + x) * np.log(alpha + T) + betaln(a, b + x)

    log_dead = np.full_like(x, -np.inf, dtype=float)
    mask = x > 0
    if mask.any():
        log_dead[mask] = (
            -(r[mask] + x[mask]) * np.log(alpha[mask] + t_x[mask])
            + np.log(a[mask])
            - np.log(np.maximum(b[mask] + x[mask] - 1, 1e-10))
            + betaln(a[mask] + 1, b[mask] + x[mask] - 1)
        )

    log_total = np.logaddexp(log_alive, log_dead)
    return np.clip(np.exp(log_alive - log_total), 0.0, 1.0)


# ──────────────────────────────────────────────────────────────────────────────
# 6. PREDICTION: EXPECTED MONETARY VALUE
# ──────────────────────────────────────────────────────────────────────────────

def predict_monetary_value(
    trace: az.InferenceData,
    data: pd.DataFrame,
    n_samples: int = 1000,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict expected average transaction value using the Gamma-Gamma posterior.

    The conditional expectation of average spend given observed data is:

        E[M | x, m̄, p, q, γ] = (q·γ + p·x·m̄) / (q + p·x − 1)

    Only valid when (q + p·x) > 1. Customers with very few purchases
    (low x) return high uncertainty; their predictions regress toward
    the population mean γ/q.

    Parameters
    ----------
    trace    : ArviZ InferenceData from a fitted Gamma-Gamma model
    data     : customer-level DataFrame (must include frequency > 0 rows)
    n_samples: number of posterior draws to use

    Returns
    -------
    predictions : np.ndarray of shape (n_samples, n_repeat_customers)
    repeat_idx  : boolean mask identifying which rows of data were used
    """
    posterior = trace.posterior

    repeat_mask = data["frequency"].values > 0
    repeat      = data[repeat_mask]

    x = repeat["frequency"].values.astype(float)
    m = repeat["monetary_value"].values.astype(float)

    p_flat     = posterior["p"].values.flatten()[:n_samples]
    q_flat     = posterior["q"].values.flatten()[:n_samples]
    gamma_flat = posterior["gamma"].values.flatten()[:n_samples]

    predictions = np.zeros((n_samples, len(repeat)))

    for s in range(n_samples):
        p_s, q_s, g_s = p_flat[s], q_flat[s], gamma_flat[s]
        # Clamp denominator to avoid division by very small numbers
        denom = np.maximum(q_s + x * p_s - 1, 1e-6)
        predictions[s] = (q_s * g_s + x * p_s * m) / denom

    return predictions, repeat_mask


# ──────────────────────────────────────────────────────────────────────────────
# 7. CLV POSTERIOR
# ──────────────────────────────────────────────────────────────────────────────

def compute_clv_posterior(
    tx_predictions: np.ndarray,
    monetary_predictions: np.ndarray,
    repeat_mask: np.ndarray,
    margin: float = 1.0,
) -> np.ndarray:
    """
    Combine transaction and monetary predictions into a CLV posterior.

    CLV = E[transactions] × E[avg spend] × margin

    Non-repeat customers (frequency = 0) have monetary_value = 0 in
    aggregate_customers(), so their CLV contribution is zero unless
    we impute a spend estimate. Here we use the population mean from
    the monetary_predictions as a simple imputation.

    Parameters
    ----------
    tx_predictions      : (n_samples, n_all_customers)  from predict_conditional_transactions()
    monetary_predictions: (n_samples, n_repeat_customers) from predict_monetary_value()
    repeat_mask         : boolean mask of shape (n_all_customers,) identifying repeaters
    margin              : profit margin multiplier (default 1.0 = revenue CLV)

    Returns
    -------
    np.ndarray of shape (n_samples, n_all_customers) — CLV posterior samples
    """
    n_samples   = tx_predictions.shape[0]
    n_customers = tx_predictions.shape[1]

    # Build a full monetary array — fill in the repeat customers' predictions,
    # impute population mean for one-time buyers
    full_monetary = np.zeros((n_samples, n_customers))

    # Repeat customers: use their predicted monetary value
    full_monetary[:, repeat_mask] = monetary_predictions

    # One-time buyers: impute the cross-sample, cross-customer mean
    pop_mean = monetary_predictions.mean()
    full_monetary[:, ~repeat_mask] = pop_mean

    clv = tx_predictions * full_monetary * margin
    return clv


# ──────────────────────────────────────────────────────────────────────────────
# 8. SAMPLING & SERIALISATION
# ──────────────────────────────────────────────────────────────────────────────

def fit_model(
    model: pm.Model,
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.9,
    random_seed: int = 42,
    save_name: Optional[str] = None,
) -> az.InferenceData:
    """
    Sample from a PyMC model using NUTS and return ArviZ InferenceData.

    NUTS (No-U-Turn Sampler) is the default HMC sampler in PyMC. It
    automatically adapts its step size and trajectory length, making
    it efficient for the correlated, high-dimensional posteriors that
    arise in hierarchical models.

    Parameters
    ----------
    model         : PyMC model from build_bgnbd() / build_hierarchical_bgnbd()
                    / build_gamma_gamma()
    draws         : number of posterior samples per chain after warm-up
    tune          : number of warm-up (adaptation) steps — discarded
    chains        : number of independent chains (≥4 recommended for R-hat)
    target_accept : NUTS step-size target (0.9 is robust; raise to 0.95 if
                    you see divergences in the trace)
    random_seed   : reproducibility seed
    save_name     : if provided, saves trace to outputs/traces/<save_name>.nc
                    (NetCDF format — fast reload with load_trace())

    Returns
    -------
    az.InferenceData — contains posterior, sample_stats, and (if available)
                       prior and posterior_predictive groups
    """
    print(f"\nSampling: {chains} chains × {draws} draws  (tune={tune})")

    with model:
        trace = pm.sample(
            draws          = draws,
            tune           = tune,
            chains         = chains,
            target_accept  = target_accept,
            random_seed    = random_seed,
            return_inferencedata = True,
            progressbar    = True,
        )

    # Quick diagnostics
    r_hat_max = float(az.rhat(trace).to_array().max())
    ess_min   = float(az.ess(trace).to_array().min())
    div_count = int(trace.sample_stats["diverging"].sum())

    print(f"\nDiagnostics:")
    print(f"  Max R-hat:      {r_hat_max:.4f}  (want < 1.01)")
    print(f"  Min ESS:        {ess_min:.0f}    (want > 400)")
    print(f"  Divergences:    {div_count}        (want 0)")

    if r_hat_max > 1.01:
        print("  ⚠ R-hat > 1.01 — chains may not have converged. "
              "Consider more tuning steps or reparameterisation.")
    if div_count > 0:
        print(f"  ⚠ {div_count} divergences — consider raising target_accept to 0.95.")

    if save_name:
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        out_path = TRACES_DIR / f"{save_name}.nc"
        trace.to_netcdf(str(out_path))
        print(f"  ✓ Trace saved to {out_path}")

    return trace


def predict_p_alive(
    trace: az.InferenceData,
    data: pd.DataFrame,
    n_samples: int = 1000,
    hierarchical: bool = False,
    segment_col: str = "country_segment",
) -> np.ndarray:
    """
    Compute mean P(alive at T | x, t_x, T) across posterior draws.

    Parameters
    ----------
    trace       : ArviZ InferenceData from a fitted BG/NBD model
    data        : customer-level DataFrame
    n_samples   : number of posterior draws to average over
    hierarchical: if True, uses per-segment posterior parameters
    segment_col : segment column name (only when hierarchical=True)

    Returns
    -------
    np.ndarray of shape (n_customers,) — mean P(alive) in [0, 1]
    """
    posterior = trace.posterior
    x   = data["frequency"].values.astype(float)
    t_x = data["recency"].values.astype(float)
    T   = data["T"].values.astype(float)

    p_alive_samples = np.zeros((n_samples, len(data)))

    if hierarchical:
        segments = data[segment_col].values
        seg_cats = pd.Categorical(segments, categories=posterior.coords["segment"].values)
        seg_idx  = seg_cats.codes
        n_seg    = len(posterior.coords["segment"])

        r_post     = posterior["r"].values.reshape(-1, n_seg)[:n_samples]
        alpha_post = posterior["alpha"].values.reshape(-1, n_seg)[:n_samples]
        a_post     = posterior["a"].values.reshape(-1, n_seg)[:n_samples]
        b_post     = posterior["b"].values.reshape(-1, n_seg)[:n_samples]

        for s in range(n_samples):
            p_alive_samples[s] = _compute_p_alive_vectorized(
                r_post[s][seg_idx], alpha_post[s][seg_idx],
                a_post[s][seg_idx], b_post[s][seg_idx],
                x, t_x, T,
            )
    else:
        r_flat     = posterior["r"].values.flatten()[:n_samples]
        alpha_flat = posterior["alpha"].values.flatten()[:n_samples]
        a_flat     = posterior["a"].values.flatten()[:n_samples]
        b_flat     = posterior["b"].values.flatten()[:n_samples]

        for s in range(n_samples):
            p_alive_samples[s] = compute_p_alive(
                r_flat[s], alpha_flat[s], a_flat[s], b_flat[s], x, t_x, T
            )

    return p_alive_samples.mean(axis=0)


def load_trace(name: str) -> az.InferenceData:
    """
    Load a previously saved ArviZ InferenceData trace from NetCDF.

    Parameters
    ----------
    name : filename stem (without .nc extension), e.g. "bgnbd_standard"

    Returns
    -------
    az.InferenceData
    """
    path = TRACES_DIR / f"{name}.nc"
    if not path.exists():
        raise FileNotFoundError(
            f"Trace '{name}.nc' not found in {TRACES_DIR}.\n"
            "Run fit_model(..., save_name='{name}') first."
        )
    trace = az.from_netcdf(str(path))
    print(f"Loaded trace from {path}")
    return trace


def summarise_trace(
    trace: az.InferenceData,
    var_names: Optional[list] = None,
) -> pd.DataFrame:
    """
    Return a tidy summary DataFrame of posterior statistics.

    Wraps az.summary() and returns mean, sd, hdi_3%, hdi_97%, r_hat, ess_bulk.

    Parameters
    ----------
    trace     : ArviZ InferenceData
    var_names : list of variable names to include (None = all)

    Returns
    -------
    pd.DataFrame — one row per parameter
    """
    summary = az.summary(
        trace,
        var_names  = var_names,
        stat_funcs = {"median": np.median},
        round_to   = 4,
    )
    return summary


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Quick smoke test with synthetic data
    print("Running smoke test with synthetic data...")

    np.random.seed(42)
    n = 200
    fake_customers = pd.DataFrame({
        "frequency"     : np.random.poisson(2, n),
        "recency"       : np.random.uniform(0, 40, n),
        "T"             : np.random.uniform(40, 52, n),
        "monetary_value": np.random.gamma(2, 100, n),
        "country_segment": np.random.choice(["UK", "Germany", "France"], n),
    })
    # Ensure recency <= T
    fake_customers["recency"] = np.minimum(
        fake_customers["recency"], fake_customers["T"]
    )
    # Ensure one-time buyers have monetary_value = 0
    fake_customers.loc[fake_customers["frequency"] == 0, "monetary_value"] = 0.0

    print("Building standard BG/NBD model...")
    model = build_bgnbd(fake_customers)
    print("  ✓ Model built")

    print("Building hierarchical BG/NBD model...")
    h_model = build_hierarchical_bgnbd(fake_customers)
    print("  ✓ Hierarchical model built")

    print("Building Gamma-Gamma model...")
    gg_model = build_gamma_gamma(fake_customers)
    print("  ✓ Gamma-Gamma model built")

    print("\nAll models built successfully. Run fit_model() to sample.")