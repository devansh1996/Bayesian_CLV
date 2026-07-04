"""
src/baselines.py
================
Non-Bayesian baseline models for CLV prediction.

Used to benchmark the BG/NBD + Gamma-Gamma models in the thesis.
All baselines share a common sklearn-style interface:

    model = SomeBaseline(**kwargs)
    model.fit(customers_train)
    predictions = model.predict(customers_test, t_future=13.0)

Baselines implemented
---------------------
    1. NaiveBaseline          — predict the training-period mean for everyone
    2. RFMHeuristicBaseline   — score customers on R, F, M then predict spend
    3. ParetoNBDBaseline      — MLE Pareto/NBD via lifetimes library (optional)
    4. XGBoostCLVBaseline     — gradient boosting on RFM + engineered features

Shared utilities
----------------
    engineer_features()       — builds the feature matrix used by XGBoost
    calibration_bin_targets() — creates observed-vs-predicted bins for plots
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import warnings


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING  (shared across baselines)
# ──────────────────────────────────────────────────────────────────────────────

def engineer_features(
    data: pd.DataFrame,
    cal_transactions: Optional[pd.DataFrame] = None,
    include_country: bool = True,
    segment_col: str = "country_segment",
) -> pd.DataFrame:
    """
    Build a feature matrix for ML-based baselines from RFM columns.

    Raw RFM captures the recent past; these derived features help the
    model pick up on non-linearities (e.g. customers who purchased very
    recently AND very often are more likely to be "hot").

    Features produced
    -----------------
    Core:
        frequency, recency, T, monetary_value

    Ratios / interactions:
        recency_ratio      : recency / T  — how recently did they last buy?
        purchase_rate      : frequency / T — purchases per week
        inter_purchase_time: T / (frequency + 1) — avg weeks between purchases
        monetary_log       : log1p(monetary_value) — de-skews the distribution

    Flags:
        is_repeat          : 1 if frequency > 0, else 0
        is_recent          : 1 if recency_ratio > 0.75 (bought in last quarter)
        high_value         : 1 if monetary_value > 75th percentile

    Country dummies (optional, one-hot encoded):
        country_seg_*      : one column per country segment

    Transaction-derived (only when `cal_transactions` is supplied and `data`
    has a `customer_id` column):
        ipt_mean, ipt_std  : inter-purchase-time mean / std (in days)
        dow_frac_*         : fraction of purchases on each day of week
        spend_trend        : late-vs-early revenue trend within the cal window

    Parameters
    ----------
    data            : customer-level DataFrame from aggregate_customers()
    cal_transactions: optional transaction-level calibration data (one row per
                      line item) used to derive inter-purchase-time and temporal
                      features. Must contain Customer ID, InvoiceDate, Revenue.
    include_country : whether to one-hot-encode the country_segment column
    segment_col     : column name for country segment

    Returns
    -------
    pd.DataFrame — feature matrix, same row order as input, no target columns
    """
    df = data.reset_index(drop=True).copy()

    # ── Core RFM ──────────────────────────────────────────────────────────────
    features = df[["frequency", "recency", "T", "monetary_value"]].copy()

    # ── Ratios ────────────────────────────────────────────────────────────────
    features["recency_ratio"]       = df["recency"] / df["T"].clip(lower=1e-6)
    features["purchase_rate"]       = df["frequency"] / df["T"].clip(lower=1e-6)
    features["inter_purchase_time"] = df["T"] / (df["frequency"] + 1)
    features["monetary_log"]        = np.log1p(df["monetary_value"])

    # ── Binary flags ─────────────────────────────────────────────────────────
    features["is_repeat"]  = (df["frequency"] > 0).astype(int)
    features["is_recent"]  = (features["recency_ratio"] > 0.75).astype(int)
    mv_75 = df["monetary_value"].quantile(0.75)
    features["high_value"] = (df["monetary_value"] > mv_75).astype(int)

    # ── Country dummies ───────────────────────────────────────────────────────
    if include_country and segment_col in df.columns:
        dummies = pd.get_dummies(
            df[segment_col], prefix="country_seg", drop_first=True
        ).astype(int)
        features = pd.concat([features, dummies], axis=1)

    # ── Transaction-derived features (optional) ───────────────────────────────
    # Inter-purchase-time and temporal (day-of-week / spend-trend) features
    # require the raw transaction stream. Merged on customer_id with a left join
    # so input row order is preserved; absent customers get 0 via fillna.
    if cal_transactions is not None and "customer_id" in df.columns:
        features["customer_id"] = df["customer_id"].values

        ipt = _compute_ipt_features(cal_transactions)
        features = features.merge(ipt, on="customer_id", how="left")

        temporal = _compute_temporal_features(cal_transactions)
        features = features.merge(temporal, on="customer_id", how="left")

        features = features.drop(columns=["customer_id"])

    return features.fillna(0).reset_index(drop=True)


def _compute_ipt_features(cal: pd.DataFrame) -> pd.DataFrame:
    """
    Inter-purchase-time statistics per customer (in days).

    Captures the regularity of a customer's buying rhythm, which RFM summary
    stats miss: two customers with the same frequency can have very different
    gap patterns (steady monthly buyer vs. one burst then silence).

    Returns
    -------
    pd.DataFrame with columns: customer_id, ipt_mean, ipt_std
    """
    results = []
    for cid, grp in cal.groupby("Customer ID"):
        dates = np.sort(grp["InvoiceDate"].unique())
        if len(dates) < 2:
            results.append({"customer_id": cid, "ipt_mean": 0.0, "ipt_std": 0.0})
            continue
        diffs = np.diff(dates).astype("timedelta64[D]").astype(float)
        results.append({
            "customer_id": cid,
            "ipt_mean"   : float(diffs.mean()),
            "ipt_std"    : float(diffs.std()) if len(diffs) > 1 else 0.0,
        })
    return pd.DataFrame(results, columns=["customer_id", "ipt_mean", "ipt_std"])


def _compute_temporal_features(cal: pd.DataFrame) -> pd.DataFrame:
    """
    Day-of-week purchase distribution and within-window spend trend per customer.

    - dow_frac_*  : fraction of a customer's purchases falling on each weekday.
                    Picks up routine (e.g. weekend) shoppers.
    - spend_trend : (late-quarter mean revenue − early-quarter mean revenue)
                    normalised by the early mean. Positive = accelerating spend.

    Returns
    -------
    pd.DataFrame with columns: customer_id, dow_frac_0..6 (as present), spend_trend
    """
    cal = cal.copy()
    cal["dow"] = cal["InvoiceDate"].dt.dayofweek

    # Fraction of purchases on each day of week
    dow_dist = (
        cal.groupby(["Customer ID", "dow"]).size()
        .unstack(fill_value=0)
        .div(cal.groupby("Customer ID").size(), axis=0)
    )
    dow_dist.columns = [f"dow_frac_{d}" for d in dow_dist.columns]

    # Spend trend: last-quarter mean revenue vs first-quarter mean revenue
    cal = cal.sort_values("InvoiceDate")
    trends = []
    for cid, grp in cal.groupby("Customer ID"):
        n = len(grp)
        if n < 4:
            trends.append({"Customer ID": cid, "spend_trend": 0.0})
            continue
        q = n // 4
        early = grp.iloc[:q]["Revenue"].mean()
        late  = grp.iloc[-q:]["Revenue"].mean()
        trends.append({"Customer ID": cid, "spend_trend": (late - early) / (early + 1e-6)})

    trend_df = pd.DataFrame(trends).set_index("Customer ID")

    features = dow_dist.join(trend_df, how="outer").reset_index()
    features = features.rename(columns={"Customer ID": "customer_id"})
    return features


# ──────────────────────────────────────────────────────────────────────────────
# BASE CLASS
# ──────────────────────────────────────────────────────────────────────────────

class BaseBaseline:
    """
    Shared interface for all baseline models.

    Subclasses must implement:
        fit(data)           : learn from calibration customers
        predict(data, t)    : return predicted transaction counts

    Optional override:
        predict_spend(data) : return predicted average spend per transaction
        predict_clv(data, t): return full CLV (transactions × spend)
    """

    name: str = "BaseBaseline"

    def fit(self, data: pd.DataFrame) -> "BaseBaseline":
        raise NotImplementedError

    def predict(self, data: pd.DataFrame, t_future: float) -> np.ndarray:
        raise NotImplementedError

    def predict_spend(self, data: pd.DataFrame) -> np.ndarray:
        """
        Default spend prediction: return per-customer monetary_value.
        Subclasses may override with a learned spend model.
        """
        return data["monetary_value"].values.copy()

    def predict_clv(self, data: pd.DataFrame, t_future: float) -> np.ndarray:
        """
        CLV = predicted transactions × predicted spend.
        """
        return self.predict(data, t_future) * self.predict_spend(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# ──────────────────────────────────────────────────────────────────────────────
# 1. NAIVE BASELINE
# ──────────────────────────────────────────────────────────────────────────────

class NaiveBaseline(BaseBaseline):
    """
    Predict the training-period mean transaction rate for every customer.

    This is the weakest possible benchmark — it completely ignores individual
    customer behaviour. Any useful model must beat it comfortably. It is
    included because:
        - It is trivially interpretable.
        - It gives a lower bound on expected performance.
        - It is a sanity check: if a model can't beat the mean, it is broken.

    Prediction
    ----------
        n_predicted = (mean_frequency / mean_T) × t_future

    The same scalar prediction is returned for all customers.
    """

    name = "Naive (mean)"

    def __init__(self):
        self.mean_rate_: Optional[float] = None
        self.mean_spend_: Optional[float] = None

    def fit(self, data: pd.DataFrame) -> "NaiveBaseline":
        # Rate = frequency per week, averaged across customers
        rates = data["frequency"] / data["T"].clip(lower=1e-6)
        self.mean_rate_  = float(rates.mean())

        # Mean spend from repeat purchasers only
        repeat = data[data["frequency"] > 0]["monetary_value"]
        self.mean_spend_ = float(repeat.mean()) if len(repeat) > 0 else 0.0

        print(f"NaiveBaseline fitted:")
        print(f"  Mean purchase rate:  {self.mean_rate_:.4f} purchases/week")
        print(f"  Mean spend:          £{self.mean_spend_:.2f}")
        return self

    def predict(self, data: pd.DataFrame, t_future: float) -> np.ndarray:
        if self.mean_rate_ is None:
            raise RuntimeError("Call fit() before predict()")
        return np.full(len(data), self.mean_rate_ * t_future)

    def predict_spend(self, data: pd.DataFrame) -> np.ndarray:
        if self.mean_spend_ is None:
            raise RuntimeError("Call fit() before predict_spend()")
        return np.full(len(data), self.mean_spend_)


# ──────────────────────────────────────────────────────────────────────────────
# 2. RFM HEURISTIC BASELINE
# ──────────────────────────────────────────────────────────────────────────────

class RFMHeuristicBaseline(BaseBaseline):
    """
    Score customers by Recency, Frequency, and Monetary quintiles,
    then use a simple weighted formula to predict future transactions.

    This mimics how RFM scoring is used in direct marketing:
        - High frequency → likely to buy again
        - High recency   → recently active, more likely to still be alive
        - High monetary  → higher-value customer

    The formula is:
        score = w_r × R_score + w_f × F_score + w_m × M_score   (out of 15)
        predicted_transactions = (score / 15) × (frequency / T) × t_future

    Where R, F, M scores are quintile ranks 1-5 (5 = best).

    This is a transparent, deterministic model that reflects common
    practitioner intuition. It makes no probabilistic claims.

    Parameters
    ----------
    n_bins    : number of quintile bins (default 5 for traditional RFM)
    weights   : (w_r, w_f, w_m) for the three dimensions (default equal)
    """

    name = "RFM Heuristic"

    def __init__(
        self,
        n_bins: int = 5,
        weights: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ):
        self.n_bins   = n_bins
        self.weights  = weights
        self.bin_edges_: Dict[str, np.ndarray] = {}
        self.base_rate_: Optional[float] = None

    def fit(self, data: pd.DataFrame) -> "RFMHeuristicBaseline":
        """
        Compute quintile bin edges from training data.

        Bin edges are stored so that test customers can be placed into the
        same bins (based on training distribution), not re-ranked.
        This is important for honest evaluation — you wouldn't have access
        to test data when building the scoring system.

        Note: recency is binned on the recency/T ratio (not raw weeks), since
        that is the quantity scored at prediction time — a ratio near 1 means
        the customer bought recently relative to their observation window.
        """
        recency_ratio = (
            data["recency"] / data["T"].clip(lower=1e-6)
        ).values

        for col, vals in [
            ("recency",        recency_ratio),
            ("frequency",      data["frequency"].values),
            ("monetary_value", data["monetary_value"].values),
        ]:
            quantiles = np.linspace(0, 100, self.n_bins + 1)
            edges = np.percentile(vals, quantiles)
            # Deduplicate edges (can happen when many customers share the same value)
            self.bin_edges_[col] = np.unique(edges)

        # Base rate: median frequency / T  (more robust to outliers than mean)
        self.base_rate_ = float(
            (data["frequency"] / data["T"].clip(lower=1e-6)).median()
        )

        print(f"RFMHeuristicBaseline fitted on {len(data):,} customers:")
        print(f"  Recency-ratio edges: {self.bin_edges_['recency'].round(3)}")
        print(f"  Frequency edges: {self.bin_edges_['frequency'].round(1)}")
        print(f"  Monetary edges:  {self.bin_edges_['monetary_value'].round(0)}")
        return self

    def _score_column(self, values: np.ndarray, col: str, higher_is_better: bool = True) -> np.ndarray:
        """Assign a 1..n_bins score to each value based on stored bin edges."""
        edges = self.bin_edges_[col]
        # np.searchsorted returns the bucket index (0-indexed, clipped to n_bins)
        scores = np.searchsorted(edges, values, side="left")
        scores = np.clip(scores, 1, self.n_bins)
        if not higher_is_better:
            scores = self.n_bins + 1 - scores  # invert so 5 = best
        return scores.astype(float)

    def _rfm_scores(self, data: pd.DataFrame) -> np.ndarray:
        """
        Compute weighted RFM composite score for each customer.

        Recency: lower recency (bought longer ago) → lower score.
            But note: in BG/NBD, *higher* recency (last purchase was more
            recent) means they might still be alive. So higher recency = better.
        Frequency: higher = better.
        Monetary:  higher = better.
        """
        w_r, w_f, w_m = self.weights

        # Recency: higher recency_ratio is better (bought recently)
        recency_ratio = data["recency"] / data["T"].clip(lower=1e-6)
        r_score = self._score_column(recency_ratio.values, "recency", higher_is_better=True)
        f_score = self._score_column(data["frequency"].values, "frequency", higher_is_better=True)
        m_score = self._score_column(data["monetary_value"].values, "monetary_value", higher_is_better=True)

        composite = w_r * r_score + w_f * f_score + w_m * m_score
        max_score = sum(self.weights) * self.n_bins
        return composite / max_score   # normalise to [0, 1]

    def predict(self, data: pd.DataFrame, t_future: float) -> np.ndarray:
        """
        Predicted transactions = score × base_rate × t_future.

        Customers with a score of 1.0 (best quintile on all dimensions)
        get the base rate; lower-scoring customers get a fraction of it.
        """
        if not self.bin_edges_:
            raise RuntimeError("Call fit() before predict()")
        scores = self._rfm_scores(data)
        return scores * self.base_rate_ * t_future

    def get_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Return a DataFrame with individual R, F, M scores and composite score.
        Useful for exploratory analysis and thesis write-up.
        """
        w_r, w_f, w_m = self.weights
        recency_ratio = data["recency"] / data["T"].clip(lower=1e-6)

        r_score = self._score_column(recency_ratio.values, "recency", higher_is_better=True)
        f_score = self._score_column(data["frequency"].values, "frequency", higher_is_better=True)
        m_score = self._score_column(data["monetary_value"].values, "monetary_value", higher_is_better=True)

        composite = (w_r * r_score + w_f * f_score + w_m * m_score) / (sum(self.weights) * self.n_bins)

        return pd.DataFrame({
            "R_score"        : r_score,
            "F_score"        : f_score,
            "M_score"        : m_score,
            "composite_score": composite,
        }, index=data.index)


# ──────────────────────────────────────────────────────────────────────────────
# 3. PARETO/NBD BASELINE  (optional — requires lifetimes library)
# ──────────────────────────────────────────────────────────────────────────────

class ParetoNBDBaseline(BaseBaseline):
    """
    Maximum-likelihood Pareto/NBD model via the lifetimes library.

    The Pareto/NBD (Schmittlein et al. 1987) is the predecessor to BG/NBD.
    It assumes a continuous-time dropout process (exponential lifetime)
    rather than BG/NBD's discrete dropout-after-purchase. Both models
    have similar empirical performance; BG/NBD is more tractable.

    This baseline lets the thesis directly compare the Bayesian BG/NBD
    against its MLE Pareto/NBD competitor.

    Requires: pip install lifetimes

    Parameters
    ----------
    penalizer_coef : L2 regularization on the log-parameters (default 0.0)
    """

    name = "Pareto/NBD (MLE)"

    def __init__(self, penalizer_coef: float = 0.0):
        self.penalizer_coef = penalizer_coef
        self._model = None

    def fit(self, data: pd.DataFrame) -> "ParetoNBDBaseline":
        try:
            from lifetimes import ParetoNBDFitter
        except ImportError:
            raise ImportError(
                "The lifetimes library is required for ParetoNBDBaseline.\n"
                "Install it with: pip install lifetimes"
            )

        self._model = ParetoNBDFitter(penalizer_coef=self.penalizer_coef)
        self._model.fit(
            data["frequency"],
            data["recency"],
            data["T"],
        )
        print(f"ParetoNBDBaseline fitted:")
        print(self._model.summary)
        return self

    def predict(self, data: pd.DataFrame, t_future: float) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("Call fit() before predict()")
        preds = self._model.conditional_expected_number_of_purchases_up_to_time(
            t_future,
            data["frequency"],
            data["recency"],
            data["T"],
        )
        return preds.values


# ──────────────────────────────────────────────────────────────────────────────
# 4. XGBOOST CLV BASELINE
# ──────────────────────────────────────────────────────────────────────────────

class XGBoostCLVBaseline(BaseBaseline):
    """
    Gradient-boosted trees (XGBoost) for CLV prediction.

    XGBoost is the strongest non-probabilistic baseline — it can capture
    non-linear interactions between RFM features that linear models miss.
    It does NOT produce uncertainty estimates, which is a key advantage
    of the Bayesian approach.

    Two separate models are trained:
        1. A transaction model  → predicts holdout transaction count
        2. A spend model        → predicts mean transaction value (repeat only)

    The CLV prediction is their product:
        CLV = pred_transactions × pred_spend

    This two-stage design mirrors the BG/NBD + Gamma-Gamma structure,
    making the comparison between Bayesian and ML approaches cleaner.

    Parameters
    ----------
    n_estimators  : number of trees (default 300)
    max_depth     : max tree depth (default 4 — shallow trees generalise better)
    learning_rate : step size (default 0.05)
    subsample     : row subsampling ratio per tree (default 0.8)
    colsample     : feature subsampling ratio per tree (default 0.8)
    random_seed   : reproducibility seed
    xgb_params    : optional dict to override all XGBoost parameters directly
    """

    name = "XGBoost (two-stage)"

    def __init__(
        self,
        n_estimators:  int   = 300,
        max_depth:     int   = 4,
        learning_rate: float = 0.05,
        subsample:     float = 0.8,
        colsample:     float = 0.8,
        random_seed:   int   = 42,
        xgb_params:    Optional[Dict[str, Any]] = None,
    ):
        self.n_estimators  = n_estimators
        self.max_depth     = max_depth
        self.learning_rate = learning_rate
        self.subsample     = subsample
        self.colsample     = colsample
        self.random_seed   = random_seed
        self.xgb_params    = xgb_params

        self._tx_model    = None
        self._spend_model = None
        self._feature_cols: Optional[list] = None
        self._cal_transactions: Optional[pd.DataFrame] = None
        self.trained_horizon_: Optional[float] = None

    def _get_xgb_params(self) -> Dict[str, Any]:
        """Return XGBoost parameters, using defaults or user overrides."""
        defaults = {
            "n_estimators"         : self.n_estimators,
            "max_depth"            : self.max_depth,
            "learning_rate"        : self.learning_rate,
            "subsample"            : self.subsample,
            "colsample_bytree"     : self.colsample,
            "objective"            : "reg:squarederror",
            "eval_metric"          : "rmse",
            "random_state"         : self.random_seed,
            "n_jobs"               : -1,
            "early_stopping_rounds": None,
        }
        if self.xgb_params:
            defaults.update(self.xgb_params)
        return defaults

    def fit(
        self,
        data: pd.DataFrame,
        holdout_truth: pd.DataFrame,
        cal_transactions: Optional[pd.DataFrame] = None,
        eval_frac: float = 0.15,
        target_horizon_weeks: Optional[float] = None,
    ) -> "XGBoostCLVBaseline":
        """
        Fit both the transaction and spend XGBoost models.

        IMPORTANT — leakage: the supervision targets in `holdout_truth` must
        come from a window that is *disjoint from the evaluation holdout*
        (e.g. the inner split produced by data.build_inner_training_set()).
        Training on the evaluation holdout makes the model's metrics
        in-sample and invalidates any comparison against unsupervised models.

        Parameters
        ----------
        data            : customer-level DataFrame for the training window
        holdout_truth   : ground-truth DataFrame from compute_holdout_truth()
                          must contain: customer_id, holdout_transactions, holdout_spend
        cal_transactions: optional transaction-level data for the training window;
                          when given, inter-purchase-time and temporal features are
                          added. Stored so predict()/predict_spend() reuse the same
                          stream unless set_prediction_transactions() is called.
        eval_frac       : fraction of training data held back for early stopping
        target_horizon_weeks : length (weeks) of the window the targets cover.
                          Stored as `trained_horizon_` so predict() can rescale
                          transaction counts to a different prediction horizon.
        """
        try:
            from xgboost import XGBRegressor
            from sklearn.model_selection import train_test_split
        except ImportError:
            raise ImportError(
                "XGBoost and scikit-learn are required for XGBoostCLVBaseline.\n"
                "Install with: pip install xgboost scikit-learn"
            )

        # ── Merge features with targets ───────────────────────────────────────
        self._cal_transactions = cal_transactions
        self.trained_horizon_  = target_horizon_weeks
        X_full = engineer_features(data, cal_transactions)
        self._feature_cols = list(X_full.columns)

        merged = data[["customer_id"]].copy().reset_index(drop=True)
        merged = merged.merge(holdout_truth, on="customer_id", how="left")
        merged["holdout_transactions"] = merged["holdout_transactions"].fillna(0)
        merged["holdout_spend"]        = merged["holdout_spend"].fillna(0.0)

        y_tx    = merged["holdout_transactions"].values.astype(float)
        y_spend = merged["holdout_spend"].values.astype(float)

        # ── Transaction model ─────────────────────────────────────────────────
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_full, y_tx,
            test_size   = eval_frac,
            random_state = self.random_seed,
        )

        params = self._get_xgb_params()
        params["early_stopping_rounds"] = 30

        self._tx_model = XGBRegressor(**params)
        self._tx_model.fit(
            X_tr, y_tr,
            eval_set       = [(X_val, y_val)],
            verbose        = False,
        )

        tx_train_preds = self._tx_model.predict(X_full)
        tx_rmse = np.sqrt(np.mean((tx_train_preds - y_tx) ** 2))

        # ── Spend model (repeat customers only) ───────────────────────────────
        # Use holdout spend / holdout transactions as the per-transaction spend
        # target. Only include customers with at least one holdout transaction.
        repeat_mask = (
            (data["frequency"].values > 0) &
            (merged["holdout_transactions"].values > 0)
        )

        if repeat_mask.sum() < 50:
            warnings.warn(
                f"Only {repeat_mask.sum()} customers have repeat calibration AND "
                "holdout transactions. Spend model may be unreliable.",
                UserWarning,
            )

        X_spend = X_full[repeat_mask]
        y_spend_per_tx = (
            merged["holdout_spend"].values[repeat_mask] /
            merged["holdout_transactions"].values[repeat_mask].clip(min=1)
        )

        X_sp_tr, X_sp_val, y_sp_tr, y_sp_val = train_test_split(
            X_spend, y_spend_per_tx,
            test_size    = eval_frac,
            random_state = self.random_seed,
        )

        self._spend_model = XGBRegressor(**params)
        self._spend_model.fit(
            X_sp_tr, y_sp_tr,
            eval_set       = [(X_sp_val, y_sp_val)],
            verbose        = False,
        )

        sp_preds = self._spend_model.predict(X_spend)
        sp_rmse  = np.sqrt(np.mean((sp_preds - y_spend_per_tx) ** 2))

        print(f"\nXGBoostCLVBaseline fitted:")
        print(f"  Training customers:  {len(data):,}")
        print(f"  Repeat (spend model):{repeat_mask.sum():,}")
        print(f"  Tx model train RMSE: {tx_rmse:.4f}")
        print(f"  Spend model RMSE:    £{sp_rmse:.2f}")
        print(f"  Features used:       {self._feature_cols}")

        return self

    def set_prediction_transactions(self, transactions: pd.DataFrame) -> None:
        """
        Swap the transaction stream used to build features at prediction time.

        When the model is trained on an inner temporal split, its stored
        stream only covers the inner window. Before predicting for the full
        calibration customers, pass the full calibration stream here so the
        IPT/temporal features are computed from the same window as the RFM
        features in the prediction table.
        """
        self._cal_transactions = transactions

    def predict(self, data: pd.DataFrame, t_future: float = 1.0) -> np.ndarray:
        """
        Predict transaction counts over a horizon of `t_future` weeks.

        XGBoost predicts a raw count over the window it was trained on
        (`trained_horizon_` weeks). When that horizon is known, predictions
        are linearly rescaled by t_future / trained_horizon_. This is a
        simplification — unlike BG/NBD, XGBoost doesn't model the rate
        directly — but keeps horizons comparable across models. If
        trained_horizon_ was not provided at fit time, the raw count is
        returned unscaled.
        """
        if self._tx_model is None:
            raise RuntimeError("Call fit() before predict()")
        X = engineer_features(data, self._cal_transactions).reindex(
            columns=self._feature_cols, fill_value=0
        )
        raw = np.maximum(self._tx_model.predict(X), 0.0)
        if self.trained_horizon_ is not None and self.trained_horizon_ > 0:
            raw = raw * (t_future / self.trained_horizon_)
        return raw

    def predict_spend(self, data: pd.DataFrame) -> np.ndarray:
        if self._spend_model is None:
            raise RuntimeError("Call fit() before predict_spend()")
        X = engineer_features(data, self._cal_transactions).reindex(
            columns=self._feature_cols, fill_value=0
        )
        raw = self._spend_model.predict(X)
        return np.maximum(raw, 0.0)

    def feature_importance(self) -> pd.DataFrame:
        """
        Return a DataFrame of feature importances from the transaction model.
        Useful for the thesis discussion section.
        """
        if self._tx_model is None:
            raise RuntimeError("Call fit() before feature_importance()")
        importance = self._tx_model.feature_importances_
        return (
            pd.DataFrame({
                "feature"   : self._feature_cols,
                "importance": importance,
            })
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )


# ──────────────────────────────────────────────────────────────────────────────
# CALIBRATION UTILITY
# ──────────────────────────────────────────────────────────────────────────────

def calibration_bin_targets(
    predictions: np.ndarray,
    actuals: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """
    Bin customers by predicted transactions and compute mean predicted vs
    mean actual per bin.

    This produces the data for the standard "calibration plot" used to
    assess model fit: if predicted ≈ actual at all points, the model is
    well-calibrated. Systematic over/under-prediction in specific bins
    reveals where the model struggles.

    Parameters
    ----------
    predictions : predicted transaction counts (1D array, n_customers)
    actuals     : actual transaction counts (1D array, n_customers)
    n_bins      : number of bins (default 10 deciles)

    Returns
    -------
    pd.DataFrame with columns:
        bin              : bin number (1 = lowest predictions)
        mean_predicted   : mean predicted transactions in bin
        mean_actual      : mean actual transactions in bin
        n_customers      : number of customers in bin
        pred_lower       : 10th percentile of predictions in bin
        pred_upper       : 90th percentile of predictions in bin
    """
    df = pd.DataFrame({"pred": predictions, "actual": actuals})
    df["bin"] = pd.qcut(df["pred"], q=n_bins, labels=False, duplicates="drop") + 1

    result = (
        df.groupby("bin")
        .agg(
            mean_predicted = ("pred",   "mean"),
            mean_actual    = ("actual", "mean"),
            n_customers    = ("pred",   "count"),
            pred_lower     = ("pred",   lambda x: np.percentile(x, 10)),
            pred_upper     = ("pred",   lambda x: np.percentile(x, 90)),
        )
        .reset_index()
    )
    return result


# ──────────────────────────────────────────────────────────────────────────────
# CONVENIENCE: FIT ALL BASELINES AT ONCE
# ──────────────────────────────────────────────────────────────────────────────

def fit_all_baselines(
    customers: pd.DataFrame,
    holdout_truth: pd.DataFrame,
    cal_transactions: Optional[pd.DataFrame] = None,
    include_pareto: bool = False,
    xgb_train: Optional[Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[float]]] = None,
) -> Dict[str, BaseBaseline]:
    """
    Fit all baselines and return them in a dict keyed by name.

    Parameters
    ----------
    customers       : calibration customer DataFrame
    holdout_truth   : ground-truth from compute_holdout_truth()
    cal_transactions: optional transaction-level calibration data, passed to the
                      XGBoost baseline to enable IPT / temporal features
    include_pareto  : whether to fit the Pareto/NBD model (requires lifetimes)
    xgb_train       : optional (customers, truth, transactions, horizon_weeks)
                      tuple from data.build_inner_training_set(). When given,
                      XGBoost trains on this leakage-free inner split instead of
                      the evaluation holdout, and its prediction-time feature
                      stream is reset to `cal_transactions`.

    Returns
    -------
    dict : {model_name: fitted_model}

    Example
    -------
        inner = build_inner_training_set(cal)
        baselines = fit_all_baselines(customers, truth,
                                      cal_transactions=cal, xgb_train=inner)
        for name, model in baselines.items():
            preds = model.predict(customers, t_future=13.0)
            print(f"{name}: {preds.mean():.3f}")
    """
    fitted = {}

    print("\n── Fitting NaiveBaseline ──")
    nb = NaiveBaseline()
    nb.fit(customers)
    fitted[nb.name] = nb

    print("\n── Fitting RFMHeuristicBaseline ──")
    rfm = RFMHeuristicBaseline()
    rfm.fit(customers)
    fitted[rfm.name] = rfm

    print("\n── Fitting XGBoostCLVBaseline ──")
    xgb = XGBoostCLVBaseline()
    if xgb_train is not None:
        # Leakage-free path: train on the inner temporal split, then point the
        # feature stream at the full calibration window for prediction.
        inner_customers, inner_truth, inner_tx, inner_horizon = xgb_train
        print(f"  Training on inner split: {len(inner_customers):,} customers, "
              f"target horizon {inner_horizon:.1f} weeks (evaluation holdout unseen)")
        xgb.fit(
            inner_customers, inner_truth,
            cal_transactions=inner_tx,
            target_horizon_weeks=inner_horizon,
        )
        if cal_transactions is not None:
            xgb.set_prediction_transactions(cal_transactions)
    else:
        warnings.warn(
            "XGBoost is training on the evaluation holdout (no xgb_train "
            "given) — its metrics will be in-sample. Pass an inner training "
            "set from data.build_inner_training_set() for a fair comparison.",
            UserWarning,
        )
        xgb.fit(customers, holdout_truth, cal_transactions=cal_transactions)
    fitted[xgb.name] = xgb

    if include_pareto:
        print("\n── Fitting ParetoNBDBaseline ──")
        try:
            pnbd = ParetoNBDBaseline()
            pnbd.fit(customers)
            fitted[pnbd.name] = pnbd
        except ImportError as e:
            print(f"  Skipping Pareto/NBD: {e}")

    print(f"\n✓ Fitted {len(fitted)} baselines: {list(fitted.keys())}")
    return fitted


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Running smoke test with synthetic data...")
    np.random.seed(42)
    n = 500

    fake_customers = pd.DataFrame({
        "customer_id"    : range(n),
        "frequency"      : np.random.poisson(2, n),
        "recency"        : np.random.uniform(0, 40, n),
        "T"              : np.random.uniform(40, 52, n),
        "monetary_value" : np.random.gamma(2, 100, n),
        "country_segment": np.random.choice(["UK", "Germany", "France", "Other"], n),
    })
    fake_customers["recency"] = np.minimum(
        fake_customers["recency"], fake_customers["T"]
    )
    fake_customers.loc[fake_customers["frequency"] == 0, "monetary_value"] = 0.0

    fake_truth = pd.DataFrame({
        "customer_id"         : range(n),
        "holdout_transactions": np.random.poisson(1.5, n),
        "holdout_spend"       : np.random.gamma(2, 150, n),
        "is_active"           : np.random.binomial(1, 0.6, n),
    })

    # Synthetic transaction stream for IPT / temporal features
    tx_rows = []
    for cid in range(n):
        n_pur = int(fake_customers.loc[cid, "frequency"]) + 1
        dates = pd.date_range("2010-01-04", periods=n_pur, freq="9D")
        for d in dates:
            tx_rows.append({
                "Customer ID": cid,
                "InvoiceDate": d,
                "Revenue"    : float(np.random.gamma(2, 50)),
            })
    fake_tx = pd.DataFrame(tx_rows)

    X = engineer_features(fake_customers, fake_tx)
    print(f"Features: {list(X.columns)}")
    print(f"Shape: {X.shape}")

    baselines = fit_all_baselines(fake_customers, fake_truth, cal_transactions=fake_tx)
    for name, model in baselines.items():
        preds = model.predict(fake_customers, t_future=13.0)
        clv   = model.predict_clv(fake_customers, t_future=13.0)
        print(f"\n{name}:")
        print(f"  Mean predicted transactions: {preds.mean():.3f}")
        print(f"  Mean predicted CLV:          £{clv.mean():.2f}")

    print("\n✓ All baselines passed smoke test")