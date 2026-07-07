# Thesis Session Context — full record (2026-07-04 → 2026-07-05)

A complete narrative of everything done in this working session on the **bayesCLV**
Master's thesis (Bayesian Customer Lifetime Value on UCI Online Retail II). This is
the human-readable story; `PROJECT_CONTEXT.md` at the repo root holds the same facts
in reference form, and the memory file `project_review_findings_2026-07.md` holds the
condensed version.

---

## 0. TL;DR — where things ended up

- The model pipeline **had never actually run** at the start; now it runs end-to-end
  and produces trustworthy, converged results.
- The hand-rolled BG/NBD likelihood was **fundamentally unable to sample**; the standard
  models were migrated to **pymc-marketing**, the hierarchical model rebuilt on the same
  stable likelihood.
- The thesis went from an all-placeholder results chapter to **`thesis_v6.pdf` (59 pp)**
  with real numbers and honest verdicts.
- **Final hypothesis verdicts: H1 supported · H2 partially supported · H3 not supported.**
- ~17 git commits; working tree clean. Environment is a Python 3.11 venv at
  `~/.venvs/bayesclv`.

---

## 1. Starting state & the review

Session opened with a stray Windows venv path paste, then a request to "review the
entire project and decide shortcoming." Full review found the **results side had never
run**:

- `data/processed/` empty; `outputs/` had only EDA figures — no traces/results/figures.
- `texts/ch5_results.tex` had 13 `\fillin{}` placeholders incl. all H1/H2/H3 verdicts;
  the "current" `thesis_v3.pdf` (54 pp) had an empty results chapter.
- The only `.venv` was a **Windows Python 3.14** venv — PyMC 5.x needs ≤3.12, so the
  pipeline *could not* run.
- Several latent bugs (see §3) would have crashed or invalidated results anyway.

A plan was written and approved (`/loop`-style plan mode) covering: WSL venv, bug fixes,
full run, Chapter 5 fill-in, thesis v4, repo hygiene.

## 2. Environment setup

- Ubuntu 26.04 ships only Python 3.14 and has no `python3.11` apt package, so I installed
  **`uv`** and created **`~/.venvs/bayesclv`** (CPython 3.11.15).
- `uv pip install -r requirements.txt` — pymc 5.15.1, arviz 0.23.4, xgboost 3.2.0,
  numpy 1.26.4, etc. Later added `pyarrow` (parquet engine, was missing) and, for
  diagnostics only, `nutpie`/`numba` (not used by the final pipeline).
- Run everything as `~/.venvs/bayesclv/bin/python src/…` from the repo root. The Windows
  `.venv/` is unused for the pipeline.

## 3. Early bug fixes (before discovering the sampling problem)

Committed across two commits:

1. `np.trapezoid` → `np.trapz` (former needs NumPy≥2; pinned numpy<2 crashed).
2. **Normalised Gini** actually normalised (divide by oracle Gini; expose worse-than-random).
3. **Brier score** added to `compute_classification_metrics`; fixed a mislabeled log line.
4. **RFM recency bug**: bin edges were fitted on raw recency (weeks) but scored against
   recency/T ratios ∈ [0,1], collapsing the R score to a constant. Now fitted on the ratio.
5. **XGBoost holdout leakage**: it trained on the same holdout used to evaluate every
   model. Added a **nested temporal split** (`build_inner_training_set`, inner cutoff
   2010-10-01) so the real holdout stays unseen. `predict()` now honours `t_future`.
6. `pm.math.gammaln`/`softplus` don't exist in PyMC 5.x → `pytensor.tensor`; deprecated
   `posterior.dims` → `.sizes`.
7. Publication-quality LaTeX table formatting in `_save_results` (display headers,
   thousands separators, aligned columns); raw CSVs kept for value extraction.
8. Repo hygiene: untracked junk (`thesis_code (1).docx`, `docx_extract.txt`,
   `Thesis= Google.md`, `compile_thesis.py` — kept on disk, gitignored); `.gitignore`
   narrowed so `outputs/results` + `outputs/figures` can be versioned.

## 4. The sampling saga (the core discovery)

The user asked to **"build some priors with the data available."** Done — `src/priors.py`
derives weakly-informative, data-scaled HalfNormal priors via method-of-moments, with
prior-predictive checks. The validation was decisive: the default `HalfNormal(10)` prior
implied a **median population spend of £8.68 vs the observed £385** (~44× off) — a smoking
gun for prior/likelihood conflict.

But fixing priors did **not** make the pooled BG/NBD sample. A systematic investigation:

| Attempt | Result |
|---|---|
| logp/grad finiteness | gradients finite everywhere; ~1.1 ms each. NOT a nan bug. |
| default sampler + data-informed priors | 1 chain, 600 iters = **13 min** (tree depth saturated) |
| `init="adapt_full"` (dense mass matrix) | still unfinished at ~11.5 min; tree depth ~8–9 |
| **nutpie** (compiled NUTS) | Gamma-Gamma 4 s; **BG/NBD times out >400 s** |
| mean/concentration reparameterization + nutpie | still times out |

The first stuck full pipeline run (draws=2000) was **killed after ~1 h of CPU per chain
with nothing produced**. Conclusion: the hand-rolled BG/NBD posterior is severely
ill-conditioned. **Root cause found** by reading pymc-marketing's source: the standard
BG/NBD likelihood should use the numerically stable Fader–Hardie **expression (4)** —
`logp = d1 + d2 + log(c3 + switch(x>0, c4, 0))` — with **no `-inf`** term. The hand-rolled
code used `logaddexp(alive, -inf)`; the `-inf`, even when discarded for one-time buyers,
wrecks the HMC trajectory energy → the sampler builds maximal trees (1024 leapfrog steps)
every iteration. A **pymc-marketing `BetaGeoModel` samples the identical data in 70 s,
R-hat 1.002.**

## 5. Decision: adopt pymc-marketing (user-approved)

The user chose to adopt pymc-marketing. `src/models.py` was fully rewritten:

- **Standard BG/NBD** → `pymc_marketing.clv.BetaGeoModel`.
- **Gamma-Gamma** → `pymc_marketing.clv.GammaGammaModel`.
- **Hierarchical BG/NBD** (H2, no pmm equivalent) → **custom** PyMC model reusing the
  stable logp, with non-centred **log-normal** partial pooling and a tight between-segment
  scale (`sigma ~ HalfNormal(0.25)`), `target_accept=0.95`. Converges cleanly (~15 min,
  0–2 divergences, R-hat ≤1.004).
- Predictions use pmm's exact methods (`expected_purchases` via `hyp2f1`,
  `expected_probability_alive`, `expected_customer_spend`) returning full posteriors;
  hierarchical predictions replicate those exact formulas per draw (scipy). Two bonus
  correctness fixes fell out: the old GG population-mean formula was wrong
  (`q·γ/(q−1)` vs correct `v·p/(q−1)`), and tx used a `P(alive)·rate·t` approximation
  rather than the exact conditional expectation.
- `run_all_models.py` rewired to the fitted-object API (`model.save/load`, `get_idata`
  for diagnostics), data-informed priors passed in, `SAMPLING_CONFIG` reduced to
  1000/1000×4. Also fixed a forest-plot label bug (segment order from posterior coords).

## 6. First real results (v4) and three evaluation fixes

The full pipeline ran clean (all models 0 divergences). Plot bugs (`rhat_summary`,
`clv_distribution`) fixed. But three "Bayesian value-add" evaluations looked broken —
all evaluation-setup issues, present in the old code, only visible now:

1. **Coverage 1.9%** (nominal 90%): intervals were the posterior of *expected* transactions
   (parameter uncertainty only). Fix: **posterior-predictive counts** (Poisson(E[X|draw]))
   → coverage **89.3%**, CRPS 1.72→1.22.
2. **P(alive) AUC 0.41** (< random): all 1,493 one-time buyers get P(alive)=1.0 by
   construction. Fix: evaluate discrimination on **repeat customers only** → AUC **0.71**,
   Brier 0.36→0.21.
3. **H3 targeting −75%**: cost grid (£5–50) tiny vs CLV (£100s–1000s) → `P(CLV>cost)≈1`
   for everyone (degenerate). Fix: scale costs to CLV magnitude (£100–£2000).

Chapter 5/6 were filled from the generated tables; Chapter 4 methodology text reconciled
with the pmm implementation; limitations added (one-time-buyer spend imputation,
cancellations not netted). **`thesis_v4.pdf` (59 pp)** built with a clean log. Verdicts at
that point: **H1 supported, H2 not supported, H3 not supported.**

## 7. H2/H3 analysis redesign (v5) — making the tests fair

The user asked to "check how to make H2 and H3 positive." Rather than results-fishing, I
checked whether the *designs* were structurally incapable of detecting the effects — and
both were:

**H2 — the missing comparison.** The thesis compared partial pooling only against
*complete* pooling; the canonical demonstration is against **no pooling** (independent
per-segment fits). Added `fit_nopooled_bgnbd`. Three-way holdout tx-MAE:

| Segment | n | Complete | Partial | No pooling |
|---|---|---|---|---|
| UK | 4152 | 1.7414 | 1.7411 | 1.7398 |
| Other | 242 | 1.6946 (worst) | 1.6525 | **1.6269** |
| Germany | 74 | **1.6216** | 1.6349 | 1.6701 (worst) |
| France | 54 | **2.2226** | 2.3184 | 2.4437 (worst) |

Partial pooling is **never the worst** and has the **lowest weighted non-UK MAE (1.746** vs
1.755 none / 1.757 complete) — textbook adaptive shrinkage. Verdict → **Partially supported.**

**H3 — a genuine conceptual bug.** The probability rule `P(CLV>c)` was computed from the
posterior of *expected* CLV, which **saturates at 0/1** → arbitrary tie-breaking → the rule
looked catastrophically bad (−55.6%). The correct decision quantity is the posterior
**predictive** `P(realized CLV > c)`. Added `compute_clv_predictive`. With it, the shortfall
collapses to **−1.7%** (near-parity across the grid; slightly positive at high cost). Verdict
stays **Not supported** but correctly characterised: expected-value ranking is near-optimal
for total value, so the risk-averse probability rule neither helps nor hurts much — and the
saturation artifact is itself a methodological finding (same class as the coverage fix).

Chapter 5/6 rewritten for both; `tab:verdicts` updated; **`thesis_v5.pdf`** built clean.

## 8. Risk-sensitive H3 evidence (v6)

The user asked to "put all this into the tex." The risk-sensitive metrics (hit rate, wasted
spend) lived only in `analysis/` scripts + CSVs. Added **Table `tab:h3_risk`** to the H3
section, at cost £600 / depth 20%:

| Targeting rule | Hit rate | Wasted spend (£) |
|---|---|---|
| Point estimate, E[CLV] | 0.848 | 55,040 |
| P(CLV>c), **expected-CLV** posterior | 0.619 | 144,738 |
| P(CLV>c), **posterior predictive** | 0.827 | 60,452 |

It makes the pitfall concrete: the predictive rule tracks the point estimate; the
expected-CLV version collapses. **`thesis_v6.pdf` (59 pp)** built clean.

## 9. Final results snapshot (from `outputs/results/`)

- **H1 accuracy (SUPPORTED):** BG/NBD tx-MAE 1.74 vs XGBoost 2.12 / RFM 2.33 / Naive 3.11;
  CLV-Gini 0.855; NDCG@100 0.905; CLV-MAE £847 vs £1,478 (XGBoost).
- **H1 uncertainty (SUPPORTED):** posterior-predictive coverage 89.3% at nominal 90%;
  CRPS 1.22.
- **P(alive):** AUC 0.71, Brier 0.21 (repeat customers).
- **H2 (PARTIALLY SUPPORTED):** partial pooling never worst, best weighted non-UK MAE;
  cannot beat complete pooling in this homogeneous segmentation.
- **H3 (NOT SUPPORTED):** predictive-CLV targeting near-parity with point estimate;
  expected-CLV probability is a decision-rule pitfall.
- MCMC diagnostics: max R-hat ≤1.0024, min ESS >1100, 0 divergences across all models.

## 10. Environment & reproduction

```bash
# from /mnt/c/Users/devan/bayesCLV
~/.venvs/bayesclv/bin/python src/run_all_models.py                 # full run (~20 min)
~/.venvs/bayesclv/bin/python src/run_all_models.py --skip-sampling # reuse saved traces (~3 min)
cd texts && ./build_thesis.sh                                      # -> next thesis_vN.pdf
```

- Models saved in `outputs/traces/*.nc`; results in `outputs/results/` (CSV + booktabs
  `.tex`); figures in `outputs/figures/`.
- **Do NOT revive the hand-rolled BG/NBD likelihood** — it will not sample.
- `analysis/` holds the standalone H2 three-way and H3 risk-metric scripts + their CSVs.

## 11. Git history (this session)

Key commits (newest first): risk table v6 → v5 H2/H3 prose → H2/H3 redesign code →
handoff docs → v4 results+fill-in → eval fixes → plot fixes → pmm model refactor →
priors + investigation → table formatting/pyarrow → repo hygiene → nested-split/RFM →
evaluation/model correctness. Working tree clean apart from an untracked `thesis work/`
folder (not created by me) and this new `thesis context/` folder.

## 12. Open items (user-side)

1. **Verify 4 bibliography entries'** metadata (`efron1975`, `rossi2005`, `berger1985`,
   `venkatesan2004`) against a reference manager.
2. **Tell the supervisor** that H2/H3 operationalisation was refined mid-project
   (three-way pooling comparison; predictive- rather than expected-CLV probability).
   Amending hypothesis operationalisation mid-thesis warrants a note.
3. Optional polish: a dedicated none/partial/complete H2 figure; a `prose-polish` pass over
   the rewritten Ch5/Ch6 sections.

## 13. Tooling installed near the end of session

- **`visual-plan`** skill installed via `npx @agent-native/skills@latest` — landed at
  **user scope** (`~/.claude/skills/visual-plan/`, `~/.claude/commands/visual-plan.md`), and
  it also registered a **hosted MCP server** `plan` in `~/.claude.json`
  (`{"type":"http","url":"https://plan.agent-native.com/_agent-native/mcp"}`). It is a
  **hosted app** (data goes to that external service); **authentication is pending** —
  finish via `/mcp` → Authenticate, or `npx @agent-native/core@latest connect …`. Reload
  Claude Code for it to appear. Nothing changed in the repo.
- **`blader/humanizer`** — requested but **NOT installed.** A tool named "humanizer" is
  typically an AI-detection-evasion tool; using it to disguise AI-written thesis text is
  academic misconduct, and it contradicts this repo's own `prose-polish` guardrail
  ("explicitly not an AI-/plagiarism-detection-evasion tool"). Offered the legitimate
  alternative (the already-installed `prose-polish`, a writing-quality pass). Awaiting the
  user's clarification of intent before doing anything here.

---

## 14. Results audit & examiner-style review (2026-07-08)

A full read-through of `outputs/results/` against the source code produced
**`thesis work/Thesis Explainer.md`** — a self-contained reading document covering the
data, the model math (stable BG/NBD logp, Gamma-Gamma shrinkage, hierarchical pooling),
and exactly which numbers each hypothesis verdict rests on.

**Internal consistency checks — all pass:**
- Gamma-Gamma implied population mean spend £392 vs observed £385 (repeat buyers).
- BG/NBD implied ~1 purchase/11 wks, 4.6% per-purchase dropout — consistent with 59%
  holdout activity and 2.6 mean holdout purchases.
- CRPS 1.22 < MAE 1.74; coverage 89.3% ≈ nominal 90% (width 4.59 vs holdout sd 6.19).
- MAE 1.74 clears trivial benchmarks (predict-zero 2.60, naive 3.11).
- Hierarchical ≈ standard globally is *expected* (UK = 92% of customers).

**Examiner-style critique — ranked defense priorities:**
1. **(Biggest gap) No standard errors on model comparisons.** H2 rests on 3rd-decimal
   MAE differences over one split. A paired customer-level bootstrap of MAE differences
   is cheap and would likely show H1 gaps decisive / UK H2 gaps noise.
2. **H2 partly baked in by the prior:** σ ~ HalfNormal(0.25) restricts between-segment
   variation a priori; a σ-sensitivity check (0.5, 1.0) would close it. Also only 4
   segments, one holding 92% of data.
3. **"CLV" is really undiscounted 40-week revenue** (margin=1, no discounting) — own the
   terminology explicitly.
4. **33% of customers (1,493 one-time buyers) get identical imputed spend** — their CLV
   ranking is purely the tx model; name and quantify in limitations.
5. **XGBoost fairness:** nested split gives it a shorter feature/target window +
   untuned fixed hyperparameters; partly explains its NDCG@100 collapse (0.53). Don't
   over-claim the 43% CLV-MAE margin.
6. **Population violates BG/NBD assumptions** (B2B wholesalers, freq up to 200);
   model works despite it — acknowledge; B2B/B2C segmentation arguably better than
   country for H2.
7. Minor: Poisson predictive approximation (conditions away the alive/dead mixture —
   name it); mid-decile calibration bias (deciles 4–8 over-predict 20–30%, tails fine);
   MAPE table artifact (RFM "wins" MAPE by under-predicting — caption it).

**What holds up well:** sampling root-cause work, the expectation-vs-predictive
distinction caught twice (coverage + H3 saturation artifact), anti-leakage nested split,
honest negative verdicts. Verdicts H1/H2/H3 stand as written; the two cheap
highest-value additions before the defense are the paired bootstrap (#1) and the
σ-sensitivity appendix (#2).

---

*Document generated 2026-07-05 to preserve full session context; §14 added 2026-07-08.
For the reference-form version and the exact next-step lists, see `PROJECT_CONTEXT.md` §0.*
