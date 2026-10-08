"""Additional metrics that separate the models more sharply than MAE/RMSE.

Run:  ~/.venvs/bayesclv/bin/python src/extra_metrics.py
Reads saved traces (no MCMC) and writes outputs/results/extra_metrics*.csv
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from scipy.stats import kendalltau

from src.run_all_models import main as run_pipeline


# ─────────────────────────────── new metrics ───────────────────────────────
def precision_at_k(y_true, y_pred, k):
    """Of the k customers we picked, how many belong in the true top k?"""
    k = min(k, len(y_true))
    top_pred = set(np.argsort(y_pred)[::-1][:k])
    top_true = set(np.argsort(y_true)[::-1][:k])
    return len(top_pred & top_true) / k


def value_capture(y_true, y_pred, frac=0.10):
    """Share of ALL realised value sitting in the top `frac` we selected.
    1.0 would mean the top decile we chose holds every pound there is."""
    n = max(1, int(round(frac * len(y_true))))
    sel = np.argsort(y_pred)[::-1][:n]
    tot = y_true.sum()
    return float(y_true[sel].sum() / tot) if tot > 0 else np.nan


def value_capture_ratio(y_true, y_pred, frac=0.10):
    """Same, as a share of the best achievable — so 1.0 is a perfect ranking."""
    n = max(1, int(round(frac * len(y_true))))
    best = np.sort(y_true)[::-1][:n].sum()
    sel = np.argsort(y_pred)[::-1][:n]
    return float(y_true[sel].sum() / best) if best > 0 else np.nan


def brier(y_true_bin, p):
    return float(np.mean((p - y_true_bin) ** 2))


def log_loss(y_true_bin, p, eps=1e-12):
    p = np.clip(p, eps, 1 - eps)
    return float(-np.mean(y_true_bin * np.log(p) + (1 - y_true_bin) * np.log(1 - p)))


def mae_by_stratum(y_true, y_pred, freq):
    """Where does the advantage actually live? Split by how much history exists."""
    bands = [("0 (one-time)", freq == 0), ("1–2", (freq >= 1) & (freq <= 2)),
             ("3–5", (freq >= 3) & (freq <= 5)), ("6+", freq >= 6)]
    out = {}
    for name, m in bands:
        out[name] = float(np.mean(np.abs(y_true[m] - y_pred[m]))) if m.sum() else np.nan
    return out


# ─────────────────────────────── driver ───────────────────────────────
CACHE = "outputs/results/_extra_metrics_cache.npz"

def _load_or_run():
    """Pipeline predictions are deterministic given the saved traces, so cache them."""
    if os.path.exists(CACHE):
        z = np.load(CACHE, allow_pickle=True)
        print(">>> using cached predictions (%s) — delete it to recompute" % CACHE)
        return z["payload"].item()
    sys.argv = ["run_all_models.py", "--skip-sampling", "--n-samples", "1000"]
    art = run_pipeline()
    payload = {
        "customers": art["customers"].reset_index(drop=True),
        "truth": art["truth"],
        "preds": {k: {kk: np.asarray(vv) for kk, vv in v.items() if vv is not None}
                  for k, v in list(art["bayesian_preds"].items()) + list(art["baseline_preds"].items())
                  if isinstance(v, dict)},
    }
    np.savez_compressed(CACHE, payload=np.array(payload, dtype=object))
    return payload


def main():
    art = _load_or_run()

    customers = art["customers"].reset_index(drop=True)
    truth = art["truth"].set_index("customer_id").reindex(customers["customer_id"]).reset_index()
    preds_all = art["preds"]
    freq = customers["frequency"].to_numpy()
    y_tx = truth["holdout_transactions"].to_numpy(float)
    y_clv = truth["holdout_spend"].to_numpy(float)
    alive = truth["is_active"].to_numpy(float)

    preds = preds_all

    rows, strat_rows, cov_rows = [], [], []
    for name, d in preds.items():
        if not isinstance(d, dict):
            continue
        tx = d.get("tx_mean"); clv = d.get("clv_mean")
        if tx is None or clv is None:
            print("    (skipping %s — no tx_mean/clv_mean)" % name); continue
        tx, clv = np.asarray(tx, float).ravel(), np.asarray(clv, float).ravel()
        r = {"model": name,
             "precision_at_100": precision_at_k(y_clv, clv, 100),
             "precision_at_500": precision_at_k(y_clv, clv, 500),
             "value_capture_top10pct": value_capture(y_clv, clv, 0.10),
             "value_capture_ratio_top10pct": value_capture_ratio(y_clv, clv, 0.10),
             "kendall_tau_tx": float(kendalltau(y_tx, tx).correlation)}
        pa = d.get("p_alive")
        if pa is not None:
            pa = np.asarray(pa, float).ravel()
            rep = freq > 0            # BG/NBD gives freq==0 customers P(alive)=1 by construction
            r["brier_p_alive_rep"] = brier(alive[rep], pa[rep])
            r["logloss_p_alive_rep"] = log_loss(alive[rep], pa[rep])
        rows.append(r)
        st = mae_by_stratum(y_tx, tx, freq); st["model"] = name
        strat_rows.append(st)

        # coverage at several nominal levels — one level can look right by luck
        pp = d.get("tx_predictive")
        if pp is not None:
            pp = np.asarray(pp, float)
            if pp.ndim == 2 and pp.shape[1] != len(y_tx) and pp.shape[0] == len(y_tx):
                pp = pp.T                                  # want (draws, customers)
            if pp.ndim == 2 and pp.shape[1] == len(y_tx):
                row = {"model": name}
                for lvl in (50, 80, 90, 95):
                    a = (100 - lvl) / 2.0
                    lo = np.percentile(pp, a, axis=0)
                    hi = np.percentile(pp, 100 - a, axis=0)
                    row["cov_%d" % lvl] = float(np.mean((y_tx >= lo) & (y_tx <= hi)))
                    row["width_%d" % lvl] = float(np.mean(hi - lo))
                cov_rows.append(row)

    extra = pd.DataFrame(rows).sort_values("precision_at_100", ascending=False)
    strat = pd.DataFrame(strat_rows).set_index("model")

    # how many customers sit in each band — context for the stratified table
    counts = {"0 (one-time)": int((freq == 0).sum()), "1–2": int(((freq >= 1) & (freq <= 2)).sum()),
              "3–5": int(((freq >= 3) & (freq <= 5)).sum()), "6+": int((freq >= 6).sum())}

    os.makedirs("outputs/results", exist_ok=True)
    extra.to_csv("outputs/results/extra_metrics.csv", index=False)
    strat.to_csv("outputs/results/extra_metrics_by_frequency.csv")
    cov = pd.DataFrame(cov_rows)
    if len(cov):
        cov.to_csv("outputs/results/extra_metrics_coverage_levels.csv", index=False)

    pd.set_option("display.width", 200)
    print("\n" + "=" * 78)
    print("ADDITIONAL DISCRIMINATING METRICS")
    print("=" * 78)
    print(extra.round(4).to_string(index=False))
    print("\nTransaction MAE split by how much history the customer has")
    print("(customers per band: %s)" % counts)
    print(strat.round(4).to_string())
    if len(cov):
        print("\nInterval honesty at several nominal levels (transactions)")
        print(cov.round(4).to_string(index=False))
    print("\nwritten: outputs/results/extra_metrics*.csv")


if __name__ == "__main__":
    main()
