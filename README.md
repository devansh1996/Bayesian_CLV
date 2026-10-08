# Bayesian Customer Lifetime Value

Customer lifetime value prediction for a non-contractual retail setting, comparing a
Bayesian BG/NBD + Gamma-Gamma model against classical and machine-learning baselines.

In a shop there is no cancellation event, so whether a customer has stopped buying is
never observed. This repository implements a generative probabilistic treatment of that
problem, estimated with MCMC, and evaluates it on three questions: predictive accuracy,
whether its stated uncertainty is calibrated, and whether that uncertainty changes a
marketing decision.

Master's thesis code. Data is the public [UCI Online Retail II][uci] dataset — a UK
giftware retailer, December 2009 to December 2011, 4,522 customers after cleaning.

[uci]: https://archive.ics.uci.edu/dataset/502/online+retail+ii

## Findings

Evaluated out-of-sample on a 40.4-week holdout period beginning 1 March 2011, which no
model sees during fitting.

| | Transaction MAE | Top 100 correct | Top-decile revenue | Calibrated intervals |
| --- | --- | --- | --- | --- |
| **Bayesian BG/NBD + Gamma-Gamma** | **1.74** | **66 / 100** | **62.6%** | 89.3% at 90% nominal |
| XGBoost (two-stage, 24 features) | 2.12 | 49 / 100 | 57.9% | — |
| RFM heuristic | 2.33 | 37 / 100 | 55.1% | — |
| Naive (population mean) | 3.11 | 1 / 100 | 8.1% | — |

- **H1 — accuracy and calibration: supported.** The gain in average error is modest; the
  separation is in ranking, which is what a finite marketing budget actually consumes.
  Predictive intervals attain approximately nominal coverage.
- **H2 — hierarchical pooling across country segments: partially supported.** Partial
  pooling gives the lowest aggregated error on small segments (1.746 against 1.755 for no
  pooling and 1.757 for complete pooling) and is never worst in any segment. The gain is
  small, and the test is conditional on a deliberately tight between-segment prior.
- **H3 — decision-theoretic targeting: not supported.** Selecting on `P(CLV > threshold)`
  does not beat ranking by expected value, across 35 combinations of contact cost and
  campaign depth. This follows from the objective being linear in value, under which the
  posterior mean is sufficient.

A separate methodological result: computing `P(CLV > threshold)` from the posterior of the
expectation rather than the posterior predictive assigns 96% of customers a probability of
exactly 0 or 1, collapsing the ranking. In the targeting simulation this reduced the hit
rate from 0.848 to 0.619 and raised wasted spend from £55,040 to £144,738, with no
diagnostic signalling the error.

## Layout

```
src/
  data.py             ETL: load, clean, temporal split, customer aggregation
  priors.py           data-scaled weakly informative priors + prior predictive checks
  models.py           PyMC models — pooled BG/NBD, hierarchical BG/NBD, Gamma-Gamma
  baselines.py        naive, RFM heuristic, Pareto/NBD, two-stage XGBoost
  evaluation.py       MAE/RMSE/Gini/NDCG, calibration, targeting simulation
  extra_metrics.py    precision@k, value capture, stratified error, multi-level coverage
  plots.py            all figures
  run_all_models.py   orchestrates the eight pipeline steps
analysis/             standalone scripts for the H2 and H3 robustness checks
slides/               builders for the defence deck and its companion documents
notebooks/            exploratory analysis
outputs/
  results/            metric tables (csv)
  figures/            plots (png)
```

## Setup

Python 3.10–3.12 only; PyMC 5.x does not support 3.13+.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The raw dataset is not tracked here. Download `online_retail_II.xlsx` from the
[UCI repository][uci] and place it at `data/raw/online_retail_II.xlsx`.

## Running

All paths are relative to the repository root, so run from there.

```bash
python src/run_all_models.py              # full pipeline, fits MCMC (~30–60 min)
python src/run_all_models.py --skip-sampling   # reuse saved traces
python src/run_all_models.py --n-samples 500   # fewer posterior draws, faster predictions
python src/data.py                        # data pipeline only
```

Individual modules run standalone against synthetic data for a smoke test:

```bash
python src/models.py
python src/baselines.py
python src/evaluation.py
```

`run_all_models.main()` returns a dict of every intermediate artefact — traces,
predictions, evaluation results, targeting simulations, country-level metrics — so the
pipeline steps can be re-run individually from a notebook.

## Notes on the model

- `frequency` is repeat purchases (invoice count − 1), so one-time buyers have
  `frequency = 0`. `monetary_value` is mean revenue per *repeat* transaction, per the
  Gamma-Gamma convention; one-time buyers are assigned 0 and receive the population mean
  at prediction time.
- Time is in weeks throughout. Countries with fewer than 30 customers collapse into
  `"Other"`.
- The pooled BG/NBD and Gamma-Gamma models are fitted with `pymc-marketing`; the
  hierarchical model is implemented directly in PyMC with a non-centred parameterisation.
- Priors are half-normal with scales derived from calibration-period summary statistics
  (`src/priors.py`). Parameters carrying units require this: the Gamma-Gamma scale is
  denominated in pounds and must be of order hundreds, where a unit-ignorant prior places
  essentially all mass below 40.
- Sampling diagnostics are reported before any substantive result: R̂ ≤ 1.0014, minimum
  effective sample size ≈ 1,900 of 4,000 draws, zero divergent transitions.

## Limitations

Stated with the direction each pushes the estimate, since a limitation without one does
not tell a reader whether the number can be used.

- **Stationarity** is assumed and violated; this over-predicts mid-frequency customers by
  20–30%, while the upper deciles that drive allocation remain calibrated.
- **Independence of frequency and transaction value** is assumed and mildly violated
  (Pearson 0.13, Spearman 0.21). Because the correlation is positive, spend is
  under-predicted for the most frequent buyers, partially offsetting the stationarity bias
  rather than compounding it.
- **Scope** is a single retailer, single market, two-year window. The magnitudes are
  setting-specific; the argument about which predictive distribution a decision rule
  requires is general.
- **Wholesale purchasing sits inside a consumer specification** — the most active customer
  records 200 repeat transactions in 65 weeks, which is procurement rather than consumer
  behaviour. Flagged rather than excluded.

## Licence

See [LICENSE](LICENSE).
