# -*- coding: utf-8 -*-
"""Deck body, v3 — restructured for delivery.
Four acts: why / how / what I found / what it means.
Slides whose notes begin [OPTIONAL] can be dropped live if running short."""

OPT = "[OPTIONAL — skip if running short]  "

# ══════════════ ACT 1 · WHY ══════════════

s = slide("The decision behind the thesis", kicker="Context",
 notes=("~90 s. I want to start with a decision rather than a model, because everything here comes "
        "out of one.\n\n"
        "A retailer has a marketing budget every week and has to choose who to spend it on. To choose "
        "well you need to know what each customer will be worth from here — not what they have already "
        "spent, because that money is in.\n\n"
        "And those two numbers come apart. Two customers can spend identically today and be worth "
        "completely different amounts tomorrow. Ranking people by what they have already spent — which "
        "is what most businesses do — cannot tell them apart."))
claim(s, "Marketing spend has to be allocated before any of the value arrives, so the question is what "
         "a customer will be worth from here — not what they have already spent.")
bullets(s, [
 ("The money goes out first", "Advertising, discounts, delivery. It only pays back if the customer returns."),
 ("Past spending is a record, not a forecast", "Two customers can spend identically today and be worth entirely different amounts tomorrow."),
 ("So the business needs a number nobody can observe", "Expected future value per customer — which is what this thesis estimates, and how well."),
], top=In(2.5), size=18)

s = slide("The data", kicker="Context",
 notes=("~60 s. Keep this short. A UK giftware retailer, two years of real transactions, from the UCI "
        "Online Retail II dataset. After cleaning, 4,522 customers.\n\n"
        "The two numbers to notice are on the right. A third of customers bought exactly once and never "
        "returned — that is the hard case and it recurs all the way through. And spending is heavily "
        "lopsided: the average basket is well above the typical one.\n\n"
        "The split matters: the model only ever sees data before 1 March 2011, and is scored on the 40 "
        "weeks after, which it never sees."))
claim(s, "Two years of real transactions from a UK giftware retailer, split by date so the model is "
         "always scored on a period it has never seen.")
stat_row(s, [("4,522","customers\nafter cleaning",NAVY),
             ("65 wks","the model sees\n(to 1 Mar 2011)",NAVY),
             ("40 wks","scored on\n(never seen)",BRAND),
             ("33%","bought once and\nnever returned",BRAND)], top=In(2.45))
bullets(s, [
 "UCI Online Retail II — a public dataset, so every result here is reproducible",
 "Spending is heavily skewed: mean basket £385 against a typical £299, with a long tail of large orders",
 "Split by date rather than at random, because predicting the future from the past is the actual task",
], top=In(4.3), size=16.5)

s = slide("Why this is hard", kicker="The problem",
 notes=("~2 min. Slow down here — this is the hinge of the thesis.\n\n"
        "If you cancel a gym membership, the gym knows. There is a date. A shop has no cancel button: "
        "customers simply stop coming and never say so.\n\n"
        "So take someone silent for fifteen weeks. Have they gone? You cannot say. If they normally buy "
        "every three weeks, that is alarming. If they buy twice a year, it is completely ordinary. The "
        "same silence means opposite things depending on whose silence it is.\n\n"
        "Two consequences, and both constrain the method. There is no record of churn for anyone, so "
        "there is nothing to train a classifier on. And any fixed cut-off — 'inactive after six months' "
        "— necessarily gets one of those two customers wrong. Whether someone is still a customer has "
        "to be worked out, not looked up."))
claim(s, "Customers never announce that they have left, so the single fact that determines future value "
         "is never recorded for anyone.")
bullets(s, [
 ("A subscription — the easy case", "You cancel, so there is a date. Churn can simply be counted."),
 ("A shop — this case", "No cancellation. People fade out silently, and nothing is recorded."),
], top=In(2.45), size=18)
box(s, [("Two customers, both silent for fifteen weeks", 16, True, NAVY),
        ("One normally buys every three weeks — alarming.     One buys twice a year — entirely normal.",
         15.5, False, INK),
        ("No fixed cut-off can separate them, and there is no churn record to learn from. "
         "Activity has to be inferred.", 15.5, True, BRAND)], In(4.45), In(1.45))

s = slide("What I set out to test", kicker="Aims",
 notes=("~2 min. Three questions, and I will give you the answers now so you can follow the reasoning "
        "rather than wait for a reveal.\n\n"
        "The first asks whether this approach predicts better than the standard alternatives — and, "
        "separately, whether it is honest about how certain it is. Supported.\n\n"
        "The second: there are 4,152 UK customers but only 54 French. Can the small markets borrow "
        "information from the large ones instead of being judged on their own thin data? Partially "
        "supported.\n\n"
        "The third asks whether carrying the full range of possible values, rather than a single best "
        "estimate, actually changes who you would target. Not supported — and that turned out to be the "
        "most informative of the three, because there is a clean reason why it had to come out that way."))
claim(s, "Three questions, each demanding more from the model's output than the last. The verdicts are "
         "stated here so the evidence that follows can be judged against them.")
bullets(s, [
 ("H1 — Is it more accurate, and is it honest about its own uncertainty?",
  "Against a simple baseline, an industry heuristic, and a strong machine-learning model.        Supported"),
 ("H2 — Can a market with 54 customers borrow strength from one with 4,152?",
  "Rather than being fitted alone, or dissolved into a single global model.        Partially supported"),
 ("H3 — Does the full range of possible values change who you target?",
  "A marketing-spend simulation under realistic costs, swept across assumptions.        Not supported"),
], top=In(2.5), size=16.5)

# ══════════════ ACT 2 · HOW ══════════════
section("The approach", "What the model assumes, and why it is estimated this way", notes="~10 s.")

s = slide("Describing behaviour instead of finding patterns", kicker="Approach",
 notes=("~2 min. This is genuinely different from standard machine learning and worth contrasting "
        "directly.\n\n"
        "Machine learning says: here are columns of data, find whatever pattern predicts the answer. "
        "It is powerful, and it needs examples of the right answer to learn from.\n\n"
        "I do the opposite. I write down, in advance, a description of how I believe shopping happens — "
        "a few simple behaviours — and then ask the data which version of that description fits best.\n\n"
        "The reason is not stylistic, it is forced. The thing I need to know is invisible. There is no "
        "record saying 'this customer has left', for anyone. A classifier cannot be trained on a label "
        "that does not exist. But a description of behaviour can contain an invisible step, and the "
        "purchase histories still constrain how likely that step was."))
claim(s, "Because the fact that matters is never recorded, the model has to state how purchasing happens "
         "rather than learn a pattern from labelled examples.")
bullets(s, [
 ("The machine-learning route", "Supply features, learn a mapping to a target. Requires that target to exist for each customer."),
 ("The route taken here", "State how purchasing arises — including a step nobody observes — and ask which version fits the data."),
], top=In(2.5), size=18)
bullets(s, [
 "There is no churn label for any customer, so the first route cannot address the question at all",
 "The second can, because the purchase histories constrain the invisible step even though it is never seen",
], top=In(4.55), size=16.5)

s = slide("What this approach buys", kicker="Approach",
 notes=("~90 s. Three things, and they map onto the three questions.\n\n"
        "First, it handles the invisible state directly — it produces a probability that each customer "
        "is still active, which nothing in the data ever told it.\n\n"
        "Second, every number in the model means something. Not a weight in a tree, but 'how often this "
        "customer buys' and 'how likely they are to stop'. That means a manager can disagree with the "
        "model on substantive grounds, which matters for adoption.\n\n"
        "Third, and this is what the whole thesis turns on: it returns a range rather than a single "
        "number. That is what makes it possible to ask whether the uncertainty is honest, and to make a "
        "decision that accounts for risk. Without it, questions one and three could not even be posed."))
claim(s, "Three things follow from this choice, and each one makes one of the three research questions "
         "answerable.")
bullets(s, [
 ("It estimates the invisible state", "Produces a probability that each customer is still active — something no column in the data records."),
 ("Every parameter means something", "Not a weight inside a tree, but a buying rate and a chance of lapsing. A manager can argue with it."),
 ("It returns a range, not a single number", "Which is what lets us ask whether the stated confidence is honest, and whether uncertainty changes a decision."),
], top=In(2.5), size=17)

s = slide("The model in four parts", kicker="The model",
 notes=("~2 min. Four behaviours, none of them complicated.\n\n"
        "One: while someone is still a customer, they buy at random but around their own typical rate. "
        "Like rainfall — you cannot predict Tuesday, but you can say it rains twice a week here.\n\n"
        "Two: after each purchase they privately decide whether that was the last one. A biased coin "
        "only they can see.\n\n"
        "Three, and this one does the real work: everybody is different, and the model says so explicitly "
        "instead of describing an average customer who does not exist.\n\n"
        "Four: how much they spend per visit, which is very lopsided.\n\n"
        "Put together: value equals how often, times how much. That multiplication assumes the two are "
        "independent, which I test rather than assume — I come back to it in the limitations."))
claim(s, "Four behavioural assumptions, estimated jointly, then combined into a value per customer.")
bullets(s, [
 ("1 · Everyone has their own pace", "While still active, purchases arrive at random around that customer's own typical rate."),
 ("2 · After each purchase, a private decision to stop", "An unobserved choice to lapse, with a probability that differs by customer."),
 ("3 · Customers differ, and that is modelled explicitly", "Not one average customer, but the whole spread of paces and lapse rates."),
 ("4 · Spend per visit", "Strongly skewed — a few very large orders pull the average well above the typical basket."),
], top=In(2.45), size=16, gap=6)
box(s, [("Value  =  how often they buy   ×   how much they spend each time       "
         "(BG/NBD with Gamma-Gamma)", 16.5, True, NAVY)], In(5.65), In(0.6))

s = slide("Customers differ far more than one rate allows", kicker="The model",
 notes=("~90 s. Part three sounds like a technicality. It is the difference between a model that works "
        "and one that does not, and the data settles it.\n\n"
        "The average customer makes 3.78 repeat purchases. There is a basic result in probability: if "
        "everybody shared a single rate, the spread of those counts would be about the same size as the "
        "average. Around 3.8.\n\n"
        "The actual spread is 77.7. More than twenty times larger.\n\n"
        "That gap is not noise — it is evidence that customers genuinely differ, and that any model built "
        "around a typical customer would be describing nobody. It is also the mechanism behind the "
        "ranking result later: thin histories get pulled toward the population instead of being taken at "
        "face value."))
claim(s, "If every customer shared one buying rate, the spread of purchase counts would roughly match the "
         "average. It is twenty times larger.")
stat_row(s, [("3.78","average repeat\npurchases",NAVY),
             ("≈ 3.8","spread if everyone\nwere alike",TEAL),
             ("77.7","spread actually\nin the data",BRAND)], top=In(2.5))
bullets(s, [
 "This is the evidence for modelling the whole range of customers rather than a representative one",
 "It is also why a customer with two purchases is treated differently from one with two hundred",
], top=In(4.35), size=17)

s = slide("The distributions, and what each one is doing", kicker="The model",
 notes=("~2 min. The model is fully specified, so it is worth setting out exactly what is assumed and "
        "what came out of the estimation.\n\n"
        "Purchases arrive at a customer-specific rate. That rate is spread across the base by a Gamma "
        "distribution, estimated at shape 0.65 and rate 7.12 — a mean of about one purchase every eleven "
        "weeks.\n\n"
        "Lapsing is a decision after each purchase, so the number of further purchases follows a "
        "geometric pattern. The chance of lapsing is spread by a Beta distribution, implying about 4.6 "
        "per cent per transaction.\n\n"
        "Spend is Gamma within a customer and Gamma across customers. The implied average basket is £391 "
        "against £385 observed — so the model is recovering the skew rather than smoothing it away.\n\n"
        "The consequence at the bottom is the one to land: counts come out more spread than a simple "
        "model allows, which is exactly what the previous slide showed in the data."))
claim(s, "Each behaviour needs a distribution to describe how it varies across customers. These are the "
         "choices, and what the data estimated them to be.")
table(s, ["Behaviour", "Distribution", "Estimated", "What it implies"], [
 ["Purchases while active",        "Poisson",      "—",                 "Random timing, no fixed cycle"],
 ["How buying pace varies",        "Gamma(r, α)",  "r = 0.65, α = 7.12","One purchase every ~11 weeks on average"],
 ["Lapsing after a purchase",      "Geometric",    "—",                 "Lapse tied to purchases, not to the calendar"],
 ["How lapse-chance varies",       "Beta(a, b)",   "a = 0.22, b = 4.47","About 4.6% chance per transaction"],
 ["Spend per visit",               "Gamma-Gamma",  "1.71, 3.97, 681",   "Implied average basket £391 (observed £385)"],
], top=In(2.45), row_h=In(0.46), size=11.5)
box(s, [("The consequence: purchase counts come out far more spread than a single-rate model allows — "
         "which is precisely the pattern the data showed on the previous slide.", 15, False, INK)],
    In(5.72), In(0.62))

s = slide("Why these distributions and not others", kicker="The model",
 notes=("~2 min. An examiner is entitled to ask why not something else, so this is the answer. Three "
        "requirements have to hold at the same time, and together they leave very little.\n\n"
        "First, the range of values. A buying rate cannot be negative, which rules out the normal "
        "distribution immediately. A probability has to sit between zero and one, which rules out the "
        "Gamma. That one requirement removes most candidates.\n\n"
        "Second, flexibility. The Gamma can describe either a base with a clear typical customer, or one "
        "where most people are barely active with a few heavy buyers. The data chose the second — the "
        "estimate is 0.65. A less flexible choice could only ever have produced one of those pictures.\n\n"
        "Third, the mathematics has to come out. These pairings have the property that the combination "
        "solves exactly. Without that, every single evaluation needs a numerical approximation for every "
        "one of 4,522 customers, thousands of times over — which is not feasible, and the approximation "
        "error degrades the estimation itself. I hit exactly that: an early hand-written version would "
        "not run at all until it was replaced with the stable closed-form one."))
claim(s, "Three requirements have to hold at once. Together they leave very few workable candidates.")
bullets(s, [
 ("1 · The range of values has to match",
  "A buying rate cannot be negative, which rules out the normal distribution. A probability must sit between 0 and 1, which rules out the Gamma."),
 ("2 · The shape must not be decided in advance",
  "The Gamma can describe a base with a typical customer, or one where most are barely active. The data chose the second — it was not imposed."),
 ("3 · The mathematics has to resolve exactly",
  "These pairings combine into a closed form. Without it, every evaluation needs a numerical approximation per customer — infeasible, and the error degrades the estimation."),
], top=In(2.45), size=15.5, gap=5)
box(s, [("A lognormal rate meets the first two requirements and fails the third. In this project an early "
         "hand-written version proved unstable and would not run until replaced by the closed-form one.",
         14.5, False, MUTE),
        ("These describe real variation between customers. They are part of the model of behaviour — not "
         "assumptions I imposed about the answer.", 15, True, NAVY)], In(5.55), In(1.05))

s = slide("Why this needs a Bayesian treatment", kicker="Estimation",
 notes=("~2 min. The usual way to fit a model like this returns one number per parameter. That is enough "
        "if all you want is a prediction. It is not enough for two of my three questions.\n\n"
        "Question one asks whether the model's stated confidence is honest. You cannot check that if the "
        "model only ever produces a single number — there is no stated confidence to test.\n\n"
        "Question three asks whether uncertainty changes a decision. A single number cannot be carried "
        "into a decision rule that is about risk; there is nothing to carry.\n\n"
        "So the Bayesian treatment is not a philosophical preference here. It is what makes two of the "
        "three questions askable at all. What it returns instead of a number is a whole range of "
        "plausible values, for every parameter and for every customer — and that range is what the rest "
        "of the thesis evaluates."))
claim(s, "Two of the three research questions are about uncertainty itself. A method that returns a "
         "single number cannot address them.")
bullets(s, [
 ("The standard approach returns one number per parameter", "Sufficient for a prediction. Nothing to test, and nothing to carry into a decision."),
 ("The Bayesian treatment returns a range", "For every parameter, and for every customer — the estimate and the confidence in one object."),
], top=In(2.5), size=18)
bullets(s, [
 "H1 asks whether the stated confidence is honest — which requires there to be a stated confidence",
 "H3 asks whether uncertainty changes a decision — which requires uncertainty to be carried through to it",
 "The cost: the answer cannot be calculated directly, so it is approximated by simulation (next slide)",
], top=In(4.5), size=16.5)

s = slide("Where the starting guesses come from", kicker="Estimation",
 notes=("~2 min. A Bayesian model needs a rough starting guess for every number it estimates, so it is "
        "fair to ask where mine came from and whether they are doing the work. The short answer is that "
        "they split into two kinds.\n\n"
        "Three of these numbers mean something in the real world. Alpha is measured in weeks, so I "
        "looked at the data: customers buy about once every thirteen weeks, and that became the starting "
        "guess. B relates to how many people stop after one purchase, and a third of customers did "
        "exactly that. Gamma is measured in pounds, and the average repeat basket is £385.\n\n"
        "The other three have no units at all. They are internal shape numbers that are naturally small "
        "— somewhere around one or two, for any dataset. So I did not read anything from the data. I "
        "just put a small value in and let the data decide.\n\n"
        "Why bother splitting them? Because one setting for everything is actively harmful here. Alpha "
        "needs to be around thirteen and gamma around two hundred and fifty. A single guess wide enough "
        "for one is badly wrong for the other — and when I started with one setting for all of them, the "
        "estimation struggled and took hours.\n\n"
        "The important point: these are deliberately vague. Each guess allows roughly ten times more or "
        "less than the value shown, so the data decides the answer, not the guess. With 4,522 customers "
        "it overrules them easily. And I checked that by simulating customers from the guesses alone, "
        "before fitting, to confirm they produced plausible purchase counts and spending.\n\n"
        "If asked the technical version: all six are half-normal priors, with scales 1.25, 16.1, 1.88, "
        "3.81, 2.0/3.76 and 322. It is empirical Bayes on the scale of otherwise-vague priors — "
        "standard and defensible, but not fully Bayesian, and the thesis says so.\n\n"
        "One number is not on this slide: the hierarchical model's between-country setting, which is the "
        "one prior that genuinely constrains a result. That has its own caveat on the H2 slide."))
claim(s, "The model needs a rough starting guess for each number. Where the number means something in "
         "the real world, the guess comes from the data. Where it does not, it is left deliberately vague.")
table(s, ["The number", "What it means", "Where its starting guess comes from"], [
 ["\u03b1", "How many weeks between purchases",      "From the data — customers buy about once every 13 weeks"],
 ["b",       "How likely people are to keep buying",  "From the data — a third of customers bought only once"],
 ["\u03b3", "The size of a typical basket",          "From the data — average repeat spend is \u00a3385"],
 ["r",       "How much customers differ from one another", "No real-world units, so left vague — a small number near 1"],
 ["a",       "Works alongside b in the same calculation",  "No real-world units, so left vague — a small number near 1.5"],
 ["p, q",    "How lopsided spending is",              "No real-world units, so left vague — small numbers, 2 and 3"],
], top=In(2.42), row_h=In(0.44), size=11)
box(s, [("One setting for everything would not work: \u03b1 is counted in weeks, \u03b3 in hundreds of pounds. "
         "A guess wide enough for one is badly wrong for the other.", 14.5, False, INK),
        ("All six guesses are deliberately vague \u2014 each allows roughly ten times more or less than the "
         "value shown, so with 4,522 customers the data decides the answer, not the guess.", 14.5, True, NAVY)],
    In(6.2), In(0.95))

s = slide("How the model is estimated", kicker="Estimation",
 notes=(OPT + "~2 min, or skip and say one sentence: 'the answer cannot be computed directly, so it is "
        "approximated by drawing four thousand samples from it.'\n\n"
        "The full version: the quantity we want cannot be written down. The top of the calculation is "
        "easy — given any candidate setting, I can say how well it explains the data. The bottom "
        "requires adding that up over every possible setting at once, and there is no formula for it.\n\n"
        "A grid will not rescue it either: seven parameters at fifty values each is about a hundred "
        "billion evaluations.\n\n"
        "So instead of computing the answer, we sample from it — the same move as polling a thousand "
        "voters instead of asking the whole country. What comes back is a table of four thousand rows, "
        "each row a complete, self-consistent set of values for every parameter. Any question we then "
        "want to ask becomes counting rows rather than solving an integral."))
claim(s, "The quantity we want cannot be written down, so it is approximated by drawing samples from it "
         "— the same logic as polling rather than counting every voter.")
bullets(s, [
 ("What cannot be done", "Computing the answer exactly requires summing over every possible parameter setting at once. No formula exists, and a grid would need ~10¹¹ evaluations."),
 ("What is done instead", "Four chains draw 4,000 samples. Each sample is one complete, self-consistent set of values for every parameter."),
 ("Why that is enough", "Settings that explain the data well get sampled often, so any question becomes counting samples rather than solving an integral."),
], top=In(2.5), size=17)
box(s, [("“Chance this customer is worth more than £600”  =  how many of the 4,000 samples say yes  ÷  4,000",
         16, True, NAVY)], In(5.7), In(0.6))

s = slide("Did the estimation actually work?", kicker="Estimation",
 notes=("~90 s. This kind of simulation can fail quietly, so nothing downstream counts until three checks "
        "pass.\n\n"
        "The first compares the four independent runs against each other. If they explored the same thing "
        "they agree; 1.00 would be perfect and mine is 1.0014.\n\n"
        "The second accounts for the fact that consecutive samples resemble each other, so 4,000 samples "
        "are worth fewer than 4,000 independent ones. Mine are worth about 1,900 — roughly half, which is "
        "good for a problem like this.\n\n"
        "The third counts places where the simulation broke down. Zero.\n\n"
        "One thing I want to say without being asked: these establish that the computation worked. They "
        "say nothing about whether the model is a good description of reality. A poor model can compute "
        "perfectly. That is exactly why I show them here, before the results, rather than offering them "
        "as evidence for the results."))
claim(s, "Three standard checks, all passed. They establish that the computation is sound — not that the "
         "model is right.")
stat_row(s, [("1.0014","the four runs agree\n(1.00 is perfect)",TEAL),
             ("≈ 1,900","independent samples' worth\nof information, from 4,000",TEAL),
             ("0","places the simulation\nbroke down",TEAL)], top=In(2.45))
box(s, [("These say the computation worked. They do not say the model is correct.", 17, True, NAVY),
        ("A poorly specified model can pass all three. That is why they are shown before the findings "
         "rather than in support of them.", 15.5, False, INK)], In(4.35), In(1.15))

# ══════════════ ACT 3 · FINDINGS ══════════════
section("What I found", "Three hypotheses, and one result I was not looking for", notes="~10 s.")

s = slide("H1 — Does it put the right customers at the top?", kicker="Finding 1 of 3",
 notes=("~2 min. There are two ways to score a prediction and here they disagree, which is the "
        "interesting part.\n\n"
        "The first is average error — how far off is a typical prediction. On that, the improvement is "
        "real but modest, and I will not oversell it.\n\n"
        "The second asks a different question: of the hundred customers the model says are most "
        "valuable, how many genuinely are? Sixty-six, against forty-nine for the machine-learning model "
        "and thirty-seven for the industry heuristic — that is the right-hand panel. And targeting the "
        "top tenth the model selects reaches 62.6 per cent of the revenue that actually materialised.\n\n"
        "If a specialist asks for the formal ranking measure: NDCG at 100 is 0.91 against 0.53. Note "
        "that measure puts XGBoost and the heuristic level, because it weights the very top of the list "
        "most heavily — they identify the top few similarly well and differ across the rest of the "
        "hundred, which is what the panel shows.\n\n"
        "The second matters more because the budget only ever reaches the top of the list. Being slightly "
        "wrong about an average customer costs nothing; getting the top hundred wrong costs the campaign.\n\n"
        "One point I should make myself: the machine-learning model was trained on a slightly shorter "
        "window, for a technical reason about fairness. So it had less to learn from, and this gap should "
        "be read as a best case rather than an exact figure."))
claim(s, "Average error improves only modestly. The separation is in whether the right customers reach "
         "the top of the list — which is the part the budget actually reaches.")
picture(s, SLD+"accuracy.png", In(2.45), max_w=In(11.4), max_h=In(3.35))
box(s, [("Targeting the top tenth this model selects reaches 62.6% of the revenue that actually "
         "materialised — against 57.9% for the machine-learning model and 55.1% for the heuristic.",
         15, True, NAVY),
        ("The comparison model was trained on a shorter window for a technical reason about fairness, so "
         "read this gap as a best case rather than an exact figure.", 14.5, False, MUTE)], In(5.95), In(1.0))

s = slide("H1 — Is it honest about what it does not know?", kicker="Finding 1 of 3",
 notes=("~2 min. A different question from accuracy, and for what follows, the more important one.\n\n"
        "The model does not only give a number. It gives a range, and says how confident it is in that "
        "range. So the confidence itself can be tested: build a 90 per cent range for all 4,522 "
        "customers, then count how many real outcomes landed inside.\n\n"
        "If the answer were 60 per cent, the model would be overstating its certainty, and every decision "
        "built on it would inherit that. The answer is 89.3.\n\n"
        "I check four levels rather than one, because one level could come out right by luck. The pattern "
        "shows the ranges are slightly too wide in the middle and slightly too narrow at the extremes — "
        "which I would rather report than average away.\n\n"
        "And note this is a question you can only ask of a model that gives ranges at all. Neither "
        "comparison model does."))
claim(s, "When the model says it is 90% confident, it is right 89.3% of the time. That is what makes the "
         "ranges usable for planning rather than decoration.")
stat_row(s, [("89.3%","of outcomes fell inside\nthe stated 90% range",TEAL),
             ("4.59","average width of that\nrange (transactions)",NAVY),
             ("0.71","ability to identify who\nis still active",NAVY)], top=In(2.45))
bullets(s, [
 "Checked at four levels, not one: 64.4% at 50, 82.5% at 80, 89.3% at 90, 92.9% at 95",
 "Slightly too wide in the middle, slightly too narrow at the extremes — reported rather than averaged away",
 "Only a model that produces ranges can be tested this way; the comparison models produce single numbers",
], top=In(4.3), size=16.5)

s = slide("One customer, start to finish", kicker="Finding 1 of 3",
 notes=("~2 min. Let me make that concrete with one real customer, number 14817. Four repeat purchases, "
        "last seen 33 weeks in, average basket £526.\n\n"
        "Run them through all four thousand samples and average: £1,364, with a range of £1,326 to "
        "£1,401. That is tight — seventy-five pounds wide. It looks like the model has this person "
        "pinned down.\n\n"
        "It does not. That tight range answers 'how well do we know this customer's underlying habits?' "
        "— not 'what will they actually do?'. Ask the second question and the range runs from zero to "
        "£2,888, including a real chance of nothing at all, because they may already have stopped.\n\n"
        "What happened: they came back twice and spent £1,010. Inside the wide range, outside the narrow "
        "one. And the narrow range would have hidden that possibility entirely.\n\n"
        "One case cannot establish anything on its own — the 89.3 per cent across 4,522 customers does "
        "that. This is here to show what the two ranges mean."))
claim(s, "The same customer, the same model, two different questions — and the answers differ by an "
         "order of magnitude.")
picture(s, FIG+"worked_example_customer.png", In(2.45), max_w=In(8.8), max_h=In(3.4))
box(s, [("“How well do we know this customer?”  £1,326 – £1,401          "
         "“What will they actually do?”  £0 – £2,888", 15.5, True, NAVY),
        ("They returned twice and spent £1,010 — inside the second range, far outside the first.",
         15, False, INK)], In(6.0), In(1.0))

s = slide("The distinction that example reveals", kicker="Finding 2 of 3  ★",
 notes=("~2.5 min. This is the result I was not looking for, and the one I would defend hardest.\n\n"
        "There are two different things you can be uncertain about, and it is easy to confuse them. "
        "Think of a coin. You can become very sure a coin is fair — that is certainty about the rule. "
        "You will never be sure what the next flip gives — that is the outcome. Knowing the rule is not "
        "knowing the result.\n\n"
        "With thousands of customers, uncertainty about the rule shrinks almost to nothing. Uncertainty "
        "about what a person will actually do never shrinks, because people are unpredictable.\n\n"
        "If a targeting rule is built on the first kind, something bad happens silently. The model is so "
        "sure about the rule that any threshold falls clearly above or below it — so 96 per cent of "
        "customers get a probability of exactly zero or one. The ranking collapses into tie-breaking "
        "among thousands of identical scores, and nothing warns you.\n\n"
        "The cost in the simulation: success rate falls from 85 to 62 per cent, and wasted spend nearly "
        "triples. Ninety thousand pounds, from a conceptual mix-up that produces perfectly working code.\n\n"
        "So I propose a one-line check anyone can run: look at the probabilities. If most of them are "
        "zero or one, the wrong one was used."))
claim(s, "Being certain about the rule is not the same as being certain about the outcome — and a "
         "decision rule built on the wrong one fails without any warning.")
picture(s, FIG+"prob_expectation_vs_predictive.png", In(2.45), max_w=In(9.8), max_h=In(2.85))
box(s, [("Success rate 85% → 62%        Wasted spend £55,040 → £144,738        "
         "96% of customers scored exactly 0 or 1", 15.5, True, NAVY),
        ("The check: look at your probabilities. If most sit at 0 or 1, the wrong kind of uncertainty was "
         "used. This applies to any model that produces ranges.", 14.5, True, BRAND)], In(5.65), In(1.05))

s = slide("H2 — Can a small market borrow from a large one?", kicker="Finding 3 of 3",
 notes=("~2 min. The UK has 4,152 customers here. Germany has 74. France has 54.\n\n"
        "Three options. Fit France on its own and you are betting everything on 54 people — you will "
        "mistake their quirks for facts. Merge all countries and France loses whatever makes it "
        "different. Or the middle route: each country keeps its own numbers, but those numbers come from "
        "a shared pool, so small markets lean on the others.\n\n"
        "The middle route gives the lowest error on the small markets — but by half a per cent, and I am "
        "not going to pretend that is decisive.\n\n"
        "What I will defend is different: the middle route is never the worst option in any market, "
        "whereas each of the other two fails badly somewhere. You are buying insurance against choosing "
        "wrong, not a large gain in accuracy. Hence partially supported.\n\n"
        "And one qualification I should give myself: I deliberately constrained how different countries "
        "were allowed to be, which works against finding a benefit. So this is a conservative test."))
claim(s, "Each market keeps its own estimates, but small markets lean on the larger ones in proportion "
         "to how little data they have.")
picture(s, SLD+"h2_pooling.png", In(2.45), max_w=In(10.4), max_h=In(3.15))
box(s, [("4,152 UK customers · 74 German · 54 French.        Error on the small markets: 1.746 shared vs 1.755 separate vs 1.757 merged",
         15, True, NAVY),
        ("Never the worst in any market, whereas both alternatives fail badly somewhere. Robustness rather "
         "than accuracy — and tested conservatively.", 14.5, False, MUTE)], In(5.9), In(1.0))

s = slide("H2 — Why borrowing works", kicker="Finding 3 of 3",
 notes=(OPT + "~90 s. Skip if short — the previous slide carries the finding.\n\n"
        "The mechanism is classical and not mine; it goes back to the 1970s.\n\n"
        "Think about judging a footballer. If you have seen three games you should not trust your "
        "impression much — you would sensibly lean it toward what a typical player does. If you have seen "
        "three hundred, you trust what you saw.\n\n"
        "The model does exactly that, automatically. The UK barely moves, because its own data "
        "overwhelms everything else. France is pulled strongly toward the overall average. Nobody tunes "
        "this — it falls out of the structure.\n\n"
        "And the underlying theory promises an improvement overall, not a win in every single market. So "
        "the modest result is exactly what it predicts."))
claim(s, "Estimates are pulled toward the overall average in proportion to how little evidence each "
         "market has — the same instinct as not judging a player on three games.")
picture(s, FIG+"hierarchical_shrinkage_r.png", In(2.5), max_w=In(7.8), max_h=In(3.4))
box(s, [("The UK (4,152 customers) is barely moved. France (54) is pulled hard. Nobody tunes this — it "
         "follows from the structure.", 15.5, False, INK),
        ("The underlying theory promises improvement overall, not in every market — so a modest result is "
         "what it predicts.", 15, True, NAVY)], In(6.0), In(1.0))

s = slide("H3 — Does the extra information change who we target?", kicker="Finding 3 of 3",
 notes=("~2 min. This is the question I most wanted to answer yes, and it came back no. I think it is "
        "the most useful of the three results, so let me explain rather than apologise.\n\n"
        "The setting is a real marketing decision: a budget, a cost per customer contacted, and a choice "
        "of who to target. There are two ways to choose.\n\n"
        "The simple way: rank everyone by what we expect them to be worth, and take the top slice.\n\n"
        "The sophisticated way: for each customer work out the chance they clear a value threshold, and "
        "pick the highest chances. This uses the whole range rather than just its middle, and it is "
        "supposed to account for risk. That is what H3 proposed.\n\n"
        "The two performed the same. The simple way picked correctly 85 per cent of the time; the "
        "sophisticated way 83. And I tested that across 35 different combinations of contact cost and "
        "campaign size, so it is not one unlucky setting — the sophisticated rule was never meaningfully "
        "ahead anywhere.\n\n"
        "Now the reason, and it is a clean one. Profit here is simply value minus cost. That is a "
        "straight line. And when the thing you care about is a straight line, only the average matters — "
        "the spread genuinely contains nothing extra for that decision. So the sophisticated rule could "
        "not have won. It is not that it was badly implemented; there was nothing for it to use.\n\n"
        "So the message is practical rather than defeatist. For a straightforward targeting decision, "
        "the average is enough and you can stop there. Save the extra effort for decisions where profit "
        "is not a straight line — a hard budget cap, a penalty for overspending, or a case where you "
        "genuinely care about the worst outcome rather than the average one.\n\n"
        "If asked for exact figures: 0.848 against 0.827 hit rate, £55,039 against £60,451 wasted, at "
        "£600 per contact targeting the top 20 per cent. Across the 35 combinations the probability "
        "rule's best was plus one per cent and its worst minus thirty-four."))
claim(s, "We tried using the full range to choose customers. It did no better than simply using the "
         "average — and there is a clear reason why it could not.")
bullets(s, [
 ("The simple way", "Rank everyone by what we expect them to be worth, and contact the top slice."),
 ("The sophisticated way", "For each customer, work out the chance they are worth more than a set amount, and contact the highest chances. This uses the whole range, not just its middle."),
], top=In(2.4), size=17)
table(s, ["How we chose who to contact", "How often we chose right", "Money wasted"], [
 ["By expected value — the simple way",    "85%", "£55,000"],
 ["By chance of clearing the bar",         "83%", "£60,000"],
], top=In(4.05), row_h=In(0.46), size=12)
box(s, [("Why it could not win: profit here is just value minus cost — a straight line. "
         "When that is true, only the average matters, and the rest of the range has nothing to add.",
         15, True, NAVY),
        ("Tested across 35 combinations of contact cost and campaign size. The sophisticated rule was "
         "never meaningfully ahead in any of them.", 14.5, False, MUTE)], In(5.65), In(1.05))

s = slide("Why the machine-learning model trails", kicker="Finding 1 of 3",
 notes=(OPT + "~90 s. Skip unless asked — the headline comparison is already on the H1 slide.\n\n"
        "The comparison model is a strong, modern, widely used method with 24 engineered inputs and "
        "tuned settings. It is not a straw man, and I would rather explain its result than celebrate it.\n\n"
        "Look at what it spends its effort learning: how recently someone bought, how often, and how much "
        "that varies. Those are exactly the things my model is told at the start.\n\n"
        "So it is using 4,522 examples to rediscover a structure I simply wrote down — and a third of "
        "those examples are people with a single purchase, so there is very little to learn from.\n\n"
        "The honest summary is that raw power does not help when the shortage is information rather than "
        "capacity. With ten times the customers I would expect this to reverse, and published work "
        "reports exactly that."))
claim(s, "It spends its capacity rediscovering structure the other model is simply told — a shortage of "
         "information, not of power.")
picture(s, FIG+"xgboost_feature_importance.png", In(2.45), max_w=In(8.6), max_h=In(3.45))
box(s, [("24 engineered inputs, two-stage design, tuned. Its effort concentrates on recency, frequency and "
         "variability — all of which the generative model assumes for free.", 15, False, INK),
        ("With ten times the customers I would expect this ordering to reverse.", 15, True, NAVY)],
    In(6.05), In(1.0))

# ══════════════ ACT 4 · WHAT IT MEANS ══════════════
section("What it means", "Against the alternatives, for the business, and what is still open", notes="~10 s.")

s = slide("How it compares against the alternatives", kicker="Impact",
 notes=("~2 min. Putting all four approaches side by side on the same held-out period.\n\n"
        "The naive baseline predicts the average for everyone — it is there to show what no model looks "
        "like. The heuristic is what the industry actually uses. The machine-learning model is the "
        "serious modern comparison.\n\n"
        "Read across the ranking columns rather than the error column. On getting the top hundred right, "
        "the gap is 66 against 49 and 37. On revenue reached, 62.6 against 57.9 and 55.1.\n\n"
        "And the last column is the one neither alternative can even fill in: whether the stated "
        "confidence holds up. A single-number model has no confidence to test.\n\n"
        "That is the summary of H1 — competitive on accuracy, clearly better on ranking, and uniquely "
        "able to say how sure it is."))
claim(s, "Competitive on average error, clearly ahead on ranking, and the only approach that can state "
         "how confident it is at all.")
table(s, ["Approach", "Average error", "Top 100 correct", "Revenue reached", "Honest confidence?"], [
 ["Bayesian model (this thesis)", "1.74", "66 of 100", "62.6%", "Yes — 89.3% at 90%"],
 ["Machine learning (XGBoost)",   "2.12", "49 of 100", "57.9%", "No range produced"],
 ["Industry heuristic (RFM)",     "2.33", "37 of 100", "55.1%", "No range produced"],
 ["Naive baseline",               "3.11", "1 of 100",  "8.1%",  "No range produced"],
], top=In(2.5), row_h=In(0.5), size=11.5)
box(s, [("Ranking is the column that matters: the budget only ever reaches the top of the list.",
         15.5, True, NAVY)], In(5.8), In(0.58))

s = slide("What this changes in practice", kicker="Impact",
 notes=("~2 min. Back to the decision I opened with — what does a business actually do differently?\n\n"
        "First, better ranking is directly budget efficiency. The same spend reaches more of the value. "
        "Sixty-six correct in the top hundred against thirty-seven is not a statistical nicety; it is "
        "most of a campaign.\n\n"
        "Second, honest ranges make risk-based planning possible. You can commit budget against a worst "
        "case rather than a point estimate, because the ranges can be trusted.\n\n"
        "Third, the model separates 'quiet' from 'gone', which a cut-off rule cannot. That changes who "
        "gets a win-back campaign and who is simply left alone.\n\n"
        "And fourth, the finding I did not expect: check which kind of uncertainty your probabilities "
        "came from. That one is nearly free to act on and, in this simulation, worth ninety thousand "
        "pounds."))
claim(s, "Four things change for a business that adopts this, in order of how much they are worth.")
bullets(s, [
 ("Better ranking is budget efficiency", "The same spend reaches more of the value — 66 correct in the top 100 against 37 is most of a campaign."),
 ("Honest ranges make risk-based planning possible", "Budget can be committed against a worst case, not just a point estimate, because the ranges hold up."),
 ("“Quiet” is separated from “gone”", "Which decides who receives a win-back campaign and who is better left alone — a cut-off rule cannot do this."),
 ("Check which uncertainty your probabilities came from", "Nearly free to act on, and worth about £90,000 in this simulation."),
], top=In(2.45), size=16, gap=6)

s = slide("Limitations", kicker="Honest assessment",
 notes=("~2 min. I state which direction each problem pushes the answer, because a limitation without a "
        "direction does not tell you whether the number can be used.\n\n"
        "The model assumes people do not change over time. They do. This over-predicts middle-of-the-road "
        "customers by 20 to 30 per cent — but the top customers, where the budget goes, stay accurate.\n\n"
        "It assumes how often you buy and how much you spend are unrelated. They are mildly related. "
        "Because the relation is positive, it under-predicts the heaviest buyers — which partly cancels "
        "the first problem rather than adding to it.\n\n"
        "One retailer, one country, two years — so the exact figures are specific, though the reasoning "
        "about uncertainty is general.\n\n"
        "And the one I like because it is so concrete: the busiest customer made 200 repeat purchases in "
        "65 weeks. That is not a person buying gifts, that is a business restocking. A wholesale buyer "
        "inside a consumer model breaks the assumptions, and I flag it rather than quietly deleting the "
        "row."))
claim(s, "Each stated with the direction it pushes the answer — and the two largest push in opposite "
         "directions rather than compounding.")
bullets(s, [
 ("It assumes people do not change over time — they do",
  "Over-predicts mid-range customers by 20–30%. The top customers, where budget is spent, remain accurate."),
 ("It assumes how often and how much are unrelated — they are mildly related",
  "Positive, so the heaviest buyers are under-predicted — partly cancelling the problem above."),
 ("One retailer, one country, two years",
  "The exact figures are specific to this business; the reasoning about uncertainty is general."),
 ("Wholesale buyers sit inside a consumer model",
  "The busiest customer made 200 repeat purchases in 65 weeks — restocking, not gift-buying. Flagged, not deleted."),
], top=In(2.4), size=15.5, gap=5)

s = slide("Summary", kicker="Conclusion",
 notes=("~90 s. Three verdicts, and a pattern across them I did not design for.\n\n"
        "H1 supported: better ranking, and confidence you can trust.\n"
        "H2 partially supported: small markets do borrow usefully, but the gain is modest and what you "
        "really buy is robustness.\n"
        "H3 not supported: for a straight-line decision the average is already enough.\n\n"
        "Put them side by side and the pattern is this. The three questions ask for progressively more "
        "from the model's output — its middle, its structure across groups, and its extremes. And the "
        "value falls off exactly where theory says it should.\n\n"
        "If I had to defend one sentence: the extra information is worth precisely as much as the "
        "question actually uses — and knowing which kind of uncertainty you are holding is worth ninety "
        "thousand pounds."))
claim(s, "Three verdicts, and a pattern across them that was not designed for.")
bullets(s, [
 ("H1 — supported", "Better ranking where the budget is spent, and stated confidence that holds up at 89.3% against 90%."),
 ("H2 — partially supported", "Small markets borrow usefully, but the gain is modest; what is bought is robustness rather than accuracy."),
 ("H3 — not supported", "For a straight-line decision the average is already sufficient — and there is a clean reason why."),
], top=In(2.45), size=17)
box(s, [("The three questions ask for progressively more of the model's output — its middle, its structure, "
         "its extremes — and the value falls away exactly where theory says it should.", 15.5, True, NAVY)],
    In(5.5), In(0.75))

s = slide("Future work", kicker="Conclusion",
 notes=("~90 s, then stop and invite questions.\n\n"
        "Three directions. Group customers by how they behave rather than where they live — a wholesaler "
        "in London probably resembles a wholesaler in Paris far more than a gift-buyer down the road, so "
        "country is a weak proxy.\n\n"
        "Build a decision where profit is not a straight line — a hard budget cap, or genuine risk "
        "aversion. That is the proper test my third question could not be.\n\n"
        "And let customers change over time, since that is the assumption I can most clearly show is "
        "broken.\n\n"
        "To close: this started with a shop that cannot see who has left. It ends with a model that does "
        "not pretend to either — it is honest about the uncertainty, and clear about when that honesty is "
        "worth paying for. Thank you."))
claim(s, "Three directions, in order of expected return.")
bullets(s, [
 ("Group customers by behaviour rather than geography",
  "A wholesaler in London resembles one in Paris more than a nearby gift-buyer. Country is a weak proxy for what actually clusters."),
 ("Build a decision where profit is not a straight line",
  "A hard budget cap, a penalty for overspending, or explicit risk aversion — the proper test H3 could not be."),
 ("Allow customers to change over time",
  "The assumption most clearly shown to be violated, and the one most likely to matter in deployment."),
], top=In(2.45), size=16.5)
box(s, [("This began with a shop that cannot see who has left.", 16, True, NAVY),
        ("It ends with a model that does not pretend to either — and is clear about when that honesty is "
         "worth paying for.", 16, False, INK)], In(5.45), In(1.0))
