# The Thesis, Explained: Bayesian CLV on Online Retail II

*A reading document generated 2026-07-08 from the actual pipeline outputs in `outputs/results/`, the source code in `src/`, and the processed data in `data/processed/`. Every number here was read from those files, not from the thesis prose. Math renders in Obsidian ($…$ blocks).*

---

## 1. The one-paragraph version

You took 4,522 customers of a UK online gift retailer, watched them for **65 weeks** (Dec 2009 – Mar 2011, the "calibration" window), and asked four models to predict what each customer would do in the following **40 weeks** (Mar – Dec 2011, the "holdout" window): how many purchases, and how much money. The Bayesian model (BG/NBD + Gamma-Gamma) beat XGBoost, an RFM heuristic, and a naive mean on essentially every accuracy and ranking metric (**H1 supported**), and it was the only model that could honestly say how *unsure* it was (89.3% of customers fell inside its 90% prediction intervals). A hierarchical version that shares information across countries helped small countries a bit but couldn't beat the simple pooled model (**H2 partially supported**). And ranking customers by "probability CLV exceeds the campaign cost" turned out to be no better than just ranking by expected CLV (**H3 not supported**) — but diagnosing *why* the naive version of that rule failed produced the most interesting methodological finding in the thesis.

---

## 2. The data

**Source:** UCI Online Retail II — invoice-level transactions of a UK-based online giftware retailer (many wholesale/B2B buyers), Dec 2009 to Dec 2011.

**Cleaning** (`src/data.py: clean_transactions`): drop rows without a customer ID, drop cancellations and non-product stock codes (postage, discounts "D", etc.), compute `Revenue = Quantity × Price`.

**Temporal split** at `CAL_END = 2011-03-01`:

| Window | Dates | Length | Rows |
|---|---|---|---|
| Calibration (training) | 2009-12-01 → 2011-02-28 | ~65 weeks | 473,386 line items |
| Holdout (evaluation) | 2011-03-01 → 2011-12-09 | ~40.4 weeks | 329,293 line items |

**Customer summary** — each of the **4,522** customers who purchased in calibration is reduced to four numbers (this is the entire input to the Bayesian models):

- $x$ = **frequency** — number of *repeat* purchases (invoices − 1). One-time buyers have $x = 0$. **1,493 customers (33%) are one-time buyers.**
- $t_x$ = **recency** — weeks between first and last purchase.
- $T$ = **age** — weeks between first purchase and the end of calibration.
- $\bar{m}$ = **monetary value** — mean revenue per *repeat* invoice (first purchase excluded, per Gamma-Gamma convention).

Key statistics: mean frequency 3.78 (max 200 — that's a wholesaler), mean $T$ = 41.8 weeks, mean monetary value £258 (repeat buyers: ~£385), median £188.

**Country segments** (for H2): countries with <30 customers collapsed into "Other" → **UK 4,152 · Other 242 · Germany 74 · France 54**. Note the imbalance: UK is 92% of the base.

**Holdout ground truth:** in the 40-week holdout, the average customer made **2.60 purchases** (sd 6.19 — hugely dispersed) and spent **£1,284**; **59% were active** (≥1 purchase). Spend is violently skewed: the top 1% of customers account for **36% of all holdout revenue**. Keep this skew in mind — it explains why the pound-denominated errors look large and why ranking metrics are the ones that matter.

---

## 3. The models and their math

### 3.1 BG/NBD — "how many purchases?" 

The Beta-Geometric/Negative-Binomial-Distribution model (Fader, Hardie & Lee 2005) tells a simple behavioral story about each customer:

1. **While alive**, a customer buys at random times, at a personal rate $\lambda$: purchases follow a Poisson process, so the number of purchases in $t$ weeks is Poisson($\lambda t$).
2. **After every purchase**, the customer flips a coin: with probability $p$ they "die" (silently churn — you never observe it).
3. **Heterogeneity:** rates vary across customers, $\lambda \sim \text{Gamma}(r, \alpha)$; dropout probabilities vary too, $p \sim \text{Beta}(a, b)$.

Only four population parameters $(r, \alpha, a, b)$ are estimated; each customer's $\lambda$ and $p$ are integrated out analytically. The likelihood for one customer with summary $(x, t_x, T)$ — the numerically stable Fader–Hardie "expression (4)" used by pymc-marketing and by your `_stable_bgnbd_logp`:

$$
\ln L = \underbrace{\ln\frac{\Gamma(r+x)}{\Gamma(r)} + \ln\frac{B(a, b+x)}{B(a,b)}}_{d_1} + \underbrace{r\ln\alpha - (r+x)\ln(\alpha+t_x)}_{d_2} + \ln\!\Big(\underbrace{\Big(\tfrac{\alpha+t_x}{\alpha+T}\Big)^{r+x}}_{c_3\,:\ \text{still alive}} + \underbrace{\mathbb{1}[x>0]\,\tfrac{a}{b+x-1}}_{c_4\,:\ \text{died at } t_x}\Big)
$$

Intuition: $c_3$ is the (relative) likelihood the customer is still alive and simply hasn't bought since $t_x$; $c_4$ is the likelihood they died right after their last purchase. The model weighs these two explanations of the silence. *(The sampling saga of last session: the original hand-rolled code expressed this same sum via `logaddexp` with a $-\infty$ term for one-time buyers, which destroyed the HMC energy landscape — mathematically equivalent, computationally fatal.)*

**Fitted posterior (your data):**

| Param | Mean | 94% HDI | Interpretation |
|---|---|---|---|
| $r$ | 0.651 | [0.61, 0.69] | shape of purchase-rate distribution |
| $\alpha$ | 7.12 | [6.62, 7.64] | scale — mean rate $r/\alpha \approx 0.091$/week ≈ **1 purchase every 11 weeks** |
| $a$ | 0.216 | [0.14, 0.29] | Beta shape |
| $b$ | 4.47 | [2.49, 6.78] | mean dropout $a/(a{+}b) \approx 4.6\%$ **per transaction** |

Sanity: a 4.6%-per-purchase death rate means a typical customer survives ~15 purchases; combined with 1 purchase/11 weeks, most of the base survives the 40-week holdout — consistent with the observed 59% active rate. The parameters tell a coherent story.

### 3.2 Gamma-Gamma — "how much per purchase?"

Fitted **only on the 3,029 repeat buyers** (you need ≥1 repeat purchase to observe an average spend). The story: customer $i$'s observed average spend $\bar{m}_i$ across $x_i$ transactions is a noisy Gamma realization around their true latent mean spend, and those latent means vary across the population:

$$
\bar{m}_i \mid \nu_i \sim \text{Gamma}(p x_i,\ \nu_i x_i), \qquad \nu_i \sim \text{Gamma}(q, \gamma)
$$

The conditional expected spend for a customer shrinks their observed average toward the population mean, with shrinkage weight decreasing in $x_i$ (more transactions = trust the customer's own average more):

$$
\mathbb{E}[m \mid \bar{m}_i, x_i] = \frac{(q-1)\,\gamma\, /\,(q-1) + \ldots}{\ldots} \;=\; \underbrace{\frac{q-1}{px_i+q-1}}_{\text{weight on population}} \cdot \frac{\gamma p}{q-1} \;+\; \underbrace{\frac{p x_i}{p x_i + q-1}}_{\text{weight on own data}} \cdot \bar{m}_i
$$

**Fitted:** $p = 1.71$, $q = 3.97$, $\nu \,(= \gamma) = 681$. Implied population mean spend $= \nu p/(q-1) = 681 \times 1.71 / 2.97 \approx \mathbf{£392}$ — vs. the observed repeat-buyer mean of **£385**. The model recovers the data almost exactly. *(This is also where the earlier prior bug lived: default priors implied a median population spend of £8.68 — 44× off — which is why `src/priors.py` now derives data-scaled HalfNormal priors by method-of-moments: $\sigma_\gamma = 321.7$, etc.)*

### 3.3 CLV = transactions × spend

$$
\text{CLV}_i = \mathbb{E}[X_i(40\text{w})] \times \mathbb{E}[m_i] \times \text{margin}
$$

computed **per posterior draw**, giving a full CLV *distribution* per customer, not one number. Two honesty notes baked into the code: margin = 1.0 and no discounting, so "CLV" here is really *expected 40-week gross revenue*; and one-time buyers (33% of the base!) have no Gamma-Gamma estimate, so they're imputed the population mean spend — their CLV variation comes entirely from the transaction model.

### 3.4 Hierarchical BG/NBD (H2)

Each country segment $s$ gets its own $(r_s, \alpha_s, a_s, b_s)$, tied together by a log-normal partial-pooling prior (non-centred parameterization for sampler stability):

$$
\theta_s = \exp(\mu_\theta + \sigma_\theta z_{\theta,s}), \quad z \sim \mathcal{N}(0,1), \quad \sigma_\theta \sim \text{HalfNormal}(0.25)
$$

The $\sigma_\theta$ hyperparameter is what the data uses to decide *how much* to share: $\sigma \to 0$ collapses to complete pooling, $\sigma \to \infty$ to independent fits. The HalfNormal(0.25) scale is deliberately tight (roughly: segments can differ by ~±25–50% a priori) — chosen for sampling stability. **Remember this choice; it matters for how to read H2 (§7).**

The fitted per-segment parameters show textbook shrinkage: France, with only 54 customers, has $r_{\text{France}} = 0.90 \pm 0.21$ (wide, pulled toward the population); the UK, with 4,152, has $r_{\text{UK}} = 0.658 \pm 0.020$ (essentially the pooled value, dominating the hyperprior).

### 3.5 The baselines

- **Naive:** everyone gets the calibration population mean purchase rate × 40 weeks. No individual variation.
- **RFM heuristic:** score customers 1–5 on recency/frequency/monetary quintiles, predict segment averages. (Fixed last session: R-score bins are now fitted on recency/T ratios, not raw weeks.)
- **XGBoost two-stage:** gradient boosting (300 trees, depth 4, lr 0.05) on ~15 engineered features (RFM + purchase rate, inter-purchase time, recency ratio, log-monetary, country dummies, spend trend…). Two separate models: transaction count and spend. Crucially, trained on a **nested temporal split** (features before Oct 2010 → targets Oct 2010–Mar 2011) so it never sees the real holdout — the leakage fix from last session.

---

## 4. How the evaluation works

Every model produces, for all 4,522 customers, (a) predicted holdout transactions and (b) predicted holdout CLV. These are compared to the realized truth:

- **MAE / RMSE** — pound-and-count accuracy.
- **Spearman / Gini / NDCG@k** — *ranking* quality: does the model order customers correctly by value? (This is what a marketer actually uses.) NDCG@100 asks specifically: of the customers you'd rank in the top 100, how much of the best-possible-top-100 value did you capture?
- **Calibration by decile** — group customers into 10 predicted-value bins, compare mean predicted vs. mean actual per bin.
- **Bayesian-only:** 90% **credible-interval coverage** (do 90% intervals contain the truth 90% of the time?) and **CRPS** (a proper scoring rule generalizing MAE to distributions — lower is better, and if your distribution is honest, CRPS < MAE).
- **P(alive) classification** — AUC/Brier for predicting who stays active, evaluated on repeat customers only (one-time buyers get P(alive)=1 by construction — the model has never seen them *not* return after a repeat purchase, so including them poisons the metric; this was one of last session's eval fixes).

One subtlety that matters enormously (it was the coverage bug): intervals must come from the **posterior predictive**, not the posterior of the expectation. The posterior of $\mathbb{E}[X]$ answers "how unsure am I about this customer's *average*?" — a narrow band. The realized count $X$ additionally has Poisson noise around that average. The code now draws $X^{rep} \sim \text{Poisson}(\mathbb{E}[X \mid \text{draw}])$ per posterior draw. Same distinction drives the H3 fix (§6.3).

---

## 5. The results, table by table

### 5.1 The headline comparison (`metrics_comparison.csv`) → H1

| Model | tx MAE | tx RMSE | CLV MAE (£) | CLV Gini | NDCG@100 |
|---|---|---|---|---|---|
| **Hierarchical BG/NBD** | **1.742** | 3.310 | **847** | 0.855 | **0.905** |
| **BG/NBD (Bayesian)** | 1.743 | **3.306** | 847 | **0.855** | 0.905 |
| XGBoost (two-stage) | 2.117 | 3.768 | 1,478 | 0.801 | 0.534 |
| RFM Heuristic | 2.330 | 6.366 | 1,160 | 0.785 | 0.531 |
| Naive (mean) | 3.114 | 6.212 | 1,620 | 0.070 | 0.017 |

**What conclusion follows from what:** BG/NBD beats XGBoost by **18% on transaction MAE** and **43% on CLV MAE**. But the most dramatic gap is **NDCG@100: 0.905 vs 0.534** — at the business-critical task of naming your top-100 customers, the Bayesian model captures ~90% of achievable value and XGBoost only ~53%. The Gini gap is much smaller (0.855 vs 0.801): XGBoost ranks the *bulk* of customers almost as well but badly misidentifies the extreme top — precisely where money is concentrated (top 1% = 36% of spend). This asymmetry is the real content of H1.

Also part of H1: **coverage 89.3% at nominal 90%**, and **CRPS 1.22 < MAE 1.74** (the distributional forecast is strictly more informative than its own point summary — exactly what a well-calibrated Bayesian model should show). No baseline can produce these quantities at all. Together: **H1 supported**, on both the accuracy leg and the uncertainty leg.

Targeting lift confirms it economically (`targeting_lift.csv`): the Bayesian top-5% captures **10.1×** random selection's value (XGBoost 9.1×, RFM 8.1×).

### 5.2 The pooling comparison (`country_level_mae.csv`) → H2

Transaction MAE by segment, three ways to treat countries plus the baselines:

| Segment | n | Complete pooling | **Partial (hier.)** | No pooling | XGBoost |
|---|---|---|---|---|---|
| UK | 4,152 | 1.7414 | 1.7411 | **1.7398** | 2.114 |
| Other | 242 | 1.6946 ⟵ worst | 1.6525 | **1.6269** | 2.057 |
| Germany | 74 | **1.6216** | 1.6349 | 1.6701 ⟵ worst | 2.366 |
| France | 54 | **2.2226** | 2.3184 | 2.4437 ⟵ worst | 2.329 |

**What conclusion follows from what:** the hypothesis said partial pooling should beat complete pooling in small segments. It doesn't, cleanly — Germany and France are actually best under *complete* pooling. But look at the pattern: complete pooling is worst for "Other," no pooling is worst for Germany and France (54–74 customers is too few for independent estimation — classic overfitting), and **partial pooling is never the worst anywhere** and has the lowest customer-weighted non-UK MAE (1.746 vs 1.755 no-pooling vs 1.757 complete). That is exactly the adaptive-shrinkage insurance policy the hierarchical literature promises. Hence the honest verdict: **partially supported** — the mechanism demonstrably operates, but on *this* dataset the countries are similar enough that complete pooling was never leaving much on the table. (Caveat in §7: the differences are in the third decimal and no significance test backs them.)

### 5.3 Targeting simulation (`targeting_simulation_*.csv`, `h3_risk_*.csv`) → H3

Two decision rules go head-to-head across a cost grid (£100–£2,000) and targeting depths (5–50%): rank by **posterior-mean CLV** (what a frequentist would do) vs. rank by **P(CLV > cost)** (risk-aware, uses the whole posterior). At the headline setting (cost £600, depth 20%):

| Rule | Hit rate | Wasted spend | Net value |
|---|---|---|---|
| Point estimate E[CLV] | 0.848 | £55,040 | £3.88M |
| P(CLV>c) from **expected**-CLV posterior (the bug) | 0.619 | £144,738 | £1.72M |
| P(CLV>c) from **posterior predictive** (correct) | 0.827 | £60,452 | £3.83M |

**What conclusion follows from what:** the correct predictive rule lands within **−1.7%** of point-estimate targeting (and reaches slight parity/positive territory at high costs and deep targeting: +0.3% at £1,200/50%). So **H3 is not supported** — for maximizing total captured value, the posterior mean was already the right statistic, which is actually a theorem-shaped result (expected value maximization only needs the expectation). The probability rule encodes *risk aversion*, and the total-value criterion never rewards it.

The interesting part is the middle row. Computing P(CLV > c) from the posterior of the *expected* CLV saturates: parameter uncertainty is small, so nearly every customer's P is ≈0 or ≈1, ranking degenerates to arbitrary tie-breaking, and performance collapses (hit rate 0.62, 2.6× the wasted spend). This is the same expectation-vs-predictive confusion as the coverage bug, now with a price tag of ~£90k of simulated wasted spend — a genuinely publishable methodological caution.

### 5.4 Diagnostics — can we trust the MCMC at all?

Yes, unambiguously: across all three models, **max R̂ = 1.0024** (threshold 1.01), **min bulk-ESS ≈ 1,126** (threshold ~400), **0 divergences**. Hierarchical per-segment R̂ ≤ 1.0022. This is as clean as MCMC output gets.

---

## 6. Do the results make internal sense? (cross-checks)

I verified these against the raw outputs; they all hold up:

1. **Gamma-Gamma recovers the observed mean spend:** implied £392 vs observed £385 (repeat buyers). ✔
2. **BG/NBD parameters ↔ observed activity:** implied ~1 purchase/11 weeks and 4.6% per-purchase dropout are consistent with 59% holdout activity and 2.6 mean holdout purchases. ✔
3. **CRPS (1.22) < MAE (1.74)** — necessary condition for the posterior being informative rather than decorative. ✔
4. **Coverage 89.3% ≈ nominal 90%** with mean interval width 4.59 transactions — wide, but honest given holdout sd of 6.19. ✔
5. **MAE 1.74 clears the trivial benchmarks:** always-predict-zero would score 2.60 (the mean actual), the fitted naive scores 3.11. ✔
6. **Naive's Spearman is blank and its Gini is 0.05** — a constant prediction has no ranking; the residual 0.05 is tie-breaking noise. Correct behavior, correctly reported. ✔
7. **Hierarchical ≈ standard everywhere** (MAE 1.7415 vs 1.7427, coverage 89.4 vs 89.3, AUC 0.709 vs 0.711): with UK = 92% of customers, the hierarchical model *must* essentially reproduce the pooled model globally. If it didn't, something would be wrong. ✔

Two things that "look bad" but are actually understood:

- **CLV MAE of £847 against mean holdout spend of £1,284** looks terrible (66% relative error) — but with top-1%-owns-36% skew, pound-level accuracy is unachievable by *any* model (XGBoost: £1,478). This is why the thesis correctly leans on ranking metrics. The honest framing: nobody can predict *how much* a whale will spend; the Bayesian model is best-in-class at predicting *who* the whales are.
- **Mid-decile calibration bias:** deciles 4–8 over-predict by 22–32% (e.g., decile 7: predicted 2.43, actual 1.91), while the tails are nearly perfect (top decile: 11.4 vs 12.0, 5% error). The model systematically over-predicts moderately active customers — likely a cohort effect (mid-frequency customers churning faster than the stationary BG/NBD story allows) plus holdout seasonality. This is real, visible in `calibration_*.csv`, and worth owning in the limitations rather than hoping nobody bins the predictions.

---

## 7. What would a PhD-level examiner say?

Overall reaction first, then the itemized critique. **This is a solid, honest piece of Master's work whose defining virtue is that it reports negative results correctly and diagnoses *why* they're negative.** The sampling investigation, the expectation-vs-predictive distinction (caught twice, in coverage and in H3), and the nested temporal split for XGBoost are all above the typical Master's bar. But an examiner would push hard on several points:

### Likely major questions (be prepared to defend)

1. **"None of your model comparisons carries a standard error."** The H2 verdict rests on MAE differences in the *third decimal* (1.7414 vs 1.7411 vs 1.7398 for the UK) over a single holdout window. A paired bootstrap over customers (resample customers, recompute each model's MAE, look at the distribution of *differences*) would cost an afternoon and would likely show the UK differences are pure noise while the H1 gaps (1.74 vs 2.12) are decisive. Without it, "partial pooling is never the worst" is a pattern claim without an uncertainty statement — ironic in a thesis about uncertainty quantification. **This is the single most attackable point in the thesis.**

2. **"Your H2 conclusion is partly baked in by the prior."** $\sigma_\theta \sim \text{HalfNormal}(0.25)$ *a priori* restricts between-country parameter variation to roughly ±25–50%. With that prior, partial pooling can never stray far from complete pooling — so "partial ≈ complete" is partly an assumption, not purely a finding. The thesis does acknowledge the tightness ("required for stable sampling"), but an examiner will ask: *did you try σ ~ HN(0.5) or HN(1.0) and check the conclusion survives?* A prior-sensitivity appendix would close this. Related: **four segments is very few** for estimating a between-group variance (the hierarchical literature usually wants ≥5–8 groups), and one group holding 92% of the data means the hyperparameters are essentially set by the UK.

3. **"This isn't CLV, it's a 40-week revenue forecast."** No profit margin, no discounting, no projection beyond the holdout horizon. The models *can* do infinite-horizon discounted CLV (the standard DERT formula). Defensible choice — you can only validate against a finite window — but the terminology should be owned explicitly: what's validated is *expected 40-week revenue*, and "CLV" is used by convention.

4. **"A third of your customers have an imputed spend."** 1,493 one-time buyers all receive the identical population-mean monetary value, so their CLV ranking is decided entirely by the transaction model. Any spend-side heterogeneity among one-time buyers (e.g., a huge first basket signaling a wholesale buyer) is invisible. An obvious refinement — using the *first-purchase* value as a covariate or prior for one-time buyers — is known in the literature (Fader & Hardie discuss the first-purchase problem). Should at minimum be a named limitation with the affected population quantified (33%).

5. **"Is XGBoost a fair opponent?"** Two handicaps: (a) the nested split is the *right* leakage fix, but it means XGBoost trains on ~10 months of features and a 5-month target window, then predicts a 40-week horizon it was never trained on (rescaled via `t_future`), while BG/NBD gets all 15 months; (b) hyperparameters are fixed (300 trees, depth 4) with no tuning/early stopping on a validation fold. The catastrophic NDCG@100 (0.534) partly reflects this: it misses whales it never saw in its truncated target window. The defense is honest ("both models get only calibration data; the split is the standard way to supervise a regressor without leakage; tuning XGBoost harder wouldn't fix a target-window problem") — but expect the question, and don't over-claim the 43% CLV-MAE margin as pure model superiority.

6. **"Your population violates the model's assumptions."** Online Retail II mixes B2C gift buyers with wholesale/B2B customers (frequency up to 200 in 65 weeks; £8,416 average basket at the extreme). BG/NBD assumes a homogeneous "buy until you die" process with Gamma-distributed rates; wholesalers on procurement cycles aren't that. The model performs well *despite* this — worth one paragraph acknowledging it, ideally noting that the hierarchical machinery could in principle segment B2B/B2C rather than geography (arguably a more promising segmentation than country, which would also strengthen the H2 story).

### Likely minor points

7. **Poisson predictive approximation:** `posterior_predictive_counts` draws $X \sim \text{Poisson}(\mathbb{E}[X|\text{draw}])$, which conditions away the alive/dead mixture — the true BG/NBD predictive is over-dispersed relative to this. Empirically the coverage (89.3%) says the approximation is adequate, and that's a fine defense, but the approximation should be named as such (it is, in the docstring — make sure it's in the thesis too).
8. **Mid-decile calibration bias** (§6): 20–30% over-prediction in deciles 4–8 deserves a sentence; the stationarity assumption is the likely culprit.
9. **MAPE cherry-pick hazard:** RFM "wins" MAPE (58.6 vs 91.8) purely because it under-predicts small values. The thesis shouldn't let that number stand without the explanation (MAPE is asymmetric and degenerate near zero actuals — good that the table reports it, but caption it).
10. **Cancellations are dropped, not netted** — returns inflate realized "value." Already in limitations; keep it there.
11. **Single dataset, single split:** conclusions are about *this* retailer in *this* year. Standard Master's-level external-validity caveat.

### What the examiner would praise

- The **root-cause diagnosis of the sampling failure** (likelihood parameterization, not priors — with the £8.68-vs-£385 prior-predictive smoking gun properly documented). Most students would have shipped the ill-conditioned sampler at 4 chains × 13 minutes and called it done.
- **Catching the expectation/predictive confusion twice** and turning the H3 failure into a methodological contribution (the saturation artifact with its £90k simulated price tag is a genuinely teachable result).
- **Anti-leakage discipline** (nested temporal split) — rarer than it should be in CLV benchmarking papers.
- **Honest verdicts.** "H2 partially supported, H3 not supported" with mechanistic explanations is worth more academically than three confirmations. The examiner has read a hundred theses where every hypothesis is miraculously supported.

### Bottom line

The results are trustworthy and the story is coherent: **defensible as-is**, with points 1 (bootstrap the MAE differences) and 2 (prior-sensitivity check for σ) being the two cheap additions with the highest defense value. Everything else is framing: own the limitations before the examiner finds them.

---

## 8. Where every number in this document came from

| Claim | Source |
|---|---|
| Comparison table, MAE/Gini/NDCG | `outputs/results/metrics_comparison.csv` |
| Coverage 89.3%, CRPS 1.22, width 4.59 | `outputs/results/credible_interval_coverage.csv` |
| P(alive) AUC 0.71, Brier 0.21 | `outputs/results/p_alive_evaluation.csv` |
| Lift 10.1× at top-5% | `outputs/results/targeting_lift.csv` |
| H2 three-way MAE table | `outputs/results/country_level_mae.csv` |
| BG/NBD & GG posteriors, R̂, ESS | `outputs/results/posterior_summary_*.csv` |
| H3 net value / improvement % | `outputs/results/targeting_simulation_bg_nbd_bayesian.csv` |
| H3 hit rate / wasted spend | `outputs/results/h3_risk_metrics.csv`, `h3_risk_predictive.csv` |
| Calibration deciles | `outputs/results/calibration_*.csv` |
| Data statistics, split dates, skew | `data/processed/*.parquet` (computed fresh) |
| Model math | `src/models.py` (`_stable_bgnbd_logp`, `build_hierarchical_bgnbd`, `compute_clv_*`), `src/priors.py` |
| Evaluation logic | `src/evaluation.py` (`targeting_simulation`, `compute_posterior_metrics`) |
