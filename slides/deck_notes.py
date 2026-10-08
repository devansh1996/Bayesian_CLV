# -*- coding: utf-8 -*-
"""Shared annotation data: metric glossary, per-slide delivery notes, and the
short definitional footnotes appended to the deck's own speaker notes."""

METRICS = [
("mae","MAE — mean absolute error","Slide 16",
 "Average size of the prediction error, in transactions or pounds.",
 "Mean of |actual − predicted| across all 4,522 customers.",
 "1.74 transactions (Bayesian) vs 2.13 XGBoost, 2.33 RFM, 3.11 naive.",
 "It treats every customer equally, so thousands of near-inactive customers dominate it. It cannot see ordering at all.",
 "“Average error improves, but modestly — I don't rest the case on it.”",
 ("Why is your MAE advantage so small?",
  "Because MAE is dominated by the ~2,800 customers with little history, where a simple heuristic does well. "
  "Split by history, RFM beats me on one-time buyers (0.80 vs 0.97) and I halve its error on the heaviest band "
  "(3.58 vs 7.01). The heavy band carries the revenue, which is why ranking separates and MAE does not.")),

("rmse","RMSE — root mean squared error","Slide 16",
 "Like MAE but squares the errors first, so large misses count far more.",
 "Square root of the mean of (actual − predicted)².",
 "3.31 transactions (Bayesian) vs 3.77 XGBoost, 6.37 RFM.",
 "A model can have decent MAE and poor RMSE if it occasionally misses badly.",
 "“RMSE penalises large misses, which is where the heuristic falls apart — 6.37 against our 3.31.”",
 ("Why report both?",
  "They answer different questions. MAE is the typical error; RMSE is sensitive to the occasional large miss. "
  "The gap between RFM's MAE (2.33) and its RMSE (6.37) shows it fails badly on a minority of customers.")),

("ndcg","NDCG@100 — normalised discounted cumulative gain","Slide 16",
 "Whether the top of the ranked list contains genuinely valuable customers.",
 "Rank customers by predicted value; take the top 100; add up each one's realised value divided by log₂(position+1), "
 "so position 1 gets full weight and position 100 about 15%. Divide by what a perfect ranking would score.",
 "0.91 (Bayesian) vs 0.53 (XGBoost). 1.0 is perfect, 0 is worst.",
 "Below ~0.5 means the top of your list is close to arbitrary.",
 "“Of the position-weighted value a perfect ranking could capture in its top 100, we capture 91 per cent.”",
 ("Why 100, and isn't the log discount arbitrary?",
  "100 is a plausible campaign size, not a tuned parameter — the conclusion holds at 50 and 500 (0.90 at 500). "
  "The log discount is the standard convention from information retrieval, where it models attention decaying "
  "down a list. It was not chosen to fit this data.")),

("p100","Precision@100","Slide 16",
 "Of the 100 customers you would actually contact, how many belong in the true top 100.",
 "Intersect the predicted top 100 with the realised top 100; divide by 100.",
 "0.66 (Bayesian) vs 0.49 (XGBoost) vs 0.37 (RFM) vs 0.01 (naive).",
 "0.01 — the naive baseline — is effectively random selection.",
 "“Sixty-six of the hundred customers we select genuinely belong there; the heuristic manages thirty-seven.”",
 ("Isn't this just NDCG again?",
  "It's the unweighted version — it ignores position within the top 100 and only asks about membership. "
  "I report it because it needs no explanation and translates directly into campaign terms.")),

("capture","Top-decile value capture","Slide 16",
 "The share of all realised revenue that falls inside the top 10% you selected.",
 "Sum the realised holdout value of the top-decile selection; divide by total realised value.",
 "62.6% (Bayesian) vs 57.9% (XGBoost) vs 55.1% (RFM). Against a perfect ranking: 0.89 vs 0.82 vs 0.78.",
 "A random decile would capture about 10%.",
 "“Targeting the decile we select reaches 62.6 per cent of the revenue that actually materialised.”",
 ("Why not just report this and drop NDCG?",
  "This is the money interpretation and NDCG is the standard one, so I report both. They agree on the ordering "
  "of models, which is the reassuring part.")),

("gini","Gini coefficient","Slide 16",
 "How well the ranking concentrates realised value toward the top, across the whole list.",
 "Area between the model's cumulative-gain curve and the diagonal of random ordering.",
 "0.855 for CLV (Bayesian) vs 0.801 XGBoost, 0.785 RFM.",
 "0 is random ordering.",
 "“Gini summarises the whole ranking; NDCG and precision@100 concentrate on the part the budget reaches.”",
 ("Gini and NDCG disagree slightly — why?",
  "Gini weights the entire list; NDCG weights the top. A model can order the bulk well and the top poorly. "
  "That is exactly what the heuristic does — its Kendall's tau is 0.477 against our 0.476, essentially tied, "
  "yet its precision@100 is 0.37 against our 0.66.")),

("coverage","Empirical coverage","Slide 17",
 "Whether a stated interval contains the truth as often as it claims.",
 "Build a 90% predictive interval for every customer; count the share of realised outcomes falling inside.",
 "89.3% at 90% nominal. Across levels: 64.4% at 50, 82.5% at 80, 92.9% at 95.",
 "60% against a 90% claim would mean the model is systematically overconfident.",
 "“When the model states ninety per cent, it is right 89.3 per cent of the time.”",
 ("Could 89.3% be luck?",
  "With 4,522 customers the standard error near 0.9 is about half a percentage point, so it sits within roughly "
  "1.5 standard errors of nominal. More convincingly, I check four levels rather than one — the pattern is "
  "conservative mid-distribution and slightly anti-conservative in the tails, which is a shape, not a fluke.")),

("width","Mean interval width (sharpness)","Slide 17",
 "How wide the intervals are. Reported with coverage because coverage alone is gameable.",
 "Average of (upper − lower) across customers.",
 "4.59 transactions at the 90% level.",
 "An interval from 0 to infinity has perfect coverage and no value.",
 "“Coverage alone is satisfiable by an arbitrarily wide interval, so I report sharpness alongside it.”",
 ("What width would worry you?",
  "Anything approaching the full range of the outcome. 4.59 transactions against a mean of 3.78 is informative "
  "— it rules out most of the plausible range for most customers.")),

("auc","AUC for P(alive)","Slide 17",
 "Whether the inferred probability of still being active separates customers who returned from those who did not.",
 "Probability that a randomly chosen returning customer is ranked above a randomly chosen non-returning one.",
 "0.71.",
 "0.5 is random. 0.71 is moderate, not strong.",
 "“Moderate — 0.71. The latent state carries real information while remaining far from deterministic.”",
 ("0.71 is not very high. Is the latent state really identified?",
  "The ceiling is low here: attrition is genuinely unobservable and a third of customers have a single purchase, "
  "so there is almost no signal for them. I would not claim more than that it carries real information. It is also "
  "the only direct check available on a quantity nobody observes.")),

("brier","Brier score / log loss","Supporting analysis",
 "Whether the P(alive) probabilities are numerically right, not merely well ordered.",
 "Brier is the mean squared difference between the stated probability and the 0/1 outcome.",
 "Brier 0.207, log loss 0.638 — computed on repeat purchasers only.",
 "0.25 is what you get by stating 0.5 for everyone. Above that is worse than useless.",
 "“AUC only tests ordering; Brier tests the probabilities themselves, and 0.207 is comfortably below the 0.25 coin-flip line.”",
 ("Why only repeat purchasers?",
  "Because the model assigns P(alive)=1 to zero-repeat customers by construction — they have had no dropout "
  "opportunity. Scoring them measures the model's structure, not its predictions. Including them inflates Brier "
  "to 0.357, which looks like failure and is an artefact.")),

("rhat","R̂ — potential scale reduction","Slide 13",
 "Whether the four independent chains agree about the posterior.",
 "Compares variance between chains against variance within them. Converges to 1.",
 "Maximum 1.0014 across all parameters.",
 "Above about 1.01 means the chains have not mixed and nothing downstream can be trusted.",
 "“The four chains agree to within 1.0014, against a conventional threshold of 1.01.”",
 ("Does that prove the model is right?",
  "No, and I say so on the slide. These are necessary, not sufficient. They establish that the sampler explored "
  "the posterior; a misspecified model can converge perfectly. That is why they precede the results rather than "
  "supporting them.")),

("ess","Effective sample size","Slide 13",
 "How many genuinely independent draws the correlated sample is worth.",
 "Discounts the 4,000 draws by their autocorrelation.",
 "Minimum ≈ 1,900 of 4,000.",
 "A few hundred from 4,000 would indicate a badly behaved sampler.",
 "“Roughly 1,900 effective draws from 4,000 — each draw is worth about half an independent one, which is good for a correlated posterior.”",
 ("Why are draws correlated at all?",
  "Because this is a Markov chain: each draw starts from the previous state. The gradient-based sampler is what "
  "keeps that correlation low — a random walk on this geometry would do far worse, since r and α correlate at 0.81.")),

("div","Divergent transitions","Slide 13",
 "Places where the numerical integration behind the sampler broke down.",
 "Counted automatically during sampling.",
 "Zero.",
 "Even a handful implies some region was avoided, so the draws are biased rather than merely inefficient.",
 "“No divergences — the sampler did not systematically avoid any region of the posterior.”",
 ("Where would they have come from?",
  "Sharp curvature — typically the funnel geometry a hierarchical model creates when the between-group variance "
  "is small. The hierarchical model uses a non-centred parameterisation precisely to avoid that, and it also "
  "reports zero.")),

("disp","Over-dispersion: mean 3.78, variance 77.7","Slide 9",
 "Evidence that customers genuinely differ, rather than sharing one rate.",
 "Compare the sample variance of repeat-transaction counts against the sample mean.",
 "Mean 3.78, variance 77.7 — more than twenty times larger.",
 "Under a single shared rate the two would be approximately equal.",
 "“A single shared rate implies variance equal to the mean. We observe twenty times the mean, which is why heterogeneity is modelled explicitly.”",
 ("Could that be outliers rather than heterogeneity?",
  "Partly — the most active customer made 200 repeat purchases in 65 weeks and is wholesale behaviour, which I "
  "flag in the limitations. But the excess is far too large to be attributed to a handful of observations, and "
  "the fitted shape parameter of 0.65 describes a smoothly spread base, not a spike plus outliers.")),

("params","Fitted parameters: r, α, a, b, p, q, γ","Slide 10",
 "The estimated population distributions governing rates, attrition and spend.",
 "Posterior means across 4,000 draws.",
 "r = 0.65, α = 7.12; a = 0.22, b = 4.47; Gamma-Gamma 1.71, 3.97, 681.",
 "—",
 "“Shape below one means the base is dominated by occasional buyers; the mean dropout probability is 4.6 per cent per transaction.”",
 ("What do those imply substantively?",
  "r/α gives a mean rate of 0.09 per week — one purchase about every eleven weeks. a/(a+b) gives a 4.6 per cent "
  "chance of lapsing after any transaction, so a typical customer has roughly twenty more purchases in them. "
  "And the spend parameters imply a mean basket of £391 against £385 observed.")),

("pool","Segment error: 1.746 / 1.755 / 1.757","Slide 20",
 "Whether partial pooling improves accuracy on small country segments.",
 "Aggregated holdout error across the small segments under three pooling strategies.",
 "1.746 partial, 1.755 none, 1.757 complete.",
 "—",
 "“Half a per cent. I would not present that as decisive — the defensible claim is that partial pooling is never the worst in any segment.”",
 ("Then is H2 supported at all?",
  "Partially, and I say so. The gain in magnitude is small. What you buy is robustness to a specification choice "
  "you would otherwise have to make blind. And the between-segment prior was deliberately tight, which biases the "
  "comparison toward the null — so this is a prior-constrained test, not a clean one.")),

("h3","Hit rate and wasted expenditure","Slide 23",
 "The cost, in the targeting simulation, of using the wrong predictive object.",
 "Hit rate is the share of contacted customers who proved worth contacting; wasted expenditure is spend on those who did not.",
 "Hit rate 0.85 → 0.62; wasted expenditure £55,040 → £144,738.",
 "—",
 "“Roughly a threefold increase in wasted spend, from a conceptual substitution that produces entirely working code.”",
 ("Isn't that just an implementation bug?",
  "No — nothing errors, nothing warns, and the output looks like a well-formed probability. That is what makes it "
  "worth reporting: both objects are correctly called posterior quantities, so the substitution survives review. "
  "I give a one-line diagnostic — inspect the probabilities; concentration at 0 and 1 indicates the wrong object.")),

("corr","Frequency–value correlation: 0.13 / 0.21","Slide 28",
 "Whether the independence assumption behind CLV = transactions × spend holds.",
 "Pearson and Spearman correlation between calibration frequency and mean transaction value.",
 "Pearson 0.13, Spearman 0.21.",
 "—",
 "“Mildly violated, and the direction matters: because it is positive, spend is under-predicted for frequent buyers.”",
 ("Doesn't that invalidate multiplying the two components?",
  "It biases the monetary component, and I quantify the direction rather than claiming it away. The useful detail "
  "is that it runs opposite to the stationarity bias — stationarity over-predicts mid-frequency customers while "
  "this under-predicts the heaviest — so the two partially offset rather than compounding.")),
]


ANNOT = {
1:("Say your name, the title, and sit down into the first slide. Do not read the title aloud — they can see it.",
   [("The two-line title","It frames the thesis as a question about an unobservable quantity. If you want one sentence: “the thing that determines customer value is never observed, and this thesis is about estimating it honestly.”")]),
2:("Set the scene in about ninety seconds. The four figures carry it; do not read the bullets verbatim.",
   [("4,522 / 40.4 wks / £385 / 33%","Say the first and last. 4,522 customers, and a third of them bought once and never returned — that is the hard case, and it recurs throughout."),
    ("Temporal split at 1 March 2011","Emphasise this: every accuracy figure is out-of-sample against a period the model never saw. Pre-empts the leakage question."),
    ("“Value is concentrated”","This justifies the whole emphasis on ranking later. Plant it here so slide 16 does not feel like special pleading.")]),
3:("The hinge of the thesis. Slow down. Two minutes, and let the 15-week example breathe.",
   [("Contractual vs non-contractual","One sentence each. The contrast does the work."),
    ("The 15-week example","Deliver as two clauses with a pause between: improbable for a three-week buyer, unremarkable for a twice-a-year buyer. Then the conclusion — recency means nothing in isolation."),
    ("“No churn label exists to train on”","This is the sentence that rules out supervised learning. If an examiner is going to challenge the whole approach, it is here, so say it deliberately.")]),
4:("Keep it short — a minute and a half. The literature review is deliberately thin and you should signal that it is deliberate.",
   [("All three gaps","Say explicitly: “I am not proposing a new estimator.” Framing the contribution as evaluative protects you from the ‘what's novel?’ question.")]),
5:("State the three verdicts out loud here. A viva is not improved by suspense.",
   [("H1 / H2 / H3 verdicts","“Supported, partially supported, and not supported.” Then: “the third is the most informative, and I will explain why it had to be.”"),
    ("“progressively more from the posterior”","This is the thesis's organising idea. Say it now and it pays off on slide 25.")]),
7:("Two minutes. The point is that the generative choice is forced, not stylistic.",
   [("Supervised vs generative","Keep the contrast to one sentence each."),
    ("“not identified for this quantity”","Correct and precise. If you want it plainer: there is no target to learn from, for any customer.")]),
8:("Walk the four components in order. Do not define Poisson or Beta unless asked.",
   [("The four components","One clause each. Rate, dropout opportunity, variation in both, transaction value."),
    ("CLV = transactions × spend","Add: “which requires the two to be independent — I test that rather than assume it, and return to it in the limitations.” Volunteering it defuses an obvious challenge.")]),
9:("The evidence slide. Thirty seconds on the comparison, then move.",
   [("3.78 vs 77.7","The whole argument: under a single shared rate these would be equal. They differ by a factor of twenty.")]),
10:("The new distributional table. Walk the rows; do not read the Implication column aloud — let them read it.",
   [("Each row","Name the component and its distribution, then give the estimate. Four rows, about fifteen seconds each."),
    ("Mean 0.09/week","Translate: one purchase roughly every eleven weeks. Numbers land better once converted."),
    ("£391 implied vs £385 observed","Worth saying explicitly — it shows the compound recovers the skew rather than smoothing it."),
    ("Negative binomial implication","Connects back to slide 9. “Which is what accommodates the dispersion I just showed.”")]),
11:("The ‘why not something else’ slide — the most likely place for a methodological challenge. Two minutes.",
   [("Support","The strongest of the three and the quickest. A rate cannot be negative; a probability cannot exceed one. That removes most candidates before flexibility is even considered."),
    ("Flexibility","The key phrase is that the data selects the shape: a shape parameter below one gives a different qualitative picture from one above, and 0.65 chooses."),
    ("Tractability","Do not apologise for conjugacy. Say it buys a closed-form likelihood, and that without it each evaluation needs a numerical integral per customer — infeasible here, and the error degrades the sampler's gradients."),
    ("The lognormal counter-example","Have this ready: it passes support and flexibility and fails tractability. It shows the criteria have teeth."),
    ("“not priors”","Say this deliberately. Mixing distributions inside the likelihood, describing real heterogeneity. The priors sit above, on r, α, a, b. It is the most common misreading of this model family.")]),
12:("Three sentences, no equations. Resist elaborating.",
   [("“available only up to a normalising constant”","The precise statement. Then: the numerator is computable, the denominator has no closed form."),
    ("10¹¹ evaluations","Justifies abandoning quadrature in one number."),
    ("“the constant never enters”","The reason sampling works. Both the acceptance ratio and the gradient use the unnormalised posterior only.")]),
13:("One minute. The last sentence is the important one.",
   [("1.0014 / 1,900 / 0","Read the three figures, then stop."),
    ("“necessary but not sufficient”","Say it unprompted. It demonstrates you know what the diagnostics do and do not establish, and removes an easy question.")]),
14:("The new ‘what we computed’ table. This is the pivot from method to results.",
   [("The five rows","Each is a question the posterior answers. Name the quantity and what it is used for; skip the middle column unless asked."),
    ("£1,326–£1,401 vs £0–£2,888","Pause here. Two intervals, same customer, same model, different questions — an order of magnitude apart."),
    ("Closing line","“Which of the two a decision rule should use becomes the methodological finding.” Plants slide 23.")]),
16:("Two minutes. The figure carries it; your job is to say which panel matters.",
   [("MAE / RMSE","Acknowledge the improvement is modest. Do not oversell."),
    ("NDCG@100 0.91 vs 0.53","The decisive comparison. See the glossary for the full derivation if pressed."),
    ("Precision@100 0.66 vs 0.49 vs 0.37","The interpretable version — 66 of the 100 you pick genuinely belong there."),
    ("62.6% revenue capture","The money version of the same claim."),
    ("The inner-split caveat","Deliver it yourself, clearly: the benchmark trained on less data, so read the gap as an upper bound. Volunteering a weakness is far stronger than conceding it under questioning.")]),
17:("The calibration slide, and arguably your most important result. Two minutes.",
   [("89.3% against 90% nominal","Deliver plainly. No emphasis needed — the number is the argument."),
    ("The four nominal levels","Conservative at 50, slightly anti-conservative at 95. Reporting the shape rather than one level pre-empts ‘did you get lucky?’"),
    ("Mean interval width 4.59","Say why it is reported beside coverage: coverage alone is satisfiable by an arbitrarily wide interval."),
    ("“only available for a distributional specification”","Important asymmetry — neither the heuristic nor the benchmark makes a claim that can be tested this way.")]),
18:("Two minutes on one customer. This is where the abstract becomes concrete.",
   [("Four repeats, week 33, £526","Set the scene quickly."),
    ("£1,364, interval £1,326–£1,401","Note how tight. Seventy-five pounds. Let it look convincing."),
    ("Then £0–£2,888","The turn. Different question — what will they actually do — and the answer spans the full range."),
    ("Realised £1,010","Inside the predictive interval, outside the expectation interval."),
    ("“the case is illustrative”","Say it. One customer cannot establish calibration; the 89.3% across 4,522 does. It shows you know what a single case can and cannot support.")]),
19:("Ninety seconds. Be generous about the benchmark — it strengthens you.",
   [("“serious comparison rather than a straw man”","Say this explicitly. 24 features, two-stage, tuned."),
    ("The gain profile","Its effort concentrates on recency, frequency and dispersion — precisely what the generative model imposes structurally."),
    ("“information rather than capacity”","The explanation. And concede the scale point: with ten times the customers I would expect this to reverse, and the literature reports that crossover.")]),
20:("Two minutes. Be honest about the magnitude.",
   [("4,152 / 74 / 54","The three segment sizes make the problem obvious without further explanation."),
    ("1.746 / 1.755 / 1.757","Say the numbers and then immediately characterise them: half a per cent, which you will not overstate."),
    ("“never the worst in any segment”","The defensible claim. Robustness, not accuracy."),
    ("The tight-prior caveat","Volunteer it. It biases toward the null, so it works against your own hypothesis — which is the strongest possible framing for a caveat.")]),
21:("Ninety seconds. The mechanism is classical and you should attribute it.",
   [("Shrinkage in inverse proportion to information","The UK barely moves; France moves substantially. Determined by the data, not tuned."),
    ("Stein / Efron–Morris","Attribute it. Then: the theorem guarantees aggregate improvement, not a win in every segment — so the modest result is consistent with theory rather than disappointing.")]),
22:("Two minutes. The most interesting negative result in the thesis — treat it as a finding, not a failure.",
   [("The simulation set-up","Budget, per-contact cost, choose whom to target."),
    ("“equivalent performance”","And swept across cost assumptions, so it is not an artefact of one calibration."),
    ("The linear-objective explanation","The key line: where profit is linear in value, expected utility depends on the posterior only through its mean. The remainder carries no decision-relevant information for that objective."),
    ("Where it would pay","Name them: non-linear objectives, budget constraints with penalties, explicit risk aversion. This turns a negative result into guidance.")]),
23:("Two and a half minutes. Your strongest slide. Do not rush it.",
   [("The two objects","Both correctly called posterior quantities. One propagates parameter uncertainty and concentrates; the other integrates over outcome variability and does not."),
    ("96% at 0 or 1","The failure mechanism. The expectation is estimated so precisely that the threshold falls outside its interval for almost everyone, so the ranking degenerates into tie-breaking."),
    ("0.85 → 0.62 and £55,040 → £144,738","Deliver slowly. These are the numbers they will remember."),
    ("“no diagnostic signals the error”","The reason it is worth reporting — working code, plausible output, wrong answer."),
    ("The proposed diagnostic","One line, and it generalises: inspect the predicted probabilities; concentration at the boundaries indicates the wrong object.")]),
25:("Ninety seconds. Pull the three together into the single organising claim.",
   [("The three-line pattern","Location and dispersion — decisive. Structure across segments — modest. Tails — nothing."),
    ("The closing claim","“The posterior is realised in proportion to how much of it the decision problem employs.” If you say one sentence from the whole defence, this is a strong candidate.")]),
26:("A minute and a half. Be direct about what is and is not novel.",
   [("“No new estimator”","Lead with it. Then state the three contributions as evaluative and methodological."),
    ("If challenged on novelty","“The field has no shortage of estimators and comparatively little honest evaluation of them. A negative result with a theoretical explanation is the kind of finding that tends not to get published and should.”")]),
27:("One minute. Read them as recommendations, briskly.",
   [("The five recommendations","Do not elaborate on each. They are a list, and the audience can read.")]),
28:("Ninety seconds. Direction of bias for each — this is what distinguishes a serious limitations slide.",
   [("Stationarity","Over-predicts mid-frequency customers by 20–30%; the upper deciles, which determine allocation, stay calibrated."),
    ("Independence at r = 0.13","Positive, so it under-predicts frequent buyers — partially offsetting stationarity rather than compounding it. Say the offset explicitly; it shows you traced the consequence."),
    ("The 200-purchase customer","Concrete and memorable. Procurement behaviour inside a consumer specification, flagged rather than excluded.")]),
29:("Ninety seconds, then stop and invite questions.",
   [("The three directions","Behavioural rather than geographic pooling; a non-linear objective; relaxing stationarity."),
    ("The closing sentence","Deliver it as a conclusion, not a summary. Then: “Thank you — I welcome your questions.”")]),
}



# ── short definitions appended to the deck's speaker notes ──────────────────
# One or two sentences each, for terms an examiner may ask you to define on the
# spot. Kept deliberately brief: these are prompts, not a script.
FOOTNOTES = {
2: "IF ASKED — Customer lifetime value: the profit expected from a customer over the remainder of the "
   "relationship. A forward estimate, not a total of past spend.",
3: "IF ASKED — Latent: unobservable in principle rather than merely unrecorded. Nobody observes whether a "
   "customer has lapsed, including the customer. Non-contractual: no cancellation event exists, so there "
   "is no date at which churn can be said to occur.",
4: "IF ASKED — Validation here means out-of-sample temporal holdout validation: the data is cut at "
   "1 March 2011, the model is fitted on the 64.9 weeks before it, and scored on the 40.4 weeks after, "
   "which it never sees. Point accuracy compares one predicted number against one realised number "
   "(MAE, RMSE, ranking). Calibration of predictive intervals is a different check on the same data: "
   "build the stated 90% interval for every customer and count how many realised outcomes fall inside. "
   "The literature does the first and rarely the second.",
5: "IF ASKED — A research question is the question; the hypothesis is the testable claim I committed to "
   "in advance. Verdicts: H1 supported, H2 partially supported, H3 not supported.",
8: "IF ASKED — BG/NBD: Beta-Geometric / Negative Binomial Distribution, the Fader-Hardie model of "
   "purchase frequency with latent dropout. Gamma-Gamma: the companion model for transaction value. "
   "Both are standard; I did not modify either.",
9: "IF ASKED — Over-dispersion: more variance in the observed counts than the assumed distribution can "
   "produce. Under a single shared Poisson rate, variance equals the mean. Observing 77.7 against a mean "
   "of 3.78 rules that out and is the evidence for modelling heterogeneity explicitly.",
10:"IF ASKED — The Gamma shape r and rate α describe how purchase rates are spread across customers; "
   "r/α is the population mean rate, here 0.09 per week. The Beta parameters a and b describe how "
   "dropout probability is spread; a/(a+b) is the mean, here 4.6% per transaction.",
11:"IF ASKED — Support: the set of values a quantity can take. Conjugacy: a pairing of distributions "
   "whose combination has a closed form, so the mixture integrates analytically. A mixing distribution "
   "sits inside the likelihood and describes real variation between customers; a prior sits above it and "
   "describes my uncertainty about the population parameters. Confusing the two is the usual misreading.",
12:"IF ASKED — Posterior: the distribution over parameters after conditioning on the data. The "
   "normalising constant is the integral in the denominator of Bayes' rule; it has no closed form here. "
   "MCMC constructs a chain whose long-run distribution is the posterior; NUTS is the variant that uses "
   "gradients to stay efficient when parameters are correlated, as r and α are at 0.81.",
13:"IF ASKED — R-hat compares variance between chains to variance within them; 1.00 means they agree. "
   "Effective sample size discounts the draws for autocorrelation. A divergence is a failure of the "
   "numerical integration, indicating a region the sampler could not traverse. All three are properties "
   "of the sampler, not of the model.",
14:"IF ASKED — Posterior of an expectation: uncertainty about the underlying rate, which shrinks as the "
   "sample grows. Posterior predictive: uncertainty about a realised outcome, which does not shrink, "
   "because outcome variability is irreducible. A statement about what one customer will actually do "
   "requires the second.",
16:"IF ASKED — NDCG@100: rank by prediction, take the top 100, sum each customer's realised value divided "
   "by log2(position+1), divide by what a perfect ranking scores. Precision@100: how many of the top 100 "
   "selected belong in the true top 100. Value capture: the share of all realised revenue falling in the "
   "selected top decile.",
17:"IF ASKED — Coverage: the share of realised outcomes falling inside the stated interval. Sharpness: "
   "the mean width of those intervals, reported because coverage alone is satisfiable by an arbitrarily "
   "wide interval. AUC: whether P(alive) orders returning customers above non-returning ones.",
19:"IF ASKED — The inner split is a second, earlier cut at 1 October 2010, used to tune the benchmark's "
   "hyperparameters so the real holdout stayed unseen by it. It is why the benchmark trained on less "
   "data, and why I treat the ranking gap as an upper bound.",
20:"IF ASKED — Complete pooling: one set of parameters for all segments. No pooling: a separate fit per "
   "segment. Partial pooling: segment parameters drawn from a common distribution, so segments inform "
   "one another in proportion to the evidence each carries.",
21:"IF ASKED — Shrinkage: individual estimates pulled toward the population mean, more strongly where "
   "the individual evidence is thin. The Stein and Efron-Morris results show this reduces aggregate "
   "squared error even though some individual estimates get worse.",
22:"IF ASKED — A linear objective is one where payoff is a straight-line function of value, here profit "
   "as value net of cost. Sufficiency means the posterior mean already carries all decision-relevant "
   "information, so the rest of the distribution cannot improve the choice.",
23:"IF ASKED — The failure is silent because both objects are correctly called posterior quantities and "
   "both produce well-formed probabilities. The diagnostic is distributional: inspect the predicted "
   "probabilities; mass concentrated at 0 and 1 indicates the expectation posterior was used where the "
   "predictive was required.",
28:"IF ASKED — Stationarity: the assumption that a customer's underlying rate does not change over the "
   "observation window. Violated here, which over-predicts mid-frequency customers by 20-30%, while the "
   "upper deciles remain calibrated.",
}
