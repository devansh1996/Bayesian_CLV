"""
src/evaluation.py
=================
Model evaluation metrics and comparison utilities for the CLV thesis.

Functions
---------
Regression metrics:
    mae(), rmse(), mape(), gini_coefficient()

Classification metrics (P(alive) / activity prediction):
    compute_classification_metrics()

Calibration:
    calibration_table()

Model comparison:
    evaluate_model()
    compare_all_models()
    targeting_lift()
    dcg_at_k(), ndcg_at_k()
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from scipy.stats import spearmanr, pearsonr


# ──────────────────────────────────────────────────────────────────────────────
# REGRESSION METRICS
# ──────────────────────────────────────────────────────────────────────────────

def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    eps: float = 1.0,
) -> float:
    """
    Mean Absolute Percentage Error, with a floor on y_true to avoid
    division by zero or instability from near-zero actuals.

    Parameters
    ----------
    eps : minimum value for y_true denominator (default 1.0 transaction)
    """
    denom = np.maximum(np.abs(y_true), eps)
    return float(np.mean(np.abs(y_true - y_pred) / denom) * 100)


def gini_coefficient(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Normalised Gini coefficient — measures how well the model ranks
    customers by their actual value.

    Range: 0 (random ordering) to 1 (perfect ranking).
    Equivalent to 2 × AUC − 1 for the regression ranking problem.

    This is particularly useful for CLV because the business goal is often
    to identify the top-N customers, not to predict exact spend values.
    A model with good Gini can still be used for targeting even if its
    absolute predictions are off.
    """
    # Sort by predicted value descending
    sorted_idx  = np.argsort(y_pred)[::-1]
    y_sorted    = y_true[sorted_idx]

    n           = len(y_true)
    cumulative  = np.cumsum(y_sorted) / (y_true.sum() + 1e-10)
    lorenz      = cumulative / cumulative[-1]

    # Area under Lorenz curve via trapezoidal rule
    auc_lorenz  = np.trapezoid(lorenz, np.linspace(0, 1, n))
    gini        = 2 * auc_lorenz - 1
    return float(np.clip(gini, 0.0, 1.0))


def spearman_rank_correlation(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Spearman rank correlation between predicted and actual values.
    Measures monotonic ranking quality, robust to outliers.
    """
    rho, _ = spearmanr(y_true, y_pred)
    return float(rho)


def pearson_correlation(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Pearson correlation between predicted and actual values."""
    r, _ = pearsonr(y_true, y_pred)
    return float(r)


# ──────────────────────────────────────────────────────────────────────────────
# CLASSIFICATION METRICS  (activity prediction)
# ──────────────────────────────────────────────────────────────────────────────

def compute_classification_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
) -> Dict[str, float]:
    """
    Compute binary classification metrics for activity prediction.

    Used to evaluate P(alive) estimates from the BG/NBD model:
        y_true  : 1 if customer made at least one holdout purchase, else 0
        y_score : P(alive) estimate from the model

    Returns
    -------
    dict with keys: accuracy, precision, recall, f1, auc_roc, auc_pr
    """
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, average_precision_score,
    )

    y_pred = (y_score >= threshold).astype(int)

    # Guard against degenerate case where all predictions are one class
    try:
        auc_roc = float(roc_auc_score(y_true, y_score))
    except ValueError:
        auc_roc = float("nan")

    try:
        auc_pr = float(average_precision_score(y_true, y_score))
    except ValueError:
        auc_pr = float("nan")

    return {
        "accuracy" : float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall"   : float(recall_score(y_true, y_pred, zero_division=0)),
        "f1"       : float(f1_score(y_true, y_pred, zero_division=0)),
        "auc_roc"  : auc_roc,
        "auc_pr"   : auc_pr,
    }


# ──────────────────────────────────────────────────────────────────────────────
# CALIBRATION
# ──────────────────────────────────────────────────────────────────────────────

def calibration_table(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """
    Bin customers by predicted transactions and compute mean predicted vs
    mean actual per bin (decile calibration table).

    This is the standard diagnostic for BG/NBD model fit. A well-calibrated
    model has predicted ≈ actual across all bins. If the model systematically
    over-predicts in the top decile, it is overestimating activity for the
    highest-frequency customers.

    Parameters
    ----------
    y_true : actual holdout transaction counts
    y_pred : predicted transaction counts
    n_bins : number of equal-frequency bins (default 10 = deciles)

    Returns
    -------
    pd.DataFrame with columns:
        bin, n_customers, mean_predicted, mean_actual, abs_error, pct_error
    """
    df = pd.DataFrame({"pred": y_pred, "actual": y_true})

    try:
        df["bin"] = pd.qcut(df["pred"], q=n_bins, labels=False, duplicates="drop") + 1
    except ValueError:
        # Fallback: equal-width bins if too many duplicate values
        df["bin"] = pd.cut(df["pred"], bins=n_bins, labels=False) + 1

    result = (
        df.groupby("bin", observed=True)
        .agg(
            n_customers    = ("pred",   "count"),
            mean_predicted = ("pred",   "mean"),
            mean_actual    = ("actual", "mean"),
        )
        .reset_index()
    )

    result["abs_error"] = np.abs(result["mean_predicted"] - result["mean_actual"])
    result["pct_error"] = (
        result["abs_error"] /
        result["mean_actual"].clip(lower=1e-6) * 100
    ).round(1)

    return result


# ──────────────────────────────────────────────────────────────────────────────
# TARGETING LIFT
# ──────────────────────────────────────────────────────────────────────────────

def targeting_lift(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    top_k_fracs: List[float] = [0.05, 0.10, 0.20, 0.30, 0.50],
) -> pd.DataFrame:
    """
    Compute targeting lift at various cutoff thresholds.

    Lift answers: "If I target the top K% of customers by predicted CLV,
    what fraction of total actual revenue do I capture?"

    This is the most business-relevant metric — it measures whether the
    model's ranking is useful for campaign targeting decisions.

    Lift at K% = (actual revenue in top K% / total actual revenue) / K%

    A lift of 2.0 at 20% means: targeting the model's top-20% customers
    captures twice the revenue you'd expect from a random 20% selection.

    Parameters
    ----------
    y_true      : actual holdout spend per customer
    y_pred      : predicted spend (or CLV) per customer
    top_k_fracs : list of fractions to evaluate (default: 5%, 10%, 20%, 30%, 50%)

    Returns
    -------
    pd.DataFrame with columns: top_k_pct, n_customers, captured_revenue_pct, lift
    """
    n = len(y_true)
    total_revenue = y_true.sum()

    # Sort by predicted value — best predictions first
    sorted_idx = np.argsort(y_pred)[::-1]
    y_sorted   = y_true[sorted_idx]
    cumrev     = np.cumsum(y_sorted)

    rows = []
    for frac in top_k_fracs:
        k         = max(1, int(np.ceil(n * frac)))
        cap_rev   = cumrev[k - 1]
        cap_frac  = cap_rev / (total_revenue + 1e-10)
        lift      = cap_frac / frac

        rows.append({
            "top_k_pct"            : round(frac * 100, 1),
            "n_customers"          : k,
            "captured_revenue_pct" : round(cap_frac * 100, 2),
            "lift"                 : round(lift, 3),
        })

    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# NDCG  (ranking quality)
# ──────────────────────────────────────────────────────────────────────────────

def dcg_at_k(relevance: np.ndarray, k: int) -> float:
    """
    Discounted Cumulative Gain at rank k.
    relevance should be non-negative (e.g. actual CLV values).
    """
    r = relevance[:k]
    ranks = np.arange(1, len(r) + 1)
    return float(np.sum(r / np.log2(ranks + 1)))


def ndcg_at_k(y_true: np.ndarray, y_pred: np.ndarray, k: int) -> float:
    """
    Normalised Discounted Cumulative Gain at rank k.

    Measures ranking quality where relevance = actual CLV.
    Range: 0 (worst) to 1 (perfect ranking).

    NDCG is more sensitive than Gini to the ordering within the top-k,
    making it useful for evaluating targeting where only the top few
    hundred customers will be contacted.
    """
    # Predicted ranking
    pred_order = np.argsort(y_pred)[::-1]
    actual_at_pred = y_true[pred_order]

    # Ideal ranking
    ideal_order  = np.argsort(y_true)[::-1]
    ideal_actual = y_true[ideal_order]

    dcg_pred  = dcg_at_k(actual_at_pred, k)
    dcg_ideal = dcg_at_k(ideal_actual, k)

    if dcg_ideal < 1e-10:
        return 0.0
    return float(dcg_pred / dcg_ideal)


# ──────────────────────────────────────────────────────────────────────────────
# BAYESIAN-SPECIFIC METRICS
# ──────────────────────────────────────────────────────────────────────────────

def coverage_probability(
    y_true: np.ndarray,
    y_lower: np.ndarray,
    y_upper: np.ndarray,
) -> float:
    """
    Fraction of actuals falling within the credible interval.

    For a 90% HDI, we expect ~90% coverage if the model is well-calibrated.
    Significantly lower coverage = overconfident model.
    Significantly higher coverage = underconfident (too-wide intervals).
    """
    inside = (y_true >= y_lower) & (y_true <= y_upper)
    return float(inside.mean())


def mean_interval_width(y_lower: np.ndarray, y_upper: np.ndarray) -> float:
    """
    Mean width of credible intervals. Narrower = more precise (good, if also
    well-calibrated). Used alongside coverage_probability to assess uncertainty.
    """
    return float(np.mean(y_upper - y_lower))


def compute_posterior_metrics(
    y_true: np.ndarray,
    posterior_samples: np.ndarray,
    hdi_prob: float = 0.9,
) -> Dict[str, float]:
    """
    Compute metrics specific to Bayesian posterior predictive distributions.

    Parameters
    ----------
    y_true           : actual holdout transaction counts (n_customers,)
    posterior_samples: predicted samples (n_samples, n_customers)
    hdi_prob         : HDI probability mass (default 0.9 = 90% interval)

    Returns
    -------
    dict with: mae, rmse, coverage, mean_interval_width, crps
    """
    y_pred_mean = posterior_samples.mean(axis=0)

    # HDI bounds per customer
    alpha = (1 - hdi_prob) / 2
    y_lower = np.quantile(posterior_samples, alpha,     axis=0)
    y_upper = np.quantile(posterior_samples, 1 - alpha, axis=0)

    # CRPS — Continuous Ranked Probability Score
    # Average of per-customer CRPS; lower is better
    crps_vals = _crps_ensemble(y_true, posterior_samples)

    return {
        "mae"                : mae(y_true, y_pred_mean),
        "rmse"               : rmse(y_true, y_pred_mean),
        f"coverage_{int(hdi_prob*100)}pct": coverage_probability(y_true, y_lower, y_upper),
        "mean_interval_width": mean_interval_width(y_lower, y_upper),
        "crps"               : float(crps_vals.mean()),
        "spearman_rho"       : spearman_rank_correlation(y_true, y_pred_mean),
        "gini"               : gini_coefficient(y_true, y_pred_mean),
    }


def _crps_ensemble(y_true: np.ndarray, ensemble: np.ndarray) -> np.ndarray:
    """
    Compute the CRPS (Continuous Ranked Probability Score) for each customer
    using the ensemble estimator (Gneiting & Raftery 2007):

        CRPS = E|X - y| - 0.5 × E|X - X'|

    where X and X' are independent draws from the forecast distribution.

    Lower CRPS is better. It penalises both inaccuracy and overconfidence.
    """
    n_samples = ensemble.shape[0]

    # E|X - y|  — mean absolute error against the truth
    mean_abs_error = np.mean(np.abs(ensemble - y_true[np.newaxis, :]), axis=0)

    # E|X - X'| — pairwise spread of the ensemble (estimating via random pairs)
    # Full pairwise is O(n^2); we subsample 500 pairs for speed
    rng  = np.random.default_rng(42)
    idx1 = rng.integers(0, n_samples, size=500)
    idx2 = rng.integers(0, n_samples, size=500)
    pairwise_spread = np.mean(np.abs(ensemble[idx1] - ensemble[idx2]), axis=0)

    return mean_abs_error - 0.5 * pairwise_spread


# ──────────────────────────────────────────────────────────────────────────────
# FULL MODEL EVALUATION
# ──────────────────────────────────────────────────────────────────────────────

def evaluate_model(
    model_name: str,
    y_true_tx: np.ndarray,
    y_pred_tx: np.ndarray,
    y_true_spend: Optional[np.ndarray] = None,
    y_pred_spend: Optional[np.ndarray] = None,
    y_true_active: Optional[np.ndarray] = None,
    y_score_alive: Optional[np.ndarray] = None,
    posterior_samples: Optional[np.ndarray] = None,
    n_bins: int = 10,
    top_k_fracs: List[float] = [0.05, 0.10, 0.20, 0.30],
) -> Dict:
    """
    Run a full evaluation suite for one model and return results as a dict.

    Parameters
    ----------
    model_name      : label for this model in output tables
    y_true_tx       : actual holdout transaction counts
    y_pred_tx       : predicted transaction counts (point estimate)
    y_true_spend    : actual holdout total spend (optional)
    y_pred_spend    : predicted total spend / CLV (optional)
    y_true_active   : binary activity ground truth (optional)
    y_score_alive   : P(alive) scores (optional)
    posterior_samples: (n_samples, n_customers) from Bayesian model (optional)
    n_bins          : bins for calibration table
    top_k_fracs     : fractions for targeting lift

    Returns
    -------
    dict with keys: model_name, metrics, calibration, lift, classification
    """
    results = {"model_name": model_name, "metrics": {}, "calibration": None,
               "lift": None, "classification": None}

    # ── Transaction metrics ───────────────────────────────────────────────────
    results["metrics"].update({
        "tx_mae"      : mae(y_true_tx, y_pred_tx),
        "tx_rmse"     : rmse(y_true_tx, y_pred_tx),
        "tx_mape"     : mape(y_true_tx, y_pred_tx),
        "tx_spearman" : spearman_rank_correlation(y_true_tx, y_pred_tx),
        "tx_gini"     : gini_coefficient(y_true_tx, y_pred_tx),
    })

    # ── Posterior metrics (Bayesian only) ─────────────────────────────────────
    if posterior_samples is not None:
        post_metrics = compute_posterior_metrics(y_true_tx, posterior_samples)
        results["metrics"].update({f"post_{k}": v for k, v in post_metrics.items()})

    # ── Spend / CLV metrics ───────────────────────────────────────────────────
    if y_true_spend is not None and y_pred_spend is not None:
        results["metrics"].update({
            "clv_mae"     : mae(y_true_spend, y_pred_spend),
            "clv_rmse"    : rmse(y_true_spend, y_pred_spend),
            "clv_mape"    : mape(y_true_spend, y_pred_spend, eps=10.0),
            "clv_spearman": spearman_rank_correlation(y_true_spend, y_pred_spend),
            "clv_gini"    : gini_coefficient(y_true_spend, y_pred_spend),
            "ndcg_100"    : ndcg_at_k(y_true_spend, y_pred_spend, k=100),
            "ndcg_500"    : ndcg_at_k(y_true_spend, y_pred_spend, k=500),
        })

    # ── Calibration table ─────────────────────────────────────────────────────
    results["calibration"] = calibration_table(y_true_tx, y_pred_tx, n_bins=n_bins)

    # ── Targeting lift ────────────────────────────────────────────────────────
    target_y = y_true_spend if y_true_spend is not None else y_true_tx
    target_p = y_pred_spend if y_pred_spend is not None else y_pred_tx
    results["lift"] = targeting_lift(target_y, target_p, top_k_fracs=top_k_fracs)

    # ── Classification (P(alive)) ─────────────────────────────────────────────
    if y_true_active is not None and y_score_alive is not None:
        results["classification"] = compute_classification_metrics(
            y_true_active, y_score_alive
        )

    return results


# ──────────────────────────────────────────────────────────────────────────────
# MULTI-MODEL COMPARISON
# ──────────────────────────────────────────────────────────────────────────────

def compare_all_models(
    evaluation_results: List[Dict],
    metrics: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Build a comparison table from a list of evaluate_model() results.

    Parameters
    ----------
    evaluation_results : list of dicts returned by evaluate_model()
    metrics            : list of metric keys to include (None = all)

    Returns
    -------
    pd.DataFrame — one row per model, one column per metric, sorted by tx_mae
    """
    rows = []
    for res in evaluation_results:
        row = {"model": res["model_name"]}
        row.update(res["metrics"])
        if res.get("classification"):
            row.update({f"cls_{k}": v for k, v in res["classification"].items()})
        rows.append(row)

    df = pd.DataFrame(rows)

    if metrics:
        keep = ["model"] + [m for m in metrics if m in df.columns]
        df = df[keep]

    # Sort by transaction MAE ascending (lower is better)
    if "tx_mae" in df.columns:
        df = df.sort_values("tx_mae").reset_index(drop=True)

    return df.round(4)


def lift_comparison_table(evaluation_results: List[Dict]) -> pd.DataFrame:
    """
    Combine lift tables from all models into a single wide-format table
    for easy comparison.

    Returns
    -------
    pd.DataFrame with columns: top_k_pct, model_1_lift, model_2_lift, ...
    """
    lift_dfs = []
    for res in evaluation_results:
        if res.get("lift") is not None:
            ldf = res["lift"][["top_k_pct", "lift"]].copy()
            ldf = ldf.rename(columns={"lift": res["model_name"]})
            lift_dfs.append(ldf.set_index("top_k_pct"))

    if not lift_dfs:
        return pd.DataFrame()

    combined = pd.concat(lift_dfs, axis=1).reset_index()
    return combined.round(3)


# ──────────────────────────────────────────────────────────────────────────────
# DECISION-THEORETIC TARGETING  (RQ3 / H3)
# ──────────────────────────────────────────────────────────────────────────────

def targeting_simulation(
    clv_posterior: np.ndarray,
    actual_holdout_value: np.ndarray,
    cost_per_customer: float,
    targeting_depths: List[float] = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50],
) -> pd.DataFrame:
    """
    Decision-theoretic targeting simulation (RQ3 / H3).

    Compares three customer-selection strategies at a range of targeting
    depths, quantifying the *business value* of having a full posterior
    rather than a single point estimate:

        1. Point estimate  — rank customers by posterior MEAN CLV (E[CLV]).
                             This is what a non-Bayesian model would do.
        2. Posterior prob  — rank by P(CLV > cost), the probability that the
                             customer is profitable to target. This uses the
                             full posterior and is risk-aware: a customer with
                             moderate mean but low variance can outrank a
                             high-mean / high-variance one.
        3. Oracle          — rank by the realised holdout value (perfect
                             foresight). Upper bound on achievable value.

    For each depth d, the top ⌈d·N⌉ customers are "targeted", incurring
    `cost_per_customer` each and realising their actual holdout value. The
    reported value is the cumulative NET value (realised − cost) captured.

    Parameters
    ----------
    clv_posterior        : (n_samples, n_customers) CLV posterior draws
    actual_holdout_value : (n_customers,) realised holdout value (spend)
    cost_per_customer    : per-customer intervention cost (same units as value)
    targeting_depths     : fractions of the customer base to target

    Returns
    -------
    pd.DataFrame — one row per depth, comparing strategies and the lift of
    the posterior-probability rule over the point-estimate rule.
    """
    clv_posterior        = np.asarray(clv_posterior, dtype=float)
    actual_holdout_value = np.asarray(actual_holdout_value, dtype=float)

    n_customers = len(actual_holdout_value)
    clv_mean     = clv_posterior.mean(axis=0)
    p_above_cost = (clv_posterior > cost_per_customer).mean(axis=0)

    # Net value of targeting a customer = realised value − intervention cost
    net_value = actual_holdout_value - cost_per_customer

    # Rankings are fixed across depths; sort once (descending)
    order_point  = np.argsort(clv_mean)[::-1]
    order_prob   = np.argsort(p_above_cost)[::-1]
    order_oracle = np.argsort(actual_holdout_value)[::-1]

    rows = []
    for depth in targeting_depths:
        k = max(1, int(np.ceil(depth * n_customers)))

        value_point  = net_value[order_point[:k]].sum()
        value_prob   = net_value[order_prob[:k]].sum()
        value_oracle = net_value[order_oracle[:k]].sum()
        # Random selection in expectation captures the population mean net value
        value_random = k * net_value.mean()

        rows.append({
            "targeting_depth"     : round(depth, 4),
            "n_targeted"          : k,
            "point_estimate_value": float(value_point),
            "posterior_prob_value": float(value_prob),
            "oracle_value"        : float(value_oracle),
            "random_value"        : float(value_random),
            "improvement"         : float(value_prob - value_point),
            "improvement_pct"     : float(
                (value_prob - value_point) / (abs(value_point) + 1e-6) * 100
            ),
        })

    return pd.DataFrame(rows)


def targeting_simulation_sweep(
    clv_posterior: np.ndarray,
    actual_holdout_value: np.ndarray,
    cost_grid: List[float],
    targeting_depths: List[float] = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50],
) -> pd.DataFrame:
    """
    Run targeting_simulation() across several intervention-cost assumptions.

    The advantage of the posterior-probability rule over the point estimate is
    sensitive to `cost_per_customer` (it only differs from E[CLV] ranking when
    the cost threshold cuts through the bulk of the posteriors). Sweeping a grid
    of costs makes the RQ3 conclusion robust rather than dependent on one number.

    Returns
    -------
    pd.DataFrame — long format with an added `cost_per_customer` column.
    """
    frames = []
    for cost in cost_grid:
        df = targeting_simulation(
            clv_posterior, actual_holdout_value,
            cost_per_customer=cost, targeting_depths=targeting_depths,
        )
        df.insert(0, "cost_per_customer", cost)
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


# ──────────────────────────────────────────────────────────────────────────────
# COUNTRY-LEVEL EVALUATION  (RQ2 / H2)
# ──────────────────────────────────────────────────────────────────────────────

def country_level_metrics(
    actual: np.ndarray,
    predictions: Dict[str, np.ndarray],
    countries: np.ndarray,
    min_customers: int = 1,
) -> pd.DataFrame:
    """
    Per-country prediction error for each model (RQ2 / H2).

    Tests whether the hierarchical BG/NBD's partial pooling actually improves
    accuracy in country segments — especially the smaller ones, where the
    pooled model has little data and shrinkage toward the global mean should
    help most.

    Parameters
    ----------
    actual        : (n_customers,) ground-truth value (transactions or CLV)
    predictions   : dict of {model_name: (n_customers,) point predictions}
    countries     : (n_customers,) country/segment label per customer
    min_customers : drop segments with fewer than this many customers

    Returns
    -------
    pd.DataFrame — one row per country (sorted by size, descending) with
    columns: country, n_customers, MAE_<model> for each model.
    """
    actual    = np.asarray(actual, dtype=float)
    countries = np.asarray(countries)

    rows = []
    for country in pd.unique(countries):
        mask = countries == country
        n = int(mask.sum())
        if n < min_customers:
            continue
        row = {"country": country, "n_customers": n}
        for name, preds in predictions.items():
            preds = np.asarray(preds, dtype=float)
            row[f"MAE_{name}"] = mae(actual[mask], preds[mask])
        rows.append(row)

    return (
        pd.DataFrame(rows)
        .sort_values("n_customers", ascending=False)
        .reset_index(drop=True)
    )


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running evaluation smoke test...")
    np.random.seed(42)
    n = 500

    y_true_tx    = np.random.poisson(2, n).astype(float)
    y_pred_tx    = y_true_tx + np.random.normal(0, 0.8, n)
    y_true_spend = np.random.gamma(2, 150, n)
    y_pred_spend = y_true_spend * np.random.uniform(0.7, 1.3, n)
    y_true_active= (y_true_tx > 0).astype(int)
    y_score_alive= np.clip(y_true_active + np.random.normal(0, 0.3, n), 0, 1)
    posterior    = np.random.poisson(2, (500, n)).astype(float)

    res = evaluate_model(
        model_name        = "BG/NBD (Bayesian)",
        y_true_tx         = y_true_tx,
        y_pred_tx         = y_pred_tx,
        y_true_spend      = y_true_spend,
        y_pred_spend      = y_pred_spend,
        y_true_active     = y_true_active,
        y_score_alive     = y_score_alive,
        posterior_samples = posterior,
    )

    print("\nMetrics:")
    for k, v in res["metrics"].items():
        print(f"  {k:<30} {v:.4f}")

    print("\nCalibration table:")
    print(res["calibration"].to_string(index=False))

    print("\nLift table:")
    print(res["lift"].to_string(index=False))

    print("\nClassification:")
    for k, v in res["classification"].items():
        print(f"  {k:<15} {v:.4f}")

    # Multi-model comparison
    res2 = evaluate_model(
        model_name   = "RFM Heuristic",
        y_true_tx    = y_true_tx,
        y_pred_tx    = y_true_tx * np.random.uniform(0.5, 1.5, n),
        y_true_spend = y_true_spend,
        y_pred_spend = y_true_spend * np.random.uniform(0.4, 1.6, n),
    )

    comparison = compare_all_models([res, res2])
    print("\nComparison table:")
    print(comparison[["model","tx_mae","tx_rmse","tx_gini","clv_mae","clv_gini"]].to_string(index=False))

    # ── Targeting simulation (RQ3 / H3) ───────────────────────────────────────
    clv_posterior = np.random.gamma(2, 150, (500, n))
    actual_value  = y_true_spend
    sim = targeting_simulation(clv_posterior, actual_value, cost_per_customer=50.0)
    print("\nTargeting simulation (cost=£50):")
    print(sim.to_string(index=False))

    # ── Country-level metrics (RQ2 / H2) ──────────────────────────────────────
    countries = np.random.choice(["UK", "Germany", "France", "Other"], n)
    cm = country_level_metrics(
        actual=y_true_spend,
        predictions={"BG/NBD": y_pred_spend, "RFM": y_true_spend * np.random.uniform(0.4, 1.6, n)},
        countries=countries,
    )
    print("\nCountry-level MAE:")
    print(cm.to_string(index=False))

    print("\n✓ Evaluation smoke test passed")