# -*- coding: utf-8 -*-
"""Slide-by-slide defence companion: the concepts on each slide, and the
questions an examiner can ask from it. q = (kind, question, answer).
kind: clarify | method | challenge | hostile | extend"""

SLIDES = [

dict(n=1, kicker="TITLE", title="Customer Lifetime Value Prediction Using Bayesian Methods",
 says="Sets the frame: a probabilistic approach to CLV in non-contractual retail.",
 concepts=[
  ("CLV", "Expected net present value of all future cash flow from one customer relationship — a forecast, not a historical total."),
  ("Non-contractual", "No cancellation event. The customer simply stops buying, so churn is never observed."),
 ],
 qs=[
  ("clarify", "In one sentence, what is your thesis about?",
   "Whether treating customer lifetime value as a full probability distribution, rather than a point estimate, produces better predictions and better decisions in a retail setting where you never observe churn. I test that on three fronts: accuracy, pooling across countries, and a targeting decision."),
  ("clarify", "Why is this worth a thesis — isn't CLV a solved problem?",
   "The prediction is well studied; the BG/NBD dates from 2005. What is not settled is whether the uncertainty these models produce is trustworthy and whether it changes decisions. The literature validates expectations against actuals and largely stops there. I validate the intervals themselves, and then test whether they alter a real decision."),
  ("challenge", "Why Bayesian rather than just fitting the same model by maximum likelihood?",
   "Maximum likelihood gives the same point prediction, and for pure accuracy it would be competitive. But it cannot propagate uncertainty into a decision rule. My third research question asks about a decision under uncertainty, and that question is not even expressible with a point estimate. The Bayesian treatment is what makes RQ3 askable."),
 ]),

dict(n=2, kicker="MOTIVATION", title="The core difficulty: customers never say goodbye",
 says="Contractual settings observe churn; non-contractual ones do not, so attrition is a latent state and the problem is irreducibly probabilistic.",
 concepts=[
  ("Latent variable", "A quantity that is unobservable in principle, not merely unmeasured. Whether a customer is still active is never recorded by anyone."),
  ("Contractual vs non-contractual", "A gym membership has a cancellation date; a shop has nothing. Survival analysis needs that date and therefore does not transfer."),
 ],
 qs=[
  ("clarify", "Why can't you just define churn as 'no purchase in six months' and use a classifier?",
   "Because that threshold has no meaning independent of the customer. Fifteen weeks of silence is alarming for someone who buys every three weeks and completely normal for someone who buys twice a year. Any fixed cutoff mislabels one of those two groups, and then you are training a classifier on labels you invented."),
  ("method", "How does the model distinguish 'slow' from 'gone' without a churn label?",
   "Through the interaction of recency and frequency. Neither is informative alone. But a silence is improbable exactly in proportion to the customer's own established rate, so a high-frequency customer going quiet drives P(alive) down sharply while a low-frequency customer going equally quiet barely moves it. The likelihood encodes that trade-off directly."),
  ("challenge", "Isn't 'latent attrition' just an untestable assumption? You can never verify a customer dropped out.",
   "Individually, correct — it is never verifiable for one customer. But it is testable in aggregate through its predictions. The model's P(alive) achieves an AUC of 0.71 against observed holdout activity, so the latent state carries real information about who comes back. That is the only kind of validation such a construct can have, and it is the standard one."),
  ("hostile", "Survival analysis handles censoring. Why not just use Cox regression?",
   "Censoring and latency are different problems. Censoring means the event has not happened yet but will be observed when it does. Here the event is never observed, for anyone, ever. Cox regression needs event times to build a partial likelihood; there are none. The BTYD family exists precisely because the survival toolkit does not apply."),
 ]),

dict(n=3, kicker="RESEARCH GAP", title="Three limitations of existing approaches",
 says="Inference, structure and decision-use; each gap maps onto one research question and one element of the design.",
 concepts=[
  ("Calibration", "Whether a stated 90% interval actually contains the truth 90% of the time. Distinct from accuracy."),
  ("Partial pooling", "Letting groups share statistical strength instead of being fitted separately or forced identical."),
 ],
 qs=[
  ("challenge", "These gaps sound convenient. Did you choose questions you knew you could answer?",
   "They were chosen before the results existed, and two of the three did not go my way: H2 is only partially supported and H3 is rejected. If I had reverse-engineered the questions from the findings I would have picked easier ones. The gaps come from what the literature reports, not from what my model does well."),
  ("clarify", "Which gap is most important?",
   "The first, calibration, because the other two depend on it. If the intervals were not honest, the pooling comparison would be measuring noise and the decision rule would be built on a distribution you could not trust. Calibration is the precondition for the rest being meaningful."),
  ("hostile", "Isn't calibration a well-known requirement? Hardly a gap.",
   "It is well known in forecasting and in the machine-learning calibration literature. It is largely absent from the applied BTYD validation tradition, which compares predicted against actual transaction counts and reports error metrics. I am importing a standard from one field into another where it was not routine, not inventing it."),
 ]),

dict(n=4, kicker="AIMS", title="Research questions and hypotheses",
 says="RQ1 accuracy with calibrated uncertainty; RQ2 hierarchical pooling by country; RQ3 decision-theoretic targeting.",
 concepts=[
  ("H1 / H2 / H3", "Supported, partially supported, and not supported respectively."),
  ("Decision-theoretic targeting", "Choosing whom to contact by P(CLV > threshold) rather than by ranked expected value."),
 ],
 qs=[
  ("clarify", "Why these three questions specifically, and in this order?",
   "They escalate in what they demand from the posterior. RQ1 needs only its centre and spread. RQ2 needs its hierarchical structure. RQ3 needs its tails. So the three together map out how much of a posterior a question actually consumes — which turned out to be the unifying finding."),
  ("challenge", "You report that H3 failed. Doesn't that undermine the thesis?",
   "It sharpens it. H3 failing has a clean theoretical explanation: for a linear objective, decision theory says the posterior mean is sufficient, so the tails cannot add anything. Demonstrating a known theorem empirically in a real business setting is a result. It also tells practitioners exactly when the extra machinery is and is not worth paying for."),
  ("method", "Did you pre-register these hypotheses?",
   "Not formally — it is not standard practice for this kind of thesis. I should be transparent that the operationalisation of H2 and H3 was refined partway through, specifically the three-way pooling comparison and the move to predictive-CLV targeting. The hypotheses themselves did not change; how I measured them became sharper."),
 ]),

dict(n=5, kicker="EMPIRICAL SETTING", title="Data and research design",
 says="4,522 customers, UCI Online Retail II, calibration/holdout split at 1 March 2011, 40.4-week horizon.",
 concepts=[
  ("Calibration/holdout split", "A temporal split: the model sees only data before the cutoff and is scored on the period after."),
  ("Frequency / recency / monetary", "Repeat purchases (total invoices minus one), time of last purchase, and mean revenue per repeat transaction."),
 ],
 qs=[
  ("method", "Why a temporal split rather than cross-validation?",
   "Because the task is forecasting the future from the past, and random k-fold would let the model see later transactions while predicting earlier ones. That is leakage of exactly the kind the research question is about. A single temporal split reproduces the deployment situation faithfully."),
  ("challenge", "One dataset, one retailer, one country. How can you generalise?",
   "I cannot claim statistical generalisation, and the thesis says so in the Generalisability section. What I claim is mechanism: the two-posteriors distinction is a mathematical property of any model producing distributional output, not a feature of this retailer. The empirical magnitudes are specific; the mechanism is not."),
  ("method", "Why is the horizon 40.4 weeks, and would the conclusions change at a different horizon?",
   "It is simply what remains after the split date, so it was determined by the data rather than chosen. A longer horizon would widen the predictive intervals and increase the gap between the two posteriors, strengthening the key finding. A much shorter one would compress it. The direction of the effect is predictable; the ranking conclusions would not flip."),
  ("hostile", "Online Retail II is a well-known benchmark. Aren't you just reproducing a standard result?",
   "The dataset is standard and that is deliberate — it makes the work reproducible and comparable. What is not standard is the evaluation: coverage of predictive intervals, a three-way pooling comparison, and a decision simulation. The data is familiar; the questions asked of it are not."),
 ]),

dict(n=7, kicker="METHODOLOGY · 1", title="A generative model of customer behaviour",
 says="BG/NBD for frequency and latent dropout, Gamma-Gamma for spend; CLV = E[transactions] × E[spend], each a distribution.",
 concepts=[
  ("BG/NBD", "Beta-Geometric / Negative Binomial Distribution. Poisson purchasing while active, a Bernoulli dropout trial after each purchase."),
  ("Gamma-Gamma", "Spend model: a customer's mean transaction value is Gamma-distributed, with a Gamma-distributed rate across customers."),
  ("Generative model", "A model that writes down a mechanism for how the data arose, rather than fitting a function from features to a target."),
 ],
 qs=[
  ("method", "Why Gamma and Beta specifically? Could you have used other distributions?",
   "Three requirements have to be met simultaneously. Support: rates are positive, which rules out the normal; probabilities lie in [0,1], which rules out the Gamma. Flexibility: the Gamma shape parameter can give a hump or a pile against zero, and the Beta can be a hump, a J, a U or flat, so the data chooses. And conjugacy: Gamma with Poisson integrates in closed form to the negative binomial, Beta with the Bernoulli trials likewise. The lognormal passes the first two and fails the third."),
  ("challenge", "Isn't conjugacy just mathematical convenience?",
   "It is a computational necessity here, not a preference. Without a closed form you need a numerical integral per customer per likelihood evaluation — 4,522 customers times thousands of sampling steps. Worse, HMC steers by gradients, and quadrature error inside the likelihood corrupts them. I hit this directly: my hand-rolled likelihood was ill-conditioned and would not sample at all until it was replaced with a stable closed-form implementation."),
  ("hostile", "The assumptions are clearly false. Purchases aren't Poisson and people don't flip coins.",
   "Agreed, and I would not defend them as literally true. They are defensible as approximations that are wrong in known directions. I test the main ones: stationarity biases mid-frequency CLV upward, the frequency-monetary independence assumption is violated at Pearson 0.13, and the most active customer made 200 purchases in 65 weeks, which is procurement, not consumer behaviour. The question is not whether the assumptions hold exactly but whether the predictions survive their violation — and the calibration result says they largely do."),
  ("method", "Why is dropout only allowed immediately after a purchase?",
   "That is the BG simplification, and it is what makes the likelihood tractable without hypergeometric functions. The continuous-time alternative is the Pareto/NBD. Fader and Hardie showed the discrete version matches its predictive accuracy at far lower computational cost, which is why it became the default. It is a modelling convenience with a demonstrated low cost."),
  ("clarify", "What does it mean that CLV is a product of two models?",
   "Value is how often multiplied by how much, so I estimate frequency and spend separately and multiply. That requires them to be independent, which I check rather than assume. The correlation is mildly positive — Pearson 0.13, Spearman 0.21 — which means the model slightly under-predicts spend for the most frequent buyers."),
 ]),

dict(n=8, kicker="METHODOLOGY · 2", title="Why Bayesian, and not maximum likelihood?",
 says="A point estimate cannot be propagated into a decision. Diagnostics: R-hat ≤ 1.002, ESS > 1,100, zero divergences.",
 concepts=[
  ("Posterior", "The full distribution over parameters after seeing the data — estimate and confidence in one object."),
  ("NUTS / HMC", "Gradient-guided sampling. Treats the negative log-posterior as a landscape and rolls a particle across it."),
  ("R-hat, ESS, divergences", "Convergence, autocorrelation-adjusted sample size, and integrator failures. All three must pass before results mean anything."),
 ],
 qs=[
  ("method", "What exactly is a posterior draw?",
   "One complete, self-consistent set of values for every parameter at once — one row of a 4,000-row table. Draw one of mine reads: shape 0.6303, rate 6.5749, and so on. That single row is one entire theory of how all 4,522 customers behave. The quoted values like r = 0.6511 are column averages, not draws."),
  ("challenge", "Your R-hat is 1.002 and you have no divergences. Does that prove the model is right?",
   "No, and the thesis says so explicitly. These diagnostics are necessary, not sufficient. They detect certain failures of the sampler; they certify nothing about whether the model is appropriate. A badly misspecified model can converge beautifully. That is why I report them before the substantive results rather than as evidence for them."),
  ("method", "What priors did you use, and how sensitive are the results to them?",
   "Weakly informative half-normals on the positive parameters, with scales set from calibration-data summary statistics, because these parameters carry units — the purchase-rate parameters are order one on a weekly scale while the Gamma-Gamma scale is in pounds and must be order hundreds. With 4,522 customers the likelihood dominates for the population parameters. The one place a prior genuinely binds is the between-segment variance in H2, which I flag prominently."),
  ("hostile", "Using the data to set your priors is double-dipping. Isn't that cheating?",
   "It is a legitimate criticism and I name it in the thesis. What I did is set prior scales from marginal summary statistics, which is the empirical-Bayes tradition and has precedent in hierarchical marketing models — Rossi and Allenby, among others. It is not fully Bayesian and I do not claim it is. The alternative, unit-ignorant priors, concentrates mass far from where the data live and degrades both inference and sampler behaviour."),
  ("extend", "Why NUTS rather than Gibbs or Metropolis-Hastings?",
   "Because the posterior has correlated parameters — r and alpha move together — and random-walk methods diffuse badly in correlated geometry. HMC uses the gradient to make long, informed proposals, and NUTS removes the need to tune trajectory length. The practical evidence is the effective sample size: over 1,100 from 4,000 draws, which a random walk would not approach on this geometry."),
 ]),

dict(n=9, kicker="METHODOLOGY · 3", title="Three methodological developments",
 says="Calibration-first evaluation, hierarchical segment pooling, and a decision-theoretic simulation.",
 concepts=[
  ("CRPS", "Continuous Ranked Probability Score — a proper scoring rule that grades a whole predictive distribution, rewarding accuracy and calibration together."),
  ("Proper scoring rule", "One that is optimised by reporting your true belief, so it cannot be gamed by overstating confidence."),
 ],
 qs=[
  ("clarify", "Why report CRPS as well as coverage?",
   "Because coverage alone is trivially gameable. An interval from zero to infinity has perfect coverage and zero value. CRPS penalises width as well as miscoverage, so reporting them together establishes that the intervals are both honest and sharp. Mine are 89.3% coverage at a mean width of 4.59 transactions."),
  ("challenge", "Are these really 'developments', or just standard practice applied here?",
   "Fair challenge, and I would not claim any of the three is novel in isolation — calibration comes from forecasting, shrinkage from Efron and Morris in the 1970s, and the linear-utility result from Berger. The contribution is their combination on this problem, and the finding that falls out of it: that the three questions consume different amounts of the posterior. I am explicit about this in the contributions section."),
 ]),

dict(n=11, kicker="FINDING 1A", title="H1 — accuracy and ranking",
 says="Error improvements are modest; the decisive panel is ranking, NDCG@100 of 0.91 against 0.53 — and that gap is an upper bound.",
 concepts=[
  ("NDCG@100", "Normalised Discounted Cumulative Gain over the top 100 — whether the ranking puts genuinely valuable customers at the top."),
  ("Why ranking matters", "Customer value is heavily concentrated, and budgets reach only the top of the list, so ordering matters more than absolute error."),
 ],
 qs=[
  ("challenge", "Your MAE advantage is small. Isn't the honest conclusion that Bayesian methods barely help?",
   "For predicting the number, largely yes, and I say so. The advantage is in ranking, and that is the operationally relevant quantity because marketing budgets reach the top decile, not the average customer. A model slightly wrong about the typical customer but right about who the top customers are is more useful, and MAE cannot see that distinction."),
  ("hostile", "You admit the NDCG gap is an upper bound. So you don't actually know the Bayesian model is better at ranking.",
   "I know it is better in this comparison, and I know the comparison favours me, so the true gap is smaller than 0.91 against 0.53. The reason is that XGBoost was trained on a shorter inner split to avoid leakage, so it had less data. I chose to state that rather than present the raw number as clean. The direction of the conclusion survives; its magnitude should be read cautiously."),
  ("method", "Why not retrain XGBoost on the full window to make it fair?",
   "Then it would be trained on data overlapping the evaluation period, which is leakage and would flatter it instead. There is no split that is symmetric for both model families, because the generative model needs no inner validation set and the supervised one does. I chose the asymmetry that disadvantages the baseline and disclosed it, rather than the one that would have inflated my own result."),
  ("extend", "Would a neural network close the gap?",
   "Possibly on accuracy; it has far more capacity. But it would face the same two structural problems. It would still need labels for a latent state nobody observes, and it would still produce point predictions unless explicitly built to be distributional — at which point the two-posteriors distinction applies to it too. That is the part of my finding that transfers to any such model."),
 ]),

dict(n=12, kicker="FINDING 1B", title="H1 — calibrated uncertainty",
 says="89.3% empirical coverage against a nominal 90%, CRPS 1.22, P(alive) AUC 0.71.",
 concepts=[
  ("Empirical coverage", "The fraction of held-out outcomes that actually fell inside the stated 90% predictive interval."),
  ("P(alive) AUC", "How well the inferred probability of being active discriminates customers who did return from those who did not."),
 ],
 qs=[
  ("clarify", "What would it have meant if coverage had come out at 60%?",
   "That the model was overconfident and its intervals were decoration. You could still use the point predictions, but any decision using the spread — risk-based budgeting, a probability threshold — would be built on a false premise. Coverage is what licenses the rest of the analysis."),
  ("challenge", "89.3% against 90% — is that difference significant, or luck?",
   "With 4,522 customers the standard error on a coverage estimate near 0.9 is about half a percentage point, so 89.3% is within roughly one and a half standard errors of nominal. I would not claim it is exactly 90%; I claim it is close enough that the stated confidence can be taken at face value, which is the operationally relevant statement."),
  ("method", "An AUC of 0.71 isn't very high. Does the model really identify churned customers?",
   "It is moderate, and I would not oversell it. But the ceiling here is low: attrition is genuinely unobservable and a third of customers have only one purchase, giving almost no signal. 0.71 says the latent state carries real information while remaining far from deterministic — which is the honest characterisation of what recency and frequency can support."),
  ("hostile", "Coverage is averaged over all customers. Could it be good on average and terrible for the customers you care about?",
   "A sharp question, and the right diagnostic is coverage by decile rather than in aggregate. The thesis reports that the top deciles remain well calibrated even where stationarity bites the middle of the distribution. So the aggregate figure is not hiding failure where the money is — though I agree the aggregate alone would not establish that."),
 ]),

dict(n=13, kicker="FINDING 1C · WORKED EXAMPLE", title="One customer, end to end",
 says="Customer 14817: expected CLV £1,364 with a £1,326–£1,401 interval; predictive £0–£2,888; realised £1,010. P(CLV > £600) = 1.00 vs 0.77.",
 concepts=[
  ("Posterior of an expectation", "Uncertainty about the underlying rule. Shrinks as data accumulates."),
  ("Posterior predictive", "Uncertainty about the realised outcome. Does not shrink, because people are genuinely variable."),
 ],
 qs=[
  ("clarify", "Explain the two intervals to a non-statistician.",
   "You can know a coin is perfectly fair — total certainty about the coin — and still not know whether the next flip is heads. The narrow interval is my confidence about this customer's underlying rate. The wide one is what they might actually spend. Knowing the rule is not the same as knowing the result."),
  ("challenge", "Why this customer? Did you pick one that makes your point?",
   "I selected a customer with enough history to be interesting — four repeat purchases — rather than one chosen for the size of the gap. The phenomenon is not special to them: it holds for every customer in the dataset, and the aggregate consequence is the 96% of customers pinned at 0 or 1 under the expectation rule. A single illustrative case is a teaching device, not the evidence."),
  ("hostile", "The realised value, £1,010, is well below your point estimate of £1,364. Your model was wrong.",
   "The point estimate was off, yes. But the relevant claim is about the predictive interval, which ran from zero to £2,888 and contained the outcome comfortably. That is exactly what calibrated uncertainty is for — and it is why I show both numbers rather than only the one that flatters the model. A single customer cannot confirm or refute calibration; the 89.3% figure across 4,522 customers does."),
  ("method", "How do you compute the predictive interval in practice?",
   "For each of the 4,000 posterior draws, instead of computing the expected value, I simulate an actual outcome from that draw: draw a transaction count from the implied negative binomial, draw the spend, multiply. That gives 4,000 realised values rather than 4,000 expectations, and the interval is their 5th and 95th percentiles."),
 ]),

dict(n=14, kicker="FINDING 1D", title="Why the strongest baseline trails",
 says="With 24 features, the learner mostly rediscovers what the generative model assumes by construction.",
 concepts=[
  ("Inductive bias", "What a model assumes before seeing data. The generative model's structure is given; XGBoost must learn it from examples."),
 ],
 qs=[
  ("clarify", "Why does a weaker model beat a stronger learner?",
   "Because the structure is known. Recency, frequency and heterogeneity are not patterns that need discovering here — they are the mechanism, and the BG/NBD has them built in. XGBoost must infer that structure from 4,522 examples, and with a third of them having a single purchase there is very little to infer from. Capacity does not help when the binding constraint is information."),
  ("challenge", "Did you tune XGBoost properly, or is this a straw man?",
   "It had 24 engineered features, a two-stage design separating transactions from spend, and hyperparameters tuned on an inner split. I would call it a serious benchmark rather than a straw man. The caveat I volunteer is that the inner split gave it less data than the Bayesian model saw, which is why I treat the ranking gap as an upper bound."),
  ("extend", "What would make XGBoost competitive?",
   "More customers, richer covariates, and a distributional output. The generative model's advantage comes from supplying structure that compensates for sparse individual histories; with tens of thousands of customers and real features — channel, product category, demographics — that advantage erodes. Chamberlain and colleagues report exactly that crossover at scale, and I cite it."),
 ]),

dict(n=15, kicker="FINDING 2", title="H2 — partial pooling across segments",
 says="Never worst in any segment; lowest aggregated error on small segments (1.746 vs 1.755 no pooling / 1.757 complete pooling). Partially supported.",
 concepts=[
  ("Complete / no / partial pooling", "One model for everyone, a separate model per country, or country-level parameters drawn from a shared distribution."),
  ("Non-centred parameterisation", "A reparameterisation that decouples the group effects from the group variance, avoiding Neal's funnel and the divergences it causes."),
 ],
 qs=[
  ("challenge", "1.746 versus 1.755 is a 0.5% improvement. Is that worth anything?",
   "On its own, almost nothing, and I do not claim otherwise — hence 'partially supported'. The defensible claim is adaptivity rather than magnitude: partial pooling is never the worst option in any segment, whereas no-pooling and complete-pooling each fail badly somewhere. You are buying robustness against picking the wrong one, not a large accuracy gain."),
  ("hostile", "You admit the between-segment prior was tight. Didn't you force the pooling result?",
   "The tight prior constrains how different segments are allowed to be, so it biases the comparison toward the null — toward finding no benefit from pooling. That works against H2, not for it. The honest framing, which the thesis uses, is that this is a prior-constrained test: I can say pooling did not hurt and helped slightly, but I cannot say how much it would help under a more permissive prior. That is a limitation I state rather than hide."),
  ("method", "Why collapse countries under 30 customers into 'Other'?",
   "Below roughly that size the segment contributes almost no information of its own and the estimate is effectively the population mean with extra variance. Keeping them separate would add parameters without adding signal. The threshold is a judgement call; the qualitative conclusion is not sensitive to moving it."),
  ("clarify", "Why does France benefit more than the UK?",
   "Because shrinkage is proportional to ignorance. The UK has 4,152 customers and its own data overwhelms the prior, so it barely moves. France has 54, so its estimate is pulled hard toward the global mean. The model weights each segment by how much evidence it actually has — that is the whole mechanism, and it is the Efron–Morris result."),
 ]),

dict(n=16, kicker="FINDING 2B", title="The mechanism: shrinkage in proportion to ignorance",
 says="Efron–Morris guarantees aggregate improvement, not a win in every group — the result is textbook, not anomalous.",
 concepts=[
  ("Stein / Efron–Morris shrinkage", "Pulling individual estimates toward a common mean reduces total squared error, even though some individual estimates get worse."),
 ],
 qs=[
  ("clarify", "If shrinkage is guaranteed to help, why is H2 only partially supported?",
   "Because the guarantee is about aggregate squared error, not about every segment, and not about the specific metric or horizon I evaluate on. Theory says total error should fall; it does. It does not promise a large fall, nor a win in each country. My verdict matches what the theorem actually promises rather than what one might hope it promises."),
  ("extend", "Could you pool on something other than country?",
   "Yes, and it might work better. Country is a proxy for behaviour, and probably a weak one — a London wholesaler likely resembles a Paris wholesaler more than a London gift-buyer. Pooling on acquisition channel, first-purchase category, or a behavioural segment would group customers who are genuinely alike. That is the first item in my future-work section."),
 ]),

dict(n=17, kicker="FINDING 3", title="H3 — decision-theoretic targeting",
 says="For a linear objective the posterior mean is sufficient — the posterior's tails earn nothing here.",
 concepts=[
  ("Linear utility", "Profit = value minus cost. Expected utility then depends only on expected value."),
  ("Sufficiency", "When a statistic contains all decision-relevant information, the rest of the distribution cannot improve the decision."),
 ],
 qs=[
  ("challenge", "H3 failed. Why include it?",
   "Because a negative result with a clean explanation is more useful than a positive one without. Berger's theorem says that for a linear objective the posterior mean is sufficient, so the tails cannot help. I demonstrated that empirically, swept across cost assumptions to show it was not an artefact of one choice. It tells a practitioner precisely when to stop paying for the extra machinery."),
  ("method", "How would you design a decision where the full posterior does pay?",
   "Make the objective non-linear. A hard budget constraint with a penalty for overspending, a convex cost of contact, or an explicitly risk-averse objective such as maximising a lower quantile of return rather than the mean. In all of those the curvature means the spread enters the expected utility, and the posterior stops being redundant. I set this out in future work."),
  ("hostile", "So the Bayesian machinery was pointless for the decision. Why build it?",
   "Not pointless — redundant for this particular decision. It was essential for calibration, which is H1, and it was essential for the probability rule to function at all, which is the methodological finding. And you only know the mean is sufficient because you computed the full posterior and checked. The negative result is only available from inside the Bayesian framework."),
 ]),

dict(n=18, kicker="METHODOLOGICAL FINDING ★", title="The pitfall: which posterior?",
 says="Using the wrong posterior: hit rate 0.85 → 0.62, wasted spend £55,040 → £144,738, roughly tripled.",
 concepts=[
  ("The 96% collapse", "Computed from the expectation posterior, P(CLV > c) lands at exactly 0 or 1 for 96% of customers, destroying the ranking."),
  ("The practical diagnostic", "If most of your predicted probabilities sit at 0 or 1, you are using the wrong distribution."),
 ],
 qs=[
  ("clarify", "Why does the probability collapse to 0 or 1?",
   "Because the expectation is known very precisely — the interval for customer 14817 is only £75 wide. A threshold at £600 is therefore either entirely above or entirely below that interval for almost everyone, so the probability is 0 or 1 with nothing in between. The ranking degenerates into arbitrary tie-breaking among thousands of customers all scored 1.00."),
  ("challenge", "Isn't this just a bug in your implementation rather than a finding?",
   "It is a conceptual error that produces working code — which is what makes it worth reporting. Nothing crashes, nothing warns, and the output looks like a confident probability. It is the kind of mistake that survives code review precisely because both objects are correctly called 'the posterior'. I give a one-line diagnostic so others can detect it."),
  ("hostile", "Any competent Bayesian knows the difference between a posterior and a posterior predictive. Is this really a contribution?",
   "The distinction is textbook, and I do not claim to have discovered it. What I contribute is the demonstration that it is a load-bearing error in applied CLV specifically — with a measured cost of roughly tripled wasted spend — plus a diagnostic that catches it. Textbook knowledge and routine applied practice are not the same thing, and the gap between them is where this sits."),
  ("extend", "Does this apply beyond CLV?",
   "To any model producing distributional output where a decision rule asks about a realised outcome. Neural networks with distributional heads, conformal prediction, quantile regression — all face the same fork. The question to ask is always: am I uncertain about the rule, or about the result? That generalises well beyond this thesis."),
 ]),

dict(n=19, kicker="FINDINGS IN THE ROUND", title="Summary of the three hypotheses",
 says="The value of a posterior is realised in proportion to how much of it the question actually uses.",
 concepts=[
  ("The synthesis", "H1 uses the posterior's centre and spread and wins. H2 uses its structure and gains a little. H3 uses its tails and gains nothing, because a linear objective ignores them."),
 ],
 qs=[
  ("clarify", "If you had to defend one sentence from this thesis, which?",
   "That there are two kinds of uncertainty and confusing them is expensive. Uncertainty about the rule shrinks with data; uncertainty about the outcome does not. Building a decision rule on the wrong one produced a system that looked confident and nearly tripled wasted spend."),
  ("challenge", "One supported, one partial, one rejected. Is that a successful thesis?",
   "I would argue it is a more informative outcome than three confirmations. The pattern is itself the finding: the three questions demand progressively more of the posterior, and the returns fall off exactly where theory predicts they should. Three supported hypotheses would have told me less about where the method's value actually lies."),
 ]),

dict(n=21, kicker="CONTRIBUTION", title="Impact on the research area",
 says="Extends BTYD validation from accuracy to calibration; positions pooling and the decision result in the literature.",
 concepts=[
  ("BTYD", "Buy Till You Die — the model family covering Pareto/NBD, BG/NBD and their relatives."),
 ],
 qs=[
  ("challenge", "What is genuinely new here, as opposed to applied?",
   "Three things, none of them a new estimator. Importing calibration validation into the BTYD tradition, which reports accuracy almost exclusively. Quantifying the cost of the two-posteriors confusion in a decision setting, with a diagnostic. And an empirical demonstration of the linear-utility sufficiency result in a real business problem. It is a methodological and evaluative contribution rather than a modelling one, and I frame it that way."),
  ("hostile", "A master's thesis that invents no new model — is that enough?",
   "I would say the field has no shortage of estimators and a real shortage of honest evaluation. Knowing when a method's extra machinery stops paying is as useful as another variant that is marginally better on one dataset. My H3 result is a negative finding with a theoretical explanation, which is exactly the kind of result that tends not to get published and should."),
 ]),

dict(n=23, kicker="HONEST ASSESSMENT", title="Limitations — and which way they bias the result",
 says="Stationarity violated (20–30% over-prediction for mid-frequency customers); the two design biases run in opposite directions.",
 concepts=[
  ("Direction of bias", "Not just naming a limitation but saying which way it pushes the conclusion and how far."),
 ],
 qs=[
  ("method", "Why state the direction of each bias rather than just listing limitations?",
   "Because a limitation without a direction is not actionable. 'Stationarity is violated' tells a reader nothing about whether to trust the number. 'It biases mid-frequency CLV upward by 20 to 30% while the top deciles stay calibrated' tells them exactly where the estimate is safe to use and where it is not."),
  ("challenge", "Which limitation worries you most?",
   "The wholesale buyers. The customer with 200 repeat purchases in 65 weeks is doing scheduled procurement, which is a different behavioural process entirely, and mixing it into a consumer model violates the Poisson assumption in a way the diagnostics will not catch. I flag it rather than dropping the rows, but a mixture model separating the two populations would be the proper fix."),
  ("hostile", "You list many limitations. Does anything survive them?",
   "The ranking conclusion and the calibration result both survive, and I argue why. The two design biases run in opposite directions — the tight prior biases H2 toward the null while the inner-split asymmetry flatters H1 — so they do not compound into one systematic distortion. And the scope limitations are monotone transformations that leave the ordering intact. That is the specific argument in the Limitations section."),
 ]),

dict(n=24, kicker="CONCLUSION", title="Summary and outlook",
 says="Bayesian generative treatment gives accurate and calibrated CLV; pooling buys robustness; the posterior must match the question.",
 concepts=[
  ("Outlook", "Covariates, non-linear objectives, behavioural rather than geographic pooling, and non-stationary extensions."),
 ],
 qs=[
  ("extend", "What would you do with another year?",
   "Three things in order. Add covariates to the hierarchical structure so pooling groups behaviourally similar customers rather than geographically co-located ones. Build a non-linear decision objective where the posterior's tails actually matter, which is the proper test H3 could not be. And relax stationarity with a time-varying rate, since that is the assumption I can most clearly show is violated."),
  ("clarify", "What is your single recommendation to a practitioner?",
   "Validate coverage, not just error. An uncalibrated interval is worse than no interval, because it invites decisions it cannot support. And when you compute a probability, be certain which distribution it came from — if most of your probabilities are 0 or 1, you have used the wrong one."),
  ("hostile", "Would you use this model in production tomorrow?",
   "For ranking customers and for honest uncertainty, yes, with two caveats: separate out the wholesale buyers, and refit regularly because stationarity decays. For absolute CLV in the middle of the distribution I would be more cautious, since that is where the 20 to 30% over-prediction sits. I would not use it where the decision has a sharply non-linear objective without re-testing the decision rule."),
 ]),
]
