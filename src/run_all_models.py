#!/usr/bin/env python3
"""
src/run_all_models.py
=====================
Master execution pipeline for the CLV thesis.

Runs in 7 sequential steps:
    1. Data preparation  (loads or rebuilds processed parquet files)
    2. Bayesian models   (BG/NBD standard + hierarchical, Gamma-Gamma)
    3. Bayesian predictions (transactions, P(alive), monetary, CLV posterior)
    4. Classical baselines  (Naive mean, RFM heuristic, XGBoost two-stage)
    5. Evaluation        (MAE/RMSE/Gini/NDCG, coverage, CRPS, lift, classification)
    6. Save results      (CSV + LaTeX tables → outputs/results/)
    6b. Decision analysis(RQ3 targeting simulation + RQ2 country-level MAE)
    7. Thesis plots      (PNG figures → outputs/figures/)

Usage
-----
    # Full run (fits new MCMC traces, ~30–60 min depending on hardware)
    python src/run_all_models.py

    # Load previously saved traces, skip MCMC
    python src/run_all_models.py --skip-sampling

    # Force re-run data pipeline even if processed files exist
    python src/run_all_models.py --force-data

    # Use fewer posterior samples for prediction (faster, less accurate)
    python src/run_all_models.py --n-samples 500

Output directories
------------------
    outputs/traces/   — ArviZ InferenceData .nc files (MCMC traces)
    outputs/results/  — .csv and .tex result tables
    outputs/figures/  — .png thesis-quality plots
"""

import sys
import os
import argparse
import warnings

# Allow running as `python src/run_all_models.py` from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")   # headless — no display required
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pymc")

# ── Project modules ───────────────────────────────────────────────────────────
from src.data import (
    run_pipeline,
    load_processed,
    build_inner_training_set,
    CAL_END,
    XGB_INNER_CAL_END,
)
from src.models import (
    fit_bgnbd,
    fit_gamma_gamma,
    fit_hierarchical_bgnbd,
    load_bgnbd,
    load_gamma_gamma,
    load_hier_trace,
    get_idata,
    predict_transactions,
    predict_p_alive,
    predict_spend,
    predict_transactions_hier,
    predict_p_alive_hier,
    compute_clv_posterior,
    summarise_trace,
)
from src.priors import data_informed_priors
from src.baselines import fit_all_baselines
from src.evaluation import (
    evaluate_model,
    compare_all_models,
    lift_comparison_table,
    targeting_simulation,
    targeting_simulation_sweep,
    country_level_metrics,
)
import src.plots as P

# ── Output directories ────────────────────────────────────────────────────────
RESULTS_DIR = Path("outputs/results")
FIGURES_DIR = Path("outputs/figures")
TRACES_DIR  = Path("outputs/traces")

for _d in [RESULTS_DIR, FIGURES_DIR, TRACES_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── MCMC sampling config ──────────────────────────────────────────────────────
# 1000 draws × 4 chains = 4000 posterior samples — ample for these low-dimensional
# models (the hierarchical model raises target_accept to 0.95 internally).
SAMPLING_CONFIG = dict(
    draws         = 1000,
    tune          = 1000,
    chains        = 4,
    target_accept = 0.9,
    random_seed   = 42,
)

# ── Targeting depths for lift evaluation ─────────────────────────────────────
TOP_K_FRACS = [0.05, 0.10, 0.20, 0.30, 0.50]

# ── Decision-theoretic targeting (RQ3 / H3) ──────────────────────────────────
# Per-customer intervention cost (e.g. a discount voucher / outreach cost), in £.
# A grid is swept for sensitivity; PRIMARY_COST drives the headline figure.
TARGETING_DEPTHS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
COST_GRID        = [5.0, 20.0, 50.0]
PRIMARY_COST     = 20.0


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _section(title: str) -> None:
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


# ── Thesis table formatting ───────────────────────────────────────────────────
# Display names for result-table columns/indices. Values may contain LaTeX
# (rendered with escape=False), so cell values must stay LaTeX-safe — the model
# and country labels used in this project contain no LaTeX specials.
_DISPLAY_NAMES = {
    # identifiers
    "model": "Model", "country": "Country",
    "top_k_pct": r"Top-$k$ (\%)", "cost_per_customer": r"Cost (\pounds)",
    "targeting_depth": "Depth", "n_customers": "$n$", "n_targeted": r"$n$ tgt.",
    # transaction metrics
    "tx_mae": "Tx MAE", "tx_rmse": "Tx RMSE", "tx_mape": r"Tx MAPE (\%)",
    "tx_spearman": "Tx Spearman", "tx_gini": "Tx Gini",
    # CLV metrics
    "clv_mae": r"CLV MAE (\pounds)", "clv_rmse": r"CLV RMSE (\pounds)",
    "clv_gini": "CLV Gini", "ndcg_100": "NDCG@100", "ndcg_500": "NDCG@500",
    # posterior / coverage
    "coverage_90pct": r"Coverage (90\%)", "mean_interval_width": "Mean width",
    "crps": "CRPS",
    # P(alive) classification
    "accuracy": "Accuracy", "precision": "Precision", "recall": "Recall",
    "f1": "F1", "auc_roc": "AUC-ROC", "auc_pr": "AUC-PR", "brier": "Brier",
    # targeting simulation (all in £)
    "point_estimate_value": r"Point (\pounds)",
    "posterior_prob_value": r"Posterior (\pounds)",
    "oracle_value": r"Oracle (\pounds)", "random_value": r"Random (\pounds)",
    "improvement": r"Improvement (\pounds)", "improvement_pct": r"Improvement (\%)",
    "lift": "Lift",
}

# Columns whose values are monetary (£) — formatted with thousands separators.
_MONEY_COLS = {
    "clv_mae", "clv_rmse", "point_estimate_value", "posterior_prob_value",
    "oracle_value", "random_value", "improvement",
}
# Columns that are integer counts.
_INT_COLS = {"n_customers", "n_targeted"}


def _pretty_col(name: str) -> str:
    """Map an internal column/index name to its thesis display label."""
    if name in _DISPLAY_NAMES:
        return _DISPLAY_NAMES[name]
    if isinstance(name, str) and name.startswith("MAE_"):
        return f"MAE: {name[4:]}"          # country_level_mae dynamic columns
    return str(name)


def _fmt_cell(col: str, v) -> str:
    """Format a single cell as a LaTeX-ready string based on its column."""
    if pd.isna(v):
        return "--"
    if not isinstance(v, (int, float, np.integer, np.floating)) or isinstance(v, bool):
        return str(v)
    if col in _INT_COLS:
        return f"{int(round(v)):,}"
    if col in _MONEY_COLS:
        return f"{v:,.1f}"
    if col == "cost_per_customer":
        return f"{v:,.0f}"
    if col in {"top_k_pct", "tx_mape", "improvement_pct"}:
        return f"{v:.1f}"
    if col == "targeting_depth":
        return f"{v:.2f}"
    # default: ratios, scores, MAE/RMSE, coverage, MAE_<model> — 3 decimals
    return f"{v:.3f}"


def _save_results(
    df: pd.DataFrame, stem: str, caption: str = "", label: str = "",
    index: bool = True,
) -> None:
    """
    Save a results DataFrame as a raw CSV (for programmatic reference) and a
    thesis-ready booktabs LaTeX table (pretty headers, per-column formatting).

    The CSV keeps the original column names and full-precision floats so the
    fill-in of Chapter 5 can read exact values; the .tex is what the thesis
    \\resulttable macro inputs.
    """
    csv_path = RESULTS_DIR / f"{stem}.csv"
    tex_path = RESULTS_DIR / f"{stem}.tex"

    df.to_csv(csv_path, index=index)

    try:
        d = df.copy()
        # Right-align numeric columns, left-align text columns (from original dtypes).
        col_align = [
            "r" if pd.api.types.is_numeric_dtype(df[c]) else "l"
            for c in d.columns
        ]
        # Per-column string formatting.
        for col in d.columns:
            d[col] = d[col].map(lambda v, c=col: _fmt_cell(c, v))
        # Format index level values (numeric levels only), then pretty-rename.
        if index:
            if d.index.nlevels > 1:
                d.index = pd.MultiIndex.from_arrays(
                    [[_fmt_cell(name, v) for v in d.index.get_level_values(name)]
                     for name in d.index.names],
                    names=[_pretty_col(n) for n in d.index.names],
                )
            else:
                name = d.index.name
                d.index = pd.Index(
                    [_fmt_cell(name, v) for v in d.index], name=_pretty_col(name)
                )
        # Pretty column headers.
        d = d.rename(columns=_pretty_col)

        n_idx = d.index.nlevels if index else 0
        column_format = "l" * n_idx + "".join(col_align)

        latex = d.to_latex(
            index         = index,
            escape        = False,      # headers carry LaTeX (\pounds, \%, $k$)
            column_format = column_format,
            caption       = caption,
            label         = label,
            position      = "htbp",
        )
        latex = "% Requires \\usepackage{booktabs}\n" + latex
        tex_path.write_text(latex, encoding="utf-8")
    except Exception as e:
        print(f"  LaTeX export warning ({stem}): {e}")

    print(f"  Saved: {csv_path.name}  /  {tex_path.name}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — DATA
# ─────────────────────────────────────────────────────────────────────────────

def step_data(force_rerun: bool = False):
    _section("STEP 1: DATA PIPELINE")

    processed_ready = all(
        Path(f"data/processed/{f}").exists()
        for f in ["customers.parquet", "holdout_truth.parquet",
                  "cal_transactions.parquet", "holdout_transactions.parquet"]
    )

    if processed_ready and not force_rerun:
        print("Processed files found — loading from cache.")
        cal, holdout, customers, truth = load_processed()
    else:
        print("Running full data pipeline...")
        _, cal, holdout, customers, truth = run_pipeline()

    # Holdout window in weeks (BG/NBD prediction horizon)
    t_future = (
        holdout["InvoiceDate"].max() - pd.Timestamp(CAL_END)
    ).days / 7.0
    print(f"\nHoldout window: {t_future:.1f} weeks  ({len(customers):,} customers)")

    return cal, holdout, customers, truth, t_future


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — FIT BAYESIAN MODELS
# ─────────────────────────────────────────────────────────────────────────────

def step_bayesian(customers: pd.DataFrame, skip_sampling: bool = False) -> dict:
    """Fit the three Bayesian models. Returns a dict of *fitted objects*:
    'bgnbd' (BetaGeoModel), 'gamma_gamma' (GammaGammaModel), 'bgnbd_hier'
    (InferenceData). Standard BG/NBD and Gamma-Gamma use pymc-marketing; the
    hierarchical model is the custom stable-logp implementation.
    """
    _section("STEP 2: BAYESIAN MODELS (MCMC)")

    # Data-informed HalfNormal priors (scaled to this dataset); see src/priors.py.
    priors = data_informed_priors(customers, verbose=False)
    models = {}

    # 2a. Standard BG/NBD (pymc-marketing) ────────────────────────────────────
    print("\n── 2a. Standard BG/NBD ──────────────────────────────────────")
    if skip_sampling and (TRACES_DIR / "bgnbd_standard.nc").exists():
        print("  Loading saved model...")
        models["bgnbd"] = load_bgnbd("bgnbd_standard")
    else:
        models["bgnbd"] = fit_bgnbd(
            customers, priors=priors["bgnbd"], save_name="bgnbd_standard",
            **SAMPLING_CONFIG,
        )

    # 2b. Hierarchical BG/NBD (custom, per country segment) ────────────────────
    print("\n── 2b. Hierarchical BG/NBD (per country segment) ────────────")
    if skip_sampling and (TRACES_DIR / "bgnbd_hierarchical.nc").exists():
        print("  Loading saved trace...")
        models["bgnbd_hier"] = load_hier_trace("bgnbd_hierarchical")
    else:
        # The hierarchical model needs a higher target_accept to control the
        # small-segment funnel geometry.
        hier_cfg = {**SAMPLING_CONFIG, "target_accept": 0.95}
        models["bgnbd_hier"] = fit_hierarchical_bgnbd(
            customers, save_name="bgnbd_hierarchical", **hier_cfg
        )

    # 2c. Gamma-Gamma (monetary, pymc-marketing) ──────────────────────────────
    print("\n── 2c. Gamma-Gamma (monetary value) ─────────────────────────")
    if skip_sampling and (TRACES_DIR / "gamma_gamma.nc").exists():
        print("  Loading saved model...")
        models["gamma_gamma"] = load_gamma_gamma("gamma_gamma")
    else:
        models["gamma_gamma"] = fit_gamma_gamma(
            customers, priors=priors["gamma_gamma"], save_name="gamma_gamma",
            **SAMPLING_CONFIG,
        )

    # Save posterior summaries ─────────────────────────────────────────────────
    print("\n── Posterior summaries ──────────────────────────────────────")
    for name, fitted in models.items():
        try:
            var_names = ["r", "alpha", "a", "b"] if name.startswith("bgnbd") else None
            summary = summarise_trace(fitted, var_names=var_names)
            out = RESULTS_DIR / f"posterior_summary_{name}.csv"
            summary.to_csv(out)
            print(f"  {name}: saved to {out.name}")
        except Exception as e:
            print(f"  {name}: summary failed — {e}")

    return models


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — BAYESIAN PREDICTIONS
# ─────────────────────────────────────────────────────────────────────────────

def step_bayesian_predictions(
    customers: pd.DataFrame,
    models: dict,
    t_future: float,
    n_samples: int = 2000,
) -> dict:
    _section("STEP 3: BAYESIAN PREDICTIONS")

    predictions = {}

    # Shared: Gamma-Gamma monetary predictions (used by both BG/NBD variants)
    print("\n── Gamma-Gamma monetary predictions ─────────────────────────")
    monetary_samples, repeat_mask = predict_spend(
        models["gamma_gamma"], customers, n_samples=n_samples
    )
    print(f"  Repeat customers: {repeat_mask.sum():,} / {len(customers):,}")
    print(f"  Mean pred monetary: £{monetary_samples.mean():.2f}")

    # ── Standard BG/NBD ──────────────────────────────────────────────────────
    print("\n── Standard BG/NBD ──────────────────────────────────────────")
    tx_bgnbd = predict_transactions(
        models["bgnbd"], customers, t_future=t_future, n_samples=n_samples,
    )
    p_alive_bgnbd = predict_p_alive(models["bgnbd"], customers, n_samples=n_samples)
    clv_bgnbd = compute_clv_posterior(tx_bgnbd, monetary_samples, repeat_mask)

    print(f"  Mean predicted tx:  {tx_bgnbd.mean(axis=0).mean():.3f}")
    print(f"  Mean P(alive):      {p_alive_bgnbd.mean():.3f}")
    print(f"  Mean predicted CLV: £{clv_bgnbd.mean(axis=0).mean():.2f}")

    predictions["BG/NBD (Bayesian)"] = {
        "tx_posterior" : tx_bgnbd,
        "tx_mean"      : tx_bgnbd.mean(axis=0),
        "p_alive"      : p_alive_bgnbd,
        "clv_posterior": clv_bgnbd,
        "clv_mean"     : clv_bgnbd.mean(axis=0),
    }

    # ── Hierarchical BG/NBD ──────────────────────────────────────────────────
    print("\n── Hierarchical BG/NBD ──────────────────────────────────────")
    tx_hier = predict_transactions_hier(
        models["bgnbd_hier"], customers, t_future=t_future, n_samples=n_samples,
    )
    p_alive_hier = predict_p_alive_hier(
        models["bgnbd_hier"], customers, n_samples=n_samples,
    )
    clv_hier = compute_clv_posterior(tx_hier, monetary_samples, repeat_mask)

    print(f"  Mean predicted tx:  {tx_hier.mean(axis=0).mean():.3f}")
    print(f"  Mean P(alive):      {p_alive_hier.mean():.3f}")
    print(f"  Mean predicted CLV: £{clv_hier.mean(axis=0).mean():.2f}")

    predictions["Hierarchical BG/NBD"] = {
        "tx_posterior" : tx_hier,
        "tx_mean"      : tx_hier.mean(axis=0),
        "p_alive"      : p_alive_hier,
        "clv_posterior": clv_hier,
        "clv_mean"     : clv_hier.mean(axis=0),
    }

    return predictions


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — CLASSICAL BASELINES
# ─────────────────────────────────────────────────────────────────────────────

def step_baselines(
    customers: pd.DataFrame,
    truth: pd.DataFrame,
    t_future: float,
    cal: Optional[pd.DataFrame] = None,
) -> dict:
    _section("STEP 4: CLASSICAL BASELINES")

    # Nested temporal split for XGBoost: train targets come from inside the
    # calibration window so the evaluation holdout stays unseen (no leakage).
    xgb_train = None
    if cal is not None:
        xgb_train = build_inner_training_set(cal, inner_cal_end=XGB_INNER_CAL_END)

    fitted = fit_all_baselines(
        customers, truth, cal_transactions=cal, include_pareto=False,
        xgb_train=xgb_train,
    )

    baseline_preds = {}
    for name, model in fitted.items():
        tx  = np.maximum(model.predict(customers, t_future=t_future), 0.0)
        clv = np.maximum(model.predict_clv(customers, t_future=t_future), 0.0)
        baseline_preds[name] = {
            "tx_mean"      : tx,
            "clv_mean"     : clv,
            "tx_posterior" : None,   # no posterior for classical models
            "p_alive"      : None,
            "clv_posterior": None,
        }
        print(f"\n  {name}:  mean tx = {tx.mean():.3f}   mean CLV = £{clv.mean():.2f}")

    return baseline_preds


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — EVALUATE ALL MODELS
# ─────────────────────────────────────────────────────────────────────────────

def step_evaluate(
    truth: pd.DataFrame,
    bayesian_preds: dict,
    baseline_preds: dict,
) -> list:
    _section("STEP 5: EVALUATION")

    y_true_tx     = truth["holdout_transactions"].values.astype(float)
    y_true_spend  = truth["holdout_spend"].values.astype(float)
    y_true_active = truth["is_active"].values.astype(int)

    all_preds = {**bayesian_preds, **baseline_preds}
    eval_results = []

    for name, preds in all_preds.items():
        print(f"\n  Evaluating: {name}")
        res = evaluate_model(
            model_name        = name,
            y_true_tx         = y_true_tx,
            y_pred_tx         = preds["tx_mean"],
            y_true_spend      = y_true_spend,
            y_pred_spend      = preds["clv_mean"],
            y_true_active     = y_true_active if preds["p_alive"] is not None else None,
            y_score_alive     = preds["p_alive"],
            posterior_samples = preds["tx_posterior"],
            top_k_fracs       = TOP_K_FRACS,
        )
        eval_results.append(res)

        m = res["metrics"]
        print(f"    TX:  MAE={m['tx_mae']:.4f}  RMSE={m['tx_rmse']:.4f}  "
              f"Spearman={m['tx_spearman']:.4f}  Gini={m['tx_gini']:.4f}")
        if "clv_mae" in m:
            print(f"    CLV: MAE=£{m['clv_mae']:.2f}  "
                  f"Gini={m['clv_gini']:.4f}  NDCG@100={m.get('ndcg_100', float('nan')):.4f}")
        if "post_coverage_90pct" in m:
            print(f"    Bayes: coverage(90%)={m['post_coverage_90pct']:.3f}  "
                  f"CRPS={m['post_crps']:.4f}")
        if res.get("classification"):
            c = res["classification"]
            print(f"    P(alive): AUC={c['auc_roc']:.4f}  AUC-PR={c['auc_pr']:.4f}  "
                  f"Brier={c['brier']:.4f}")

    return eval_results


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — SAVE RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def step_save_results(eval_results: list) -> pd.DataFrame:
    _section("STEP 6: SAVING RESULTS TABLES")

    # ── Main metrics comparison ───────────────────────────────────────────────
    comparison = compare_all_models(
        eval_results,
        metrics=[
            "tx_mae", "tx_rmse", "tx_mape", "tx_spearman", "tx_gini",
            "clv_mae", "clv_rmse", "clv_gini", "ndcg_100", "ndcg_500",
        ],
    )
    _save_results(
        comparison,
        "metrics_comparison",
        caption="Model comparison across transaction and CLV prediction metrics.",
        label="tab:metrics_comparison",
        index=False,
    )
    print("\nMetrics comparison table:")
    print(comparison.to_string())

    # ── Calibration tables (one per model) ────────────────────────────────────
    for res in eval_results:
        if res.get("calibration") is not None:
            safe = (
                res["model_name"]
                .lower()
                .replace("/", "_")
                .replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
            )
            res["calibration"].to_csv(RESULTS_DIR / f"calibration_{safe}.csv", index=False)
    print(f"  Calibration tables saved.")

    # ── Targeting lift comparison ─────────────────────────────────────────────
    lift_combined = lift_comparison_table(eval_results)
    if not lift_combined.empty:
        _save_results(
            lift_combined.set_index("top_k_pct"),
            "targeting_lift",
            caption="Targeting lift at various customer targeting depths.",
            label="tab:targeting_lift",
        )

    # ── Bayesian-specific: credible interval coverage + CRPS ─────────────────
    coverage_rows = []
    for res in eval_results:
        m = res["metrics"]
        key = "post_coverage_90pct"
        if key in m:
            coverage_rows.append({
                "model"                : res["model_name"],
                "coverage_90pct"       : m[key],
                "mean_interval_width"  : m.get("post_mean_interval_width", float("nan")),
                "crps"                 : m.get("post_crps", float("nan")),
            })
    if coverage_rows:
        cov_df = pd.DataFrame(coverage_rows).set_index("model")
        _save_results(
            cov_df,
            "credible_interval_coverage",
            caption="Posterior predictive credible interval coverage and CRPS.",
            label="tab:coverage",
        )

    # ── P(alive) classification metrics ──────────────────────────────────────
    palive_rows = []
    for res in eval_results:
        if res.get("classification"):
            palive_rows.append({"model": res["model_name"], **res["classification"]})
    if palive_rows:
        palive_df = pd.DataFrame(palive_rows).set_index("model")
        _save_results(
            palive_df,
            "p_alive_evaluation",
            caption="P(alive) evaluation: binary activity prediction metrics.",
            label="tab:p_alive",
        )

    print(f"\nAll results written to {RESULTS_DIR}/")
    return comparison


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6b — DECISION-THEORETIC & COUNTRY-LEVEL ANALYSIS  (RQ2 / RQ3)
# ─────────────────────────────────────────────────────────────────────────────

def step_decision_analysis(
    customers: pd.DataFrame,
    truth: pd.DataFrame,
    bayesian_preds: dict,
    baseline_preds: dict,
) -> tuple:
    """
    RQ3/H3 — decision-theoretic targeting: for each Bayesian model, compare
    posterior-probability vs point-estimate vs oracle targeting across a grid
    of intervention costs (uses the CLV posterior).

    RQ2/H2 — country-level transaction MAE for every model, to test whether the
    hierarchical model's partial pooling helps within country segments.

    Returns (targeting_sims, country_metrics) for downstream plotting.
    """
    _section("STEP 6b: DECISION-THEORETIC & COUNTRY-LEVEL ANALYSIS")

    y_true_spend = truth["holdout_spend"].values.astype(float)
    y_true_tx    = truth["holdout_transactions"].values.astype(float)
    countries    = customers["country_segment"].values

    # ── RQ3: targeting simulation (Bayesian models only — need a posterior) ───
    targeting_sims = {}
    for name, preds in bayesian_preds.items():
        if preds.get("clv_posterior") is None:
            continue
        print(f"\n── Targeting simulation: {name} ──")
        sweep = targeting_simulation_sweep(
            preds["clv_posterior"], y_true_spend,
            cost_grid=COST_GRID, targeting_depths=TARGETING_DEPTHS,
        )
        targeting_sims[name] = sweep

        safe = name.lower().replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
        _save_results(
            sweep.set_index(["cost_per_customer", "targeting_depth"]),
            f"targeting_simulation_{safe}",
            caption=f"Decision-theoretic targeting ({name}): posterior-probability vs "
                    f"point-estimate vs oracle net value, swept over intervention cost.",
            label=f"tab:targeting_sim_{safe}",
        )
        primary = sweep[sweep["cost_per_customer"] == PRIMARY_COST]
        if not primary.empty:
            print(primary.to_string(index=False))

    # ── RQ2: per-country transaction MAE for all models ───────────────────────
    print("\n── Country-level transaction MAE ──")
    all_preds = {**bayesian_preds, **baseline_preds}
    tx_predictions = {name: preds["tx_mean"] for name, preds in all_preds.items()}
    country_metrics = country_level_metrics(
        actual=y_true_tx, predictions=tx_predictions, countries=countries,
    )
    _save_results(
        country_metrics.set_index("country"),
        "country_level_mae",
        caption="Per-country transaction-prediction MAE by model (RQ2/H2).",
        label="tab:country_mae",
    )
    print(country_metrics.to_string(index=False))

    return targeting_sims, country_metrics


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — THESIS PLOTS
# ─────────────────────────────────────────────────────────────────────────────

def step_plots(
    customers: pd.DataFrame,
    truth: pd.DataFrame,
    models: dict,
    bayesian_preds: dict,
    eval_results: list,
    targeting_sims: Optional[dict] = None,
    country_metrics: Optional[pd.DataFrame] = None,
) -> None:
    _section("STEP 7: GENERATING THESIS PLOTS")

    # Diagnostic plots need InferenceData; pmm models expose it via get_idata().
    idatas = {k: get_idata(v) for k, v in models.items()}

    y_true_tx    = truth["holdout_transactions"].values.astype(float)
    y_true_spend = truth["holdout_spend"].values.astype(float)

    def _save(fig, name):
        P.save_figure(fig, name)
        plt.close(fig)

    def _try(fn, name, *args, **kwargs):
        try:
            fig = fn(*args, **kwargs)
            _save(fig, name)
        except Exception as e:
            print(f"  Warning [{name}]: {e}")

    # ── EDA ───────────────────────────────────────────────────────────────────
    _try(P.plot_rfm_distributions,  "rfm_distributions",  customers)
    _try(P.plot_monetary_distribution, "monetary_distribution", customers)
    _try(P.plot_recency_vs_T,        "recency_vs_T",       customers)

    # ── MCMC diagnostics ─────────────────────────────────────────────────────
    _try(P.plot_trace,  "trace_bgnbd_standard",
         idatas["bgnbd"], ["r", "alpha", "a", "b"], "BG/NBD Standard")

    _try(P.plot_rhat_summary, "rhat_bgnbd_standard",
         idatas["bgnbd"], "BG/NBD (Standard)")
    _try(P.plot_rhat_summary, "rhat_bgnbd_hierarchical",
         idatas["bgnbd_hier"], "BG/NBD (Hierarchical)")
    _try(P.plot_rhat_summary, "rhat_gamma_gamma",
         idatas["gamma_gamma"], "Gamma-Gamma")

    _try(P.plot_posterior_pairs, "pairs_bgnbd",
         idatas["bgnbd"], ["r", "alpha", "a", "b"], "BG/NBD")

    # ── Calibration (all models, side by side) ────────────────────────────────
    cal_dict = {
        res["model_name"]: res["calibration"]
        for res in eval_results
        if res.get("calibration") is not None
    }
    _try(P.plot_calibration_comparison, "calibration_comparison", cal_dict)

    # Individual calibration panels
    for res in eval_results:
        if res.get("calibration") is not None:
            safe = (
                res["model_name"]
                .lower()
                .replace("/", "_").replace(" ", "_")
                .replace("(", "").replace(")", "")
            )
            _try(P.plot_calibration, f"calibration_{safe}",
                 res["calibration"], res["model_name"])

    # ── Lift / targeting ──────────────────────────────────────────────────────
    lift_dict = {
        res["model_name"]: res["lift"]
        for res in eval_results
        if res.get("lift") is not None
    }
    _try(P.plot_lift_curves, "targeting_lift_curves", lift_dict)

    # ── CLV distribution & uncertainty ───────────────────────────────────────
    bgnbd_clv = bayesian_preds["BG/NBD (Bayesian)"]["clv_posterior"]
    _try(P.plot_clv_distribution, "clv_distribution_bgnbd", bgnbd_clv)
    _try(P.plot_clv_uncertainty,  "clv_uncertainty_bgnbd",  bgnbd_clv, customers)

    hier_clv = bayesian_preds["Hierarchical BG/NBD"]["clv_posterior"]
    _try(P.plot_clv_distribution, "clv_distribution_hierarchical", hier_clv)

    # ── P(alive) ─────────────────────────────────────────────────────────────
    _try(P.plot_p_alive_distribution, "p_alive_bgnbd_standard",
         bayesian_preds["BG/NBD (Bayesian)"]["p_alive"], customers, "BG/NBD Standard")
    _try(P.plot_p_alive_distribution, "p_alive_bgnbd_hierarchical",
         bayesian_preds["Hierarchical BG/NBD"]["p_alive"], customers, "Hierarchical BG/NBD")

    # ── Posterior predictive ──────────────────────────────────────────────────
    _try(P.plot_posterior_predictive, "posterior_predictive_bgnbd",
         y_true_tx, bayesian_preds["BG/NBD (Bayesian)"]["tx_posterior"])

    # ── Hierarchical shrinkage (forest plots) ─────────────────────────────────
    # Use the posterior's own segment order so forest-plot labels line up.
    seg_names = list(idatas["bgnbd_hier"].posterior.coords["segment"].values)
    for param in ["r", "alpha", "a", "b"]:
        _try(P.plot_hierarchical_segments,
             f"hierarchical_shrinkage_{param}",
             idatas["bgnbd_hier"], seg_names, param)

    # ── Decision-theoretic targeting (RQ3 / H3) ───────────────────────────────
    if targeting_sims:
        for name, sweep in targeting_sims.items():
            safe = (
                name.lower().replace("/", "_").replace(" ", "_")
                .replace("(", "").replace(")", "")
            )
            primary = sweep[sweep["cost_per_customer"] == PRIMARY_COST]
            if not primary.empty:
                _try(P.plot_targeting_simulation,
                     f"targeting_simulation_{safe}",
                     primary.reset_index(drop=True), name)

    # ── Country-level error (RQ2 / H2) ────────────────────────────────────────
    if country_metrics is not None and not country_metrics.empty:
        _try(P.plot_country_mae_comparison, "country_mae_comparison",
             country_metrics)

    print(f"\nAll figures saved to {FIGURES_DIR}/")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CLV thesis model pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--skip-sampling", action="store_true",
        help="Load previously saved MCMC traces instead of re-running NUTS",
    )
    parser.add_argument(
        "--force-data", action="store_true",
        help="Re-run data pipeline even when processed parquet files exist",
    )
    parser.add_argument(
        "--n-samples", type=int, default=2000,
        help="Number of posterior draws used for predictions (per model)",
    )
    args = parser.parse_args()

    print("\n" + "=" * 65)
    print("  CLV THESIS — FULL MODEL PIPELINE")
    print("=" * 65)
    print(f"  skip_sampling : {args.skip_sampling}")
    print(f"  force_data    : {args.force_data}")
    print(f"  n_samples     : {args.n_samples}")

    # Step 1 — data
    cal, holdout, customers, truth, t_future = step_data(
        force_rerun=args.force_data
    )

    # Step 2 — Bayesian models (MCMC)
    models = step_bayesian(customers, skip_sampling=args.skip_sampling)

    # Step 3 — Bayesian predictions
    bayesian_preds = step_bayesian_predictions(
        customers, models, t_future, n_samples=args.n_samples
    )

    # Step 4 — Classical baselines
    baseline_preds = step_baselines(customers, truth, t_future, cal=cal)

    # Step 5 — Evaluate all models
    eval_results = step_evaluate(truth, bayesian_preds, baseline_preds)

    # Step 6 — Save results tables
    comparison = step_save_results(eval_results)

    # Step 6b — Decision-theoretic (RQ3) + country-level (RQ2) analysis
    targeting_sims, country_metrics = step_decision_analysis(
        customers, truth, bayesian_preds, baseline_preds
    )

    # Step 7 — Thesis plots
    step_plots(
        customers, truth, models, bayesian_preds, eval_results,
        targeting_sims=targeting_sims, country_metrics=country_metrics,
    )

    print("\n" + "=" * 65)
    print("  PIPELINE COMPLETE")
    print(f"  Results  → {RESULTS_DIR}/")
    print(f"  Figures  → {FIGURES_DIR}/")
    print(f"  Traces   → {TRACES_DIR}/")
    print("=" * 65 + "\n")

    return {
        "customers"    : customers,
        "truth"        : truth,
        "models"       : models,
        "bayesian_preds": bayesian_preds,
        "baseline_preds": baseline_preds,
        "eval_results" : eval_results,
        "comparison"   : comparison,
        "targeting_sims": targeting_sims,
        "country_metrics": country_metrics,
    }


if __name__ == "__main__":
    main()
