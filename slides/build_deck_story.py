"""Defence deck, story-led rewrite. Same layout engine, new narrative.
Technical terms are kept but each is glossed on the slide in plain words."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_engine.py")).read())

def term(s, word, gloss, top=In(6.05)):
    """A glossed technical term — keeps the word, defuses it in one line."""
    rect(s, In(0.85), top, In(11.6), In(0.62), SOFT)
    rect(s, In(0.85), top, Pt(4), In(0.62), TEAL)
    t = tb(s, In(1.08), top + In(0.10), In(11.2), In(0.45), anchor=MSO_ANCHOR.MIDDLE)
    p = t.paragraphs[0]; p.space_after = Pt(0)
    r = p.add_run(); r.text = word + "  "
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(15), True, TEAL, FONT
    r2 = p.add_run(); r2.text = gloss
    r2.font.size, r2.font.bold, r2.font.color.rgb, r2.font.name = Pt(15), False, INK, FONT

def stat_row(s, items, top=In(2.1), h=In(1.35)):
    n = len(items); gap = In(0.25)
    w = Emu(int((In(11.6) - gap*(n-1)) / n))
    for i,(k,v,c) in enumerate(items):
        l = In(0.85) + Emu(int(i*(w+gap)))
        rect(s, l, top, w, h, SOFT); rect(s, l, top, w, Pt(3.5), c)
        t = tb(s, l+In(0.18), top+In(0.22), w-In(0.36), h-In(0.3))
        put(t, k, 26, True, c, 2, first=True)
        for ln in v.split("\n"): put(t, ln, 12, False, MUTE, 0)

# ════════════════════════════ 1  TITLE
s = prs.slides.add_slide(BLANK); _n["i"] += 1
rect(s, 0, 0, W, In(0.22), NAVY); rect(s, 0, In(0.30), W, Pt(2), ORANGE)
t = tb(s, In(1.0), In(1.70), In(11.3), In(2.1))
put(t, "What is a customer worth", 42, True, NAVY, 4, first=True)
put(t, "when they never say goodbye?", 42, True, NAVY, 14)
put(t, "Customer Lifetime Value Prediction Using Bayesian Methods", 17, False, MUTE, 0, italic=True)
rect(s, In(1.0), In(4.30), In(2.0), Pt(3), ORANGE)
t = tb(s, In(1.0), In(4.60), In(11.0), In(1.6))
put(t, "Devansh", 20, True, INK, 8, first=True)
put(t, "Master's Thesis  ·  M.Sc.", 14.5, False, MUTE, 4)
put(t, "First Supervisor: Professor Dr. Tilo Wendler    ·    Second Supervisor: Dr. Guido Möser",
    13.5, False, MUTE, 0)
rect(s, 0, In(7.28), W, In(0.22), NAVY)
s.notes_slide.notes_text_frame.text = (
 "~40 s. Good morning. I want to start with a shop, not a model. Everything in this thesis comes out "
 "of one decision a real business has to make every week, and the fact that the information it needs "
 "to make it does not exist. 25 minutes: the problem, what I built, what I found, and what I got wrong.")

# ════════════════════════════ 2  THE SHOP
s = slide("A shop, and a decision it makes every week", kicker="The setting",
 notes=("~1.5 min. A UK giftware retailer, two years of real transactions — the Online Retail II "
        "dataset. After cleaning, 4,522 customers. Every week this business has a marketing budget "
        "and has to choose who to spend it on. Spend on someone who was coming back anyway and you "
        "wasted it; miss someone valuable and you lose them. To choose well you need to know what "
        "each customer is WORTH IN FUTURE — not what they have spent. That is customer lifetime "
        "value, and it is a forecast, not a receipt."))
stat_row(s, [("4,522","customers\nafter cleaning",NAVY),
             ("2 years","of real transactions\n2009–2011",NAVY),
             ("£385","mean basket\n(median £299)",NAVY),
             ("33%","bought once\nand never returned",ORANGE)])
bullets(s, [
 "The business question is not “what have they spent?” but “what will they spend?”",
 "Acquisition costs money up front; it only pays back if the customer returns",
 "So every week, someone must rank customers by a number nobody can observe",
], top=In(3.85), size=18)
term(s, "Customer lifetime value", "the profit a customer is expected to bring in future — a forecast, not a total.")

# ════════════════════════════ 3  TWO CUSTOMERS
s = slide("Two customers, one identical receipt", kicker="The intuition",
 notes=("~1 min. Here is the whole problem in one picture. Two people spend ten pounds today. On the "
        "till they are indistinguishable. One lives nearby and will come back monthly for three years; "
        "the other was passing through. They spent the same today. They are not worth the same "
        "tomorrow. Any method that scores customers on what they have already spent cannot tell these "
        "two apart — and that is most of what businesses actually do."))
bullets(s, [
 ("Customer A  ·  spends £10 today", "Comes back every month for three years. Worth several hundred pounds."),
 ("Customer B  ·  spends £10 today", "Never returns. Worth £10, and the cost of acquiring them."),
], top=In(2.05), size=20)
bullets(s, [
 "Identical in the transaction record. Opposite in value.",
 "Ranking by past spend — what RFM scoring does — scores them the same",
], top=In(4.35), size=18)
takeaway(s, "The past is a receipt. Lifetime value is a forecast. The two are not the same number.")

# ════════════════════════════ 4  NOBODY SAYS GOODBYE
s = slide("The information you need does not exist", kicker="Why this is hard",
 notes=("~2 min. This is the hinge of the thesis, so let me be careful. In a contract business — a gym, "
        "a phone plan — the customer cancels. There is a date. You can count who left and when. A shop "
        "has no cancel button. People simply stop coming, and they never announce it.\n\n"
        "So take a customer silent for fifteen weeks. Have they gone? You cannot answer. If they "
        "normally buy every three weeks, fifteen weeks is alarming. If they buy twice a year, fifteen "
        "weeks is a Tuesday. The SAME silence means opposite things depending on whose silence it is.\n\n"
        "Whether a customer is still active is therefore LATENT — hidden in principle, not just "
        "unmeasured. Nobody knows it, including the customer. That is what rules out the obvious "
        "approaches."))
bullets(s, [
 ("Contractual  ·  the easy case", "Gym, phone plan, subscription. The customer cancels, so churn has a date."),
 ("Non-contractual  ·  this case", "A shop. No cancellation. Customers simply fade out, silently."),
], top=In(2.0), size=19)
rect(s, In(0.85), In(4.05), In(11.6), In(1.55), SOFT)
rect(s, In(0.85), In(4.05), Pt(4), In(1.55), ORANGE)
t = tb(s, In(1.10), In(4.20), In(11.1), In(1.3))
put(t, "Two customers, both silent for 15 weeks", 16, True, NAVY, 6, first=True)
put(t, "One normally buys every 3 weeks — the silence is alarming.    "
       "One buys twice a year — the silence is completely normal.", 15, False, INK, 4)
put(t, "Same silence. Opposite meaning. It only means anything relative to that person's own rhythm.",
    15, True, ORANGE, 0)
term(s, "Latent", "hidden in principle — not merely unrecorded. It has to be inferred, never looked up.")

# ════════════════════════════ 5  THE GAP
s = slide("Three things the field has not settled", kicker="Research gap",
 notes=("~1.5 min. Keeping the literature short. Probabilistic CLV models have existed since 2005 and "
        "they work. Three things are still open, and each became one of my research questions.\n\n"
        "First: these models produce uncertainty, but almost nobody checks whether that uncertainty is "
        "HONEST. The applied tradition validates predicted against actual counts and stops there.\n\n"
        "Second: customers are usually pooled into one population or split into separate groups. The "
        "middle option — letting groups share strength — is rarely tested on this problem.\n\n"
        "Third, and this is the one I care most about: nobody checks whether all this uncertainty "
        "actually changes a decision. That is, after all, the point of computing it."))
bullets(s, [
 ("1 · Uncertainty is produced, but rarely shown to be trustworthy",
  "Models report intervals. Almost no one checks whether a 90% interval contains the truth 90% of the time."),
 ("2 · Groups are either merged or separated, never partially shared",
  "A model per country overfits small countries; one global model erases them. The middle is under-tested."),
 ("3 · Uncertainty is computed, but not shown to change any decision",
  "If carrying the full distribution never alters an action, the extra machinery is not earning its cost."),
], top=In(2.0), size=17)
takeaway(s, "Each gap becomes one research question — and one deliberate piece of the empirical design.")

# ════════════════════════════ 6  THE QUESTIONS
s = slide("What I asked", kicker="Aims and hypotheses",
 notes=("~1.5 min. Three questions, and they escalate in how much of the model's output they actually "
        "use. RQ1 asks whether the Bayesian model predicts well and whether its uncertainty is honest. "
        "RQ2 asks whether sharing information across countries helps the small ones. RQ3 asks whether "
        "that uncertainty changes who you would target.\n\n"
        "I will tell you the answers now so you can follow the argument rather than wait for a reveal: "
        "yes, partly, and no. The 'no' is the most interesting of the three and I will explain why it "
        "had to be no."))
bullets(s, [
 ("RQ1 — Does it predict better, and is it honest about what it doesn't know?",
  "Against a naive baseline, an RFM heuristic, and a tuned XGBoost model. H1."),
 ("RQ2 — Does letting countries share information help the small ones?",
  "UK has 4,152 customers. France has 54. Can France borrow strength? H2."),
 ("RQ3 — Does carrying the full uncertainty change who you target?",
  "A marketing-spend simulation with real cost assumptions. H3."),
], top=In(2.0), size=17.5)
takeaway(s, "Answers, up front: H1 supported · H2 partially supported · H3 not supported — and the last is the interesting one.")

# ════════════════════════════ 7  SECTION
section("How I went about it", "A story about behaviour, and a way to compute with it",
 notes="~10 s. Now the method — in three steps: write down a story, discover you cannot solve it, roll a marble.")

# ════════════════════════════ 8  A STORY NOT A CURVE
s = slide("Write down a story, rather than fit a curve", kicker="Methodology · the idea",
 notes=("~2 min. This is the part I would most like to land, because it is genuinely different from "
        "standard machine learning.\n\n"
        "The usual approach throws features at an algorithm and lets it find patterns. I do the "
        "opposite. I write down a story about how customers behave — in probability — and then ask "
        "which version of that story best matches the data. The model is a claim about human "
        "behaviour, not a curve fitted to columns.\n\n"
        "That matters here for a specific reason: the thing I need to know is unobservable. A learner "
        "cannot be trained on 'has this customer churned' because that label does not exist for anyone. "
        "But a story can contain an invisible step, and the data can still tell you how likely it was."))
bullets(s, [
 ("Machine learning", "Here are 24 features. Find the pattern that predicts the target."),
 ("Generative model", "Here is how I believe purchases happen. Which version of that fits the data?"),
], top=In(2.0), size=19)
bullets(s, [
 "Because the key quantity — is this customer still active? — is never observed, there is no label to learn from",
 "A story can contain an invisible step; a classifier cannot be trained on one",
 "The reward is interpretability: every parameter means something a manager can argue with",
], top=In(4.15), size=17)
term(s, "Generative model", "a model that states how the data came about, instead of mapping inputs to an output.")

# ════════════════════════════ 9  FOUR BEHAVIOURS
s = slide("The story, in four behaviours", kicker="Methodology · the model",
 notes=("~2.5 min. The story has four parts.\n\n"
        "One: while a customer is active, they buy at random but at their own pace. Like rainfall — you "
        "cannot predict Tuesday, but you can say it rains twice a week here.\n\n"
        "Two: after each purchase they privately decide whether to stop forever. A coin flip, with their "
        "own bias.\n\n"
        "Three, and this is the one doing the real work: everybody is different, and that difference is "
        "modelled explicitly. In my data the average customer makes 3.78 repeat purchases, but the "
        "variance is 77.7 — more than twenty times the mean. If everyone shared one rate those would be "
        "roughly equal. That gap is hard evidence that customers genuinely differ.\n\n"
        "Four: basket size, which is heavily skewed — mean £385 against a median of £299.\n\n"
        "These combine into the BG/NBD and Gamma-Gamma models. Value equals how often, times how much."))
bullets(s, [
 ("1 · A pace", "While active, purchases arrive at random at that customer's own rate (Poisson)."),
 ("2 · A coin", "After each purchase, a private decision to stop for good (Beta-Geometric)."),
 ("3 · Everyone differs", "Rates and quit-chances vary across people, drawn from a population spread (Gamma, Beta)."),
 ("4 · A basket size", "Spend per visit, heavily right-skewed — a few enormous orders (Gamma-Gamma)."),
], top=In(1.95), size=16.5, gap=7)
rect(s, In(0.85), In(5.55), In(11.6), In(0.52), SOFT)
rect(s, In(0.85), In(5.55), Pt(4), In(0.52), ORANGE)
t = tb(s, In(1.08), In(5.62), In(11.2), In(0.4), anchor=MSO_ANCHOR.MIDDLE)
put(t, "Evidence for part 3: mean repeat purchases 3.78, variance 77.7 — over 20× the mean. "
       "One shared rate would make them equal.", 14.5, True, NAVY, 0, first=True)
term(s, "Over-dispersion", "more spread in the data than a single-rate model can produce. The proof that customers differ.", top=In(6.28))

# ════════════════════════════ 10  THE EQUATION
s = slide("The equation nobody can solve", kicker="Methodology · why Bayesian is expensive",
 notes=("~2 min. Writing the story down is the easy half. Now I have to work out which version of it "
        "the data supports, and that runs into a wall.\n\n"
        "Bayes' rule says the answer is the likelihood times the prior, divided by a normalising "
        "constant. The top I can compute in milliseconds for any candidate. The bottom requires "
        "integrating over every possible combination of the parameters at once, and for this model no "
        "closed form exists.\n\n"
        "So I am in a strange position: I know the SHAPE of the answer everywhere but not its SCALE. I "
        "can say one setting is forty times more plausible than another but cannot say what either "
        "probability is.\n\n"
        "A grid will not save me. Seven parameters at fifty slices each is ten to the eleven likelihood "
        "evaluations — years of compute. The escape is that I never need the constant: sampling only "
        "ever uses ratios, and the constant cancels."))
bullets(s, [
 ("The top — likelihood × prior", "Computable for any candidate setting in milliseconds."),
 ("The bottom — the normalising constant", "An integral over the whole parameter space. No closed form exists."),
], top=In(2.0), size=19)
bullets(s, [
 "A grid is hopeless: 7 parameters × 50 slices each ≈ 10¹¹ evaluations — years of compute",
 "But every method I use compares two settings — and in a ratio, the unknown constant cancels",
 "So: stop trying to compute the distribution. Draw from it instead.",
], top=In(4.2), size=17)
term(s, "Posterior", "the updated belief about the parameters after seeing the data — a distribution, not a number.")

# ════════════════════════════ 11  FOUR THOUSAND WORLDS
s = slide("Four thousand versions of the world", kicker="Methodology · what sampling returns",
 notes=("~2 min. This is the concept I would most like you to take away, because everything in the "
        "results depends on it.\n\n"
        "The sampler does not return a formula. It returns a list — four thousand rows. Each row holds "
        "a complete set of values for every parameter at once. One row is one DRAW, and it is one "
        "entire, self-consistent theory of how all 4,522 customers behave. Row two is a different "
        "complete theory. Both are compatible with what I observed.\n\n"
        "The familiar numbers — r equals 0.65 — are not draws. They are averages of a column.\n\n"
        "And the payoff: settings that explain the data well get visited often, so they fill many rows. "
        "So I never need that impossible integral. I count rows. The probability a customer is worth "
        "over six hundred pounds is just: how many rows say yes, divided by four thousand."))
bullets(s, [
 ("One draw = one complete theory of the customer base",
  "r = 0.6303, α = 6.5749, a = 0.2171, b = 4.0104 — a whole self-consistent world, not an error bar."),
 ("Four chains × 1,000 draws = 4,000 worlds",
  "Each one could have produced the data I actually observed."),
 ("Frequency becomes probability",
  "Plausible settings get visited often. So any question becomes counting rows, not solving an integral."),
], top=In(2.0), size=17)
rect(s, In(0.85), In(5.5), In(11.6), In(0.55), SOFT)
rect(s, In(0.85), In(5.5), Pt(4), In(0.55), TEAL)
t = tb(s, In(1.08), In(5.58), In(11.2), In(0.42), anchor=MSO_ANCHOR.MIDDLE)
put(t, "P(customer worth > £600)  =  how many of the 4,000 rows say yes  ÷  4,000", 15.5, True, NAVY, 0, first=True)
term(s, "Draw", "one complete set of parameter values. Used whole — the parameters are correlated.", top=In(6.25))

# ════════════════════════════ 12  DIAGNOSTICS
s = slide("Did the machinery actually work?", kicker="Methodology · trust before results",
 notes=("~1 min. Sampling can fail quietly, so nothing downstream counts until three checks pass. "
        "R-hat compares the four chains against each other — near 1.00 means they agree about the "
        "terrain. Effective sample size discounts for consecutive draws being correlated. Divergences "
        "flag places the simulation broke down; you want zero.\n\n"
        "All three pass. But I want to be explicit, because an examiner will ask: these are NECESSARY, "
        "not sufficient. They say the sampler worked. They say nothing about whether the model is right. "
        "A badly misspecified model can converge beautifully. That is exactly why I report them before "
        "any result rather than as evidence for one."))
stat_row(s, [("1.0014","R̂ — the four chains\nagree (want < 1.01)",TEAL),
             ("~2,000","effective draws\nout of 4,000",TEAL),
             ("0","divergences —\nnothing broke",TEAL)], top=In(2.15))
bullets(s, [
 "Four independent chains, started apart, each adapting its own step size during warm-up",
 "They agree on the answer to four decimal places — strong evidence the whole posterior was explored",
], top=In(4.0), size=17.5)
takeaway(s, "Necessary, not sufficient. These say the sampler worked — not that the model is right.")

# ════════════════════════════ 13  SECTION
section("What I found", "Three questions, three different kinds of answer",
 notes="~10 s. Now the findings. One supported, one partly, one rejected — and a fourth I did not go looking for.")

# ════════════════════════════ 14  H1a RANKING
s = slide("Can it rank the customers who matter?", kicker="Finding 1a · accuracy and ranking",
 notes=("~2 min. On raw error the Bayesian model wins, but modestly — and I will not oversell it. The "
        "decisive panel is on the right: NDCG at 100, which asks whether the TOP of the ranking is "
        "right. 0.91 against 0.53 for XGBoost.\n\n"
        "Why does ranking matter more than error? Because customer value is severely concentrated and "
        "marketing budgets reach the top decile, not the average customer. Being slightly wrong about a "
        "typical customer costs nothing. Getting the top 100 wrong costs the whole campaign.\n\n"
        "The mechanism is borrowing strength: the generative model shrinks sparse customers toward the "
        "population instead of judging them on two purchases.\n\n"
        "One honest caveat, which I put in writing: XGBoost trained on a shorter inner split to avoid "
        "leakage, so it had less data. Read that gap as an upper bound on my advantage."))
picture(s, SLD+"accuracy.png", In(1.95), max_w=In(11.4), max_h=In(3.9))
takeaway(s, "Budgets are spent on the top of the ranking — and the gap is an upper bound, not a point estimate.")

# ════════════════════════════ 15  H1b CALIBRATION
s = slide("Is it honest about what it doesn't know?", kicker="Finding 1b · calibration",
 notes=("~1.5 min. This is a different question from accuracy and, I would argue, a more important one.\n\n"
        "If I state a 90% interval for every customer, how many real outcomes actually fall inside? If "
        "the answer is 60%, the model is bluffing and every decision built on it inherits that "
        "overconfidence. The answer here is 89.3% against a nominal 90%.\n\n"
        "Coverage alone is gameable — an interval from zero to infinity covers everything — so I report "
        "it alongside CRPS, which penalises width too.\n\n"
        "The business translation: you can take these intervals at face value, which is what makes them "
        "usable for budgeting rather than decoration. And note this is a question you can only ASK of a "
        "model that makes distributional claims. Neither RFM nor standard XGBoost makes any."))
stat_row(s, [("89.3%","empirical coverage\n(nominal 90%)",TEAL),
             ("1.22","CRPS — accuracy and\ncalibration together",NAVY),
             ("0.71","P(alive) AUC — the hidden\nstate is recoverable",NAVY)], top=In(2.1))
bullets(s, [
 "A 90% interval that contains the truth 89.3% of the time can be trusted as stated",
 "Coverage alone is gameable, so it is reported with sharpness and a proper scoring rule",
 "Only a model making distributional claims can be tested this way — the baselines cannot be",
], top=In(3.95), size=17)
term(s, "Calibration", "whether the stated confidence matches reality. Separate from, and often more useful than, accuracy.")

# ════════════════════════════ 16  WORKED EXAMPLE
s = slide("One customer, end to end", kicker="Finding 1c · customer 14817",
 notes=("~2 min. Let me make this concrete with one real customer, number 14817. Four repeat purchases, "
        "last seen 33 weeks in, average basket £526.\n\n"
        "Run them through all 4,000 worlds and average: expected value £1,364, with a 90% interval of "
        "£1,326 to £1,401. That is tight. Seventy-five pounds wide. It looks like I have this customer "
        "nailed down.\n\n"
        "I did not. That interval answers 'how well do I know the underlying rate?' — not 'what will "
        "this person actually do?' Ask the second question and the interval runs from zero to £2,888, "
        "including a real chance of nothing at all, because they may already be gone.\n\n"
        "What happened? They returned twice and spent £1,010. Comfortably inside the wide interval. And "
        "notice the tight one would have hidden that story completely."))
picture(s, FIG+"worked_example_customer.png", In(1.90), max_w=In(9.4), max_h=In(4.0))
takeaway(s, "Expected £1,364 (interval £1,326–£1,401).  Realised £1,010.  The honest interval was £0–£2,888.")

# ════════════════════════════ 17  XGBOOST
s = slide("Why the strongest competitor trails", kicker="Finding 1d · the benchmark",
 notes=("~1.5 min. XGBoost is a serious benchmark here — 24 engineered features, two-stage design, "
        "tuned hyperparameters. It is not a straw man, and I want to explain its result rather than "
        "celebrate it.\n\n"
        "Look at what it spends its capacity learning: recency, frequency, and spread. Those are "
        "exactly the things the generative model ASSUMES by construction. So the learner is using 4,522 "
        "examples to rediscover structure I simply wrote down — and a third of those examples have a "
        "single purchase, so there is very little to learn from.\n\n"
        "The honest framing is that capacity does not help when the binding constraint is information. "
        "At ten times the customer base, with real covariates, I would expect this to reverse — and the "
        "literature reports exactly that crossover."))
picture(s, FIG+"xgboost_feature_importance.png", In(1.95), max_w=In(9.0), max_h=In(3.95))
takeaway(s, "With 24 features the learner mostly rediscovers what the generative model assumes for free.")

# ════════════════════════════ 18  H2
s = slide("Can France borrow strength from the UK?", kicker="Finding 2 · partial pooling",
 notes=("~2 min. The UK has 4,152 customers in this data. Germany has 74. France has 54.\n\n"
        "You have three options. Fit France on its own and you are betting everything on 54 people — "
        "you will overfit their quirks. Pool everyone together and France loses whatever genuinely "
        "makes it different. Or: partial pooling, where each country keeps its own parameters but those "
        "parameters are themselves drawn from a shared distribution.\n\n"
        "The result: partial pooling has the lowest aggregated error on the small segments, 1.746 "
        "against 1.755 and 1.757. That is half a percent, and I will not pretend it is dramatic.\n\n"
        "The defensible claim is adaptivity, not magnitude: partial pooling is never the WORST option "
        "in any segment, whereas the other two each fail badly somewhere. You are buying insurance "
        "against choosing wrong."))
picture(s, SLD+"h2_pooling.png", In(1.90), max_w=In(10.6), max_h=In(3.5))
bullets(s, [
 "Never the worst in any segment — the other two strategies each fail badly somewhere",
 "Verdict: partially supported. Adaptivity rather than uniform gain — and conditional on a deliberately tight prior",
], top=In(5.45), size=16)

# ════════════════════════════ 19  SHRINKAGE
s = slide("The mechanism: shrinkage in proportion to ignorance", kicker="Finding 2b · why it works",
 notes=("~1.5 min. The mechanism is worth a slide because it is one of the genuinely beautiful results "
        "in statistics, and it is not mine — it goes back to Stein, and Efron and Morris in the 1970s.\n\n"
        "Each country's estimate is pulled toward the global average in proportion to how little "
        "evidence it has. The UK, with 4,152 customers, barely moves — its own data overwhelms the "
        "prior. France, with 54, is pulled hard.\n\n"
        "The model is deciding how much to trust each group automatically, based on how much it knows. "
        "Nobody tunes that.\n\n"
        "And the theorem promises aggregate improvement, not a win in every group. So my modest result "
        "is exactly what theory says to expect — textbook, not anomalous."))
picture(s, FIG+"hierarchical_shrinkage_r.png", In(1.95), max_w=In(8.2), max_h=In(3.95))
term(s, "Shrinkage", "pulling small-sample estimates toward the group average — more pull where there is less evidence.")

# ════════════════════════════ 20  H3
s = slide("The decision test — and why it failed", kicker="Finding 3 · targeting",
 notes=("~2 min. This is the question I most wanted to answer yes, and it came back no.\n\n"
        "The set-up is a realistic marketing decision: a budget, a cost per contact, choose who to "
        "target. The sophisticated approach says do not just rank by expected value — compute the "
        "probability each customer exceeds a threshold, because that accounts for risk.\n\n"
        "It did not win. Ranking by plain expected value did just as well, across a whole sweep of cost "
        "assumptions so it is not an artefact of one choice.\n\n"
        "And there is a clean reason. When the objective is LINEAR in value — profit is value minus "
        "cost — decision theory says the optimal action depends only on the expected value. The rest of "
        "the distribution contains nothing relevant to THAT decision. This is a known theorem. What I "
        "did was demonstrate it empirically in a real business problem.\n\n"
        "So the practitioner message is precise: for a straightforward targeting decision, the mean is "
        "enough, and the extra machinery is not earning its keep."))
picture(s, SLD+"h3_targeting.png", In(1.95), max_w=In(10.4), max_h=In(3.9))
takeaway(s, "For a LINEAR objective the posterior mean is already sufficient — the tails cannot add anything.")

# ════════════════════════════ 21  THE PITFALL
s = slide("The mistake that costs £90,000", kicker="Methodological finding ★",
 notes=("~2.5 min. This is the finding I did not go looking for, and the one I would defend hardest.\n\n"
        "There are two things both correctly called 'the posterior', and they answer different "
        "questions. Uncertainty about the RULE — how well do I know this customer's rate — shrinks as "
        "data accumulates. Uncertainty about the OUTCOME — what will they actually do — never shrinks, "
        "because people are genuinely unpredictable.\n\n"
        "If you build a decision rule on the first one, something disastrous happens quietly. The "
        "expectation is known so precisely that a threshold is either entirely above or entirely below "
        "it — so 96% of customers get a probability of exactly 0 or exactly 1. Your ranking collapses "
        "into arbitrary tie-breaking, and nothing warns you.\n\n"
        "The cost in my simulation: hit rate falls from 0.85 to 0.62, and wasted spend nearly triples — "
        "from £55,040 to £144,738. Ninety thousand pounds, from a conceptual error that produces "
        "working code.\n\n"
        "So I give a one-line diagnostic: look at your probabilities. If most are 0 or 1, you used the "
        "wrong distribution. That applies to any model with distributional output, including neural ones."))
picture(s, FIG+"prob_expectation_vs_predictive.png", In(1.85), max_w=In(10.2), max_h=In(3.3))
rect(s, In(0.85), In(5.35), In(11.6), In(0.6), SOFT)
rect(s, In(0.85), In(5.35), Pt(4), In(0.6), ORANGE)
t = tb(s, In(1.08), In(5.44), In(11.2), In(0.45), anchor=MSO_ANCHOR.MIDDLE)
put(t, "Hit rate 0.85 → 0.62     ·     Wasted spend £55,040 → £144,738     ·     96% of customers pinned at 0 or 1",
    15, True, NAVY, 0, first=True)
term(s, "Posterior predictive", "uncertainty about the OUTCOME, not the rule. The one a decision about a real customer needs.", top=In(6.15))

# ════════════════════════════ 22  SECTION
section("What it means", "For the field, for practice, and what I would do next",
 notes="~10 s. Finally: what these three answers add up to.")

# ════════════════════════════ 23  SYNTHESIS
s = slide("Three answers, one pattern", kicker="Findings in the round",
 notes=("~1.5 min. Put the three side by side and a pattern appears that I did not design for.\n\n"
        "The three questions demand progressively more of the posterior. H1 uses its centre and spread "
        "— and wins. H2 uses its structure across groups — and gains a little. H3 uses its tails — and "
        "gains nothing, because a linear objective ignores tails by construction.\n\n"
        "So the honest one-line summary of this thesis is: the value of a posterior is realised in "
        "proportion to how much of it the question actually uses. That is more useful than three "
        "confirmations would have been, because it tells a practitioner where to stop paying."))
picture(s, SLD+"verdicts.png", In(1.95), max_w=In(11.0), max_h=In(2.6))
bullets(s, [
 ("H1 uses the posterior's centre and spread", "Decisive — better ranking, and honest intervals."),
 ("H2 uses its structure across groups", "A modest, adaptive gain — robustness rather than accuracy."),
 ("H3 uses its tails", "Nothing, because a linear objective cannot see them."),
], top=In(4.75), size=15.5, gap=4)
takeaway(s, "A posterior pays off in proportion to how much of it the question actually uses.", top=In(6.5))

# ════════════════════════════ 24  CONTRIBUTION
s = slide("What this adds", kicker="Contribution",
 notes=("~1.5 min. I invent no new estimator, and I want to be straightforward about that. The "
        "contribution is methodological and evaluative.\n\n"
        "First, I import calibration validation into a tradition that reports accuracy almost "
        "exclusively — the applied BTYD literature validates expectations against actuals and rarely "
        "checks coverage.\n\n"
        "Second, I quantify the cost of the two-posteriors confusion in a decision setting and give a "
        "diagnostic for catching it.\n\n"
        "Third, I demonstrate a known decision-theory result — linear objectives need only the mean — "
        "empirically, in a real business problem, which makes it visible to practitioners who will "
        "never read Berger.\n\n"
        "I would argue the field has no shortage of estimators and a real shortage of honest evaluation."))
bullets(s, [
 ("Extends validation from accuracy to calibration",
  "The BTYD tradition validates expectations against actuals; coverage of predictive intervals is rarely reported."),
 ("Quantifies the cost of using the wrong posterior",
  "Roughly tripled wasted spend — plus a one-line diagnostic that catches it before deployment."),
 ("Makes a decision-theory result visible in practice",
  "Linear objectives need only the mean. Known theoretically; now demonstrated on a real targeting problem."),
], top=In(2.0), size=17)
takeaway(s, "No new estimator. A clearer account of when the existing ones are worth their cost.")

# ════════════════════════════ 25  PRACTICE
s = slide("What a practitioner should do on Monday", kicker="Practitioner guidance",
 notes=("~1 min. Four concrete things, in order of how much they matter.\n\n"
        "Validate coverage, not just error — an uncalibrated interval is worse than no interval because "
        "it invites decisions it cannot support. Use the predictive distribution for any question about "
        "a real outcome. Check your probabilities: if most are 0 or 1, you used the wrong one. And pool "
        "small segments rather than fitting or dropping them."))
bullets(s, [
 "Validate coverage, not only error — an uncalibrated interval is worse than an honest absence of one",
 "For any question about a real outcome, use the predictive distribution, never the posterior of an expectation",
 "Inspect your probabilities before deploying — if most sit at 0 or 1, the wrong distribution was used",
 "Pool small segments rather than fitting them alone or dropping them — you buy robustness cheaply",
 "Expect the generative model's edge to be in ranking, not in absolute error",
], top=In(2.1), size=17.5, gap=14)
takeaway(s, "The cheapest improvement available to most CLV pipelines is checking whether the uncertainty is honest.")

# ════════════════════════════ 26  LIMITATIONS
s = slide("Limitations, and which way each one bites", kicker="Honest assessment",
 notes=("~1.5 min. I state direction of bias rather than just listing caveats, because a limitation "
        "without a direction tells a reader nothing about whether to trust the number.\n\n"
        "Stationarity is violated — customers change — and this over-predicts mid-frequency customers by "
        "20 to 30%. But the top deciles, where the money is, stay calibrated.\n\n"
        "Frequency and spend are mildly correlated, 0.13, which the model assumes away. Because it is "
        "positive, it under-predicts spend for the most frequent buyers — partially OFFSETTING the "
        "stationarity bias rather than compounding it.\n\n"
        "And my favourite, because it is so concrete: the most active customer made 200 repeat purchases "
        "in 65 weeks. That is not a consumer buying gifts; that is a business doing procurement. "
        "Wholesale buyers in a consumer model break the assumptions, and I flag it rather than quietly "
        "dropping the row."))
bullets(s, [
 ("Stationarity is violated — customers change over time",
  "Over-predicts mid-frequency customers by 20–30%. The top deciles, where the budget goes, stay calibrated."),
 ("Frequency and spend are assumed independent — they correlate at 0.13",
  "Positive, so it under-predicts the heaviest buyers — partially offsetting the bias above, not compounding it."),
 ("One retailer, one country, one two-year window",
  "Magnitudes are specific. The two-posteriors mechanism is mathematical and transfers."),
 ("Wholesale buyers sit inside a consumer model",
  "The most active customer made 200 repeat purchases in 65 weeks. That is procurement, not gift-buying."),
], top=In(1.95), size=16, gap=6)
takeaway(s, "The two design biases run in opposite directions — the result is conservative in one place, generous in another.")

# ════════════════════════════ 27  CLOSE
s = slide("Where this goes next", kicker="Conclusion and outlook",
 notes=("~1.5 min, then questions. Three things I would do with another year.\n\n"
        "Pool on behaviour rather than geography — a London wholesaler resembles a Paris wholesaler more "
        "than a London gift-buyer, so country is probably a weak proxy. Build a decision with a "
        "non-linear objective, which is the proper test H3 could not be. And relax stationarity with a "
        "time-varying rate, since that is the assumption I can most clearly show is broken.\n\n"
        "To close: the thesis began with a shop that cannot see who has left. It ends with a model that "
        "does not pretend to either — it reports honest uncertainty about it, and is explicit about "
        "when that uncertainty is worth paying for and when it is not.\n\n"
        "Thank you. I welcome your questions."))
bullets(s, [
 ("Pool on behaviour, not geography",
  "A London wholesaler resembles a Paris wholesaler more than a London gift-buyer. Country is a weak proxy."),
 ("Build a decision with a non-linear objective",
  "Budget constraints, convex costs, or explicit risk aversion — the proper test H3 could not be."),
 ("Relax stationarity with a time-varying rate",
  "The assumption I can most clearly show is violated, and the one most likely to matter in deployment."),
], top=In(1.95), size=17)
rect(s, In(0.85), In(5.2), In(11.6), In(0.95), SOFT)
rect(s, In(0.85), In(5.2), Pt(4), In(0.95), ORANGE)
t = tb(s, In(1.10), In(5.34), In(11.1), In(0.75))
put(t, "The thesis began with a shop that cannot see who has left.", 15.5, True, NAVY, 3, first=True)
put(t, "It ends with a model that does not pretend to either — and is explicit about when that honesty "
       "is worth paying for.", 15.5, False, INK, 0)

# ════════════════════════════ 28  THANK YOU
s = prs.slides.add_slide(BLANK); _n["i"] += 1
rect(s, 0, 0, W, H, NAVY)
t = tb(s, In(1.4), In(2.9), In(10.5), In(2.0))
put(t, "Thank you", 44, True, WHITE, 10, first=True)
put(t, "I welcome your questions.", 20, False, C(0xBF,0xC9,0xD4), 16)
put(t, "Devansh   ·   Customer Lifetime Value Prediction Using Bayesian Methods",
    14, False, C(0x8E,0x9E,0xAE), 0)
rect(s, In(1.4), In(2.5), In(1.6), Pt(3.5), ORANGE)

prs.save(OUT)
print("saved %s  ·  %d slides" % (OUT, len(prs.slides.__iter__.__self__._sldIdLst)))
