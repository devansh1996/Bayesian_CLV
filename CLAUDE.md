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

The working WSL environment for this repo is a **Python 3.11 venv at `~/.venvs/bayesclv`** (Ubuntu 26.04 ships only 3.14, so it was created with `uv`; the in-repo Windows `.venv/` is unused for the pipeline). Run everything as `~/.venvs/bayesclv/bin/python src/…` from the repo root. Standard BG/NBD and Gamma-Gamma are fitted with **pymc-marketing** (the hand-rolled likelihood was ill-conditioned and would not sample); the hierarchical model is custom. See `PROJECT_CONTEXT.md` for the full history.

```bash
# Reproduce the environment (uv installs CPython 3.11)
uv venv ~/.venvs/bayesclv --python 3.11
uv pip install -r requirements.txt --python ~/.venvs/bayesclv/bin/python
# (classic path, if python3.11 is available:)
#   python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
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

**Versioned output convention:** each round of edits produces an incrementing `texts/thesis_vN.pdf` (v1, v2, v3, …). `build_thesis.sh` auto-bumps to the next unused number. Do not overwrite an existing version. As of the last session: **v15 is current (74 pages)** — v1 = first clean build, v2 = em-dash/prose-polish pass, v3 = supervisor-feedback revisions, v4 = first build with real pipeline results (Chapter 5/6 filled from `outputs/`, methodology reconciled), v5 = H2/H3 analysis redesign (three-way pooling comparison; predictive-CLV targeting), v6 = added H3 risk-sensitive metrics table (hit rate, wasted spend), v7 = second round of supervisor feedback (prose tightened in Ch1–2; explicit Gap 1–3 → RQ → methodology chain; recent-literature engagement + original-contribution statement; restructured Limitations + new Generalisability section; abstract now reports findings; fixed ch4 cost-grid inconsistency and the managerial-implications contradiction with H3; 4 new bib entries `bachmann2021`, `valendin2022`, `angelopoulos2023`, `pymcmarketing2024` — metadata to be user-verified), v8–v10 = Chapter 3 theory additions (probability distributions, data-context subsection, HMC/NUTS exposition), v11 = understandability pass (front-matter List of Abbreviations + Notation; metric-intuition table 4.2; NDCG-gap and P(alive)-AUC explanations in Ch5; worked-example customer 14817 walked end-to-end in new §5.2.4 with Fig 5.8; posterior-predictive-vs-expectation saturation figure 5.12 in §5.4), v12 = fixed wide result tables overflowing the right margin (5.1/5.4/5.5 etc.): generated `.tex` tables now wrapped in `\begin{adjustbox}{max width=\linewidth}` + `\centering`, `adjustbox` added to the preamble, and the `_save_result` export in `run_all_models.py` emits the wrapper so re-runs stay fitted), v13 = fixed monospace `\texttt` paths overflowing the right margin (e.g. `src/run_all_models.py` in the Ch5 "Note on reproduction"): added `\setlength{\emergencystretch}{3em}` to the preamble and inserted `\allowbreak` after slashes in long paths so they break cleanly without hyphens), v14 = fixed the wide NBD equation (3.3, `eq:nbd`) whose equation number was dropping onto its own line below: broke it across two lines aligned at `=` using a `split` environment inside `equation`), v15 = expanded the XGBoost benchmark for comparison: new methodology subsection §4.7.1 with a 24-feature table (`tab:xgb-features`), two-stage design, hyperparameters, and leakage-safe inner-split training; new results subsection §5.2.2 with a gain-based feature-importance figure (`outputs/figures/xgboost_feature_importance.png`, Fig 5.6, generated out-of-pipeline from a reproduced inner-split fit) and a discussion of why XGBoost trails on ranking + uncertainty.

> **STATUS (2026-07-26): pipeline + thesis complete through v15.** Final hypothesis verdicts: **H1 supported, H2 partially supported, H3 not supported** (see `outputs/results/` and `PROJECT_CONTEXT.md`). The standard models use **pymc-marketing** (do not revive the hand-rolled BG/NBD likelihood); the working env is the Python 3.11 venv at `~/.venvs/bayesclv`; run `~/.venvs/bayesclv/bin/python src/… --skip-sampling` to regenerate results from saved traces. v11 added an understandability pass (worked example, front-matter glossaries, saturation figure); the two new figures (`worked_example_customer.png`, `prob_expectation_vs_predictive.png`) were generated from saved traces, not a re-sample. Open user items: verify the 4 added bib entries' metadata; a note to the supervisor that H2/H3 operationalisation was refined mid-thesis; sanity-check the v11 worked-example framing (model point estimate £1,364 vs realised £1,010 for customer 14817).

**`prose-polish` skill** (`.claude/skills/prose-polish/`): an academic copy-edit pass (remove em-dashes → correct punctuation, vary cadence, cut AI clichés). It is explicitly **not** an AI-/plagiarism-detection-evasion tool and must not be used or described as one — improve writing quality only; the author owns authorship/policy decisions. Note: en-dashes in numeric ranges (`--`) are correct and left alone; only em-dashes (`---`, `—`) are removed; never touch citations, refs, equations, numbers, or `tikz_*.tex`.

**Last session's feedback revisions (in v3):** added Ch. 2 sections — *Probabilistic Models for Customer-Base Analysis* (Pareto/NBD → BG/NBD, Gamma-Gamma foreshadowing), *Foundations for the Hierarchical and Decision-Theoretic Extensions* (H2/H3 literature), and *Research Gap*; softened over-strong claims about ML uncertainty and "no existing approach"; added a source note to Table 2.1 (`tikz_evolution_table.tex`). Added 4 references to `references_clv.bib`: `efron1975`, `rossi2005`, `berger1985`, `venkatesan2004` — **user still to verify their metadata** against a reference manager.

**Git:** the repo is pushed to **https://github.com/devansh1996/Bayesian_CLV** (default branch `main`; the local branch was renamed from `master` to match). WSL git uses the Windows Git Credential Manager (`credential.helper` set globally). `.gitignore` excludes LaTeX build artifacts (`*.aux`, `*.bcf`, `*.log`, etc.), `.venv/`, and `.obsidian/` while keeping the versioned PDFs.

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
