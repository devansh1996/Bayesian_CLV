# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Thesis project implementing Bayesian Customer Lifetime Value (CLV) models on the UCI Online Retail II dataset. The goal is to compare Bayesian BG/NBD + Gamma-Gamma models against classical baselines (Naive, RFM heuristic, XGBoost) for transaction and CLV prediction.

The codebase is organized around three thesis research questions, and many functions are tagged with these labels in comments/docstrings:
- **RQ1** — predictive accuracy of Bayesian vs. classical models (the core comparison table).
- **RQ2 / H2** — does hierarchical (per-country) pooling improve country-level accuracy? (`build_hierarchical_bgnbd`, country-level MAE in `evaluation.py`).
- **RQ3 / H3** — decision-theoretic value: targeting simulation comparing models on a marketing-spend decision (`targeting_simulation` in `evaluation.py`).

## Environment setup

**Python 3.10–3.12 only** — PyMC 5.x is not compatible with 3.13+.

```bash
# WSL/Ubuntu one-time setup
sudo apt update && sudo apt install -y build-essential python3-dev libhdf5-dev libnetcdf-dev python3-venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

All commands below assume the `.venv` is activated **and that you run from the repo root** — every path in the code is relative to the working directory (e.g. `data/raw/...`, `outputs/...`), and `run_all_models.py` does `sys.path.insert(0, <repo root>)` and imports as `from src.data import ...`.

## Common commands

```bash
# Run the full 8-step pipeline (fits MCMC, ~30–60 min)
python src/run_all_models.py

# Skip MCMC and load previously saved traces
python src/run_all_models.py --skip-sampling

# Force data re-run even if processed parquet files exist
python src/run_all_models.py --force-data

# Faster prediction pass (fewer posterior draws)
python src/run_all_models.py --n-samples 500

# Run only the data pipeline
python src/data.py

# Smoke-test individual modules (synthetic data, no MCMC)
python src/models.py
python src/baselines.py
python src/evaluation.py

# Exploratory notebook
jupyter lab
```

## Architecture

### Data flow

```
data/raw/online_retail_II.xlsx
    └─ src/data.py: load_raw() → clean_transactions() → temporal_split()
                    → aggregate_customers() → collapse_countries()
                    → compute_holdout_truth()
    └─ data/processed/*.parquet  (cal, holdout, customers, truth)

customers.parquet (one row per customer, calibration window only)
    ├─ src/models.py  → MCMC traces → outputs/traces/*.nc
    ├─ src/baselines.py → fitted baseline objects
    └─ src/evaluation.py → metrics, calibration tables, lift

outputs/
    ├─ traces/    — ArviZ InferenceData as NetCDF (.nc)
    ├─ results/   — CSV + LaTeX tables for thesis
    └─ figures/   — PNG plots for thesis
```

### Module responsibilities

- **`src/data.py`** — Full ETL. `run_pipeline()` is the single entry point; `load_processed()` skips re-processing when parquet files already exist. The calibration/holdout split date is `CAL_END = "2011-03-01"` (global constant).

- **`src/models.py`** — Three PyMC models: `build_bgnbd()` (pooled), `build_hierarchical_bgnbd()` (per country segment, non-centered parameterization), `build_gamma_gamma()` (monetary value, repeat purchasers only). `fit_model()` runs NUTS and saves traces as `.nc`. Prediction functions (`predict_conditional_transactions`, `predict_monetary_value`, `compute_clv_posterior`, `predict_p_alive`) work directly on ArviZ `InferenceData` objects.

- **`src/baselines.py`** — sklearn-style interface (`fit` / `predict` / `predict_clv`). Four models: `NaiveBaseline`, `RFMHeuristicBaseline`, `ParetoNBDBaseline` (requires optional `lifetimes` package), `XGBoostCLVBaseline` (two-stage: separate transaction and spend models). `fit_all_baselines()` fits all three standard baselines at once.

- **`src/evaluation.py`** — `evaluate_model()` runs the full suite (MAE/RMSE/Gini/NDCG, calibration table, targeting lift, P(alive) classification). `compare_all_models()` produces the thesis comparison table (RQ1). Bayesian-specific: `compute_posterior_metrics()` adds CRPS and credible interval coverage. RQ2/RQ3 live here too: `targeting_simulation()` (decision-theoretic targeting, swept over cost assumptions for robustness) and the per-country MAE evaluation.

- **`src/plots.py`** — All figures return `matplotlib.Figure`. `save_figure()` writes to `outputs/figures/`. Consistent color palette in `MODEL_COLORS` and `PAL` dicts.

- **`src/run_all_models.py`** — Orchestrates the 8 pipeline steps. Each step is a standalone function (`step_data`, `step_bayesian`, `step_bayesian_predictions`, `step_baselines`, `step_evaluate`, `step_save_results`, `step_decision_analysis`, `step_plots`) so individual steps can be re-run in notebooks. `main()` returns a dict of every intermediate artifact (traces, preds, eval results, targeting sims, country metrics) for interactive use.

### Key data conventions

- **`frequency`** = repeat purchases (total invoice count − 1); one-time buyers have `frequency = 0`
- **`monetary_value`** = mean revenue per *repeat* transaction (first purchase excluded, per Gamma-Gamma convention); one-time buyers get `monetary_value = 0`
- Time units are **weeks** (`time_unit="W"`) throughout
- Countries with fewer than 30 customers are collapsed into `"Other"` in `country_segment`
- The Gamma-Gamma model is only fitted on repeat purchasers (`frequency > 0`); CLV for one-time buyers imputes the population mean spend

### Thesis LaTeX

**Active source is `texts/thesis_clv.tex`** (NOT the older `texts/thesis.tex`, and NOT `compile_thesis.py`, which targets an outdated online API). It `\input`s the chapter files `ch4_methodology.tex`, `ch5_results.tex`, `ch6_conclusion.tex` and the diagram files `tikz_*.tex`. Chapters 1–3 (Introduction, Theoretical Foundations, Bayesian Probabilistic CLV Models) live inline in `thesis_clv.tex`. Bibliography is `references_clv.bib` (biblatex + biber, APA style); results tables/figures are pulled from `outputs/` via the `\condfig` and `\resulttable` helpers.

**Build with the local toolchain** (latexmk + pdflatex + biber are installed in WSL):
```bash
cd texts && ./build_thesis.sh        # compiles thesis_clv.tex, writes the next thesis_vN.pdf
cd texts && ./build_thesis.sh -v 5   # force a specific version number
```
After building, confirm a clean log: no `^!` errors, no "Citation ... undefined", no "Reference ... undefined".

**Versioned output convention:** each round of edits produces an incrementing `texts/thesis_vN.pdf` (v1, v2, v3, …). `build_thesis.sh` auto-bumps to the next unused number. Do not overwrite an existing version. As of the last session: **v3 is current (54 pages)** — v1 = first clean build, v2 = em-dash/prose-polish pass, v3 = supervisor-feedback revisions.

**`prose-polish` skill** (`.claude/skills/prose-polish/`): an academic copy-edit pass (remove em-dashes → correct punctuation, vary cadence, cut AI clichés). It is explicitly **not** an AI-/plagiarism-detection-evasion tool and must not be used or described as one — improve writing quality only; the author owns authorship/policy decisions. Note: en-dashes in numeric ranges (`--`) are correct and left alone; only em-dashes (`---`, `—`) are removed; never touch citations, refs, equations, numbers, or `tikz_*.tex`.

**Last session's feedback revisions (in v3):** added Ch. 2 sections — *Probabilistic Models for Customer-Base Analysis* (Pareto/NBD → BG/NBD, Gamma-Gamma foreshadowing), *Foundations for the Hierarchical and Decision-Theoretic Extensions* (H2/H3 literature), and *Research Gap*; softened over-strong claims about ML uncertainty and "no existing approach"; added a source note to Table 2.1 (`tikz_evolution_table.tex`). Added 4 references to `references_clv.bib`: `efron1975`, `rossi2005`, `berger1985`, `venkatesan2004` — **user still to verify their metadata** against a reference manager.

**Open item:** repo has **no git commits yet**; the thesis source and `thesis_vN.pdf` files are untracked. An initial commit was offered but not yet made. `.gitignore` already excludes LaTeX build artifacts (`*.aux`, `*.bcf`, `*.log`, etc.) and `.venv/` while keeping the versioned PDFs.
