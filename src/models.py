"""
src/models.py
=============
Bayesian CLV models.

The standard (pooled) BG/NBD and the Gamma-Gamma monetary model use the
validated **pymc-marketing** implementations. Their log-likelihoods use the
numerically-stable Fader-Hardie form (BG/NBD expression 4, no ``-inf`` terms),
which samples efficiently — the earlier hand-rolled ``logaddexp(alive, -inf)``
form was severely ill-conditioned and would not sample in practical time.

The **hierarchical BG/NBD** (the H2 contribution) has no pymc-marketing
equivalent, so it is a custom PyMC model. It reuses the same stable BG/NBD
likelihood with per-country-segment parameters under a non-centred, log-normal
partial-pooling prior. A tight between-segment scale (``sigma ~ HalfNormal(0.25)``)
controls the funnel geometry induced by the small country segments.

Public API
----------
Fitting (each returns a fitted object; pass to the matching predict fn):
    fit_bgnbd(customers, ...)            -> BetaGeoModel
    fit_gamma_gamma(customers, ...)      -> GammaGammaModel
    fit_hierarchical_bgnbd(customers, .) -> arviz.InferenceData

Prediction (full posteriors, shape (n_samples, n_customers)):
    predict_transactions(bg_model, customers, t_future)
    predict_p_alive(bg_model, customers)                  -> (n_customers,)
    predict_spend(gg_model, customers)                    -> (samples, repeat_mask)
    predict_transactions_hier(idata, customers, t_future)
    predict_p_alive_hier(idata, customers)                -> (n_customers,)
    compute_clv_posterior(tx, spend, repeat_mask, margin)

I/O & summaries:
    save_model / load_bgnbd / load_gamma_gamma / load_hier_trace
    get_idata(fitted)  -> arviz.InferenceData  (for plotting/diagnostics)
    summarise_trace(idata, var_names=None)

References
----------
    Fader, Hardie, Lee (2005) — BG/NBD ("Counting Your Customers the Easy Way")
    Fader & Hardie (2013)     — The Gamma-Gamma Model of Monetary Value
"""

import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
import arviz as az
from scipy.special import hyp2f1, expit
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union

from pymc_marketing.clv import BetaGeoModel, GammaGammaModel
from pymc_marketing.prior import Prior

TRACES_DIR = Path("outputs/traces")


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _bgnbd_df(customers: pd.DataFrame) -> pd.DataFrame:
    """Frame in the shape pymc-marketing's BetaGeoModel expects."""
    return pd.DataFrame({
        "customer_id": np.asarray(customers["customer_id"]),
        "frequency":   customers["frequency"].to_numpy(dtype=float),
        "recency":     customers["recency"].to_numpy(dtype=float),
        "T":           customers["T"].to_numpy(dtype=float),
    })


def _gg_df(repeat: pd.DataFrame) -> pd.DataFrame:
    """Frame for GammaGammaModel (repeat purchasers only)."""
    return pd.DataFrame({
        "customer_id":    np.asarray(repeat["customer_id"]),
        "frequency":      repeat["frequency"].to_numpy(dtype=float),
        "monetary_value": repeat["monetary_value"].to_numpy(dtype=float),
    })


def _halfnormal_config(
    priors: Optional[Dict[str, float]], names: list
) -> Optional[Dict[str, Prior]]:
    """Turn a {name_sigma: value} dict into a pymc-marketing model_config.

    Returns None (⇒ library defaults, HalfFlat) when no priors are given.
    """
    if not priors:
        return None
    cfg = {}
    for n in names:
        key = f"{n}_sigma"
        if key in priors:
            cfg[f"{n}_prior"] = Prior("HalfNormal", sigma=float(priors[key]))
    return cfg or None


def _stack_samples(da, n_samples: Optional[int] = None,
                   seed: int = 42) -> np.ndarray:
    """xarray (chain, draw, <customer>) → np.ndarray (n_draws, n_customers).

    Optionally subsample to `n_samples` posterior draws (random, reproducible).
    """
    cust_dims = [d for d in da.dims if d not in ("chain", "draw")]
    arr = da.transpose("chain", "draw", *cust_dims).values
    arr = arr.reshape(arr.shape[0] * arr.shape[1], -1)   # (n_draws, n_cust)
    if n_samples is not None and n_samples < arr.shape[0]:
        rng = np.random.default_rng(seed)
        idx = rng.choice(arr.shape[0], size=n_samples, replace=False)
        arr = arr[idx]
    return arr


def _report(idata: az.InferenceData, name: str) -> None:
    try:
        rhat = float(az.rhat(idata).to_array().max())
        ess  = float(az.ess(idata).to_array().min())
        div  = int(idata.sample_stats["diverging"].sum()) if "sample_stats" in idata else -1
        print(f"  {name} diagnostics: max R-hat={rhat:.4f}  min ESS={ess:.0f}  divergences={div}")
        if rhat > 1.01:
            print("    ⚠ R-hat > 1.01 — chains may not have converged.")
        if div and div > 0:
            print(f"    ⚠ {div} divergences.")
    except Exception as e:
        print(f"  {name}: diagnostics failed — {e}")


def get_idata(fitted: Union[BetaGeoModel, GammaGammaModel, az.InferenceData]) -> az.InferenceData:
    """Return the InferenceData for plotting/diagnostics from any fitted object."""
    if isinstance(fitted, az.InferenceData):
        return fitted
    return fitted.idata


# ──────────────────────────────────────────────────────────────────────────────
# 1. STANDARD BG/NBD  (pymc-marketing)
# ──────────────────────────────────────────────────────────────────────────────

def fit_bgnbd(
    customers: pd.DataFrame,
    priors: Optional[Dict[str, float]] = None,
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.9,
    random_seed: int = 42,
    progressbar: bool = True,
    save_name: Optional[str] = None,
) -> BetaGeoModel:
    """Fit the pooled BG/NBD via pymc-marketing's BetaGeoModel.

    priors : optional {r_sigma, alpha_sigma, a_sigma, b_sigma} to use
             HalfNormal priors instead of the library default (HalfFlat).
    """
    model = BetaGeoModel(
        data=_bgnbd_df(customers),
        model_config=_halfnormal_config(priors, ["r", "alpha", "a", "b"]),
    )
    model.build_model()
    print(f"\nSampling BG/NBD (pooled): {chains} chains × {draws} draws (tune={tune})")
    model.fit(draws=draws, tune=tune, chains=chains, target_accept=target_accept,
              random_seed=random_seed, progressbar=progressbar)
    _report(model.idata, "BG/NBD")
    if save_name:
        save_model(model, save_name)
    return model


def predict_transactions(
    bg_model: BetaGeoModel,
    customers: pd.DataFrame,
    t_future: float,
    n_samples: Optional[int] = None,
) -> np.ndarray:
    """Posterior of expected repeat transactions over the next `t_future` weeks.

    Returns (n_samples, n_customers). Uses the exact BG/NBD conditional
    expectation (pymc-marketing `expected_purchases`).
    """
    da = bg_model.expected_purchases(data=_bgnbd_df(customers), future_t=float(t_future))
    return _stack_samples(da, n_samples)


def predict_p_alive(
    bg_model: BetaGeoModel,
    customers: pd.DataFrame,
    n_samples: Optional[int] = None,
) -> np.ndarray:
    """Posterior-mean P(alive at T) per customer. Returns (n_customers,)."""
    da = bg_model.expected_probability_alive(data=_bgnbd_df(customers))
    return _stack_samples(da, n_samples).mean(axis=0)


# ──────────────────────────────────────────────────────────────────────────────
# 2. GAMMA-GAMMA  (pymc-marketing)
# ──────────────────────────────────────────────────────────────────────────────

def fit_gamma_gamma(
    customers: pd.DataFrame,
    priors: Optional[Dict[str, float]] = None,
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.9,
    random_seed: int = 42,
    progressbar: bool = True,
    save_name: Optional[str] = None,
) -> GammaGammaModel:
    """Fit the Gamma-Gamma monetary model on repeat purchasers (frequency > 0)."""
    repeat = customers[customers["frequency"] > 0]
    if len(repeat) == 0:
        raise ValueError("No repeat purchasers found. Check your data.")
    print(f"  Gamma-Gamma on {len(repeat):,} repeat purchasers "
          f"(mean spend £{repeat['monetary_value'].mean():.2f})")
    model = GammaGammaModel(
        data=_gg_df(repeat),
        model_config=_halfnormal_config(priors, ["p", "q", "v"]),
    )
    model.build_model()
    print(f"\nSampling Gamma-Gamma: {chains} chains × {draws} draws (tune={tune})")
    model.fit(draws=draws, tune=tune, chains=chains, target_accept=target_accept,
              random_seed=random_seed, progressbar=progressbar)
    _report(model.idata, "Gamma-Gamma")
    if save_name:
        save_model(model, save_name)
    return model


def predict_spend(
    gg_model: GammaGammaModel,
    customers: pd.DataFrame,
    n_samples: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Posterior of expected mean spend per repeat customer.

    Returns (predictions, repeat_mask) where predictions is
    (n_samples, n_repeat_customers) and repeat_mask marks the rows of
    `customers` (frequency > 0) it corresponds to.
    """
    repeat_mask = customers["frequency"].to_numpy() > 0
    repeat = customers[repeat_mask]
    da = gg_model.expected_customer_spend(data=_gg_df(repeat))
    return _stack_samples(da, n_samples), repeat_mask


# ──────────────────────────────────────────────────────────────────────────────
# 3. HIERARCHICAL BG/NBD  (custom, per country segment)
# ──────────────────────────────────────────────────────────────────────────────

def _stable_bgnbd_logp(x, t_x, T, a, b, r, alpha):
    """Fader-Hardie BG/NBD log-likelihood, expression (4) — numerically stable.

    Same formulation pymc-marketing uses; no ``-inf`` terms (which wreck HMC
    trajectory energy). `a, b, r, alpha` may be per-customer (indexed) arrays.
    """
    x_nonzero = x > 0
    d1 = (pt.gammaln(r + x) - pt.gammaln(r) + pt.gammaln(a + b)
          + pt.gammaln(b + x) - pt.gammaln(b) - pt.gammaln(a + b + x))
    d2 = r * pt.log(alpha) - (r + x) * pt.log(alpha + t_x)
    c3 = ((alpha + t_x) / (alpha + T)) ** (r + x)
    c4 = a / (b + x - 1)
    return d1 + d2 + pt.log(c3 + pt.switch(x_nonzero, c4, 0))


def _hier_log_centers(customers: pd.DataFrame) -> Dict[str, float]:
    """Data-driven log-scale centres for the hierarchical location hyperpriors."""
    rate = (customers["frequency"] / customers["T"].clip(lower=1e-6))
    mean_rate = float(rate.mean())
    p_drop = float((customers["frequency"] == 0).mean())
    a_c = 1.5
    b_c = a_c * (1.0 - p_drop) / max(p_drop, 1e-6)
    return {
        "r":     np.log(1.0),
        "alpha": np.log(1.0 / max(mean_rate, 1e-6)),
        "a":     np.log(a_c),
        "b":     np.log(b_c),
    }


def build_hierarchical_bgnbd(
    customers: pd.DataFrame,
    segment_col: str = "country_segment",
    sigma_scale: float = 0.25,
) -> Tuple[pm.Model, np.ndarray, list]:
    """Custom hierarchical BG/NBD: per-segment (r, α, a, b) with non-centred,
    log-normal partial pooling and a tight between-segment scale.

        θ_s = exp(μ_θ + σ_θ · z_θ,s),   z ~ Normal(0, 1),  σ_θ ~ HalfNormal(0.25)

    Returns (model, seg_idx, segments).
    """
    seg = pd.Categorical(customers[segment_col])
    seg_idx = seg.codes.astype("int64")
    segments = list(seg.categories)

    x   = customers["frequency"].to_numpy(dtype=float)
    t_x = customers["recency"].to_numpy(dtype=float)
    T   = customers["T"].to_numpy(dtype=float)
    lc  = _hier_log_centers(customers)

    with pm.Model(coords={"segment": segments}) as model:
        def hier(name: str) -> pt.TensorVariable:
            mu = pm.Normal(f"mu_{name}", lc[name], 1.0)
            sd = pm.HalfNormal(f"sigma_{name}", sigma_scale)
            z  = pm.Normal(f"z_{name}", 0.0, 1.0, dims="segment")
            return pm.Deterministic(name, pm.math.exp(mu + sd * z), dims="segment")

        r     = hier("r")
        alpha = hier("alpha")
        a     = hier("a")
        b     = hier("b")

        logp = _stable_bgnbd_logp(
            x, t_x, T,
            a[seg_idx], b[seg_idx], r[seg_idx], alpha[seg_idx],
        )
        pm.Potential("likelihood", logp.sum())

    return model, seg_idx, segments


def fit_hierarchical_bgnbd(
    customers: pd.DataFrame,
    segment_col: str = "country_segment",
    draws: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    target_accept: float = 0.95,
    random_seed: int = 42,
    progressbar: bool = True,
    save_name: Optional[str] = None,
) -> az.InferenceData:
    """Sample the custom hierarchical BG/NBD. Returns InferenceData with
    per-segment ``r, alpha, a, b`` (dims 'segment')."""
    model, _, segments = build_hierarchical_bgnbd(customers, segment_col=segment_col)
    print(f"\nSampling hierarchical BG/NBD ({len(segments)} segments): "
          f"{chains} chains × {draws} draws (tune={tune}, target_accept={target_accept})")
    with model:
        idata = pm.sample(
            draws=draws, tune=tune, chains=chains, target_accept=target_accept,
            random_seed=random_seed, progressbar=progressbar,
            compute_convergence_checks=False,
        )
    _report(idata, "Hierarchical BG/NBD")
    if save_name:
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        idata.to_netcdf(str(TRACES_DIR / f"{save_name}.nc"))
        print(f"  ✓ Trace saved to {TRACES_DIR / f'{save_name}.nc'}")
    return idata


# ── Hierarchical prediction (numpy replicas of the pymc-marketing formulas) ────

def _segment_param_draws(idata: az.InferenceData, name: str,
                         seg_idx: np.ndarray, n_samples: Optional[int],
                         seed: int = 42) -> np.ndarray:
    """Return (n_draws, n_customers) posterior draws of a per-segment parameter,
    broadcast to customers via seg_idx."""
    da = idata.posterior[name]                              # (chain, draw, segment)
    arr = da.transpose("chain", "draw", "segment").values
    arr = arr.reshape(arr.shape[0] * arr.shape[1], arr.shape[2])   # (n_draws, n_seg)
    if n_samples is not None and n_samples < arr.shape[0]:
        rng = np.random.default_rng(seed)
        arr = arr[rng.choice(arr.shape[0], size=n_samples, replace=False)]
    return arr[:, seg_idx]                                  # (n_draws, n_cust)


def predict_transactions_hier(
    idata: az.InferenceData,
    customers: pd.DataFrame,
    t_future: float,
    segment_col: str = "country_segment",
    n_samples: Optional[int] = None,
) -> np.ndarray:
    """Posterior of expected transactions for the hierarchical model.

    Replicates pymc-marketing's exact BG/NBD `expected_purchases` per draw,
    with per-segment parameters. Returns (n_samples, n_customers).
    """
    seg = pd.Categorical(customers[segment_col],
                         categories=list(idata.posterior.coords["segment"].values))
    seg_idx = seg.codes.astype("int64")

    x   = customers["frequency"].to_numpy(dtype=float)
    t_x = customers["recency"].to_numpy(dtype=float)
    T   = customers["T"].to_numpy(dtype=float)
    t   = float(t_future)

    r     = _segment_param_draws(idata, "r",     seg_idx, n_samples)
    alpha = _segment_param_draws(idata, "alpha", seg_idx, n_samples)
    a     = _segment_param_draws(idata, "a",     seg_idx, n_samples)
    b     = _segment_param_draws(idata, "b",     seg_idx, n_samples)

    num = 1.0 - ((alpha + T) / (alpha + T + t)) ** (r + x) * hyp2f1(
        r + x, b + x, a + b + x - 1.0, t / (alpha + T + t)
    )
    num = num * (a + b + x - 1.0) / np.where(np.abs(a - 1.0) < 1e-6, 1e-6, a - 1.0)
    denom = 1.0 + (x > 0) * (a / np.maximum(b + x - 1.0, 1e-10)) * (
        (alpha + T) / (alpha + t_x)
    ) ** (r + x)
    return np.clip(num / denom, 0.0, None)


def predict_p_alive_hier(
    idata: az.InferenceData,
    customers: pd.DataFrame,
    segment_col: str = "country_segment",
    n_samples: Optional[int] = None,
) -> np.ndarray:
    """Posterior-mean P(alive) for the hierarchical model. Returns (n_customers,)."""
    seg = pd.Categorical(customers[segment_col],
                         categories=list(idata.posterior.coords["segment"].values))
    seg_idx = seg.codes.astype("int64")

    x   = customers["frequency"].to_numpy(dtype=float)
    t_x = customers["recency"].to_numpy(dtype=float)
    T   = customers["T"].to_numpy(dtype=float)

    r     = _segment_param_draws(idata, "r",     seg_idx, n_samples)
    alpha = _segment_param_draws(idata, "alpha", seg_idx, n_samples)
    a     = _segment_param_draws(idata, "a",     seg_idx, n_samples)
    b     = _segment_param_draws(idata, "b",     seg_idx, n_samples)

    log_div = (r + x) * np.log((alpha + T) / (alpha + t_x)) + np.log(
        a / (b + np.maximum(x, 1) - 1.0)
    )
    p_alive = np.where(x == 0, 1.0, expit(-log_div))
    return p_alive.mean(axis=0)


# ──────────────────────────────────────────────────────────────────────────────
# 4. CLV POSTERIOR
# ──────────────────────────────────────────────────────────────────────────────

def posterior_predictive_counts(
    expected_tx_posterior: np.ndarray, seed: int = 42
) -> np.ndarray:
    """Posterior *predictive* of the holdout transaction count.

    `expected_tx_posterior` is the posterior of the conditional *expected*
    transactions E[X] (one row per draw). It captures parameter uncertainty but
    not the count sampling variability, so credible intervals built from it are
    far too narrow to cover integer outcomes. Here we add that variability by
    drawing an actual count per (draw, customer) from Poisson(E[X | draw]) — a
    standard conditional-mean posterior-predictive approximation for BG/NBD.

    Returns an array the same shape as the input (float counts).
    """
    rng = np.random.default_rng(seed)
    return rng.poisson(np.clip(expected_tx_posterior, 0.0, None)).astype(float)


def compute_clv_posterior(
    tx_predictions: np.ndarray,
    monetary_predictions: np.ndarray,
    repeat_mask: np.ndarray,
    margin: float = 1.0,
) -> np.ndarray:
    """Combine transaction and spend posteriors into a CLV posterior.

        CLV = E[transactions] × E[avg spend] × margin

    One-time buyers (frequency = 0) have no Gamma-Gamma spend estimate, so the
    population-mean predicted spend is imputed for them.

    tx_predictions       : (n_samples, n_all_customers)
    monetary_predictions : (n_samples, n_repeat_customers)
    repeat_mask          : (n_all_customers,) boolean, True for repeat customers
    """
    n_samples, n_customers = tx_predictions.shape

    # Align sample counts (the two models are fit independently).
    if monetary_predictions.shape[0] != n_samples:
        m = min(n_samples, monetary_predictions.shape[0])
        tx_predictions = tx_predictions[:m]
        monetary_predictions = monetary_predictions[:m]
        n_samples = m

    full_monetary = np.empty((n_samples, n_customers))
    full_monetary[:, repeat_mask] = monetary_predictions
    full_monetary[:, ~repeat_mask] = monetary_predictions.mean()   # impute pop mean

    return tx_predictions * full_monetary * margin


# ──────────────────────────────────────────────────────────────────────────────
# 5. I/O & SUMMARIES
# ──────────────────────────────────────────────────────────────────────────────

def save_model(model: Union[BetaGeoModel, GammaGammaModel], save_name: str) -> None:
    """Persist a fitted pymc-marketing model to outputs/traces/<name>.nc."""
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    path = TRACES_DIR / f"{save_name}.nc"
    model.save(str(path))
    print(f"  ✓ Model saved to {path}")


def load_bgnbd(save_name: str) -> BetaGeoModel:
    return BetaGeoModel.load(str(TRACES_DIR / f"{save_name}.nc"))


def load_gamma_gamma(save_name: str) -> GammaGammaModel:
    return GammaGammaModel.load(str(TRACES_DIR / f"{save_name}.nc"))


def load_hier_trace(save_name: str) -> az.InferenceData:
    path = TRACES_DIR / f"{save_name}.nc"
    if not path.exists():
        raise FileNotFoundError(f"Trace '{save_name}.nc' not found in {TRACES_DIR}.")
    return az.from_netcdf(str(path))


def summarise_trace(
    fitted: Union[BetaGeoModel, GammaGammaModel, az.InferenceData],
    var_names: Optional[list] = None,
) -> pd.DataFrame:
    """Tidy posterior summary (mean, sd, hdi, r_hat, ess) for any fitted object."""
    idata = get_idata(fitted)
    return az.summary(idata, var_names=var_names, round_to=4)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Smoke test on processed data (fast configs)...")
    from src.data import load_processed
    _, _, customers, _ = load_processed()

    bg = fit_bgnbd(customers, draws=300, tune=300, chains=2, progressbar=False)
    tx = predict_transactions(bg, customers, t_future=13.0, n_samples=200)
    pa = predict_p_alive(bg, customers, n_samples=200)
    print(f"  tx posterior {tx.shape}, mean {tx.mean():.3f} | P(alive) mean {pa.mean():.3f}")

    gg = fit_gamma_gamma(customers, draws=300, tune=300, chains=2, progressbar=False)
    spend, mask = predict_spend(gg, customers, n_samples=200)
    print(f"  spend posterior {spend.shape}, mean £{spend.mean():.2f}, repeat {mask.sum()}")

    clv = compute_clv_posterior(tx, spend, mask)
    print(f"  CLV posterior {clv.shape}, mean £{clv.mean():.2f}")
    print("✓ models.py smoke test passed")
