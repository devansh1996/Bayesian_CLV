# -*- coding: utf-8 -*-
# Academic register. Terminology is used where it is load-bearing and not
# otherwise; no formalism is introduced that the argument does not require.

# ── 2 ───────────────────────────────────────────────────────────────────────
s = slide("Motivation and empirical setting", kicker="Introduction",
 notes=("~1.5 min. Customer lifetime value governs acquisition and retention spend. The difficulty is "
        "that acquisition cost is incurred before any value is realised, so allocation requires a "
        "forward estimate rather than an accounting record of past spend.\n\n"
        "The empirical setting is the UCI Online Retail II dataset — a UK giftware retailer, two years "
        "of transactions, 4,522 customers after cleaning. The calibration/holdout split is at 1 March "
        "2011, giving a 40.4-week evaluation window. Every accuracy figure I report is out-of-sample "
        "against that window."))
claim(s, "Spend allocation requires a forward estimate of customer value; historical spend is an "
         "accounting record, not a predictor of future contribution.")
stat_row(s, [("4,522","customers after cleaning",NAVY),
             ("40.4 wks","holdout evaluation window",NAVY),
             ("£385","mean transaction value\n(median £299)",NAVY),
             ("33%","single-purchase customers",BRAND)], top=In(2.45))
bullets(s, [
 "UCI Online Retail II — UK giftware retailer, December 2009 to December 2011",
 "Temporal calibration/holdout split at 1 March 2011; all reported accuracy is out-of-sample",
 "Value is concentrated, so allocation depends on ordering customers correctly rather than on average error",
], top=In(4.25), size=17)

# ── 3 ───────────────────────────────────────────────────────────────────────
s = slide("The identification problem", kicker="Problem statement",
 notes=("~2 min. This is the hinge of the thesis. In a contractual setting the customer cancels, so "
        "churn is observed and dated, and standard survival methods apply. In a non-contractual "
        "setting there is no such event: customers cease purchasing without notice.\n\n"
        "The consequence is that a given interval of inactivity is uninformative in isolation. Fifteen "
        "weeks of silence is improbable for a customer purchasing every three weeks and entirely "
        "ordinary for one purchasing twice a year. Recency acquires meaning only relative to that "
        "customer's own established rate.\n\n"
        "Two implications follow, and both constrain the method. First, no churn label exists for any "
        "customer, so a supervised formulation of attrition is not identified. Second, a fixed recency "
        "threshold imposes an arbitrary cut that necessarily misclassifies one of those two profiles. "
        "Activity status must therefore be inferred jointly with the purchase rate."))
claim(s, "Attrition is never observed in a non-contractual setting, so activity status must be inferred "
         "jointly with the purchase rate rather than measured.")
bullets(s, [
 ("Contractual settings", "Cancellation is observed and dated; survival methods apply directly."),
 ("Non-contractual settings", "Purchasing ceases without notice. No attrition event is ever recorded."),
], top=In(2.5), size=18)
box(s, [("Fifteen weeks of inactivity is improbable for a customer purchasing every three weeks, "
         "and unremarkable for one purchasing twice a year.", 16, False, INK),
        ("Recency is informative only relative to that customer's own rate — which is why no fixed "
         "threshold can separate the two, and why no churn label exists to train on.", 16, True, NAVY)],
    In(4.5), In(1.35))

# ── 4 ───────────────────────────────────────────────────────────────────────
s = slide("Research gap", kicker="Literature",
 notes=("~1.5 min. Probabilistic customer-base models are well established since Fader and Hardie in "
        "2005, and I am not proposing a new estimator. Three issues remain open in the applied "
        "literature, and each maps onto one research question.\n\n"
        "First, these models produce predictive distributions, but validation is almost exclusively "
        "against point accuracy. Whether the stated intervals attain their nominal coverage is rarely "
        "examined.\n\n"
        "Second, segment structure is normally handled by complete pooling or by separate estimation. "
        "Partial pooling is standard in hierarchical modelling but under-tested on this problem.\n\n"
        "Third, and most consequentially, the posterior is computed but is seldom shown to alter a "
        "decision. If it does not, the additional inferential cost is not recovered."))
claim(s, "Three issues remain open in the applied literature; each motivates one research question "
         "and one element of the empirical design.")
bullets(s, [
 ("Validation addresses point accuracy, not the calibration of predictive intervals",
  "The customer-base literature reports error metrics; nominal coverage of stated intervals is rarely verified."),
 ("Segment structure is handled by complete pooling or separate estimation",
  "Partial pooling is standard in hierarchical modelling but has seen limited testing in this application."),
 ("Posterior uncertainty is computed but seldom shown to change a decision",
  "Absent a demonstrated effect on action, the additional inferential cost is not recovered."),
], top=In(2.5), size=16.5)

# ── 5 ───────────────────────────────────────────────────────────────────────
s = slide("Research questions and hypotheses", kicker="Aims",
 notes=("~1.5 min. Three questions. I state the verdicts now so the argument can be followed "
        "directly: H1 supported, H2 partially supported, H3 not supported.\n\n"
        "The third is the most informative of the three, because its rejection has a clean "
        "theoretical explanation rather than being an empirical disappointment. I will return to "
        "that."))
claim(s, "The three questions draw progressively more from the posterior — its location, its structure "
         "across segments, and its tails.")
bullets(s, [
 ("RQ1 — Predictive accuracy and interval calibration",
  "Against a naive baseline, an RFM heuristic and a tuned gradient-boosted benchmark.        H1: supported"),
 ("RQ2 — Partial pooling across country segments",
  "4,152 UK customers against 54 French; does sharing structure improve small-segment accuracy?        H2: partially supported"),
 ("RQ3 — Decision-theoretic value of the full posterior",
  "A targeting simulation under realistic cost assumptions, swept for robustness.        H3: not supported"),
], top=In(2.5), size=16.5)

# ── 6 SECTION ───────────────────────────────────────────────────────────────
section("Methodology", "Specification, estimation, and diagnostics", notes="~10 s.")

# ── 7 ───────────────────────────────────────────────────────────────────────
s = slide("Modelling approach", kicker="Methodology",
 notes=("~2 min. The specification states a behavioural mechanism rather than learning a mapping from "
        "features to a target, and that choice is forced rather than stylistic.\n\n"
        "The quantity governing future value — whether a customer remains active — is latent. A "
        "supervised formulation requires a target, and none exists. A generative specification can "
        "contain an unobserved component and still be estimated, because the observed purchase "
        "histories constrain it.\n\n"
        "The secondary benefit is interpretability: each parameter corresponds to a stated behavioural "
        "assumption, so the model can be criticised on substantive grounds rather than only on fit."))
claim(s, "A generative specification is required here rather than preferred: the state governing future "
         "value is latent, so no supervised target exists.")
bullets(s, [
 ("Supervised formulation", "Learns a mapping from engineered features to an observed target. Requires that target to exist."),
 ("Generative specification", "States how purchasing arises, including an unobserved component, and estimates it from histories."),
], top=In(2.5), size=18)
bullets(s, [
 "No attrition label exists for any customer, so the supervised route is not identified for this quantity",
 "Each parameter corresponds to a stated behavioural assumption, so the model is open to substantive criticism",
], top=In(4.55), size=16.5)

# ── 8 ───────────────────────────────────────────────────────────────────────
s = slide("Model components", kicker="Methodology",
 notes=("~2 min. Four components, combining the BG/NBD model of Fader and Hardie with the Gamma-Gamma "
        "specification for transaction value.\n\n"
        "While active, a customer purchases at an individual rate. After each transaction there is an "
        "opportunity to become inactive, with an individual probability. Both of those individual "
        "quantities vary across the customer base, and that variation is modelled explicitly rather "
        "than represented by a population average. Transaction value is modelled separately and is "
        "strongly right-skewed.\n\n"
        "Expected value is then the product of expected transactions and expected spend. That product "
        "requires the two components to be independent, which I test rather than assume — the "
        "correlation is 0.13, and I return to its consequence in the limitations."))
claim(s, "Purchase incidence, attrition, cross-customer variation and transaction value, estimated "
         "jointly and combined multiplicatively.")
bullets(s, [
 ("Purchase incidence", "While active, transactions arrive at a customer-specific rate."),
 ("Attrition", "Each transaction carries an opportunity to become permanently inactive, at a customer-specific probability."),
 ("Cross-customer variation", "Both quantities vary across the base and are modelled as distributions, not population averages."),
 ("Transaction value", "Modelled separately; strongly right-skewed, with a small number of large orders."),
], top=In(2.45), size=16, gap=6)
box(s, [("Expected value  =  expected transactions  ×  expected spend per transaction        "
         "(BG/NBD with Gamma-Gamma)", 16.5, True, NAVY)], In(5.65), In(0.58))

# ── 9 ───────────────────────────────────────────────────────────────────────
s = slide("Evidence for cross-customer variation", kicker="Methodology",
 notes=("~1.5 min. The third component is the one carrying the weight, and the data justifies it "
        "directly rather than by appeal to plausibility.\n\n"
        "Mean repeat transactions is 3.78. Under a single shared rate, the variance of the counts "
        "would be approximately equal to that mean. The observed variance is 77.7 — more than twenty "
        "times larger.\n\n"
        "That excess dispersion is what rules out a representative-customer specification, and it is "
        "what the mixing distributions are introduced to accommodate. It is also the mechanism behind "
        "the ranking result later: individual estimates are regularised toward the population where a "
        "customer's own history is thin."))
claim(s, "Observed dispersion is an order of magnitude beyond what a single shared rate admits, which "
         "rules out a representative-customer specification.")
stat_row(s, [("3.78","mean repeat transactions",NAVY),
             ("≈ 3.8","variance implied by a\nsingle shared rate",TEAL),
             ("77.7","variance observed\nin the data",BRAND)], top=In(2.45))
bullets(s, [
 "Over-dispersion of this magnitude is evidence of genuine heterogeneity, not sampling noise",
 "Modelling it explicitly regularises individual estimates toward the population where histories are thin",
 "This is the mechanism underlying the ranking advantage reported in the results",
], top=In(4.3), size=16.5)

# ── Distributional assumptions ──────────────────────────────────────────────
s = slide("Distributional assumptions", kicker="Methodology",
 notes=("~2 min. The specification is fully parametric, so it is worth setting out exactly what is "
        "assumed and what was estimated.\n\n"
        "While a customer is active, transactions follow a Poisson process at an individual rate. That "
        "rate varies across the base according to a Gamma distribution, estimated at shape 0.65 and "
        "rate 7.12 — implying a mean of about 0.09 transactions per week, or one roughly every eleven "
        "weeks.\n\n"
        "Attrition is a Bernoulli trial after each transaction, so the number of further transactions "
        "is geometric. That probability varies according to a Beta distribution, estimated at 0.22 and "
        "4.47, implying a mean dropout probability of 4.6 per cent per transaction.\n\n"
        "Transaction value is Gamma-distributed within a customer, with a Gamma-distributed rate across "
        "customers. The implied mean transaction value is £391, against £385 observed — so the "
        "compound is recovering the skew rather than smoothing it.\n\n"
        "The observable implication is that counts are negative binomial rather than Poisson, which is "
        "what accommodates the dispersion on the previous slide."))
claim(s, "The specification is fully parametric; each component and its estimated population parameters "
         "are set out below.")
table(s, ["Component", "Distribution", "Estimated", "Implication"], [
 ["Purchase incidence, while active", "Poisson(λ)", "—", "Memoryless timing; no scheduled cycle"],
 ["Variation in λ across customers",  "Gamma(r, α)", "r = 0.65,  α = 7.12", "Mean 0.09/week; one purchase per ~11 weeks"],
 ["Attrition, after each transaction", "Bernoulli → Geometric", "—", "Dropout tied to occasions, not calendar time"],
 ["Variation in dropout probability",  "Beta(a, b)", "a = 0.22,  b = 4.47", "Mean 4.6% per transaction"],
 ["Transaction value",                 "Gamma–Gamma(p, q, γ)", "1.71,  3.97,  681", "Implied mean £391 (observed £385)"],
], top=In(2.45), row_h=In(0.46), size=11.5)
box(s, [("Observable implication: transaction counts are negative binomial rather than Poisson — "
         "the variance exceeds the mean, which is what accommodates the dispersion shown previously.",
         15, False, INK)], In(5.72), In(0.62))

# ── Rationale for the distributional choices ────────────────────────────────
s = slide("Rationale for the distributional choices", kicker="Methodology",
 notes=("~2 min. These are not arbitrary selections, and an examiner is entitled to ask why not "
        "something else. Three criteria have to be satisfied simultaneously, and they narrow the "
        "field almost completely.\n\n"
        "Support. A purchase rate is positive, which excludes the normal distribution outright. A "
        "dropout probability lies on the unit interval, which excludes the Gamma. That single "
        "criterion removes most candidates.\n\n"
        "Flexibility. The Gamma shape parameter admits both a monotone decreasing density, where most "
        "customers are near-inactive, and a unimodal one, where a typical customer exists. The data "
        "selects between them; the estimate of 0.65 indicates the former. The Beta similarly admits "
        "J-shaped, U-shaped, unimodal and uniform forms, and the estimates produce the J-shape that "
        "encodes a large near-permanent sub-population.\n\n"
        "Tractability. Conjugacy yields a closed-form marginal likelihood — the Gamma-Poisson mixture "
        "integrates to the negative binomial, and the Beta-Bernoulli likewise. Without it, each "
        "likelihood evaluation requires a numerical integral per customer, which is infeasible at this "
        "scale; and quadrature error propagates into the gradients that the sampler depends on. In "
        "this project an early hand-written likelihood proved ill-conditioned and would not sample, "
        "which is a concrete instance of exactly that.\n\n"
        "One clarification worth stating: these are mixing distributions within the likelihood, "
        "describing population heterogeneity. They are not priors. The priors sit above them, on r, "
        "alpha, a and b."))
claim(s, "Three criteria must hold simultaneously; together they leave very few admissible candidates.")
bullets(s, [
 ("Support — the domain of the quantity",
  "A rate is positive, which excludes the normal; a probability lies on [0,1], which excludes the Gamma. Most candidates fall here."),
 ("Flexibility — the specification should not pre-judge the shape",
  "The Gamma shape admits both monotone-decreasing and unimodal densities; the estimate of 0.65 selects the former. The Beta admits J, U, unimodal and uniform forms."),
 ("Tractability — a closed-form marginal likelihood",
  "Conjugacy integrates the Gamma–Poisson mixture to the negative binomial. Otherwise each evaluation requires a numerical integral per customer, and quadrature error propagates into the sampler's gradients."),
], top=In(2.45), size=15.5, gap=5)
box(s, [("A lognormal rate satisfies the first two criteria and fails the third. In this project an "
         "early hand-written likelihood proved ill-conditioned and would not sample at all.", 14.5, False, MUTE),
        ("These are mixing distributions within the likelihood, describing population heterogeneity — "
         "not priors. The priors are placed above them, on r, α, a and b.", 15, True, NAVY)],
    In(5.55), In(1.05))

# ── 10 ──────────────────────────────────────────────────────────────────────
s = slide("Estimation", kicker="Methodology",
 notes=("~2 min. Specifying the model is tractable; evaluating the posterior is not.\n\n"
        "The posterior is proportional to the likelihood times the prior, and that product is "
        "computable for any candidate parameter vector. The normalising constant requires integration "
        "over the full parameter space and has no closed form here.\n\n"
        "Numerical quadrature does not rescue it. The two standard models carry seven parameters "
        "between them; a grid of fifty points per dimension is of order ten to the eleven likelihood "
        "evaluations, each sweeping 4,522 customers.\n\n"
        "Inference therefore proceeds by sampling. The relevant property is that the acceptance ratio "
        "and the gradient both depend on the unnormalised posterior only, so the intractable constant "
        "never has to be evaluated. I used Hamiltonian Monte Carlo with the No-U-Turn sampler, which "
        "uses the gradient to remain efficient in a correlated parameter geometry — here r and alpha "
        "correlate at 0.81."))
claim(s, "The posterior is available only up to a normalising constant, so inference proceeds by "
         "sampling rather than by evaluation.")
bullets(s, [
 ("Tractable", "Likelihood × prior, evaluated at any candidate parameter vector."),
 ("Not tractable", "The normalising constant — integration over the full parameter space, with no closed form."),
], top=In(2.5), size=18)
bullets(s, [
 "Quadrature is infeasible: seven parameters at fifty points per dimension is of order 10¹¹ likelihood evaluations",
 "Both the acceptance ratio and the gradient depend on the unnormalised posterior alone, so the constant never enters",
 "Hamiltonian Monte Carlo with NUTS, which remains efficient under the correlated geometry here (r, α correlate at 0.81)",
], top=In(4.5), size=16)

# ── 11 ──────────────────────────────────────────────────────────────────────
s = slide("Convergence diagnostics", kicker="Methodology",
 notes=("~1 min. Four chains of a thousand post-warmup draws. Potential scale reduction is at most "
        "1.0014, minimum effective sample size is approximately 1,900, and there were no divergent "
        "transitions.\n\n"
        "I want to be explicit that these are necessary and not sufficient conditions. They establish "
        "that the sampler explored the posterior; they establish nothing about whether the model is "
        "appropriate to the data. A misspecified model can converge cleanly. That is why they are "
        "reported before the substantive results rather than offered in support of them."))
claim(s, "Sampling diagnostics establish that the posterior was explored; they carry no implication "
         "about the adequacy of the specification.")
stat_row(s, [("1.0014","maximum R̂\n(threshold 1.01)",TEAL),
             ("≈ 1,900","minimum effective\nsample size",TEAL),
             ("0","divergent transitions",TEAL)], top=In(2.45))
bullets(s, [
 "Four chains, dispersed initialisation, 1,000 post-warmup draws each; step size adapted per chain",
 "Necessary but not sufficient — a misspecified model can satisfy all three, which is why they precede the results",
], top=In(4.3), size=16.5)

# ── Quantities obtained from the posterior ──────────────────────────────────
s = slide("Quantities obtained from the posterior", kicker="Methodology",
 notes=("~2 min. It is worth being explicit about what the Bayesian treatment actually yields, since "
        "this is what the results then evaluate.\n\n"
        "Sampling returns 4,000 joint draws of the population parameters. Each draw is propagated "
        "through the model to the customer level, so every customer receives a distribution rather "
        "than a point. Any posterior quantity is then a sample average over those draws — no further "
        "derivation is required for each new question.\n\n"
        "Four classes of quantity follow. The posterior of the expectation, which is what the accuracy "
        "comparison uses. The posterior predictive for a realised outcome, which is what the interval "
        "coverage and the decision rule require. The probability that a customer remains active. And "
        "the probability that value exceeds any threshold, which is the decision quantity in RQ3.\n\n"
        "The figures in the final column are for customer 14817, which I return to in the results. "
        "Note that the expectation interval and the predictive interval differ by an order of "
        "magnitude — that distinction becomes the methodological finding."))
claim(s, "Each population draw is propagated to the customer level, so every reported quantity is a "
         "sample average over 4,000 draws rather than a separate derivation.")
table(s, ["Quantity", "Obtained as", "Used for", "Customer 14817"], [
 ["Expected transactions / CLV", "Mean over draws", "Accuracy and ranking comparison", "£1,364"],
 ["Posterior of the expectation", "Quantiles over draws", "Precision of the estimate", "£1,326 – £1,401"],
 ["Posterior predictive", "Simulate an outcome per draw", "Interval coverage; decision rules", "£0 – £2,888"],
 ["P(active at end of calibration)", "Mean over draws", "Latent activity classification", "—"],
 ["P(CLV > threshold)", "Share of draws exceeding it", "Decision-theoretic targeting (RQ3)", "0.77"],
], top=In(2.45), row_h=In(0.46), size=11.5)
box(s, [("The expectation interval and the predictive interval differ by an order of magnitude. "
         "Which of the two a decision rule should use becomes the methodological finding in the results.",
         15, True, NAVY)], In(5.72), In(0.62))

# ── 12 SECTION ──────────────────────────────────────────────────────────────
section("Results", "Three hypotheses and one methodological finding", notes="~10 s.")

# ── 13 ──────────────────────────────────────────────────────────────────────
s = slide("H1 — predictive accuracy and ranking", kicker="Results",
 notes=("~2 min. Improvement in average error is present but modest, and I do not rest the case on it. "
        "The separation is in ranking.\n\n"
        "Normalised discounted cumulative gain over the top 100 is 0.91 against 0.53 for the "
        "gradient-boosted benchmark. The more directly interpretable figure is precision at 100: of "
        "the hundred customers selected, 66 belong in the true top hundred, against 49 for the "
        "benchmark and 37 for the RFM heuristic. Targeting the selected top decile reaches 62.6 per "
        "cent of realised holdout revenue, against 55.1 for RFM.\n\n"
        "Ranking is the operationally relevant criterion because value is concentrated and budgets "
        "reach the upper tail rather than the typical customer.\n\n"
        "One qualification, which I state in the thesis: the benchmark was trained on a shorter inner "
        "split to avoid leakage, so it had less data. The ranking gap should be read as an upper bound "
        "on the advantage."))
claim(s, "Separation between specifications is modest in average error and substantial in ranking, "
         "which is the operationally relevant criterion.")
picture(s, SLD+"accuracy.png", In(2.45), max_w=In(11.4), max_h=In(3.35))
box(s, [("Precision@100  0.66 vs 0.49 (benchmark) and 0.37 (RFM)        "
         "Top-decile revenue capture  62.6% vs 57.9% and 55.1%", 15.5, True, NAVY),
        ("The benchmark trained on a shorter inner split to avoid leakage; the ranking gap is therefore "
         "an upper bound on the advantage.", 14.5, False, MUTE)], In(5.95), In(1.0))

# ── 14 ──────────────────────────────────────────────────────────────────────
s = slide("H1 — calibration of predictive intervals", kicker="Results",
 notes=("~2 min. Calibration is a separate criterion from accuracy and, for the decision analysis that "
        "follows, the more important one.\n\n"
        "Empirical coverage of the 90 per cent predictive intervals is 89.3 per cent, with a mean "
        "width of 4.59 transactions. Coverage is reported jointly with that width because coverage "
        "alone is trivially satisfiable by an arbitrarily wide interval.\n\n"
        "Examining several nominal levels rather than one gives a more complete picture: the intervals "
        "are conservative at the 50 per cent level and slightly anti-conservative at 95 per cent. "
        "Calibration is therefore good in the operational range and imperfect in the tails, which I "
        "would rather state than average away.\n\n"
        "Note also that this criterion is only available for a specification that issues a predictive "
        "distribution; neither the heuristic nor the standard benchmark does."))
claim(s, "Stated intervals attain approximately nominal coverage, which is what licenses their use in "
         "the decision analysis that follows.")
stat_row(s, [("89.3%","coverage at 90% nominal",TEAL),
             ("4.59","mean interval width\n(transactions)",NAVY),
             ("0.71","AUC, latent activity",NAVY)], top=In(2.45))
bullets(s, [
 "Coverage across nominal levels: 64.4% at 50, 82.5% at 80, 89.3% at 90, 92.9% at 95",
 "Conservative in the middle of the distribution and slightly anti-conservative in the tails",
 "Reported jointly with sharpness, since coverage alone is satisfiable by an arbitrarily wide interval",
], top=In(4.3), size=16.5)

# ── 15 ──────────────────────────────────────────────────────────────────────
s = slide("Illustrative case: customer 14817", kicker="Results",
 notes=("~2 min. A single case makes the distinction concrete. Four repeat transactions, last observed "
        "at week 33, mean transaction value £526.\n\n"
        "The posterior of expected value is tightly concentrated: £1,364, with a 90 per cent interval "
        "of £1,326 to £1,401. That interval quantifies uncertainty about the rate, not about the "
        "realisation.\n\n"
        "The posterior predictive interval for the realised outcome runs from zero to £2,888, and "
        "includes a non-negligible probability of no further purchase, since the customer may already "
        "have become inactive.\n\n"
        "The realised holdout value was £1,010, which lies inside the predictive interval and well "
        "outside the interval for the expectation. The case is illustrative; the aggregate evidence is "
        "the coverage figure on the previous slide."))
claim(s, "Uncertainty about the expectation and uncertainty about the realisation are different "
         "quantities, and only the second is relevant to a statement about an individual outcome.")
picture(s, FIG+"worked_example_customer.png", In(2.45), max_w=In(8.8), max_h=In(3.45))
box(s, [("Expected value £1,364, 90% interval £1,326–£1,401.      "
         "Posterior predictive interval £0–£2,888.      Realised: £1,010.", 15.5, True, NAVY)],
    In(6.05), In(0.6))

# ── 16 ──────────────────────────────────────────────────────────────────────
s = slide("Benchmark analysis", kicker="Results",
 notes=("~1.5 min. The benchmark is a tuned two-stage gradient-boosted model with 24 engineered "
        "features, separating the transaction and spend components. It is a serious comparison rather "
        "than a straw man, and its result deserves explanation rather than assertion.\n\n"
        "Its gain profile concentrates on recency, frequency and dispersion — quantities the "
        "generative specification imposes structurally. The benchmark is therefore expending capacity "
        "recovering structure that is assumed, from 4,522 observations of which a third have a single "
        "transaction.\n\n"
        "The constraint is information rather than capacity. At substantially larger scale, and with "
        "informative covariates, I would expect this ordering to reverse, and the literature reports "
        "precisely that crossover."))
claim(s, "The benchmark expends capacity recovering structure the generative specification imposes, "
         "under an information constraint rather than a capacity constraint.")
picture(s, FIG+"xgboost_feature_importance.png", In(2.45), max_w=In(8.6), max_h=In(3.45))
box(s, [("Two-stage design, 24 engineered features, tuned on an inner split.      "
         "Gain concentrates on recency, frequency and dispersion — all imposed structurally by the generative model.",
         15, False, INK)], In(6.05), In(0.6))

# ── 17 ──────────────────────────────────────────────────────────────────────
s = slide("H2 — partial pooling across country segments", kicker="Results",
 notes=("~2 min. The UK contributes 4,152 customers, Germany 74, France 54. Separate estimation "
        "overfits the small segments; complete pooling removes segment-level variation entirely. "
        "Partial pooling estimates segment parameters as draws from a common distribution.\n\n"
        "Aggregated error across the small segments is 1.746 under partial pooling, against 1.755 "
        "for no pooling and 1.757 for complete pooling. That is a difference of roughly half a per "
        "cent, and I will not represent it as more than it is.\n\n"
        "The defensible claim is adaptivity rather than magnitude. Partial pooling is never worst in "
        "any segment, whereas each alternative fails materially somewhere. The improvement is in "
        "robustness to specification choice.\n\n"
        "One qualification: the prior on between-segment variation was deliberately tight, which "
        "biases the comparison toward the null. H2 is therefore a prior-constrained test."))
claim(s, "Partial pooling yields a small aggregate improvement and, more defensibly, is never the "
         "worst specification in any segment.")
picture(s, SLD+"h2_pooling.png", In(2.45), max_w=In(10.4), max_h=In(3.15))
box(s, [("Aggregated small-segment error  1.746 partial  ·  1.755 none  ·  1.757 complete", 15.5, True, NAVY),
        ("Verdict: partially supported. The between-segment prior was deliberately tight, biasing the "
         "comparison toward the null — H2 is a prior-constrained test.", 14.5, False, MUTE)],
    In(5.9), In(1.0))

# ── 18 ──────────────────────────────────────────────────────────────────────
s = slide("H2 — the shrinkage mechanism", kicker="Results",
 notes=("~1.5 min. The mechanism is classical and worth stating precisely, since it is not a property "
        "of this model but of the hierarchical structure.\n\n"
        "Segment estimates are drawn toward the population mean in inverse proportion to the "
        "information available in that segment. The UK barely moves; France moves substantially. The "
        "weighting is determined by the data rather than tuned.\n\n"
        "The Stein and Efron–Morris results guarantee improvement in aggregate risk, not a gain in "
        "every segment. The modest result reported is therefore consistent with theory rather than "
        "anomalous."))
claim(s, "Segment estimates are drawn toward the population mean in inverse proportion to the "
         "information available in that segment.")
picture(s, FIG+"hierarchical_shrinkage_r.png", In(2.45), max_w=In(7.8), max_h=In(3.4))
box(s, [("The UK (4,152 customers) is essentially unmoved; France (54) shrinks substantially. "
         "The weighting is determined by the data, not tuned.", 15.5, False, INK),
        ("Stein / Efron–Morris guarantee improvement in aggregate risk, not in every segment — the "
         "modest result is consistent with theory.", 15, True, NAVY)], In(6.0), In(1.0))

# ── 19 ──────────────────────────────────────────────────────────────────────
s = slide("H3 — decision-theoretic targeting", kicker="Results",
 notes=("~2 min. The simulation allocates a fixed marketing budget under a per-contact cost. The "
        "comparison is between ranking on expected value and selecting on the posterior probability "
        "of exceeding a value threshold.\n\n"
        "Ranking on expected value performs equivalently, and the result is stable across a sweep of "
        "cost assumptions, so it is not an artefact of a particular calibration.\n\n"
        "The explanation is theoretical rather than empirical. Where the objective is linear in value "
        "— profit as value net of cost — expected utility depends on the posterior only through its "
        "mean. The remainder of the distribution carries no decision-relevant information for that "
        "objective. The contribution is to demonstrate this in an applied setting, and to delimit "
        "where the additional inferential cost is recovered: non-linear objectives, budget constraints "
        "with penalties, or explicit risk aversion."))
claim(s, "Where the objective is linear in value, expected utility depends on the posterior only "
         "through its mean; the remainder carries no decision-relevant information.")
picture(s, SLD+"h3_targeting.png", In(2.45), max_w=In(10.2), max_h=In(3.25))
box(s, [("Verdict: not supported. Equivalent performance across a sweep of cost assumptions.", 15.5, True, NAVY),
        ("The result delimits where the posterior earns its cost: non-linear objectives, budget "
         "constraints with penalties, or explicit risk aversion.", 14.5, False, MUTE)],
    In(5.95), In(1.0))

# ── 20 ──────────────────────────────────────────────────────────────────────
s = slide("Methodological finding: selecting the predictive distribution", kicker="Results",
 notes=("~2.5 min. This finding was not anticipated and is the one I would defend most strongly.\n\n"
        "Two distinct objects are both properly termed posterior quantities. The posterior of the "
        "expectation propagates parameter uncertainty only, and concentrates as the sample grows. The "
        "posterior predictive additionally integrates over the sampling distribution of the outcome, "
        "and does not concentrate, because outcome variability is irreducible.\n\n"
        "A decision rule defined on a probability of exceeding a threshold is a statement about a "
        "realisation, and therefore requires the predictive distribution. Computed instead from the "
        "expectation posterior, 96 per cent of customers receive a probability of exactly zero or one, "
        "because the expectation is estimated precisely enough that the threshold falls outside its "
        "interval for almost every customer. The ranking degenerates into arbitrary tie-breaking, and "
        "no diagnostic signals the error.\n\n"
        "In the simulation the hit rate falls from 0.85 to 0.62 and wasted expenditure rises from "
        "£55,040 to £144,738. I propose a one-line diagnostic: inspect the distribution of predicted "
        "probabilities; concentration at the boundaries indicates the wrong object. This generalises "
        "to any specification issuing distributional output."))
claim(s, "A decision rule defined on a realisation requires the posterior predictive; substituting the "
         "posterior of the expectation degrades the decision without any diagnostic signalling it.")
picture(s, FIG+"prob_expectation_vs_predictive.png", In(2.45), max_w=In(9.8), max_h=In(2.85))
box(s, [("Hit rate 0.85 → 0.62        Wasted expenditure £55,040 → £144,738        "
         "96% of customers assigned probability 0 or 1", 15.5, True, NAVY),
        ("Proposed diagnostic: inspect the distribution of predicted probabilities. Concentration at "
         "the boundaries indicates the wrong object. Generalises to any distributional specification.",
         14.5, False, MUTE)], In(5.65), In(1.05))

# ── 21 SECTION ──────────────────────────────────────────────────────────────
section("Discussion", "Synthesis, contribution, limitations", notes="~10 s.")

# ── 22 ──────────────────────────────────────────────────────────────────────
s = slide("Synthesis of findings", kicker="Discussion",
 notes=("~1.5 min. Taken together the three results exhibit a pattern that was not designed for.\n\n"
        "The three questions draw on progressively more of the posterior. The first uses its location "
        "and dispersion, and is decisive. The second uses its structure across segments, and yields a "
        "modest adaptive gain. The third uses its tails, and yields nothing, because a linear "
        "objective is insensitive to them.\n\n"
        "The posterior is therefore realised in proportion to how much of it the decision problem "
        "actually employs. That is a more informative outcome than three confirmations, because it "
        "delimits where the method's cost is recovered."))
claim(s, "The posterior is realised in proportion to how much of it the decision problem employs.")
picture(s, SLD+"verdicts.png", In(2.4), max_w=In(10.8), max_h=In(2.3))
bullets(s, [
 ("RQ1 draws on location and dispersion", "Decisive — ranking advantage and approximately nominal coverage."),
 ("RQ2 draws on structure across segments", "Modest and adaptive — robustness rather than accuracy."),
 ("RQ3 draws on the tails", "No gain, because a linear objective is insensitive to them."),
], top=In(4.95), size=15.5, gap=4)

# ── 23 ──────────────────────────────────────────────────────────────────────
s = slide("Contribution", kicker="Discussion",
 notes=("~1.5 min. No new estimator is proposed, and I would characterise the contribution as "
        "evaluative and methodological.\n\n"
        "First, calibration validation is imported into a literature that reports point accuracy "
        "almost exclusively.\n\n"
        "Second, the cost of selecting the wrong predictive object is quantified in a decision "
        "setting, with a diagnostic for detecting it.\n\n"
        "Third, a known decision-theoretic result is demonstrated empirically in an applied problem, "
        "which delimits the conditions under which the inferential cost is recovered."))
claim(s, "No new estimator is proposed; the contribution is evaluative and methodological.")
bullets(s, [
 ("Extends validation from point accuracy to interval calibration",
  "The customer-base literature validates expectations against realisations; coverage is rarely verified."),
 ("Quantifies the cost of selecting the wrong predictive object",
  "Approximately threefold increase in wasted expenditure, with a diagnostic for detecting it pre-deployment."),
 ("Demonstrates a decision-theoretic result in an applied setting",
  "Linear objectives are sufficient in the posterior mean — known theoretically, delimited here empirically."),
], top=In(2.45), size=16.5)

# ── 24 ──────────────────────────────────────────────────────────────────────
s = slide("Implications for practice", kicker="Discussion",
 notes=("~1 min. Four recommendations, in order of consequence. Validate coverage and not only error. "
        "Define decision rules on the predictive distribution where the question concerns a "
        "realisation. Inspect predicted probabilities before deployment. Pool small segments rather "
        "than estimating them separately or excluding them."))
claim(s, "Four recommendations follow directly from the findings.")
bullets(s, [
 "Validate interval coverage, not only point error — an uncalibrated interval invites decisions it cannot support",
 "Define decision rules on the predictive distribution wherever the question concerns a realised outcome",
 "Inspect the distribution of predicted probabilities before deployment; concentration at 0 and 1 indicates the wrong object",
 "Pool small segments rather than estimating them separately or excluding them — the gain is in robustness",
 "Expect the advantage of a generative specification in ranking rather than in average error",
], top=In(2.45), size=16.5, gap=13)

# ── 25 ──────────────────────────────────────────────────────────────────────
s = slide("Limitations", kicker="Discussion",
 notes=("~1.5 min. I state the direction of bias for each, since a limitation without a direction does "
        "not inform the reader whether the estimate can be used.\n\n"
        "Stationarity is violated: rates are assumed constant, which over-predicts mid-frequency "
        "customers by 20 to 30 per cent. The upper deciles, which determine allocation, remain "
        "calibrated.\n\n"
        "Independence of frequency and transaction value is violated mildly, at a correlation of 0.13. "
        "Because the correlation is positive, the specification under-predicts spend among the most "
        "frequent purchasers, which partially offsets the stationarity bias rather than compounding it.\n\n"
        "Scope is a single retailer in a single market. And wholesale purchasing is present within a "
        "consumer specification — the most active customer recorded 200 repeat transactions in 65 "
        "weeks, which is procurement behaviour, and I flag it rather than excluding the observation."))
claim(s, "Each limitation is stated with its direction of bias; the two design biases run in opposite "
         "directions rather than compounding.")
bullets(s, [
 ("Stationarity — rates are assumed constant over the observation window",
  "Over-predicts mid-frequency customers by 20–30%. Upper deciles, which determine allocation, remain calibrated."),
 ("Independence of frequency and transaction value — violated at r = 0.13",
  "Positive, so spend is under-predicted among frequent purchasers, partially offsetting the stationarity bias."),
 ("Scope — a single retailer, single market, two-year window",
  "Magnitudes are setting-specific; the argument concerning predictive objects is general."),
 ("Wholesale purchasing within a consumer specification",
  "The most active customer recorded 200 repeat transactions in 65 weeks — procurement rather than consumer behaviour."),
], top=In(2.4), size=15.5, gap=5)

# ── 26 ──────────────────────────────────────────────────────────────────────
s = slide("Further work", kicker="Conclusion",
 notes=("~1.5 min, then questions. Three directions, in order of expected return.\n\n"
        "Pooling on behavioural rather than geographic segments: country is plausibly a weak proxy for "
        "the behaviour that actually clusters.\n\n"
        "A non-linear decision objective — a budget constraint with a penalty, or explicit risk "
        "aversion — which is the proper test that RQ3 could not provide.\n\n"
        "Relaxing stationarity through a time-varying rate, that being the assumption most clearly "
        "demonstrated to be violated.\n\n"
        "To conclude: the thesis establishes that a Bayesian generative treatment delivers accurate "
        "and calibrated customer-level predictions, that pooling buys robustness rather than accuracy, "
        "and that the posterior must be matched to the question being asked. Thank you — I welcome "
        "your questions."))
claim(s, "Three directions, in order of expected return.")
bullets(s, [
 ("Pooling on behavioural rather than geographic segments",
  "Country is plausibly a weak proxy for the behaviour that clusters; acquisition channel or first-category are candidates."),
 ("A non-linear decision objective",
  "A budget constraint with penalty, or explicit risk aversion — the proper test RQ3 could not provide."),
 ("Relaxation of stationarity through a time-varying rate",
  "The assumption most clearly demonstrated to be violated, and the one most consequential in deployment."),
], top=In(2.45), size=16.5)
box(s, [("The specification delivers accurate and calibrated customer-level predictions; pooling buys "
         "robustness; and the posterior must be matched to the question asked.", 15.5, True, NAVY)],
    In(5.55), In(0.7))
