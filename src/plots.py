"""
src/plots.py
============
All thesis-quality plots in one place.

Every function returns a matplotlib Figure so callers can save or display
as needed. Consistent styling is enforced via _apply_style().

Sections
--------
    1. EDA plots
    2. Model diagnostics (trace, R-hat, divergences)
    3. Calibration plots
    4. Prediction plots
    5. Targeting / lift plots
    6. CLV distribution plots
    7. Comparison plots
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import arviz as az
from pathlib import Path
from typing import Dict, List, Optional, Tuple

FIGURES_DIR = Path("outputs/figures")

# ── Palette ──────────────────────────────────────────────────────────────────
PAL = {
    "bayesian"  : "#2E4057",
    "heuristic" : "#E76F51",
    "xgboost"   : "#1D9E75",
    "naive"     : "#AAAAAA",
    "pareto"    : "#8ECAE6",
    "actual"    : "#2E4057",
    "predicted" : "#E76F51",
    "accent"    : "#E63946",
    "light_gray": "#F1EFE8",
    "grid"      : "#DDDDDD",
}

MODEL_COLORS = {
    "BG/NBD (Bayesian)"      : PAL["bayesian"],
    "Hierarchical BG/NBD"    : "#534AB7",
    "Pareto/NBD (MLE)"       : PAL["pareto"],
    "RFM Heuristic"          : PAL["heuristic"],
    "XGBoost (two-stage)"    : PAL["xgboost"],
    "Naive (mean)"           : PAL["naive"],
}


def _apply_style(ax: plt.Axes, title: str = "", xlabel: str = "", ylabel: str = "") -> None:
    """Apply consistent thesis styling to an axis."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PAL["grid"])
    ax.spines["bottom"].set_color(PAL["grid"])
    ax.tick_params(colors="#555555", labelsize=10)
    ax.grid(True, linestyle="--", alpha=0.4, color=PAL["grid"], zorder=0)
    if title:   ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    if xlabel:  ax.set_xlabel(xlabel, fontsize=11)
    if ylabel:  ax.set_ylabel(ylabel, fontsize=11)


def save_figure(fig: plt.Figure, name: str, dpi: int = 200) -> Path:
    """Save figure to outputs/figures/ and return the path."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"  ✓ Saved {path}")
    return path


# ──────────────────────────────────────────────────────────────────────────────
# 1. EDA PLOTS
# ──────────────────────────────────────────────────────────────────────────────

def plot_rfm_distributions(customers: pd.DataFrame) -> plt.Figure:
    """
    3-panel histogram of Frequency, Recency, and T distributions.
    Shows the raw shapes of the BG/NBD input variables.
    """
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))

    for ax, col, label, clip_pct in zip(
        axes,
        ["frequency", "recency", "T"],
        ["Frequency (repeat purchases)", "Recency (weeks)", "T (weeks)"],
        [0.98, 1.0, 1.0],
    ):
        vals = customers[col].clip(upper=customers[col].quantile(clip_pct))
        ax.hist(vals, bins=40, color=PAL["bayesian"], edgecolor="white",
                alpha=0.85, linewidth=0.5)
        ax.axvline(customers[col].mean(), color=PAL["accent"],
                   linestyle="--", linewidth=1.5,
                   label=f"Mean: {customers[col].mean():.1f}")
        ax.legend(fontsize=9)
        _apply_style(ax, title=label, xlabel=label, ylabel="Customers")
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{x/1e3:.0f}K" if x >= 1000 else f"{x:.0f}")
        )

    fig.suptitle("Calibration Period RFM Distributions", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    return fig


def plot_monetary_distribution(customers: pd.DataFrame) -> plt.Figure:
    """
    Side-by-side raw and log-scale monetary value distributions for repeat customers.
    """
    repeat = customers[customers["frequency"] > 0]["monetary_value"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].hist(repeat.clip(upper=repeat.quantile(0.99)), bins=50,
                 color=PAL["bayesian"], edgecolor="white", alpha=0.85)
    axes[0].axvline(repeat.mean(), color=PAL["accent"], linestyle="--",
                    linewidth=1.5, label=f"Mean: £{repeat.mean():.0f}")
    axes[0].legend()
    _apply_style(axes[0], "Monetary Value (raw)", "Avg Transaction Value (£)", "Customers")

    axes[1].hist(np.log1p(repeat), bins=50,
                 color=PAL["heuristic"], edgecolor="white", alpha=0.85)
    _apply_style(axes[1], "Monetary Value (log scale)", "log(1 + value)", "Customers")

    fig.tight_layout()
    return fig


def plot_recency_vs_T(customers: pd.DataFrame) -> plt.Figure:
    """
    Scatter plot of recency vs T, coloured by frequency.
    Every point must fall below the diagonal (recency ≤ T).
    """
    fig, ax = plt.subplots(figsize=(7, 6))

    freq_clipped = customers["frequency"].clip(upper=customers["frequency"].quantile(0.95))
    sc = ax.scatter(
        customers["T"], customers["recency"],
        c=freq_clipped, cmap="Blues",
        alpha=0.3, s=8, linewidths=0,
    )
    max_T = customers["T"].max()
    ax.plot([0, max_T], [0, max_T], "--", color=PAL["accent"],
            linewidth=1.5, label="recency = T (boundary)")
    ax.legend(fontsize=9)

    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("Frequency", fontsize=10)

    _apply_style(ax, "Recency vs Observation Period (T)",
                 "T (weeks)", "Recency (weeks)")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 2. MODEL DIAGNOSTICS
# ──────────────────────────────────────────────────────────────────────────────

def plot_trace(
    trace,
    var_names: List[str],
    model_name: str = "BG/NBD",
) -> plt.Figure:
    """
    Trace plot for selected parameters using ArviZ.
    Returns the ArviZ figure for embedding in thesis.
    """
    axes = az.plot_trace(trace, var_names=var_names, compact=True)
    fig = axes.ravel()[0].figure
    fig.suptitle(f"{model_name} — Posterior Trace", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_posterior_pairs(
    trace,
    var_names: List[str],
    model_name: str = "BG/NBD",
) -> plt.Figure:
    """
    Pair plot of posterior marginals. Reveals correlations between parameters.
    """
    axes = az.plot_pair(
        trace, var_names=var_names,
        divergences=True, kde_kwargs={"fill_last": False}
    )
    fig = axes.ravel()[0].figure
    fig.suptitle(f"{model_name} — Posterior Pairs", fontsize=13, fontweight="bold")
    return fig


def plot_rhat_summary(trace, model_name: str = "Model") -> plt.Figure:
    """
    Bar chart of per-parameter R-hat values.
    Red dashed line at 1.01 marks the convergence threshold.
    """
    rhat_df = az.rhat(trace).to_dataframe().reset_index()
    rhat_df.columns = ["parameter", "rhat"]
    rhat_df = rhat_df.sort_values("rhat", ascending=False)

    fig, ax = plt.subplots(figsize=(8, max(4, len(rhat_df) * 0.4)))
    colors = [PAL["accent"] if r > 1.01 else PAL["bayesian"] for r in rhat_df["rhat"]]
    ax.barh(rhat_df["parameter"], rhat_df["rhat"], color=colors,
            edgecolor="white", linewidth=0.5)
    ax.axvline(1.01, color=PAL["accent"], linestyle="--", linewidth=1.5,
               label="R-hat = 1.01 threshold")
    ax.axvline(1.0,  color=PAL["grid"],  linestyle="-",  linewidth=1.0)
    ax.legend(fontsize=9)
    _apply_style(ax, f"{model_name} — R-hat Convergence Diagnostics",
                 "R-hat", "Parameter")
    ax.set_xlim(left=0.99)
    fig.tight_layout()
    return fig


def plot_energy(trace, model_name: str = "Model") -> plt.Figure:
    """
    Energy plot for diagnosing HMC sampling quality.
    A well-behaved chain has its energy and energy transition distributions overlapping.
    """
    ax = az.plot_energy(trace)
    fig = ax.figure
    fig.suptitle(f"{model_name} — Energy Diagnostic", fontsize=12, fontweight="bold")
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 3. CALIBRATION PLOTS
# ──────────────────────────────────────────────────────────────────────────────

def plot_calibration(
    calibration_df: pd.DataFrame,
    model_name: str = "Model",
    ax: Optional[plt.Axes] = None,
) -> plt.Figure:
    """
    Calibration plot: mean predicted vs mean actual transactions per decile.

    Points on the diagonal = perfectly calibrated.
    Points above = model over-predicts that decile.
    Points below = model under-predicts.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(6, 6))
    else:
        fig = ax.figure

    ax.scatter(
        calibration_df["mean_predicted"],
        calibration_df["mean_actual"],
        s=calibration_df["n_customers"] / calibration_df["n_customers"].max() * 200 + 30,
        color=PAL["bayesian"], alpha=0.8, zorder=3,
        label="Decile (size ∝ n customers)",
    )

    # Perfect calibration line
    max_val = max(
        calibration_df["mean_predicted"].max(),
        calibration_df["mean_actual"].max(),
    ) * 1.05
    ax.plot([0, max_val], [0, max_val], "--", color=PAL["accent"],
            linewidth=1.5, label="Perfect calibration")

    # Annotate bins
    for _, row in calibration_df.iterrows():
        ax.annotate(
            f"{row['bin']:.0f}",
            (row["mean_predicted"], row["mean_actual"]),
            textcoords="offset points", xytext=(5, 5),
            fontsize=8, color="#555555",
        )

    ax.legend(fontsize=9)
    _apply_style(ax, f"{model_name} — Calibration Plot",
                 "Mean Predicted Transactions",
                 "Mean Actual Transactions")
    fig.tight_layout()
    return fig


def plot_calibration_comparison(
    calibration_results: Dict[str, pd.DataFrame],
) -> plt.Figure:
    """
    Multi-panel calibration plot — one panel per model, same axis scale.
    """
    n_models = len(calibration_results)
    fig, axes = plt.subplots(1, n_models, figsize=(6 * n_models, 5))
    if n_models == 1:
        axes = [axes]

    all_max = max(
        max(df["mean_predicted"].max(), df["mean_actual"].max())
        for df in calibration_results.values()
    ) * 1.1

    for ax, (name, cal_df) in zip(axes, calibration_results.items()):
        color = MODEL_COLORS.get(name, PAL["bayesian"])
        ax.scatter(cal_df["mean_predicted"], cal_df["mean_actual"],
                   color=color, s=60, alpha=0.85, zorder=3)
        ax.plot([0, all_max], [0, all_max], "--", color=PAL["accent"],
                linewidth=1.5)
        ax.set_xlim(0, all_max)
        ax.set_ylim(0, all_max)
        _apply_style(ax, name, "Predicted", "Actual")

    fig.suptitle("Calibration Comparison (Predicted vs Actual Transactions)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 4. PREDICTION PLOTS
# ──────────────────────────────────────────────────────────────────────────────

def plot_predicted_vs_actual(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str = "Model",
    sample_n: int = 2000,
) -> plt.Figure:
    """
    Scatter plot of predicted vs actual values (subsampled for large datasets).
    """
    fig, ax = plt.subplots(figsize=(6, 6))

    if len(y_true) > sample_n:
        idx = np.random.choice(len(y_true), sample_n, replace=False)
        yt, yp = y_true[idx], y_pred[idx]
    else:
        yt, yp = y_true, y_pred

    ax.scatter(yt, yp, alpha=0.3, s=8, color=PAL["bayesian"],
               linewidths=0, zorder=3)

    max_val = max(yt.max(), yp.max()) * 1.05
    ax.plot([0, max_val], [0, max_val], "--", color=PAL["accent"],
            linewidth=1.5, label="Perfect prediction")
    ax.legend(fontsize=9)
    _apply_style(ax, f"{model_name} — Predicted vs Actual",
                 "Actual", "Predicted")
    fig.tight_layout()
    return fig


def plot_posterior_predictive(
    y_true: np.ndarray,
    posterior_samples: np.ndarray,
    model_name: str = "BG/NBD (Bayesian)",
    n_customers_show: int = 20,
) -> plt.Figure:
    """
    Plot posterior predictive distributions for a sample of customers.
    Shows the full uncertainty, not just point predictions.
    Each violin is one customer's posterior predictive distribution.
    """
    # Pick customers with interesting diversity: some one-timers, some frequent
    rng = np.random.default_rng(42)
    idx = rng.choice(len(y_true), min(n_customers_show, len(y_true)), replace=False)
    idx = idx[np.argsort(y_true[idx])]   # sort by actual for readability

    fig, ax = plt.subplots(figsize=(14, 5))

    parts = ax.violinplot(
        [posterior_samples[:, i] for i in idx],
        positions=range(len(idx)),
        showmedians=True,
        showextrema=False,
    )
    for pc in parts["bodies"]:
        pc.set_facecolor(PAL["bayesian"])
        pc.set_alpha(0.5)
    parts["cmedians"].set_color(PAL["bayesian"])

    ax.scatter(range(len(idx)), y_true[idx],
               color=PAL["accent"], s=50, zorder=5, label="Actual", marker="D")

    ax.set_xticks(range(len(idx)))
    ax.set_xticklabels([f"C{i}" for i in range(len(idx))], fontsize=8)
    ax.legend(fontsize=9)
    _apply_style(ax, f"{model_name} — Posterior Predictive (sample of customers)",
                 "Customer", "Predicted Transactions")
    fig.tight_layout()
    return fig


def plot_p_alive_distribution(
    p_alive: np.ndarray,
    customers: pd.DataFrame,
    model_name: str = "BG/NBD",
) -> plt.Figure:
    """
    Histogram of P(alive) estimates coloured by frequency.
    High-frequency customers should generally have higher P(alive).
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Overall distribution
    axes[0].hist(p_alive, bins=40, color=PAL["bayesian"],
                 edgecolor="white", alpha=0.85)
    axes[0].axvline(p_alive.mean(), color=PAL["accent"], linestyle="--",
                    linewidth=1.5, label=f"Mean: {p_alive.mean():.2f}")
    axes[0].legend()
    _apply_style(axes[0], "P(alive) Distribution", "P(alive)", "Customers")

    # P(alive) vs frequency
    freq_bins = [0, 1, 3, 6, 10, np.inf]
    freq_labels = ["0", "1-2", "3-5", "6-9", "10+"]
    freq_groups = pd.cut(customers["frequency"], bins=freq_bins, labels=freq_labels)
    for label in freq_labels:
        mask = freq_groups == label
        if mask.sum() > 0:
            axes[1].hist(p_alive[mask], bins=30, alpha=0.6,
                         label=f"freq={label} (n={mask.sum()})", edgecolor="none")
    axes[1].legend(fontsize=8)
    _apply_style(axes[1], "P(alive) by Frequency Group", "P(alive)", "Customers")

    fig.suptitle(f"{model_name} — P(alive) Estimates", fontsize=13,
                 fontweight="bold")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 5. TARGETING / LIFT PLOTS
# ──────────────────────────────────────────────────────────────────────────────

def plot_lift_curves(
    lift_results: Dict[str, pd.DataFrame],
    random_baseline: bool = True,
) -> plt.Figure:
    """
    Cumulative gain curves for all models on one plot.

    X-axis: fraction of customers targeted (ordered by model's predictions)
    Y-axis: fraction of total revenue captured

    The steeper the curve rises before reaching the diagonal, the better
    the model is at identifying high-value customers.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ── Left: Lift curves ────────────────────────────────────────────────────
    ax = axes[0]
    for name, lift_df in lift_results.items():
        color = MODEL_COLORS.get(name, "#555555")
        x = lift_df["top_k_pct"] / 100
        y = lift_df["captured_revenue_pct"] / 100
        ax.plot(x, y, "o-", color=color, linewidth=2, markersize=6, label=name)

    if random_baseline:
        ax.plot([0, 1], [0, 1], "--", color=PAL["naive"],
                linewidth=1.5, label="Random baseline")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.legend(fontsize=9, loc="lower right")
    _apply_style(ax, "Cumulative Gain Curves",
                 "% Customers Targeted", "% Revenue Captured")

    # ── Right: Lift values ───────────────────────────────────────────────────
    ax2 = axes[1]
    x_pos = np.arange(len(next(iter(lift_results.values()))["top_k_pct"]))
    bar_width = 0.8 / len(lift_results)
    x_labels = [f"{p}%" for p in next(iter(lift_results.values()))["top_k_pct"]]

    for i, (name, lift_df) in enumerate(lift_results.items()):
        color = MODEL_COLORS.get(name, "#555555")
        offset = (i - len(lift_results) / 2 + 0.5) * bar_width
        ax2.bar(x_pos + offset, lift_df["lift"], width=bar_width,
                color=color, alpha=0.85, label=name, edgecolor="white")

    ax2.axhline(1.0, color=PAL["naive"], linestyle="--", linewidth=1.5,
                label="Lift = 1.0 (random)")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(x_labels)
    ax2.legend(fontsize=8)
    _apply_style(ax2, "Lift at Various Targeting Thresholds",
                 "% Customers Targeted", "Lift")

    fig.suptitle("Targeting Performance", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_targeting_simulation(
    sim: pd.DataFrame,
    model_name: str = "BG/NBD (Bayesian)",
) -> plt.Figure:
    """
    Decision-theoretic targeting plot (RQ3 / H3).

    Visualises the output of evaluation.targeting_simulation():
      Left  — cumulative net value vs targeting depth for each strategy
               (posterior P(CLV>cost), point estimate, oracle, random).
      Right — the incremental value of posterior-probability ranking over
               point-estimate ranking, in £, at each depth.

    Parameters
    ----------
    sim : DataFrame from targeting_simulation() for a SINGLE cost
          (must have a single cost — filter a sweep before plotting).
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    depths = sim["targeting_depth"].values

    # ── Left: strategy value curves ──────────────────────────────────────────
    ax = axes[0]
    ax.plot(depths, sim["posterior_prob_value"], "o-",
            color=PAL["bayesian"], linewidth=2.5, markersize=7,
            label="Posterior  P(CLV > cost)")
    ax.plot(depths, sim["point_estimate_value"], "s--",
            color=PAL["heuristic"], linewidth=2, markersize=6,
            label="Point estimate  E[CLV]")
    ax.plot(depths, sim["oracle_value"], "^:",
            color="#555555", linewidth=1.5, markersize=6,
            label="Oracle (perfect info)")
    if "random_value" in sim.columns:
        ax.plot(depths, sim["random_value"], "-",
                color=PAL["naive"], linewidth=1.5, label="Random")

    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    ax.legend(fontsize=9, loc="best")
    _apply_style(ax, "Cumulative Net Value by Targeting Strategy",
                 "Targeting Depth (fraction of customers)",
                 "Cumulative Net Value")

    # ── Right: incremental value of the posterior rule ───────────────────────
    ax2 = axes[1]
    colors = [PAL["bayesian"] if v >= 0 else PAL["accent"]
              for v in sim["improvement"]]
    ax2.bar(depths, sim["improvement"], width=0.8 * np.min(np.diff(depths))
            if len(depths) > 1 else 0.04,
            color=colors, alpha=0.85, edgecolor="white")
    ax2.axhline(0, color="#555555", linewidth=1.0)
    ax2.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x:,.0f}"))
    _apply_style(ax2, "Posterior-Rule Advantage over Point Estimate",
                 "Targeting Depth (fraction of customers)",
                 "Net Value Gain (posterior − point)")

    fig.suptitle(f"{model_name} — Decision-Theoretic Targeting",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 6. CLV DISTRIBUTION PLOTS
# ──────────────────────────────────────────────────────────────────────────────

def plot_clv_distribution(
    clv_posterior: np.ndarray,
    top_n: int = 20,
) -> plt.Figure:
    """
    Two plots:
        Left  — histogram of mean CLV across all customers
        Right — top-N customers with 90% credible intervals (caterpillar plot)
    """
    clv_mean  = clv_posterior.mean(axis=0)
    clv_lower = np.percentile(clv_posterior, 5,  axis=0)
    clv_upper = np.percentile(clv_posterior, 95, axis=0)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ── Left: overall CLV distribution ───────────────────────────────────────
    axes[0].hist(clv_mean.clip(upper=np.percentile(clv_mean, 99)),
                 bins=50, color=PAL["bayesian"], edgecolor="white", alpha=0.85)
    axes[0].axvline(clv_mean.mean(), color=PAL["accent"], linestyle="--",
                    linewidth=1.5, label=f"Mean: £{clv_mean.mean():.0f}")
    axes[0].legend()
    axes[0].xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"£{x:.0f}")
    )
    _apply_style(axes[0], "Predicted CLV Distribution",
                 "12-week CLV (£)", "Customers")

    # ── Right: caterpillar plot for top-N ─────────────────────────────────────
    top_idx    = np.argsort(clv_mean)[-top_n:][::-1]
    top_mean   = clv_mean[top_idx]
    top_lower  = clv_lower[top_idx]
    top_upper  = clv_upper[top_idx]
    y_pos      = np.arange(top_n)

    axes[1].barh(y_pos, top_mean, color=PAL["bayesian"], alpha=0.7,
                 edgecolor="white", label="Mean CLV")
    axes[1].errorbar(
        top_mean, y_pos,
        xerr=[top_mean - top_lower, top_upper - top_mean],
        fmt="none", color=PAL["bayesian"], alpha=0.5, linewidth=1.5,
        capsize=3,
    )
    axes[1].set_yticks(y_pos)
    axes[1].set_yticklabels([f"C{i+1}" for i in range(top_n)], fontsize=8)
    axes[1].xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"£{x:.0f}")
    )
    _apply_style(axes[1], f"Top {top_n} Customers by Predicted CLV (90% CI)",
                 "12-week CLV (£)", "Customer rank")

    fig.tight_layout()
    return fig


def plot_clv_uncertainty(
    clv_posterior: np.ndarray,
    customers: pd.DataFrame,
) -> plt.Figure:
    """
    Coefficient of variation of CLV posterior vs frequency.
    High-frequency customers should have tighter posteriors (more data).
    """
    clv_mean = clv_posterior.mean(axis=0)
    clv_std  = clv_posterior.std(axis=0)
    cv       = clv_std / np.maximum(clv_mean, 1e-6)

    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(
        customers["frequency"].clip(upper=customers["frequency"].quantile(0.95)),
        cv,
        alpha=0.3, s=8, c=clv_mean,
        cmap="Blues", linewidths=0,
    )
    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("Mean CLV (£)", fontsize=9)
    _apply_style(ax, "CLV Uncertainty vs Frequency",
                 "Frequency (repeat purchases)",
                 "CLV Coefficient of Variation (σ/μ)")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# 7. COMPARISON PLOTS
# ──────────────────────────────────────────────────────────────────────────────

def plot_metrics_comparison(
    comparison_df: pd.DataFrame,
    metrics: List[str] = ["tx_mae", "tx_rmse", "tx_gini", "clv_gini"],
    lower_is_better: List[bool] = [True, True, False, False],
) -> plt.Figure:
    """
    Grouped bar chart comparing all models on multiple metrics.

    Parameters
    ----------
    comparison_df    : output of evaluation.compare_all_models()
    metrics          : metric column names to include
    lower_is_better  : for each metric, whether lower = better
                       (used to shade the best bar)
    """
    models  = comparison_df["model"].tolist()
    n_models  = len(models)
    n_metrics = len(metrics)

    fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 5))
    if n_metrics == 1:
        axes = [axes]

    for ax, metric, lib in zip(axes, metrics, lower_is_better):
        vals   = comparison_df[metric].values
        colors = [MODEL_COLORS.get(m, PAL["bayesian"]) for m in models]

        # Highlight the best model
        best_idx = np.argmin(vals) if lib else np.argmax(vals)
        alphas   = [0.9 if i == best_idx else 0.5 for i in range(n_models)]

        bars = ax.bar(range(n_models), vals, color=colors, alpha=1.0,
                      edgecolor="white", linewidth=0.5)
        for bar, alpha in zip(bars, alphas):
            bar.set_alpha(alpha)

        # Value labels on bars
        for i, (bar, val) in enumerate(zip(bars, vals)):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() * 1.02,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=8)

        ax.set_xticks(range(n_models))
        ax.set_xticklabels(models, rotation=25, ha="right", fontsize=8)
        metric_label = metric.replace("_", " ").upper()
        _apply_style(ax, metric_label, "", metric_label)

    fig.suptitle("Model Comparison", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return fig


def plot_hierarchical_segments(
    trace,
    segment_names: List[str],
    param: str = "r",
) -> plt.Figure:
    """
    Forest plot of a hierarchical parameter across country segments.
    Shows the posterior mean and 90% HDI per segment.
    """
    posterior = trace.posterior[param].values
    # Shape: (chains, draws, segments) → (total_draws, segments)
    draws = posterior.reshape(-1, len(segment_names))

    means  = draws.mean(axis=0)
    lowers = np.percentile(draws, 5,  axis=0)
    uppers = np.percentile(draws, 95, axis=0)

    order  = np.argsort(means)
    y_pos  = np.arange(len(segment_names))

    fig, ax = plt.subplots(figsize=(8, max(4, len(segment_names) * 0.5)))

    ax.errorbar(
        means[order], y_pos,
        xerr=[means[order] - lowers[order], uppers[order] - means[order]],
        fmt="o", color=PAL["bayesian"], ecolor=PAL["bayesian"],
        elinewidth=1.5, capsize=4, markersize=6,
    )
    ax.set_yticks(y_pos)
    ax.set_yticklabels([segment_names[i] for i in order], fontsize=9)
    ax.axvline(means.mean(), color=PAL["accent"], linestyle="--",
               linewidth=1.5, label="Global mean")
    ax.legend(fontsize=9)
    _apply_style(ax, f"Hierarchical {param.upper()} — Per-Segment Posterior (90% HDI)",
                 param, "Country Segment")
    fig.tight_layout()
    return fig


def plot_country_mae_comparison(
    country_metrics: pd.DataFrame,
    top_n: Optional[int] = None,
) -> plt.Figure:
    """
    Grouped bar chart of per-country MAE for each model (RQ2 / H2).

    Consumes evaluation.country_level_metrics(): expects a `country` column,
    an `n_customers` column, and one `MAE_<model>` column per model. Used to
    show whether the hierarchical model reduces error in specific (especially
    smaller) country segments relative to the pooled and classical models.
    """
    df = country_metrics.copy()
    if top_n is not None:
        df = df.head(top_n)

    mae_cols    = [c for c in df.columns if c.startswith("MAE_")]
    model_names = [c[len("MAE_"):] for c in mae_cols]

    fig, ax = plt.subplots(figsize=(max(8, len(df) * 1.2), 5.5))
    x = np.arange(len(df))
    width = 0.8 / max(1, len(mae_cols))

    for i, (col, name) in enumerate(zip(mae_cols, model_names)):
        offset = (i - len(mae_cols) / 2 + 0.5) * width
        ax.bar(x + offset, df[col].values, width,
               label=name, color=MODEL_COLORS.get(name, "#555555"),
               alpha=0.85, edgecolor="white", linewidth=0.5)

    labels = [f"{c}\n(n={n:,})" for c, n in zip(df["country"], df["n_customers"])]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.legend(fontsize=9)
    _apply_style(ax, "Prediction Error (MAE) by Country Segment", "", "MAE")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running plots smoke test with synthetic data...")
    np.random.seed(42)
    n = 500

    fake_customers = pd.DataFrame({
        "customer_id"    : range(n),
        "frequency"      : np.random.poisson(2, n),
        "recency"        : np.random.uniform(0, 40, n),
        "T"              : np.random.uniform(40, 52, n),
        "monetary_value" : np.random.gamma(2, 100, n),
        "country_segment": np.random.choice(["UK", "Germany", "France"], n),
    })
    fake_customers["recency"] = np.minimum(
        fake_customers["recency"], fake_customers["T"]
    )
    fake_customers.loc[fake_customers["frequency"] == 0, "monetary_value"] = 0.0

    y_true = np.random.poisson(2, n).astype(float)
    y_pred = y_true + np.random.normal(0, 0.8, n)
    posterior = np.random.poisson(2, (500, n)).astype(float)

    from evaluation import calibration_table, targeting_lift

    cal = calibration_table(y_true, y_pred)
    lift_df = targeting_lift(y_true, y_pred)

    figs = {
        "rfm_distributions"  : plot_rfm_distributions(fake_customers),
        "monetary_dist"      : plot_monetary_distribution(fake_customers),
        "recency_T"          : plot_recency_vs_T(fake_customers),
        "calibration"        : plot_calibration(cal, "Test Model"),
        "pred_vs_actual"     : plot_predicted_vs_actual(y_true, y_pred),
        "clv_dist"           : plot_clv_distribution(posterior),
        "clv_uncertainty"    : plot_clv_uncertainty(posterior, fake_customers),
    }

    for name, fig in figs.items():
        save_figure(fig, f"test_{name}")
        plt.close(fig)

    print("\n✓ All plots generated and saved to outputs/figures/")
