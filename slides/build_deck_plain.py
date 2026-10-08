"""Defence deck written for an undergraduate audience.

Rule applied throughout: the SLIDE says it in plain words; the technical name is
demoted to a small chip at the bottom. Nothing is dumbed down — the numbers and
claims are identical — but no sentence depends on jargon to be understood.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_engine.py")).read())
OUT = "outputs/Defence_CLV_Plain.pptx"

def chip(s, proper, top=In(6.78)):
    """'The proper name for this is ...' — small, so plain words lead."""
    t = tb(s, In(0.85), top, In(11.6), In(0.34))
    p = t.paragraphs[0]; p.space_after = Pt(0)
    r = p.add_run(); r.text = "The proper name for this:  "
    r.font.size, r.font.color.rgb, r.font.name = Pt(11), C(0x9A,0x9A,0x9A), FONT
    r2 = p.add_run(); r2.text = proper
    r2.font.size, r2.font.bold, r2.font.color.rgb, r2.font.name = Pt(11), True, TEAL, FONT

def question(s, q, top=In(1.80)):
    """A plain-English question, stated big, under the title."""
    t = tb(s, In(0.85), top, In(11.6), In(0.6))
    put(t, q, 21, False, ORANGE, 0, first=True, italic=True)

def stat_row(s, items, top=In(2.1), h=In(1.35)):
    n = len(items); gap = In(0.25)
    w = Emu(int((In(11.6) - gap*(n-1)) / n))
    for i,(k,v,c) in enumerate(items):
        l = In(0.85) + Emu(int(i*(w+gap)))
        rect(s, l, top, w, h, SOFT); rect(s, l, top, w, Pt(3.5), c)
        t = tb(s, l+In(0.18), top+In(0.22), w-In(0.36), h-In(0.3))
        put(t, k, 26, True, c, 2, first=True)
        for ln in v.split("\n"): put(t, ln, 12, False, MUTE, 0)

def box(s, lines, top, h=In(1.0), accent=ORANGE):
    rect(s, In(0.85), top, In(11.6), h, SOFT)
    rect(s, In(0.85), top, Pt(4), h, accent)
    t = tb(s, In(1.10), top+In(0.13), In(11.1), h-In(0.2))
    for i,(txt,sz,bold,col) in enumerate(lines):
        put(t, txt, sz, bold, col, 4, first=(i==0))

# ════════════════════ 1 TITLE
s = prs.slides.add_slide(BLANK); _n["i"] += 1
rect(s, 0, 0, W, In(0.22), NAVY); rect(s, 0, In(0.30), W, Pt(2), ORANGE)
t = tb(s, In(1.0), In(1.70), In(11.3), In(2.1))
put(t, "How much is a customer worth,", 40, True, NAVY, 4, first=True)
put(t, "when you can't tell who has left?", 40, True, NAVY, 14)
put(t, "Customer Lifetime Value Prediction Using Bayesian Methods", 17, False, MUTE, 0, italic=True)
rect(s, In(1.0), In(4.30), In(2.0), Pt(3), ORANGE)
t = tb(s, In(1.0), In(4.60), In(11.0), In(1.6))
put(t, "Devansh", 20, True, INK, 8, first=True)
put(t, "Master's Thesis  ·  M.Sc.", 14.5, False, MUTE, 4)
put(t, "First Supervisor: Professor Dr. Tilo Wendler    ·    Second Supervisor: Dr. Guido Möser",
    13.5, False, MUTE, 0)
rect(s, 0, In(7.28), W, In(0.22), NAVY)
s.notes_slide.notes_text_frame.text = (
 "~40 s. Good morning. I'll keep the vocabulary plain and put the technical names in small "
 "print at the bottom of each slide, so the argument is followable whether or not you work in "
 "this area. Four parts: the problem, how the model works, what I found, and what it means.")

# ════════════════════ 2 THE SHOP
s = slide("A shop that has to guess", kicker="The setting",
 notes=("~1.5 min. A real UK shop selling gifts. Two years of sales records — 4,522 customers after "
        "cleaning. Every week it has some money for marketing and must choose who to spend it on.\n\n"
        "To choose well you need to know what each customer will be worth IN FUTURE. Not what they "
        "have already spent — that money is in. What they will spend from here. That is the number "
        "this whole thesis is about, and nobody can look it up."))
question(s, "Who should the shop spend its marketing money on this week?")
stat_row(s, [("4,522","customers in\nthe dataset",NAVY),
             ("2 years","of real sales\n2009–2011",NAVY),
             ("£385","average basket\n(typical: £299)",NAVY),
             ("33%","bought once and\nnever came back",ORANGE)], top=In(2.55))
bullets(s, [
 "Winning a customer costs money up front — ads, discounts, delivery",
 "It only pays back if they come back. So you need to know who will.",
 "That future number is what we are trying to predict. It is not what they have spent so far.",
], top=In(4.3), size=18)
chip(s, "Customer Lifetime Value (CLV)")

# ════════════════════ 3 TWO CUSTOMERS
s = slide("Two customers who look identical", kicker="Why past spending misleads",
 notes=("~1 min. The whole problem in one picture. Two people spend ten pounds today. In the sales "
        "record they are the same row. One lives nearby and will shop monthly for three years. The "
        "other was visiting. Same spend today, completely different value tomorrow.\n\n"
        "Most businesses rank customers by what they have already spent. That method cannot tell "
        "these two apart — it gives them the same score."))
question(s, "They spent the same today. Are they worth the same tomorrow?")
bullets(s, [
 ("Customer A — spends £10 today", "Comes back every month for three years. Worth several hundred pounds."),
 ("Customer B — spends £10 today", "Never returns. Worth £10, minus what it cost to win them."),
], top=In(2.5), size=20)
box(s, [("Identical in the sales record. Opposite in value.", 17, True, NAVY),
        ("Scoring customers by past spending — which is what most businesses do — gives both the same score.",
         16, False, INK)], In(4.75), In(1.1))
chip(s, "RFM scoring (recency, frequency, monetary value)")

# ════════════════════ 4 THE INVISIBLE THING
s = slide("Nobody tells you they've gone", kicker="Why this is hard",
 notes=("~2 min. This is the hinge of the thesis so I'll go slowly.\n\n"
        "If you cancel a gym membership, the gym knows. There's a date. You can count who left.\n\n"
        "A shop has no cancel button. People just stop coming, and never announce it. So imagine a "
        "customer who hasn't bought for fifteen weeks. Have they left? You cannot say. If they "
        "normally buy every three weeks, fifteen weeks is alarming. If they buy twice a year, "
        "fifteen weeks is nothing. The same silence means opposite things.\n\n"
        "So whether someone is still a customer is invisible — not just unrecorded, but genuinely "
        "unknown to everybody, including them. You can never check your answer. That rules out the "
        "two obvious approaches: a cut-off rule picks a number out of the air, and you can't train a "
        "machine-learning classifier because there are no labels to train on."))
question(s, "Has this customer left, or are they just slow?")
bullets(s, [
 ("A gym membership — the easy case", "You cancel. There is a date. Churn can be counted."),
 ("A shop — this case", "No cancellation. People simply fade away, silently."),
], top=In(2.45), size=19)
box(s, [("Two customers, both silent for 15 weeks", 16, True, NAVY),
        ("One normally buys every 3 weeks — alarming.      One buys twice a year — completely normal.",
         15.5, False, INK),
        ("Same silence, opposite meaning. A fixed cut-off rule would get one of them wrong.",
         15.5, True, ORANGE)], In(4.5), In(1.5))
chip(s, "A latent (hidden) state in a non-contractual setting")

# ════════════════════ 5 THE QUESTIONS
s = slide("The three questions I asked", kicker="Aims",
 notes=("~1.5 min. Three questions, and I'll give you the answers now so you can follow the reasoning "
        "instead of waiting for a reveal.\n\n"
        "One: does this approach predict better than the standard alternatives, and — separately — is "
        "it honest about how sure it is? Yes.\n\n"
        "Two: there are 4,152 UK customers but only 54 French ones. Can France borrow information from "
        "the UK rather than being judged on 54 people? Partly.\n\n"
        "Three: does having a full range of possible answers, rather than a single best guess, actually "
        "change who you'd target? No — and that turned out to be the most interesting of the three, "
        "because there's a clean reason why it had to be no."))
question(s, "Does this approach predict better, work for small groups, and change decisions?")
bullets(s, [
 ("1 · Is it more accurate — and is it honest about how sure it is?",
  "Compared against three alternatives, including a strong machine-learning model.      Answer: yes"),
 ("2 · Can a country with 54 customers borrow information from one with 4,152?",
  "Instead of being fitted alone, or lumped in with everyone else.      Answer: partly"),
 ("3 · Does knowing the full range of possibilities change who you'd target?",
  "A realistic marketing-spend simulation with real costs.      Answer: no — and that is the interesting one"),
], top=In(2.5), size=17)
chip(s, "RQ1 / RQ2 / RQ3 — hypotheses H1, H2, H3")

# ════════════════════ 6 SECTION
section("How the model works", "Four behaviours, one sum we can't do, and a way round it",
 notes="~10 s.")

# ════════════════════ 7 DESCRIBE BEHAVIOUR
s = slide("Describe behaviour, don't hunt for patterns", kicker="The approach",
 notes=("~2 min. This is genuinely different from standard machine learning, so let me contrast them.\n\n"
        "Machine learning says: here are 24 columns of data, find whatever pattern predicts the answer. "
        "It's powerful, and it needs examples of the right answer to learn from.\n\n"
        "I do the opposite. I write down, in advance, a description of how I think shopping happens — "
        "a few simple behaviours — and then ask the data which version of that description fits best.\n\n"
        "Why does that matter here? Because the thing I need to know is invisible. There are no labels "
        "saying 'this customer churned', for anyone, ever. A machine-learning model can't be trained on "
        "a label that doesn't exist. But a description of behaviour CAN contain an invisible step, and "
        "the data can still tell you how likely that step was.\n\n"
        "The bonus is that every number in the model means something you can argue with in a meeting."))
question(s, "If you can't see who left, how can you model it?")
bullets(s, [
 ("The machine-learning way", "Here are 24 columns. Find the pattern that predicts the answer. Needs examples of the right answer."),
 ("The way used here", "Describe how shopping happens. Ask which version of that description fits the data best."),
], top=In(2.5), size=19)
bullets(s, [
 "There are no labels saying “this customer has left” — so there is nothing to train a classifier on",
 "But a description of behaviour can include an invisible step, and the data still constrains it",
 "Side benefit: every number in the model means something a manager can question",
], top=In(4.6), size=16.5)
chip(s, "A generative probabilistic model")

# ════════════════════ 8 THE FOUR BEHAVIOURS
s = slide("The description, in four parts", kicker="The model",
 notes=("~2.5 min. Four behaviours. None of them is complicated.\n\n"
        "One — while someone is still a customer, they buy at random, but at their own typical rate. "
        "Like rainfall: you can't say it'll rain on Tuesday, but you can say it rains about twice a "
        "week here.\n\n"
        "Two — after each purchase, they privately decide whether that was the last one. Think of it as "
        "flipping a biased coin only they can see. Some people's coins almost never say stop.\n\n"
        "Three — and this is the one doing the real work — everybody is different, and the model says "
        "so explicitly rather than using one average person.\n\n"
        "Four — how much they spend per visit, which is very lopsided: a few enormous orders drag the "
        "average well above what a typical customer does.\n\n"
        "Put it together: value equals how often, times how much."))
bullets(s, [
 ("1 · Everyone has their own pace",
  "While still a customer, purchases happen at random — but around that person's own typical rate. Like rainfall."),
 ("2 · After each purchase, a private decision to stop",
  "Think of a biased coin only they can see. For most customers it almost never says stop."),
 ("3 · Everybody is different, and the model says so",
  "Rather than one average customer, it describes the whole spread of paces and stopping-chances."),
 ("4 · How much they spend per visit",
  "Very lopsided — a few huge orders pull the average well above the typical basket."),
], top=In(1.95), size=16.5, gap=7)
box(s, [("Value  =  how often they buy   ×   how much they spend each time", 18, True, NAVY)],
    In(5.6), In(0.62))
chip(s, "BG/NBD for purchases and dropout; Gamma-Gamma for spend")

# ════════════════════ 9 PEOPLE REALLY DIFFER
s = slide("Proof that people really do differ", kicker="Why part 3 matters",
 notes=("~1.5 min. Part three sounds like a technicality. It isn't — it's the difference between a "
        "model that works and one that doesn't, and the data proves it.\n\n"
        "In this dataset the average customer makes 3.78 repeat purchases. Now, there's a basic result "
        "in probability: if everybody shared one single rate, then the spread of the counts should be "
        "roughly the same size as that average. About 3.8.\n\n"
        "The actual spread is 77.7. More than twenty times bigger.\n\n"
        "That gap is not noise. It's hard evidence that customers are genuinely different from one "
        "another — and that any model built around one typical customer would be describing nobody.\n\n"
        "Think of reading habits: if everyone read the same amount, book counts would cluster tightly. "
        "They don't, because people differ enormously."))
question(s, "Could one “average customer” describe this shop?")
stat_row(s, [("3.78","average repeat\npurchases",NAVY),
             ("≈ 3.8","the spread you'd see\nif everyone were alike",TEAL),
             ("77.7","the spread actually\nin the data",ORANGE)], top=In(2.5))
box(s, [("More than twenty times wider than “everyone is alike” allows.", 17, True, NAVY),
        ("So the model describes the whole range of customers, not one typical one. "
         "This is what lets it handle someone with two purchases differently from someone with two hundred.",
         16, False, INK)], In(4.35), In(1.25))
chip(s, "Over-dispersion — handled with mixing distributions (Gamma, Beta)")

# ════════════════════ 10 THE SUM WE CANT DO
s = slide("The sum nobody can do", kicker="Why this needs a computer",
 notes=("~2 min. Writing the description down is the easy half. Now I need to work out which version "
        "of it the data supports, and that hits a wall.\n\n"
        "The rule for updating beliefs with evidence is a fraction. The top — how well a particular "
        "setting explains the data — I can work out in milliseconds for any setting you name. The "
        "bottom requires adding up that quantity over every possible combination of settings at once. "
        "There is no formula for it.\n\n"
        "The obvious fix is to try settings on a grid. But with seven numbers to pin down and fifty "
        "values each, that's fifty to the power of seven — about a hundred billion calculations, each "
        "one sweeping all 4,522 customers. Years of computing.\n\n"
        "The escape is this: every method I use only ever COMPARES two settings. And in a comparison, "
        "that impossible bottom number appears on both sides and cancels. So I never need it."))
question(s, "Why can't you just work out the answer directly?")
bullets(s, [
 ("The top of the fraction — easy", "How well does this particular setting explain the data? Milliseconds."),
 ("The bottom of the fraction — impossible", "The same thing added up over every possible setting at once. No formula exists."),
], top=In(2.5), size=19)
box(s, [("A grid won't rescue it: 7 numbers to pin down × 50 values each ≈ 100 billion calculations — years of computing.",
         16, False, INK),
        ("But every method here only COMPARES two settings — and in a comparison the impossible number cancels out.",
         16.5, True, ORANGE)], In(4.75), In(1.2))
chip(s, "The posterior; its denominator is the marginal likelihood (“evidence”)")

# ════════════════════ 11 SAMPLES
s = slide("So take samples instead", kicker="The way round it",
 notes=("~2 min. Here's the idea, and it's one you already trust in a different setting.\n\n"
        "Nobody counts every voter to find out what a country thinks. You poll a thousand people and "
        "the proportions in the sample tell you the proportions in the country. You trade an impossible "
        "count for a manageable sample.\n\n"
        "Same move here. Instead of computing the full range of plausible settings, I take four "
        "thousand samples from it. And the way to picture how: imagine the possible settings as a "
        "landscape where likely ones are valleys. Roll a ball across it. The ball naturally spends most "
        "of its time in the valleys — and simply recording where it has been, over and over, builds up "
        "a picture of the whole landscape.\n\n"
        "The computer does this four separate times, from four different starting points, so I can "
        "check they agree."))
question(s, "How do you measure something you can't calculate?")
bullets(s, [
 ("You already trust this idea", "Nobody asks every voter. You poll 1,000 people and the proportions tell you the country."),
 ("Same move here", "Instead of computing every plausible setting, take 4,000 samples from them."),
 ("How the samples are taken", "Picture the settings as a landscape where likely ones are valleys. Roll a ball. It spends most of its time in the valleys — so recording where it goes maps the landscape."),
], top=In(2.5), size=17)
box(s, [("Done 4 separate times, from 4 different starting points — so the runs can be checked against each other.",
         16.5, True, NAVY)], In(5.75), In(0.6))
chip(s, "Markov chain Monte Carlo; specifically Hamiltonian Monte Carlo with the NUTS sampler")

# ════════════════════ 12 WHAT COMES BACK
s = slide("What the computer hands back", kicker="The output",
 notes=("~2 min. This is the one idea I'd most like to land, because every result depends on it.\n\n"
        "The computer doesn't return a formula, and it doesn't return a single best answer. It returns "
        "a list. Four thousand rows. Each row is a complete set of values for all the model's numbers "
        "at once.\n\n"
        "One row is one entire, self-consistent version of how all 4,522 customers behave. The next row "
        "is a different complete version. Both are consistent with what actually happened.\n\n"
        "And here's the payoff. Settings that explain the data well get visited often, so they fill "
        "lots of rows. Settings that explain it badly barely appear. So I never need that impossible "
        "sum — I just count rows. The chance a customer is worth more than six hundred pounds is simply: "
        "how many rows say yes, divided by four thousand."))
question(s, "Not one answer — four thousand of them. Why is that useful?")
bullets(s, [
 ("Each row is one complete version of the world",
  "Not an error bar. A whole self-consistent description of how all 4,522 customers behave."),
 ("4,000 rows = 4,000 versions, all consistent with what happened",
  "Good settings get visited often, so they fill many rows. Bad ones barely appear."),
], top=In(2.5), size=18)
box(s, [("So any question becomes counting, not calculating:", 16, False, MUTE),
        ("“Chance this customer is worth over £600”   =   how many of the 4,000 rows say yes   ÷   4,000",
         17, True, NAVY)], In(4.7), In(1.15), accent=TEAL)
chip(s, "Posterior draws / samples")

# ════════════════════ 13 DID IT WORK
s = slide("Did the computer do it properly?", kicker="Checks before results",
 notes=("~1 min. This kind of computation can fail quietly, so nothing counts until three checks pass.\n\n"
        "First: the four separate runs are compared. If they explored the same landscape they'll agree. "
        "A score of 1.00 means perfect agreement; mine is 1.0014.\n\n"
        "Second: consecutive samples are a bit similar to each other, so 4,000 samples are worth fewer "
        "than 4,000 truly independent ones. Mine are worth about 2,000 — which is good.\n\n"
        "Third: a count of places where the simulation broke down. You want zero. I have zero.\n\n"
        "One thing I want to say plainly, because it's a fair question: these checks say the COMPUTATION "
        "worked. They say nothing about whether the model is a good description of reality. A bad model "
        "can compute beautifully. That's exactly why I show these before any result, not as evidence for one."))
question(s, "How do you know the computer didn't quietly get it wrong?")
stat_row(s, [("1.0014","the 4 runs agree\n(1.00 = perfect)",TEAL),
             ("~2,000","samples' worth of real\ninformation, out of 4,000",TEAL),
             ("0","places where the\nsimulation broke down",TEAL)], top=In(2.5))
box(s, [("These checks say the computation worked. They do not say the model is right.", 17, True, NAVY),
        ("A poor model can compute perfectly. That is why they are shown before the results, not as evidence for them.",
         16, False, INK)], In(4.4), In(1.15))
chip(s, "R-hat, effective sample size, divergent transitions")

# ════════════════════ 14 SECTION
section("What I found", "Three questions, three different kinds of answer",
 notes="~10 s.")

# ════════════════════ 15 TOP OF THE LIST
s = slide("Did it put the right people at the top?", kicker="Question 1, part a",
 notes=("~2 min. There are two ways to score a prediction, and here they disagree — which is the "
        "interesting part.\n\n"
        "The first is average error: how far off is the typical prediction? On that, my model wins, but "
        "only modestly, and I won't oversell it.\n\n"
        "The second asks a different question: of the hundred customers the model says are most "
        "valuable, how many really are? That's the right-hand panel. 0.91 out of a possible 1.0, "
        "against 0.53 for the machine-learning model.\n\n"
        "Why does the second matter more? Because the shop's budget only reaches the top of the list. "
        "Being slightly wrong about an average customer costs nothing. Getting the top hundred wrong "
        "costs the entire campaign.\n\n"
        "One honest point: the machine-learning model was trained on a slightly shorter stretch of data, "
        "for a technical reason to do with fairness. So it had less to learn from, and that gap should "
        "be read as a best case for my model, not an exact figure."))
question(s, "Of the 100 customers it says are most valuable — how many really are?")
picture(s, SLD+"accuracy.png", In(2.45), max_w=In(11.4), max_h=In(3.5))
box(s, [("The shop's budget only reaches the top of the list, so getting the top right is what matters.",
         16, True, NAVY),
        ("Caveat I state openly: the machine-learning model trained on less data, so this gap is a best case, not an exact figure.",
         15, False, MUTE)], In(6.08), In(0.95))
chip(s, "NDCG@100 — a ranking-quality score", top=In(7.08))

# ════════════════════ 16 HONESTY
s = slide("When it says “90% sure”, is it right 90% of the time?", kicker="Question 1, part b",
 notes=("~1.5 min. This is a completely different question from accuracy, and I'd argue it matters more.\n\n"
        "The model doesn't just give a number — it gives a range, and says how confident it is in that "
        "range. So you can test the confidence itself. Make a 90% range for every one of the 4,522 "
        "customers, then go and check how many real outcomes actually landed inside.\n\n"
        "If the answer were 60%, the model would be bluffing, and every decision built on it would "
        "inherit that overconfidence. The answer is 89.3%.\n\n"
        "That's what makes these ranges usable for planning a budget rather than just decorating a "
        "slide. And note: this is a question you can only ASK of a model that gives ranges. The "
        "standard alternatives give a single number, so there's nothing to check."))
question(s, "A weather forecaster who says 90% rain should be right about 9 times in 10.")
stat_row(s, [("89.3%","of real outcomes landed\ninside the 90% range",TEAL),
             ("1.22","combined score for\naccuracy and honesty",NAVY),
             ("0.71","ability to spot who is\nstill shopping",NAVY)], top=In(2.5))
bullets(s, [
 "If this had come out at 60%, the model would be bluffing — and every decision built on it would inherit that",
 "At 89.3% you can take its confidence at face value, which is what makes it usable for budgeting",
 "You can only ask this of a model that gives ranges — the standard alternatives give one number, so there is nothing to check",
], top=In(4.35), size=16.5)
chip(s, "Calibration / empirical coverage; CRPS; AUC for P(alive)")

# ════════════════════ 17 ONE CUSTOMER
s = slide("One real customer, start to finish", kicker="Question 1, part c",
 notes=("~2 min. Let me make all of that concrete with one real customer — number 14817. Four repeat "
        "purchases, last seen 33 weeks in, average basket £526.\n\n"
        "Run them through all 4,000 versions of the world and average the answers: £1,364, with a range "
        "of £1,326 to £1,401. That's a narrow range — seventy-five pounds. It looks like I have this "
        "person pinned down.\n\n"
        "I don't. That narrow range answers 'how well do I know this customer's underlying habits?' — "
        "not 'what will they actually do?'. Those are different questions. Ask the second one and the "
        "range runs from zero to £2,888, including a real chance of nothing at all, because they might "
        "already have left.\n\n"
        "What actually happened? They came back twice and spent £1,010. Comfortably inside the wide "
        "range. And notice the narrow range would have hidden that possibility entirely."))
question(s, "How well do we know this person — and what will they actually do?")
picture(s, FIG+"worked_example_customer.png", In(2.45), max_w=In(8.8), max_h=In(3.6))
box(s, [("Best guess £1,364, narrow range £1,326–£1,401.      What they actually spent: £1,010.", 16.5, True, NAVY),
        ("The honest range — “what will they really do” — was £0 to £2,888. The narrow one would have hidden that.",
         15.5, False, INK)], In(6.15), In(0.95))
chip(s, "Posterior of an expectation vs posterior predictive", top=In(7.15))

# ════════════════════ 18 WHY ML LOST
s = slide("Why the machine-learning model did worse", kicker="Question 1, part d",
 notes=("~1.5 min. The comparison model here is XGBoost — a strong, modern, widely-used method, with 24 "
        "engineered inputs and tuned settings. It isn't a straw man, and I'd rather explain its result "
        "than celebrate it.\n\n"
        "Look at what it spends its effort learning: how recently someone bought, how often, and how "
        "much that varies. Those are exactly the things my model is TOLD at the start. So the "
        "machine-learning model is using 4,522 examples to rediscover a structure I simply wrote down — "
        "and a third of those examples are people with a single purchase, so there's almost nothing to "
        "learn from.\n\n"
        "The honest summary is that raw power doesn't help when the shortage is information, not "
        "capacity. With ten times the customers and richer data I'd expect this to flip — and published "
        "work reports exactly that."))
question(s, "A more powerful method, with more inputs. Why did it lose?")
picture(s, FIG+"xgboost_feature_importance.png", In(2.45), max_w=In(8.6), max_h=In(3.6))
box(s, [("It spends its effort rediscovering what my model is simply told at the start.", 16.5, True, NAVY),
        ("Power doesn't help when the shortage is information. With 10× the customers I would expect this to reverse.",
         15.5, False, INK)], In(6.15), In(0.95))
chip(s, "Gradient-boosted trees (XGBoost), 24 features, two-stage", top=In(7.15))

# ════════════════════ 19 BORROWING
s = slide("Can a country with 54 customers borrow from one with 4,152?", kicker="Question 2",
 notes=("~2 min. The UK has 4,152 customers here. Germany has 74. France has 54.\n\n"
        "You've got three options. Fit France on its own, and you're betting everything on 54 people — "
        "you'll mistake their quirks for facts. Lump all countries together, and France loses whatever "
        "genuinely makes it different. Or the middle option: let each country keep its own numbers, but "
        "have those numbers come from a shared pool — so small countries lean on the others.\n\n"
        "The middle option gives the lowest error on the small countries: 1.746 against 1.755 and 1.757. "
        "That's half a percent. I'm not going to pretend it's dramatic.\n\n"
        "The claim I will defend is different: the middle option is never the WORST in any country, "
        "whereas each of the other two fails badly somewhere. You're buying insurance against choosing "
        "wrong, not a big accuracy gain."))
question(s, "Fit it alone and overfit, or lump it in and lose what makes it different?")
picture(s, SLD+"h2_pooling.png", In(2.45), max_w=In(10.4), max_h=In(3.2))
box(s, [("Never the worst in any country — the other two strategies each fail badly somewhere.", 16.5, True, NAVY),
        ("Answer: partly. You buy insurance against choosing wrong, not a large gain in accuracy.",
         15.5, False, INK)], In(5.95), In(0.95))
chip(s, "Partial pooling in a hierarchical model", top=In(6.95))

# ════════════════════ 20 WHY BORROWING WORKS
s = slide("Why borrowing works", kicker="Question 2, the mechanism",
 notes=("~1.5 min. The mechanism deserves a slide because it's one of the genuinely lovely results in "
        "statistics, and it's not mine — it dates from the 1970s.\n\n"
        "Think about judging a footballer. If you've seen three games, you shouldn't trust your "
        "impression much — you'd sensibly lean it toward what a typical player does. If you've seen "
        "three hundred, you trust what you saw.\n\n"
        "The model does exactly that, automatically. The UK, with 4,152 customers, barely moves — its "
        "own data overwhelms everything else. France, with 54, gets pulled strongly toward the overall "
        "average. Nobody tunes this; it falls out of the structure.\n\n"
        "And the theory promises an improvement overall, not a win in every single country. So my "
        "modest result is exactly what it predicts — ordinary, not disappointing."))
question(s, "Would you judge a footballer on 3 games the same way you'd judge one on 300?")
picture(s, FIG+"hierarchical_shrinkage_r.png", In(2.5), max_w=In(7.8), max_h=In(3.5))
box(s, [("Estimates get pulled toward the overall average in proportion to how little evidence they have.", 16.5, True, NAVY),
        ("The UK (4,152 customers) barely moves. France (54) is pulled hard. Nobody tunes this — it falls out of the structure.",
         15.5, False, INK)], In(6.1), In(0.95))
chip(s, "Shrinkage — the Stein / Efron–Morris result", top=In(7.1))

# ════════════════════ 21 DECISION
s = slide("Does any of this change who you'd target?", kicker="Question 3",
 notes=("~2 min. This is the question I most wanted to answer yes, and it came back no.\n\n"
        "Set-up: a budget, a cost per customer contacted, choose who to target. The clever approach says "
        "don't just rank people by their expected value — work out the chance each one clears a "
        "threshold, because that accounts for risk.\n\n"
        "It didn't win. Plain ranking by expected value did just as well, and I tested that across a "
        "whole range of cost assumptions so it isn't a fluke of one choice.\n\n"
        "But there's a clean reason, and it's worth understanding. When profit is simply value minus "
        "cost — a straight line — then the only thing that matters is the average. The rest of the "
        "range genuinely contains nothing extra for that decision. This is a known mathematical result; "
        "what I did was show it happening in a real business problem.\n\n"
        "So the practical message is precise, not defeatist: for a straightforward targeting decision, "
        "the average is enough. Save the extra machinery for decisions where it isn't."))
question(s, "Is the extra information worth anything when you actually have to choose?")
picture(s, SLD+"h3_targeting.png", In(2.45), max_w=In(10.2), max_h=In(3.4))
box(s, [("When profit is just value minus cost — a straight line — only the average matters.", 16.5, True, NAVY),
        ("Answer: no. The rest of the range contains nothing extra for THAT decision. A known result, shown here on a real problem.",
         15.5, False, INK)], In(6.1), In(0.95))
chip(s, "Decision theory — a linear utility makes the posterior mean sufficient", top=In(7.1))

# ════════════════════ 22 THE MISTAKE
s = slide("The mistake that cost £90,000", kicker="The finding I didn't go looking for ★",
 notes=("~2.5 min. This is the result I'd defend hardest, and I found it by making the mistake myself.\n\n"
        "There are two completely different things you can be unsure about, and it's easy to confuse "
        "them. Think of a coin. You can become very sure the coin is fair — that's being sure about the "
        "RULE. But you'll never be sure what the next flip gives — that's the OUTCOME. Knowing the rule "
        "is not the same as knowing the result.\n\n"
        "With thousands of customers, uncertainty about the rule shrinks almost to nothing. Uncertainty "
        "about what a person will actually do never shrinks, because people are unpredictable.\n\n"
        "If you build your targeting rule on the first kind, something bad happens silently. The model "
        "is so sure about the rule that any threshold is either clearly above or clearly below it — so "
        "96% of customers get a probability of exactly 0 or exactly 1. Your ranking collapses into "
        "coin-flipping between thousands of tied customers, and nothing warns you.\n\n"
        "The cost: success rate falls from 85% to 62%, and wasted spend nearly triples — £55,000 to "
        "£145,000. Ninety thousand pounds, from a conceptual mix-up that produces perfectly working code.\n\n"
        "So I give a one-line check anyone can run: look at your probabilities. If most are 0 or 1, you "
        "used the wrong one."))
question(s, "You can be certain a coin is fair and still not know the next flip.")
picture(s, FIG+"prob_expectation_vs_predictive.png", In(2.45), max_w=In(9.8), max_h=In(2.9))
box(s, [("Success rate 85% → 62%        Wasted spend £55,040 → £144,738        96% of customers scored exactly 0 or 1",
         16, True, NAVY),
        ("The check: look at your probabilities. If most sit at 0 or 1, you used the wrong kind of uncertainty.",
         15.5, True, ORANGE)], In(5.65), In(1.15))
chip(s, "Posterior of an expectation vs posterior predictive distribution", top=In(6.95))

# ════════════════════ 23 SECTION
section("What it means", "For the field, for practice, and what I'd do next",
 notes="~10 s.")

# ════════════════════ 24 SYNTHESIS
s = slide("The three answers together", kicker="Findings in the round",
 notes=("~1.5 min. Put the three side by side and a pattern shows up that I didn't design for.\n\n"
        "The three questions ask for progressively more from the model's output. The first needs its "
        "middle and its width — and wins clearly. The second needs its structure across groups — and "
        "gains a little. The third needs its extremes — and gains nothing, because a straight-line "
        "profit calculation can't see extremes.\n\n"
        "So the one-sentence summary of this thesis is: the extra information is worth exactly as much "
        "as the question actually uses. That's more useful than three yeses would have been, because it "
        "tells a practitioner where to stop spending effort."))
picture(s, SLD+"verdicts.png", In(2.3), max_w=In(10.8), max_h=In(2.4))
bullets(s, [
 ("Question 1 uses the middle and the width of the range", "Clear win — better ranking, and honest confidence."),
 ("Question 2 uses its structure across groups", "A small, adaptive gain — reliability rather than accuracy."),
 ("Question 3 uses its extremes", "Nothing, because a straight-line profit calculation cannot see extremes."),
], top=In(4.95), size=15.5, gap=4)
box(s, [("The extra information is worth exactly as much as the question actually uses.", 17, True, NAVY)],
    In(6.5), In(0.56))

# ════════════════════ 25 CONTRIBUTION
s = slide("What this adds", kicker="Contribution",
 notes=("~1.5 min. I don't invent a new method, and I want to be straightforward about that. The "
        "contribution is about how these models are tested and when they're worth using.\n\n"
        "First: this field almost always checks accuracy and stops. I check whether the confidence is "
        "honest, which is a different and arguably more important question.\n\n"
        "Second: I put a price on a specific, easy mistake — roughly tripled waste — and give a one-line "
        "check for catching it before it reaches production.\n\n"
        "Third: I show a known mathematical result actually happening in a real business problem, which "
        "makes it visible to people who'll never read the theory.\n\n"
        "I'd argue the field has plenty of methods and not enough honest testing of them."))
bullets(s, [
 ("Tests whether the confidence is honest, not only whether the prediction is close",
  "This field reports accuracy almost exclusively. Whether the stated ranges hold up is rarely checked."),
 ("Puts a price on a specific, easy mistake",
  "Roughly tripled waste — plus a one-line check that catches it before it reaches production."),
 ("Shows a known mathematical result happening in a real business",
  "Straight-line decisions need only the average. Known in theory; now visible in practice."),
], top=In(2.1), size=17)
box(s, [("No new method. A clearer account of when the existing ones are worth their cost.", 17, True, NAVY)],
    In(5.6), In(0.56))

# ════════════════════ 26 PRACTICE
s = slide("What someone should actually do with this", kicker="In practice",
 notes=("~1 min. Four concrete things, most important first. Check whether your ranges hold up, not just "
        "whether your predictions are close. For any question about what a real person will do, use the "
        "'what will they actually do' range, not the 'how well do we know the rule' one. Before you "
        "deploy, look at your probabilities — if most are 0 or 1, something's wrong. And let small "
        "groups borrow from large ones rather than fitting them alone or dropping them."))
bullets(s, [
 "Check whether your ranges hold up — an overconfident range is worse than admitting you don't know",
 "For questions about what a real person will do, use the “what will they actually do” range",
 "Before deploying, look at your probabilities — if most are 0 or 1, the wrong kind of uncertainty was used",
 "Let small groups borrow from large ones, rather than fitting them alone or dropping them",
 "Expect the advantage to show up in ranking people, not in the size of the average error",
], top=In(2.1), size=17.5, gap=14)
box(s, [("The cheapest improvement available to most of these systems is checking whether the confidence is honest.",
         17, True, NAVY)], In(6.0), In(0.56))

# ════════════════════ 27 LIMITATIONS
s = slide("What's wrong with it", kicker="Honest assessment",
 notes=("~1.5 min. I state which DIRECTION each problem pushes the answer, because a limitation without "
        "a direction tells you nothing about whether to trust the number.\n\n"
        "The model assumes people don't change over time. They do. This makes it over-predict "
        "middle-of-the-road customers by 20 to 30%. But the top customers, where the money is, stay "
        "accurate.\n\n"
        "It assumes how often you buy and how much you spend are unrelated. They're mildly related. "
        "Because the relation is positive, it under-predicts the heaviest buyers — which partly CANCELS "
        "the first problem rather than adding to it.\n\n"
        "And my favourite because it's so concrete: the busiest customer made 200 repeat purchases in 65 "
        "weeks. That's not a person buying gifts, that's a business restocking. A wholesale buyer inside "
        "a consumer model breaks the assumptions, and I flag it rather than quietly deleting the row."))
bullets(s, [
 ("It assumes people don't change over time — they do",
  "Over-predicts middle-of-the-road customers by 20–30%. The top customers, where the budget goes, stay accurate."),
 ("It assumes how often and how much are unrelated — they're mildly related",
  "Because the relation is positive, it under-predicts the heaviest buyers — partly cancelling the problem above."),
 ("One shop, one country, two years",
  "The exact figures are specific to this business. The reasoning about uncertainty is general."),
 ("Wholesale buyers are sitting inside a consumer model",
  "The busiest customer made 200 repeat purchases in 65 weeks. That is restocking, not gift-buying."),
], top=In(2.0), size=16, gap=6)
box(s, [("The two biggest problems push in opposite directions — so they partly cancel rather than compounding.",
         16.5, True, NAVY)], In(6.0), In(0.56))

# ════════════════════ 28 NEXT
s = slide("Where this goes next", kicker="Conclusion",
 notes=("~1.5 min, then questions. Three things I'd do with more time.\n\n"
        "Group customers by how they behave rather than where they live — a wholesaler in London "
        "probably resembles a wholesaler in Paris more than a gift-buyer down the road. Country is a "
        "weak proxy.\n\n"
        "Build a decision where profit ISN'T a straight line — a hard budget cap, or genuine risk "
        "aversion. That's the proper test my third question couldn't be.\n\n"
        "And let customers change over time, since that's the assumption I can most clearly show is "
        "broken.\n\n"
        "To close: this started with a shop that can't see who has left. It ends with a model that "
        "doesn't pretend to either — it's honest about the uncertainty, and clear about when that "
        "honesty is worth paying for. Thank you."))
bullets(s, [
 ("Group customers by behaviour, not geography",
  "A wholesaler in London resembles one in Paris more than a gift-buyer nearby. Country is a weak proxy."),
 ("Build a decision where profit isn't a straight line",
  "A hard budget cap, or genuine risk aversion — the proper test my third question couldn't be."),
 ("Let customers change over time",
  "The assumption I can most clearly show is broken, and the one most likely to matter in practice."),
], top=In(2.1), size=17)
box(s, [("This began with a shop that can't see who has left.", 16, True, NAVY),
        ("It ends with a model that doesn't pretend to either — and is clear about when that honesty is worth paying for.",
         16, False, INK)], In(5.4), In(1.0))

# ════════════════════ 29 THANK YOU
s = prs.slides.add_slide(BLANK); _n["i"] += 1
rect(s, 0, 0, W, H, NAVY)
t = tb(s, In(1.4), In(2.9), In(10.5), In(2.0))
put(t, "Thank you", 44, True, WHITE, 10, first=True)
put(t, "I welcome your questions.", 20, False, C(0xBF,0xC9,0xD4), 16)
put(t, "Devansh   ·   Customer Lifetime Value Prediction Using Bayesian Methods",
    14, False, C(0x8E,0x9E,0xAE), 0)
rect(s, In(1.4), In(2.5), In(1.6), Pt(3.5), ORANGE)

prs.save(OUT)
print("saved %s · %d slides" % (OUT, len(prs.slides._sldIdLst)))
