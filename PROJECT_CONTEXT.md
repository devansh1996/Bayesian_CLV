# PROJECT_CONTEXT.md — session handoff & full state (updated 2026-07-05)

Reference document for the "fix shortcomings → produce real thesis results" effort.
Companion docs: `CLAUDE.md` (repo instructions), memory `project_review_findings_2026-07.md`.
Sections §1–§7j are the historical narrative; **§0 below is the live status — read it first.**

---

## 0. CURRENT STATUS & NEXT STEPS (read this first)

**Where we are:** the pipeline runs end-to-end and produces trustworthy results.
`thesis_v4.pdf` (59 pp) is the last *built* PDF. Since v4, the **H2/H3 analysis
redesign** was implemented in CODE + DATA but the **thesis prose is not yet updated
and v5 is not built.** All code committed (HEAD = commit `8ebfc26`), working tree clean.

**What the redesign changed (committed, results regenerated in `outputs/`):**
- **H2** — added the no-pooling arm (`fit_nopooled_bgnbd` in `models.py`; wired into
  `step_decision_analysis`). `country_level_mae.csv` now has a "No pooling (per
  segment)" column. Three-way holdout tx-MAE: no-pooling worst in every small segment
  (France 2.444, Germany 1.670) but best for "Other" (1.627); complete worst for
  "Other" (1.695); **partial pooling never worst, lowest weighted non-UK MAE 1.746**
  (vs none 1.755, complete 1.757). ⇒ H2 verdict should become **Partially supported**.
- **H3** — targeting sim now uses the posterior **predictive** CLV
  (`compute_clv_predictive`), not the expected-CLV posterior (which saturated
  P(CLV>c) at 0/1). `improvement_pct` at cost=600/depth=0.20 went **−55.6% → −1.7%**
  (near-parity; slightly positive at high cost). ⇒ H3 verdict stays **Not supported**
  but is now "near-parity, expected-value ranking suffices"; the saturation artifact
  is itself a methodological finding (non-predictive posteriors are a decision-rule
  pitfall — same class as the coverage fix). `analysis/h3_risk_metrics.py` +
  `outputs/results/h3_risk*.csv` hold hit-rate / wasted-spend numbers for the writeup.

**NEXT SESSION — remaining work to produce v5:**
1. **ch5_results.tex H2 section** (`sec:results-h2`): rewrite for the three-way
   comparison; report the no-pooling column (now in `tab:country_mae`); verdict
   "Partially supported" — partial pooling beats no-pooling in small segments and is
   the best aggregate, but cannot beat complete pooling where segments barely differ.
2. **ch5_results.tex H3 section** (`sec:results-h3`): update numbers to the predictive
   sim (headline −1.7% at £600/20%, near-parity across grid); add the
   expected-vs-predictive-probability pitfall as a finding. Old prose still cites the
   −55.6% figure — replace.
3. **ch5 verdicts table** (`tab:verdicts`): H2 → "Partially supported".
4. **ch6_conclusion.tex**: mirror H2 (partially supported, adaptive shrinkage) and H3
   (near-parity + pitfall) in the summary paragraphs (L18/L21 area).
5. **Optional**: `plot_country_mae_comparison` now shows 6 models incl. no-pooling —
   check the figure reads well; a dedicated 3-way (none/partial/complete) panel would
   be cleaner for the H2 figure.
6. **Build**: `cd texts && ./build_thesis.sh` → `thesis_v5.pdf`; confirm clean log
   (no `^!`, no undefined refs/citations). Commit prose + v5.
7. Exact fill-in numbers are in §7j and §0 above; read CSVs in `outputs/results/` for
   anything else. Flag to user: amending hypothesis operationalisation mid-thesis is
   worth a note to their supervisor.

**Env reminder:** run `~/.venvs/bayesclv/bin/python src/…` from repo root;
`run_all_models.py --skip-sampling` reuses saved traces (~3 min incl. the 4 no-pooling
fits). Do NOT resurrect the hand-rolled BG/NBD likelihood (see §7f).

---

## 1. Why this work exists

A full project review (2026-07-04) found the thesis results chapter was **empty**:

- The model pipeline had **never run to completion**: `data/processed/` empty, no
  `outputs/traces|results|figures` (only `outputs/eda/*.png` existed).
- `texts/ch5_results.tex` has **13 `\fillin{…}` placeholders** (incl. all H1/H2/H3 verdicts);
  `texts/ch6_conclusion.tex` has 6 more on lines ~15/18/21. `thesis_v3.pdf` (the "current"
  54-page build) therefore has placeholder boxes throughout Chapter 5.
- The only `.venv` was a **Windows Python 3.14** venv (`.venv/Scripts/`) — PyMC 5.x needs
  Python ≤ 3.12, so the pipeline *could not* run. This `.venv` is deliberately left
  untouched (may serve Windows-side Jupyter).
- Several bugs would have crashed or invalidated the results even if it had run (see §3).

## 2. Decisions taken (user-approved)

| Decision | Choice |
|---|---|
| Python env | **Linux-side venv `~/.venvs/bayesclv`** (WSL), created with `uv`-managed CPython 3.11.15 — Ubuntu 26.04 ships only Python 3.14, no python3.11 apt package |
| XGBoost leakage fix | **Nested temporal split** inside the calibration window (`XGB_INNER_CAL_END = "2010-10-01"`) |
| Scope | Env + bug fixes + full pipeline run + **ch5/ch6 fill-in + thesis v4** + **repo hygiene** + **metric/prose fixes** |
| Explicitly declined / out of scope | pytest suite; hierarchical `mu_* ~ Normal` prior change (future work — would alter RQ2 results); git remote setup; verifying the 4 bib entries (`efron1975`, `rossi2005`, `berger1985`, `venkatesan2004` — user's open item) |

## 3. Bugs found & fixed (all committed)

| # | Bug | Fix | File |
|---|---|---|---|
| 1 | `np.trapezoid` needs NumPy ≥ 2, pinned `numpy<2.0` → crash in step 5 | `np.trapz` | `src/evaluation.py` `gini_coefficient` |
| 2 | "Normalised" Gini never divided by oracle; clipped to [0,1] | Now `raw_gini(model)/raw_gini(oracle)`; negative (worse-than-random) visible | `src/evaluation.py` |
| 3 | Brier score promised in ch5 prose but never computed; log line printed AUC-PR labelled "Brier" | Added `"brier"` via `brier_score_loss`; fixed log line | `src/evaluation.py`, `src/run_all_models.py` (~line 381) |
| 4 | RFM recency: bin edges fitted on **raw recency (weeks)** but scored on **recency/T ratio ∈ [0,1]** → R score constant (RFM was really FM) | Edges now fitted on the ratio; verified R_score spreads 1–5 across quintiles | `src/baselines.py` `RFMHeuristicBaseline.fit` |
| 5 | **XGBoost data leakage**: trained on the same `holdout_truth` used to evaluate all models → in-sample RQ1 numbers | Nested temporal split (see §4) | `src/data.py`, `src/baselines.py`, `src/run_all_models.py` |
| 6 | `XGBoostCLVBaseline.predict()` ignored `t_future` despite docstring | Scales by `t_future / trained_horizon_` when horizon known | `src/baselines.py` |
| 7 | `pm.math.gammaln` / `pm.math.softplus` **don't exist in PyMC 5.x** (proof the MCMC never ran) | `import pytensor.tensor as pt`; `pt.gammaln` / `pt.softplus` | `src/models.py` (all likelihoods) |
| 8 | `posterior.dims["segment"]` deprecated in new xarray | `posterior.sizes["segment"]` | `src/models.py` `predict_conditional_transactions` |
| 9 | `pyarrow` missing from requirements → parquet save crashed on first pipeline attempt | Installed; added `pyarrow>=14.0` to `requirements.txt` | `requirements.txt` |

## 4. Nested temporal split (leakage fix) — how it works

- `src/data.py`: new constant `XGB_INNER_CAL_END = "2010-10-01"` + new
  `build_inner_training_set(cal, …) -> (inner_customers, inner_truth, inner_cal, inner_horizon)`.
  Splits *calibration* transactions at 2010-10-01: features from before, supervision
  targets from [2010-10-01, CAL_END). Real holdout (CAL_END = 2011-03-01 onward) unseen
  by every model. Inner target horizon ≈ 21.6 weeks.
- `src/baselines.py`: `XGBoostCLVBaseline.fit(..., target_horizon_weeks=)` stores
  `trained_horizon_`; `predict()` linearly rescales counts to the requested horizon;
  new `set_prediction_transactions()` swaps in the **full** calibration stream at predict
  time (so IPT/temporal features match the full-window RFM table).
  `fit_all_baselines(..., xgb_train=(inner_customers, inner_truth, inner_cal, inner_horizon))`
  takes the inner split; **warns loudly** if called without it (leaky legacy path).
- `src/run_all_models.py` `step_baselines()`: builds the inner set when `cal` is given
  and passes it through. Naive/RFM unchanged (they never used holdout targets).

## 5. Environment (reproducible)

```bash
# uv was installed to ~/.local/bin/uv (curl -LsSf https://astral.sh/uv/install.sh | sh)
~/.local/bin/uv python install 3.11          # CPython 3.11.15
~/.local/bin/uv venv ~/.venvs/bayesclv --python 3.11
~/.local/bin/uv pip install -r requirements.txt --python ~/.venvs/bayesclv/bin/python
```

- **Run everything as** `~/.venvs/bayesclv/bin/python src/…` **from the repo root**
  `/mnt/c/Users/devan/bayesCLV` (all paths in code are CWD-relative).
- Key versions installed: pymc 5.15.1, numpy 1.26.4, arviz 0.23.4, xgboost 3.2.0,
  xarray 2026.4.0, pyarrow 24.0.0.
- Harmless warning on every run: `WARNING (pytensor.tensor.blas): Using NumPy C-API
  based implementation for BLAS functions.` (no optimized BLAS linked; models are tiny,
  acceptable).
- The Windows `.venv/` (Python 3.14) is dead weight for the pipeline — do not use it.

## 6. Git state

Branch `master`, **no remote**. Commits this session (after initial `1d2966a`):

1. `f281c23` — fix: evaluation + PyMC model correctness (bugs 1,2,3,7,8)
2. `d58ce78` — feat: leakage-free XGBoost nested split + RFM recency fix (bugs 4,5,6 + log line)
3. `7f19786` — chore: untrack junk (`thesis_code (1).docx`, `docx_extract.txt`,
   `Thesis= Google.md`, `compile_thesis.py` — **still on disk**, now gitignored);
   `.gitignore` narrowed from `outputs/` to `outputs/*` with `!outputs/eda|results|figures`
   so result tables/figures can be versioned (traces stay ignored via `*.nc` + no unignore).
4. `841e7ba` — results: publication-quality LaTeX table layer in `_save_results`
   (see §7a) + `pyarrow` added to `requirements.txt` (bug 9).

**Still to commit** (see §8): pipeline outputs (`outputs/results/`, `outputs/figures/`),
ch5/ch6 edits + `thesis_v4.pdf`, `CLAUDE.md` update, this file.

## 7a. Thesis-ready result tables (how results reach the thesis)

The thesis pulls generated artefacts by **stable filename**, so nothing in the .tex
needs editing when numbers change:
- Tables: `\resulttable{stem}{fallback caption}{label}` → `\input{../outputs/results/stem.tex}`
  if it exists, else a "pending" placeholder box.
- Figures: `\condfig{../outputs/figures/name.png}{width}{caption}{label}`.

`_save_results()` (in `run_all_models.py`) now writes **two** files per table:
- `outputs/results/<stem>.csv` — raw column names + full-precision floats (parse these
  for the Chapter 5 fill-in).
- `outputs/results/<stem>.tex` — booktabs table with display headers
  (`Tx MAE`, `CLV MAE (\pounds)`, `NDCG@100`, `Coverage (90\%)`, …), thousands
  separators for money, integer counts, 3-dp ratios, formatted index levels, and
  proper column alignment. Requires `booktabs`, `multirow`, `tabularx` (all already
  in the preamble, verified). Table stems the thesis expects: `metrics_comparison`,
  `credible_interval_coverage`, `p_alive_evaluation`, `targeting_lift`,
  `targeting_simulation_bg_nbd_bayesian` (and `_hierarchical_bg_nbd`),
  `country_level_mae`.

**Important:** the pipeline process running now imported the *old* `_save_results`, so
its Step 6 will emit raw-header tables. **Regenerate the pretty tables + figures from the
saved traces after MCMC finishes** with:
```bash
~/.venvs/bayesclv/bin/python src/run_all_models.py --skip-sampling
```
This reloads the new code, reuses `outputs/traces/*.nc` (no re-sampling), and overwrites
all `outputs/results/*` and `outputs/figures/*`.

## 7. Pipeline run (in progress at time of writing)

- Command: `~/.venvs/bayesclv/bin/python src/run_all_models.py` (background task
  `byv9noxmn`; output file
  `/tmp/claude-1000/-mnt-c-Users-devan-bayesCLV/9c5016f3-94f6-43cd-b9bb-1dffc465315a/tasks/byv9noxmn.output`;
  a Monitor watches for STEP transitions / R-hat / divergences / Tracebacks).
- First attempt crashed at parquet save (bug 9); relaunched after installing pyarrow.
- Sampling config: 4 chains × 2000 draws, 2000 tune, target_accept 0.9, seed 42.
  Models: pooled BG/NBD, hierarchical BG/NBD (per country segment), Gamma-Gamma.
- **Data facts from the run** (for sanity-checking ch5 numbers):
  - Calibration ends `CAL_END = 2011-03-01`; holdout horizon ≈ 40.7 weeks (to 2011-12-09).
  - 4,522 calibration customers; 2,670 active in holdout (59.0%); mean holdout
    transactions 2.60; total holdout revenue £5,808,484.
  - Inner XGBoost split: 2010-10-01, horizon ≈ 21.6 weeks.

### Expected outputs when done
- `outputs/traces/`: `bgnbd_standard.nc`, `bgnbd_hierarchical.nc`, `gamma_gamma.nc`
- `outputs/results/`: `metrics_comparison.csv/.tex`, `credible_interval_coverage.*`,
  `p_alive_evaluation.*`, `targeting_lift.*`, `targeting_simulation_*.*`,
  `country_level_mae.*`, `calibration_*.csv`, `posterior_summary_*.csv`
- `outputs/figures/`: rfm/monetary/recency EDA, trace + rhat + pairs diagnostics,
  calibration panels, lift curves, CLV distribution/uncertainty, p_alive,
  posterior predictive, hierarchical shrinkage forests, targeting simulation,
  country MAE comparison

### Acceptance checks
- Max R-hat < 1.01, few/no divergences (else rerun that model with `target_accept=0.95`).
- Every model beats Naive on `tx_mae`; XGBoost errors plausible (not near-zero in-sample).
- If MCMC diagnostics are bad, do **not** fill ch5 with those numbers — refit first.

## 7b. Chapter 5/6 fill-in map (exact source for each `\fillin`)

Read the **raw CSVs** (`outputs/results/*.csv`, original column names) plus MCMC
diagnostics. Model row keys: `BG/NBD (Bayesian)`, `Hierarchical BG/NBD`,
`XGBoost (two-stage)`, `RFM Heuristic`, `Naive (mean)`.

**ch5_results.tex (13 fillins):**
- L23 diagnostics "converged / require attention" ← max `r_hat` over
  `posterior_summary_*.csv` (want <1.01) + divergences from run log.
- L33 H1 accuracy: tx MAE BG/NBD, XGBoost, RFM ← `metrics_comparison.csv` `tx_mae`;
  CLV Gini ← `clv_gini` (BG/NBD row); "summary of finding" ← read spearman/gini/ndcg.
- L44 uncertainty: coverage ← `credible_interval_coverage.csv` `coverage_90pct`
  (BG/NBD); "interpretation" ← compare to 0.90.
- L53 activity: AUC ← `p_alive_evaluation.csv` `auc_roc`; Brier ← `brier`;
  "interpretation" ← qualitative from AUC.
- L60 H1 verdict ← synthesize from above.
- L65 H2: hier vs pooled MAE for Germany & France ← `country_level_mae.csv`
  columns `MAE_Hierarchical BG/NBD` vs `MAE_BG/NBD (Bayesian)` (report each or the
  pair); "change of value" ← difference.
- L76 H2 verdict ← from L65.
- L87 H3: posterior vs point net value at cost=20/depth=0.20 ←
  `targeting_simulation_bg_nbd_bayesian.csv` `posterior_prob_value` /
  `point_estimate_value`; improvement ← `improvement` (or `improvement_pct`);
  "consistent across grid" ← sign of `improvement` at costs 5/20/50.
- L92 H3 verdict ← from L87.

**ch6_conclusion.tex (6 fillins, must match ch5 verdicts):**
- L15: competitive/superior, well/poorly, borne out/qualified (H1).
- L18: reduced / did not reduce (H2).
- L21: outperformed / did not outperform, robust / sensitive (H3).

**Also add to ch6 §Limitations (L36):** one sentence on the one-time-buyer CLV
imputation (constant population-mean spend → understated uncertainty for ~1,493
one-time buyers). The other limitations (GG independence r=0.13, single dataset,
segment granularity, horizon/covariates) are already written.

**tab:verdicts summary table (ch5 L107–111):** 3 `\fillin{verdict}` — fill with the
one-word H1/H2/H3 outcomes.

## 7c. Build toolchain — VERIFIED (2026-07-04)

`cd texts && latexmk -pdf -interaction=nonstopmode -file-line-error thesis_clv.tex`
compiles clean: exit 0, **no `^!` errors, no undefined citations/references, 54 pages**
(placeholder boxes where results are pending). biber runs automatically. The final
build uses `./build_thesis.sh` (bumps to `thesis_v4.pdf`). Do the test-compile without
the version copy to avoid consuming a version number.

## 7d. Prior mis-scaling discovered — pipeline killed, priors.py added (2026-07-04)

**The first full pipeline run was killed:** the pooled BG/NBD (Step 2a) burned ~60 min
CPU per chain × 4 and never finished a 4-parameter model — pathological, almost
certainly max-tree-depth hammering from badly-*scaled* default priors
(`HalfNormal(sigma=10)` on every parameter). No trace was saved; nothing lost.

**Root cause (from `data/processed/customers.parquet` moments):**
- Mean weekly purchase rate 0.078 → BG/NBD `alpha` ~ 1/rate ≈ 12.9 wk, `r` ≈ 1
  (O(1)); `a,b` are O(1). `HalfNormal(10)` is ~10× too diffuse for `r,a,b` → stiff
  geometry.
- Mean repeat spend £385 → Gamma-Gamma `gamma` carries money units, must be O(few
  hundred). `HalfNormal(10)` puts a prior-predictive *median population mean spend of
  £8.68* (vs observed £385) — a ~44× conflict. **Smoking gun.**

**New file `src/priors.py`** (committed? see §6 — check `git log`):
- `data_informed_priors(customers)` → HalfNormal sigmas scaled by method-of-moments,
  usable directly via the existing `build_bgnbd(..., priors=)` /
  `build_gamma_gamma(..., priors=)` API. Derived values:
  - bgnbd: `r_sigma≈1.25, alpha_sigma≈16.1, a_sigma≈1.88, b_sigma≈3.81`
  - gamma_gamma: `p_sigma=2.0, q_sigma≈3.76, gamma_sigma≈321.7`
- `prior_predictive_bgnbd` / `prior_predictive_gamma_gamma` + `__main__` checks.
  Validation: data-informed brackets observed frequency (sim mean 2.77 vs 3.78) and
  spend (median £367 vs £385); default badly misses spend (£8.68 median).
- Run it: `~/.venvs/bayesclv/bin/python src/priors.py`

**NOT yet done / open decisions:**
- The **hierarchical** model (`build_hierarchical_bgnbd`) hyperpriors are ALSO
  mis-scaled (`mu_* ~ HalfNormal(10)`, `sigma_* ~ HalfNormal(5)` on the *softplus-input*
  scale). Must be rescaled before re-running or it will be pathological too. Target
  softplus-input centers: mu_r≈0.54, mu_alpha≈12.85, mu_a≈1.25, mu_b≈2.95;
  between-segment `sigma_*` small (~0.5). Plan: give it a `priors=` arg and extend
  `data_informed_priors` with a `hierarchical` sub-dict.
- **Wiring + re-run** (long) is a methodological choice for the thesis (prior
  specification) — get user go-ahead. When adopting: pass priors in
  `run_all_models.step_bayesian`, and consider reducing `SAMPLING_CONFIG` from
  2000/2000 to 1000/1000 draws/tune (plenty for the thesis; halves time).
- Optional thesis material: prior-sensitivity comparison (default vs data-informed) —
  but default may not sample at all, so may be moot.

## 7e. Sampling pathology — full investigation (2026-07-04)

After fixing prior *scaling* (§7d), the pooled **BG/NBD still will not sample in
practical time**. Systematic diagnosis:

| Attempt | Result |
|---|---|
| logp/grad finiteness | **Gradients finite everywhere** (0/200 non-finite random pts); logp/grad ~1.1ms each. NOT a nan-gradient bug. |
| default sampler + data-informed priors | 1 chain, 600 iters = **13 min**. ~1.3s/iter ⇒ tree depth saturated (~1024 leapfrog/iter). |
| `init="adapt_full"` (dense mass matrix) | 2 chains × 1500 iters still unfinished at **11.5 min**; tree depth only ~8–9. Correlation is not purely linear. |
| **nutpie 0.13.2** (compiled NUTS, numba) | **Gamma-Gamma: 4s** (well-conditioned, 3 params). **BG/NBD: >400s timeout** at full config; >200s even at 300/500×2. |
| mean/concentration **reparameterization** (φ=a/(a+b), κ=a+b; μ=r/α, r) + nutpie | Still **timed out** at 300/500×2. |

**Conclusion:** the hand-rolled BG/NBD posterior is severely ill-conditioned
(the `(r,α)` and `(a,b)` ridges), and neither better priors, a full-rank mass
matrix, a compiled backend, nor a first-pass reparameterization rescued it within
a practical budget. Gamma-Gamma is fine. This is a **model/parameterization**
problem, not scaling/backend.

**New dependencies installed this session (keep — useful regardless):**
`nutpie==0.13.2` (must pin <0.14 for pymc 5.15 — 0.16 breaks on
`pymc.pytensorf.compile`), `numba==0.66.0`, `llvmlite==0.48.0`. Add to
`requirements.txt` if adopted.

**New file `src/priors.py`** is committed-worthy but **not yet committed** (check
`git status`). Verify before relying on it.

### Decision pending (do NOT proceed without user)
Path to real, trustworthy results — options put to the user:
- **(A) Use `pymc-marketing` reference models** (`BetaGeoModel`, `GammaGammaModel`
  — already a declared dep) for the standard models; they use a validated,
  well-conditioned implementation that samples efficiently. Rewire predictions to
  their API. Build the **hierarchical** H2 variant on the same foundation (or keep
  a custom, reparameterized hierarchical model). Fastest path to results; changes
  the "own implementation" narrative for the pooled models.
- **(B) Keep the custom models, invest in a proper reparameterization** (pooled +
  hierarchical) until they sample. Preserves authorship; uncertain time, first
  attempt already failed.
- A grounding benchmark was run: does pymc-marketing's BetaGeo sample this exact
  data fast? (result in `git`/context when done — if yes, strongly supports A.)

The hierarchical BG/NBD (thesis H2 contribution) must sample regardless, so its
parameterization needs the same fix whichever path is chosen.

## 7f. DECISION MADE: adopt pymc-marketing (2026-07-05)

User chose to adopt `pymc-marketing` (v0.8.0, already installed). Benchmarks on the
real data (`customers.parquet`):
- `BetaGeoModel` (pooled BG/NBD): **69.5s**, R-hat 1.002, ESS 1581 (default sampler).
- `GammaGammaModel`: fast (~seconds).
- Root cause of the hand-rolled failure identified: pmm uses **Fader-Hardie
  expression (4)** — `logp = d1 + d2 + log(c3 + switch(x>0, c4, 0))`, `c4=a/(b+x-1)`,
  `c3=((α+t_x)/(α+T))^(r+x)` — with **no `-inf`** in the graph. The custom model used
  `logaddexp(alive, -inf dead)`, and the `-inf` wrecks HMC trajectory energy → max
  tree depth. (Bonus: the custom GG population-mean formula was WRONG — used
  `q·γ/(q-1)`; pmm correctly uses `v·p/(q-1)`. pmm GG vars are `p, q, v` not `p,q,gamma`.)

### pmm API facts (v0.8.0)
- `BetaGeoModel(data=df)` where df has `customer_id, frequency, recency, T`.
  Posterior vars `r, alpha, a, b`. Methods return FULL posteriors `(chain,draw,customer)`:
  `expected_purchases(data, future_t=)`, `expected_probability_alive(data)`.
  Default priors HalfFlat. Override via `model_config={'r_prior': Prior('HalfNormal', sigma=..)}`.
  Persist with `model.save(path)` / `BetaGeoModel.load(path)`.
- `GammaGammaModel(data=df)` df has `customer_id, frequency, monetary_value` (repeat
  customers, frequency>0). Vars `p,q,v`. `expected_customer_spend(data)` → full posterior.
- Integration plan for `src/models.py`: replace `build_bgnbd`/`build_gamma_gamma` with
  pmm wrappers; rewrite prediction fns to call pmm methods (stack chain×draw →
  (n_samples, n_cust)); keep `compute_clv_posterior` (tx × spend). Update
  `run_all_models.step_bayesian` / `step_bayesian_predictions` to hold pmm model objects
  and use `model.save/load` for `--skip-sampling`. `plots.py` reads posterior `r,alpha,a,b`
  — still present, should keep working.

### Hierarchical H2 model — the hard part (still being resolved)
pmm has NO hierarchical BG/NBD. Custom model with the STABLE logp + log-normal
non-centered partial pooling **still funnels badly**: even 1000 iters times out; the
tiny segments (France n=54, Germany n=74) drive a severe funnel that non-centering +
tight `sigma~HalfNormal(0.25)` + `target_accept=0.95` haven't cleanly fixed. A full
1000/1000x4 run is going in the background (task `bbazo2zid`) to get real
divergence/R-hat numbers. If it converges acceptably → use it. If not, options:
(a) make only purchase-rate `(r,alpha)` hierarchical, keep dropout `(a,b)` pooled
(halves the funnels, still tests H2); (b) even tighter sigma / stronger pooling;
(c) reconsider segmentation. **This is the main open technical risk.** Segments (from
data): United Kingdom 4152, Other 242, Germany 74, France 54.

## 7g. Methodology text to reconcile with pmm rewrite (do during fill-in)

The model rewrite (§7f) changed the implementation, so parts of the methodology
chapter now describe code that no longer exists. Update during the ch5/ch6 pass:
- `ch4_methodology.tex:72-78`: "implemented ... as a \texttt{Potential}" and
  "HalfNormal($\sigma=10$)" and "softplus transform" — update to: standard BG/NBD +
  Gamma-Gamma via **pymc-marketing** (numerically stable Fader-Hardie form);
  **data-informed** HalfNormal priors (see `src/priors.py`); hierarchical uses a
  **log-normal** mapping `θ_s = exp(μ+σz)` (not softplus) with tight
  `σ~HalfNormal(0.25)`; `target_accept=0.95`.
- `thesis_clv.tex:517` (non-centred / Neal's funnel) is still accurate — the
  small-segment funnel was real and the tight scale + non-centring resolved it (can
  cite the observed drop in tree depth / 2 divergences as evidence).
- `thesis_clv.tex:342` "fully Bayesian implementation of BG/NBD and Gamma-Gamma" is
  still fine (pmm is PyMC/HMC).
Framing: honest and defensible — "estimated with PyMC via the pymc-marketing library's
numerically stable implementation." The novel hierarchical H2 model remains custom.

## 7h. Pipeline STATUS: full run launched (2026-07-05)
Full `run_all_models.py` running in background (task `b344dtf6t`). Config: pmm pooled
(~70s) + hierarchical (~15 min, target_accept 0.95) + GG (~10s) + baselines (nested
split) + eval + pretty tables + plots. Expect ~20 min. Watch diagnostics: pooled
R-hat should be ~1.00; hierarchical ~1.004 with few divergences. On completion verify
`outputs/results/*.csv|tex` + `outputs/figures/*.png` populated, then do ch5/ch6
fill-in (§7b) + methodology reconcile (§7g) + build v4.

## 7i. RESULTS ARE IN (2026-07-05) — pipeline runs clean, but 2 eval issues

Full pipeline completed. All models converged 0 divergences (pooled R-hat 1.0014
ESS 1923; hierarchical 1.0031 ESS 1097; GG 1.0024 ESS 1126). Outputs populated:
`outputs/results/*.csv|tex` (15 tables) + `outputs/figures/*.png` (28, all fixed).

**RQ1/H1 accuracy — strongly supported.** `metrics_comparison.csv`:
| model | tx_mae | clv_gini | ndcg_100 |
|---|---|---|---|
| Hierarchical BG/NBD | 1.742 | 0.855 | 0.905 |
| BG/NBD (Bayesian)   | 1.743 | 0.855 | 0.905 |
| XGBoost (two-stage) | 2.117 | 0.801 | 0.534 |
| RFM Heuristic       | 2.330 | 0.785 | 0.531 |
| Naive (mean)        | 3.114 | 0.070 | 0.017 |
Bayesian beats all baselines on error AND ranking. Hierarchical ≈ pooled (tight
pooling; small segments differ little — see country table).

**RQ2/H2 — weak/mixed.** `country_level_mae.csv`: hierarchical vs pooled tx-MAE:
UK 1.7411 vs 1.7414 (tie), Other 1.653 vs 1.695 (hier better), Germany 1.635 vs
1.622 (pooled better), France 2.318 vs 2.223 (pooled better). Partial pooling does
NOT clearly help the small segments here → H2 likely "not / partially supported".

**RQ3/H3 — pending read** of `targeting_simulation_bg_nbd_bayesian.csv` (values
saved; interpret posterior-prob vs point at cost=20/depth=0.20).

### TWO EVALUATION-DESIGN ISSUES (affect H1 uncertainty + activity claims)
Both pre-existed in the old code; only visible now that the pipeline runs.
1. **Coverage = 1.9%** (`credible_interval_coverage.csv`), mean width 0.15. The
   "posterior predictive" fed to coverage is actually the posterior of the
   *expected* transaction count E[X] (parameter uncertainty only), not a predictive
   of the integer outcome. Proper fix: sample actual holdout counts per draw
   (BG/NBD posterior predictive incl. count variability) → meaningful coverage.
2. **P(alive) AUC = 0.41** (< random), recall 0.98 (`p_alive_evaluation.csv`). All
   1,493 one-time buyers get P(alive)=1.0 by construction (BG/NBD: no repeat ⇒
   can't have dropped out), which anti-correlates with holdout activity. Fix:
   evaluate P(alive) discrimination on repeat customers (frequency>0) only, and/or
   report the caveat.

3. **H3 targeting FAILS spuriously — cost grid mis-scaled.** Posterior-prob rule
   captures £1.07M vs point-estimate £4.40M at cost=£20/depth=0.20 (improvement
   -75%, negative at every depth/cost). Cause: cost grid (£5/£20/£50) is tiny vs
   CLV (mean £423, up to thousands), so `P(CLV>cost) ≈ 1` for almost everyone →
   the probability ranking is uninformative and point-estimate wins. The
   decision-theoretic advantage only appears when the cost threshold cuts through
   the bulk of the CLV posteriors. Fix: scale `COST_GRID` / `PRIMARY_COST` to CLV
   magnitude (e.g. £100/£300/£600) in `run_all_models.py`.

**Decision needed from user** before ch5 fill-in: all THREE Bayesian-value
evaluations (H1 uncertainty coverage, P(alive), H3 targeting) have setup/scaling
issues that make the Bayesian advantage look worse than it is. Recommended: fix all
three (posterior-predictive coverage; repeat-only P(alive); CLV-scaled cost grid),
re-run `--skip-sampling`, then fill ch5. The H1 *accuracy* story stands regardless.
These are evaluation-setup fixes, not model changes (traces are saved, so re-eval
is ~2 min each).

## 7j. FINAL RESULTS (2026-07-05) — eval fixes applied, verdicts settled

All three evaluation issues fixed (commit 9b889a7) and pipeline re-run
(`--skip-sampling`). Final, trustworthy numbers:

- **H1 accuracy — SUPPORTED.** BG/NBD tx-MAE 1.743 (hier 1.742) vs XGBoost 2.117,
  RFM 2.330, Naive 3.114; CLV-Gini 0.855 vs 0.80/0.78; NDCG@100 0.905 vs 0.53.
- **H1 uncertainty — SUPPORTED.** Posterior-predictive coverage **0.893 / 0.894**
  (nominal 0.90); CRPS 1.22; mean interval width now realistic. (Was 1.9% before
  the posterior-predictive fix.)
- **P(alive) — good.** On repeat customers: AUC **0.71**, AUC-PR 0.87, Brier 0.21.
- **H2 pooling — MIXED / NOT clearly supported.** Per-country tx-MAE hier vs pooled:
  UK tie, Other hier-better (1.653 vs 1.695), Germany pooled-better (1.635 vs 1.622),
  France pooled-better (2.318 vs 2.223). Tight pooling ⇒ hier≈pooled; no consistent
  small-segment gain.
- **H3 targeting — NOT SUPPORTED.** `improvement_pct` (posterior-prob vs
  point-estimate) is negative across the £100–2000 grid, approaching parity only at
  very high cost (e.g. cost 1200/depth 0.20 = -2.2%; cost 600/depth 0.50 = 0.0%).
  Honest reason: maximising *total captured value* is near-optimal under
  expected-value (posterior-mean) ranking, so the risk-averse P(CLV>cost) rule
  gives up value. The posterior's decision-value would appear under a risk-averse /
  loss-minimising objective — good discussion point for Ch6.

Balanced thesis story: H1 strong (accuracy + calibrated uncertainty), H2 mixed, H3
negative (with a principled explanation). PRIMARY_COST=600, COST_GRID 100–2000.

Result CSVs to read for exact fill-in values: `outputs/results/metrics_comparison.csv`,
`credible_interval_coverage.csv`, `p_alive_evaluation.csv`, `country_level_mae.csv`,
`targeting_simulation_bg_nbd_bayesian.csv`, `posterior_summary_*.csv`.

**NOTE for ch5 prose:** update the H3 numbers — old prose says "headline cost £20"
and "grid (£5, £20, £50)"; now £600 headline, grid £100–£2000. And ch5 currently
frames H3 as expected-to-succeed; rewrite to the honest not-supported finding.

## 8. Remaining work (in order)

1. **Wait for pipeline** → verify outputs + diagnostics per §7 acceptance checks.
2. **Chapter 5 fill-in** (`texts/ch5_results.tex`, 13 `\fillin`): read
   `outputs/results/*.csv` + posterior summaries; insert real values; write H1/H2/H3
   verdicts honestly (supported / partially / not — no over-claiming).
   `\condfig`/`\resulttable` macros pick up generated files automatically.
3. **Chapter 6 fill-in** (`texts/ch6_conclusion.tex` lines ~15/18/21, 6 `\fillin`):
   verdict phrasing must match ch5.
4. **Limitations note** (ch5 or ch6, one short passage): (a) one-time buyers' CLV uses a
   constant population-mean spend imputation (`compute_clv_posterior`,
   `src/models.py` ~line 603) → their uncertainty understated; (b) cancellations dropped
   rather than netted → revenue slightly overstated.
5. **Build v4**: `cd texts && ./build_thesis.sh` → auto-bumps to `thesis_v4.pdf`
   (never overwrite v1–v3). Check log: no `^!` errors, no undefined citations/references;
   grep ch5/ch6 for zero remaining `\fillin`; page count should exceed v3's 54.
6. **Commits** (logical units):
   - `fix: add pyarrow to requirements` (requirements.txt)
   - `results: pipeline outputs` (`outputs/results/`, `outputs/figures/`; traces ignored)
   - `docs: fill ch5/ch6 with pipeline results + thesis_v4.pdf` (+ this file)
   - `docs: update CLAUDE.md` — v4 current, pipeline has run, venv location
     `~/.venvs/bayesclv`, pyarrow requirement, PyMC-5 API fixes
7. **Update memory** (`~/.claude/projects/-mnt-c-Users-devan-bayesCLV/memory/`):
   mark review-findings memory items as fixed; record venv path + v4 status.

## 9. Known remaining issues (deliberately NOT addressed)

- Hierarchical hyperpriors: `mu_* ~ HalfNormal` constrains segment-parameter locations
  on the softplus scale; `Normal` would be more standard → **note as future work in
  thesis, do not change now** (would alter RQ2 results).
- No remote backup: thesis lives on one disk. Recommend private GitHub push (user decision).
- No pytest suite (user declined).
- 4 bib entries need metadata verification by the user.
- `texts/thesis.tex` (legacy) still tracked — harmless, superseded by `thesis_clv.tex`.
- XGBoost horizon rescale is linear (documented simplification in `predict()` docstring).

## 10. Quick command reference

```bash
cd /mnt/c/Users/devan/bayesCLV

# Full pipeline (fresh MCMC ~30–60 min)
~/.venvs/bayesclv/bin/python src/run_all_models.py
# Reuse saved traces (fast re-run of predictions/eval/plots)
~/.venvs/bayesclv/bin/python src/run_all_models.py --skip-sampling
# Module smoke tests (synthetic data, no MCMC)
~/.venvs/bayesclv/bin/python src/evaluation.py
~/.venvs/bayesclv/bin/python src/baselines.py
~/.venvs/bayesclv/bin/python src/models.py

# Thesis build (writes next thesis_vN.pdf)
cd texts && ./build_thesis.sh
```
