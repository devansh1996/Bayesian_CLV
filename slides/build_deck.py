"""Build the thesis defence deck (16:9, 25 min)."""
from pptx import Presentation
from pptx.util import Inches as In, Pt, Emu
from pptx.dml.color import RGBColor as C
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
import os

NAVY, ORANGE, TEAL = C(0x2E,0x40,0x57), C(0xE7,0x6F,0x51), C(0x1D,0x7A,0x5F)
INK, MUTE, LINE, SOFT = C(0x22,0x22,0x22), C(0x5A,0x5A,0x5A), C(0xD8,0xD8,0xD8), C(0xF1,0xEF,0xE8)
WHITE = C(0xFF,0xFF,0xFF)
FONT = "Calibri"
W, H = In(13.333), In(7.5)
OUT = "outputs/Defence_CLV_Bayesian.pptx"
FIG, SLD = "outputs/figures/", "outputs/slides/"

prs = Presentation(); prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]
_n = {"i": 0}

def tb(slide, l, t, w, h, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(l, t, w, h); tf = box.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.paragraphs[0].alignment = align
    return tf

def put(tf, text, size=18, bold=False, color=INK, space_after=8, first=False,
        align=None, italic=False, bullet=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    if align: p.alignment = align
    p.space_after = Pt(space_after)
    r = p.add_run(); r.text = ("•  " if bullet else "") + text
    r.font.size, r.font.bold, r.font.italic = Pt(size), bold, italic
    r.font.color.rgb, r.font.name = color, FONT
    return p

def rect(slide, l, t, w, h, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line: s.line.color.rgb = line; s.line.width = Pt(1)
    else: s.line.fill.background()
    s.shadow.inherit = False
    return s

def slide(title, kicker=None, notes=None, number=True):
    s = prs.slides.add_slide(BLANK)
    _n["i"] += 1
    if kicker:
        t = tb(s, In(0.85), In(0.42), In(11.6), In(0.3))
        put(t, kicker.upper(), 12.5, True, ORANGE, 2, first=True)
    t = tb(s, In(0.85), In(0.70) if kicker else In(0.60), In(11.6), In(0.8))
    put(t, title, 30, True, NAVY, 0, first=True)
    rect(s, In(0.85), In(1.52), In(1.5), Pt(3.2), ORANGE)
    if number:
        f = tb(s, In(11.9), In(6.92), In(0.6), In(0.3), align=PP_ALIGN.RIGHT)
        put(f, str(_n["i"]), 11, False, C(0x9A,0x9A,0x9A), 0, first=True)
        g = tb(s, In(0.85), In(6.92), In(8.0), In(0.3))
        put(g, "Bayesian CLV in non-contractual e-commerce", 10, False, C(0xAA,0xAA,0xAA), 0, first=True)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s

def section(title, sub, notes=None):
    s = prs.slides.add_slide(BLANK); _n["i"] += 1
    rect(s, 0, 0, W, H, NAVY)
    t = tb(s, In(1.4), In(3.0), In(10.5), In(1.6))
    put(t, title, 40, True, WHITE, 6, first=True)
    put(t, sub, 18, False, C(0xBF,0xC9,0xD4), 0)
    rect(s, In(1.4), In(2.6), In(1.6), Pt(3.5), ORANGE)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s

def picture(s, path, top, max_w=In(11.0), max_h=In(4.1), left=None):
    iw, ih = Image.open(path).size
    w, h = max_w, Emu(int(max_w * ih / iw))
    if h > max_h: h = max_h; w = Emu(int(max_h * iw / ih))
    l = left if left is not None else Emu(int((W - w)/2))
    return s.shapes.add_picture(path, l, top, width=w, height=h)

def takeaway(s, text, top=In(6.05)):
    rect(s, In(0.85), top, In(11.6), In(0.62), SOFT)
    rect(s, In(0.85), top, Pt(4), In(0.62), ORANGE)
    t = tb(s, In(1.08), top + In(0.10), In(11.2), In(0.45), anchor=MSO_ANCHOR.MIDDLE)
    put(t, text, 15, True, NAVY, 0, first=True)

def bullets(s, items, top=In(1.95), left=In(0.95), width=In(11.4), size=18, gap=11):
    avail = max(In(0.5), H - top - In(0.15))      # never declare a box past the slide edge
    tf = tb(s, left, top, width, min(In(4.0), avail))
    for i, it in enumerate(items):
        if isinstance(it, tuple):
            head, sub = it
            put(tf, head, size, True, NAVY, 2, first=(i == 0))
            put(tf, sub, size-3, False, MUTE, gap+2)
        else:
            put(tf, it, size, False, INK, gap, first=(i == 0), bullet=True)
    return tf

# ══════════════════════════════════ 1 TITLE
s = prs.slides.add_slide(BLANK); _n["i"] += 1
rect(s, 0, 0, W, In(0.22), NAVY); rect(s, 0, In(0.30), W, Pt(2), ORANGE)
t = tb(s, In(1.0), In(1.75), In(11.3), In(2.0))
put(t, "Customer Lifetime Value Prediction", 42, True, NAVY, 4, first=True)
put(t, "Using Bayesian Methods", 42, True, NAVY, 14)
put(t, "A probabilistic approach to non-contractual customer-base analysis in e-commerce", 17, False, MUTE, 0, italic=True)
rect(s, In(1.0), In(4.25), In(2.0), Pt(3), ORANGE)
t = tb(s, In(1.0), In(4.55), In(11.0), In(1.6))
put(t, "Devansh", 20, True, INK, 8, first=True)
put(t, "Master's Thesis  ·  M.Sc.", 14.5, False, MUTE, 4)
put(t, "First Supervisor: Professor Dr. Tilo Wendler    ·    Second Supervisor: Dr. Guido Möser", 13.5, False, MUTE, 0)
rect(s, 0, In(7.28), W, In(0.22), NAVY)
s.notes_slide.notes_text_frame.text = (
 "~30 s. Good morning. My thesis asks whether a Bayesian treatment of customer-lifetime-value "
 "models earns its cost in a non-contractual e-commerce setting. I'll cover the research questions, "
 "the methodology I developed, the three findings, and what they mean for the field. 25 minutes.")

# ══════════════════════════════════ 2 PROBLEM
s = slide("The core difficulty: customers never say goodbye", kicker="Motivation",
 notes=("~1.5 min. In a contract business, churn is observed — the customer cancels. In e-commerce "
        "nobody announces departure; they simply stop buying. So a 15-week silence is ambiguous: a slow "
        "but loyal customer, or someone already gone. Extrapolating past frequency systematically "
        "overvalues the departed. The attrition state is LATENT — this is why the problem is inherently "
        "probabilistic, and it is the hinge of the whole thesis."))
bullets(s, [
 ("Contractual settings are easy", "The customer cancels — churn is observed, survival analysis applies."),
 ("Non-contractual settings are not", "No cancellation signal. Silence is ambiguous by construction."),
 ("The same 15-week silence can mean two opposite things",
  "A slow but active buyer  ·  or a customer who has already defected."),
], top=In(1.95))
rect(s, In(0.95), In(4.85), In(11.4), In(0.95), SOFT)
t = tb(s, In(1.25), In(4.98), In(10.9), In(0.75), anchor=MSO_ANCHOR.MIDDLE)
put(t, "Attrition is a latent state  →  the problem is irreducibly probabilistic,", 18, True, NAVY, 2, first=True)
put(t, "not merely a prediction problem.", 18, True, NAVY, 0)

# ══════════════════════════════════ 3 GAP
s = slide("Three limitations of existing approaches", kicker="Research gap",
 notes=("~1.5 min. Rather than survey the literature, I'll name the three gaps that motivated the work. "
        "ONE: uncertainty is either absent (RFM, deterministic formulas) or asserted but not demonstrated "
        "to be calibrated. TWO: customer bases are unevenly distributed across segments, yet models are "
        "fitted to one homogeneous population. THREE: where a distribution does exist, it is collapsed to "
        "a number before the decision — the very information that distinguishes a probabilistic model is "
        "discarded at the final step. Each gap becomes one research question."))
bullets(s, [
 ("1 · Inference — uncertainty is produced but rarely shown to be calibrated",
  "RFM and deterministic formulas give no confidence measure; ML retrofits it; BTYD is fitted by maximum likelihood."),
 ("2 · Structure — segment imbalance is pervasive, the pooling question rarely tested",
  "Applied studies fit a single homogeneous population; small markets are noisy or absorbed into the average."),
 ("3 · Decisions — posteriors are computed, then discarded",
  "The distribution is collapsed to a point estimate before the targeting decision is made."),
], top=In(2.0))
takeaway(s, "Each gap maps one-to-one onto a research question — and onto a dedicated element of the empirical design.", In(5.85))

# ══════════════════════════════════ 4 RQs
s = slide("Research questions and hypotheses", kicker="Aims",
 notes=("~1.5 min. Three questions. RQ1: does a Bayesian BG/NBD plus Gamma-Gamma match or beat RFM and "
        "XGBoost on out-of-sample accuracy AND deliver calibrated uncertainty? RQ2: does hierarchical "
        "partial pooling across country segments reduce error for small markets — tested against BOTH "
        "extremes, complete pooling and no pooling. RQ3: does targeting by the posterior probability that "
        "CLV exceeds the campaign cost beat ranking by the point estimate? Note RQ3 is a decision question, "
        "not a prediction question — that distinction matters later."))
for i, (tag, q, sub) in enumerate([
 ("RQ1", "Accuracy with calibrated uncertainty",
  "Does the Bayesian BG/NBD + Gamma-Gamma match or exceed RFM and XGBoost — and are its intervals calibrated?"),
 ("RQ2", "Hierarchical partial pooling",
  "Does partial pooling across country segments beat BOTH complete pooling and no pooling in sparse markets?"),
 ("RQ3", "Decision-theoretic targeting",
  "Does targeting by P(CLV > c) realise more value than ranking by point-estimate CLV?")]):
    y = In(2.05 + i*1.42)
    rect(s, In(0.95), y, In(1.15), In(1.05), NAVY)
    t = tb(s, In(0.95), y + In(0.26), In(1.15), In(0.5), align=PP_ALIGN.CENTER)
    put(t, tag, 21, True, WHITE, 0, first=True)
    t = tb(s, In(2.35), y + In(0.10), In(10.1), In(0.95))
    put(t, q, 20, True, NAVY, 3, first=True)
    put(t, sub, 15, False, MUTE, 0)
takeaway(s, "Hypotheses H1–H3 state the expected answer to each; the thesis tests all three empirically.", In(6.35))

# ══════════════════════════════════ 5 DATA
s = slide("Data and research design", kicker="Empirical setting",
 notes=("~1.5 min. UCI Online Retail II — a real UK giftware retailer, about a million line items, "
        "December 2009 to December 2011. After cleaning: 4,522 customers. The design is a strict TEMPORAL "
        "calibration-holdout split at 1 March 2011 — models see only the calibration window and are scored "
        "on a 40.4-week future they never saw. Temporal, not random, so there is no leakage from the future. "
        "A third of customers are one-time buyers, which is exactly the hard case for latent attrition. "
        "Note the segment imbalance: 4,152 UK against 74 Germany and 54 France — that imbalance is what "
        "makes RQ2 worth asking."))
for i,(k,v,c) in enumerate([("4,522","customers after cleaning",NAVY),("40.4 wks","holdout horizon",NAVY),
                            ("33%","one-time buyers",ORANGE),("4,152 / 74 / 54","UK / Germany / France",ORANGE)]):
    x = In(0.95 + i*2.95)
    rect(s, x, In(2.0), In(2.7), In(1.25), SOFT)
    t = tb(s, x, In(2.18), In(2.7), In(1.0), align=PP_ALIGN.CENTER)
    put(t, k, 25, True, c, 2, first=True)
    put(t, v, 12.5, False, MUTE, 0, align=PP_ALIGN.CENTER)
bullets(s, [
 ("Temporal calibration–holdout split (cut-off 1 March 2011)",
  "Every model is fitted on the past only and scored on a future it has never seen — no look-ahead leakage."),
 ("All models receive identical inputs and are scored on identical targets",
  "Differences in performance are attributable to the models, not to the data partition."),
], top=In(3.65))
takeaway(s, "Pronounced segment imbalance + one-third one-time buyers = a genuinely hard, realistic test bed.", In(5.95))

# ══════════════════════════════════ 6 SECTION: METHOD
section("Methodology", "The generative model, Bayesian estimation, and three developments",
 notes="~10 s. Now the methodology — the part I developed.")

# ══════════════════════════════════ 7 MODEL
s = slide("A generative model of customer behaviour", kicker="Methodology · 1",
 notes=("~2 min. Rather than regress future value on features, the BTYD approach writes down HOW customers "
        "behave. While active, a customer buys at a Poisson rate lambda. After each purchase they may drop "
        "out with probability p — a coin flip. Both vary across the population: lambda is Gamma-distributed, "
        "p is Beta-distributed. That is the BG/NBD. It is silent on spend, so the Gamma-Gamma model supplies "
        "monetary value, with each customer's average basket drawn from a Gamma whose own rate varies. "
        "CLV is the product. The crucial property: because dropout is IN the model, the model INTERPRETS "
        "silence rather than extrapolating through it."))
bullets(s, [
 ("BG/NBD — purchase frequency and latent dropout",
  "While active, purchases arrive as a Poisson process (rate λ). After each purchase, dropout occurs with probability p."),
 ("Heterogeneity is built in, not assumed away",
  "λ ~ Gamma(r, α) across customers   ·   p ~ Beta(a, b) across customers."),
 ("Gamma-Gamma — monetary value",
  "Average transaction value is Gamma-distributed, with a customer-specific rate drawn from a second Gamma."),
], top=In(1.95), size=17.5)
rect(s, In(0.95), In(5.0), In(11.4), In(0.85), SOFT)
t = tb(s, In(1.25), In(5.12), In(10.9), In(0.65), anchor=MSO_ANCHOR.MIDDLE)
put(t, "CLV  =  E[transactions]  ×  E[spend per transaction]      — and in the Bayesian form, each term is a distribution",
    15.5, True, NAVY, 0, first=True)
takeaway(s, "Because dropout is part of the model, the model interprets silence instead of extrapolating through it.", In(6.1))

# ══════════════════════════════════ 8 BAYES
s = slide("Why Bayesian, and not maximum likelihood?", kicker="Methodology · 2",
 notes=("~2 min. These models are conventionally fitted by maximum likelihood, which returns a point "
        "estimate and at best an asymptotic standard error. The decisive limitation is not that it reports "
        "less uncertainty — it is that a point estimate cannot be PROPAGATED. RQ3 needs a full distribution "
        "over each customer's value to compute P(CLV > cost). The Bayesian treatment targets the full "
        "posterior. For these models it has no closed form, so I estimate it by Hamiltonian Monte Carlo with "
        "the No-U-Turn Sampler. Intuition: HMC rolls a puck across a frictionless landscape whose valleys are "
        "high-probability regions — one flick of momentum travels a long way and still lands somewhere "
        "plausible. Four chains, 1,000 draws, R-hat below 1.002, no divergences."))
bullets(s, [
 ("Maximum likelihood gives a number; decisions need a distribution",
  "A point estimate cannot be propagated into the targeting decision that RQ3 poses."),
 ("The posterior is analytically intractable → Hamiltonian Monte Carlo (NUTS)",
  "Intuition: a puck rolling across a frictionless landscape whose valleys are the high-probability regions."),
 ("Uncertainty then flows end-to-end",
  "Parameters → predicted transactions → predicted spend → CLV → the marketing decision itself."),
], top=In(1.95), size=17.5)
for i,(k,v) in enumerate([("R̂ ≤ 1.002","convergence"),("ESS > 1,100","effective samples"),("0","divergent transitions")]):
    x = In(0.95 + i*3.85)
    rect(s, x, In(5.05), In(3.6), In(1.0), SOFT)
    t = tb(s, x, In(5.20), In(3.6), In(0.8), align=PP_ALIGN.CENTER)
    put(t, k, 21, True, TEAL, 2, first=True)
    put(t, v, 12.5, False, MUTE, 0, align=PP_ALIGN.CENTER)
takeaway(s, "Inference is trustworthy before any result is interpreted — diagnostics come first.", In(6.25))

# ══════════════════════════════════ 9 DEVELOPMENTS
s = slide("Three methodological developments", kicker="Methodology · 3",
 notes=("~2 min. This is the methodological contribution. ONE: an end-to-end Bayesian implementation "
        "evaluated CALIBRATION-FIRST — I test whether the intervals actually cover, which the BTYD "
        "literature validates expectations but not intervals. TWO: a THREE-way pooling comparison — the "
        "literature benchmarks hierarchical models against complete pooling only; testing both extremes "
        "changes what you can conclude. THREE: a decision-theoretic targeting simulation on realised "
        "holdout outcomes, which is where I found the pitfall I'll show you in a moment. Also a "
        "leakage-safe benchmark: XGBoost is supervised, so it cannot train on the window it is scored on — "
        "I built a nested inner split for it."))
bullets(s, [
 ("1 · Calibration-first evaluation",
  "Not only 'is the prediction accurate?' but 'do the 90% intervals actually contain 90% of outcomes?' — coverage, CRPS, interval width."),
 ("2 · A three-way pooling comparison",
  "Complete pooling vs partial pooling vs no pooling. The literature usually tests only against complete pooling."),
 ("3 · A decision-theoretic targeting simulation",
  "Rules are scored on realised holdout value under a swept intervention cost — not on predictive error."),
 ("Leakage-safe benchmarking",
  "The supervised baseline is trained on a nested inner split, so the evaluation holdout stays unseen by every model."),
], top=In(1.95), size=17, gap=9)

# ══════════════════════════════════ 10 SECTION: FINDINGS
section("Findings", "Three hypotheses, three different kinds of answer",
 notes="~10 s. To the findings.")

# ══════════════════════════════════ 11 H1 ACCURACY
s = slide("H1 — accuracy and ranking", kicker="Finding 1a",
 notes=("~2 min. On point accuracy the Bayesian model leads: transaction MAE 1.74 against 2.12 for XGBoost, "
        "2.33 RFM, 3.11 naive. But the decisive panel is on the right. NDCG@100 measures whether the TOP of "
        "the ranking is right — and marketing budgets are spent on the top of a list, not its average member. "
        "0.91 against 0.53. Why? The generative model borrows strength across the customer base, so sparse "
        "histories still get sensibly ordered; XGBoost minimises average error and is comparatively "
        "indifferent to ordering inside the small high-value tail. IMPORTANT CAVEAT, and I want to be "
        "explicit: the leakage-safe design gives XGBoost a shorter supervision window, so part of this gap "
        "is that handicap. I read the NDCG margin as an UPPER BOUND on the Bayesian advantage."))
picture(s, SLD+"accuracy.png", In(1.95), max_w=In(11.4), max_h=In(3.9))
takeaway(s, "Budgets are spent on the top of the ranking — that is where the advantage is largest (and an upper bound).", In(6.1))

# ══════════════════════════════════ 12 H1 CALIBRATION
s = slide("H1 — calibrated uncertainty", kicker="Finding 1b",
 notes=("~2 min. This is the claim I regard as least contestable. A nominal 90% predictive interval "
        "contained the realised outcome 89.3% of the time. The model's stated confidence is trustworthy. "
        "And note the asymmetry: you can only TEST calibration on a model that makes distributional claims "
        "in the first place — neither RFM nor standard XGBoost makes any. So this is not a narrow win on a "
        "metric; it is a categorical difference in what the model delivers. Managerially this is what lets "
        "you commit budget only when the LOWER credible bound clears the campaign cost — fixing your "
        "tolerance for wasted spend in advance rather than discovering it afterwards."))
for i,(k,v,c) in enumerate([("89.3%","empirical coverage\n(nominal 90%)",TEAL),
                            ("1.22","CRPS\n(accuracy + calibration)",NAVY),
                            ("0.71","P(alive) AUC\nlatent activity recovered",NAVY)]):
    x = In(0.95 + i*3.85)
    rect(s, x, In(2.05), In(3.6), In(1.5), SOFT)
    t = tb(s, x, In(2.25), In(3.6), In(1.25), align=PP_ALIGN.CENTER)
    put(t, k, 30, True, c, 3, first=True)
    for ln in v.split("\n"): put(t, ln, 12.5, False, MUTE, 0, align=PP_ALIGN.CENTER)
bullets(s, [
 ("Calibration can only be tested on a model that makes distributional claims",
  "Neither the RFM heuristic nor standard XGBoost makes any — so this is a categorical difference, not a narrow win."),
 ("Managerial form: commit budget when the LOWER credible bound clears the cost",
  "The firm fixes its tolerance for wasted spend in advance instead of discovering it after the campaign."),
], top=In(3.85), size=17)
takeaway(s, "Trustworthy confidence — not merely a lower error — is what the Bayesian treatment adds.", In(6.15))

# ══════════════════════════════════ 13 WORKED EXAMPLE
s = slide("One customer, end to end", kicker="Finding 1c · worked example",
 notes=("~2 min. Customer 14817 makes it concrete. Four repeat purchases, last seen 33 weeks into a "
        "49-week window, average basket £526. The model returns: probably still alive, 0.88. Expected "
        "2.81 transactions over the holdout. Expected CLV £1,364 — with a very tight interval, £1,326 to "
        "£1,401. But that tight band reflects only PARAMETER uncertainty. The distribution of what this "
        "customer will ACTUALLY do — the posterior predictive, in blue — runs from £0 to £2,888, with real "
        "mass at zero because he might simply not come back. Ask the targeting question at a £600 cost and "
        "the two disagree completely: the narrow orange spike says probability 1.00, a false certainty; "
        "the predictive says 0.77, acknowledging a one-in-four chance of not covering the cost. He actually "
        "returned twice and spent £1,010 — inside the predictive interval."))
picture(s, FIG+"worked_example_customer.png", In(1.90), max_w=In(9.4), max_h=In(4.0))
takeaway(s, "Same customer, same model: P(CLV > £600) = 1.00 from the expectation, 0.77 from the predictive. Realised: £1,010.", In(6.05))

# ══════════════════════════════════ 14 XGB
s = slide("Why the strongest baseline trails", kicker="Finding 1d",
 notes=("~1.5 min. XGBoost got 24 engineered features — RFM, ratios, inter-purchase-time statistics, "
        "day-of-week fractions, spend trend. Look where the gain concentrates: frequency and purchase rate "
        "alone account for about 45%. Given 24 features, the learner spends most of its capacity "
        "REDISCOVERING the recency-frequency signal that the generative model encodes structurally, by "
        "construction. The engineered behavioural extras add remarkably little. This is consistent with "
        "Chamberlain et al. — learned representations win at industrial scale with rich covariates; here, "
        "with a few thousand customers and bare transaction summaries, structure beats flexibility."))
picture(s, FIG+"xgboost_feature_importance.png", In(1.95), max_w=In(9.0), max_h=In(3.95))
takeaway(s, "With 24 features, the learner mostly rediscovers what the generative model assumes by construction.", In(6.1))

# ══════════════════════════════════ 15 H2
s = slide("H2 — partial pooling across segments", kicker="Finding 2",
 notes=("~2.5 min. H2 predicted partial pooling would beat BOTH extremes. Against no pooling it does — "
        "clearly, in every small segment. Against complete pooling it does not. But look at the PATTERN, "
        "not any single bar. No pooling is worst in Germany and France, where sparse data overfit. Complete "
        "pooling is worst in 'Other' — the one behaviourally distinct segment — where imposing global "
        "parameters suppresses a real difference. Partial pooling is NEVER the worst anywhere, and has the "
        "lowest error aggregated across the small segments. So its contribution here is ADAPTIVITY: it "
        "approximates whichever extreme is right for a given segment without the analyst knowing in advance "
        "which that is. Two honest qualifications: the differences are small, and the between-segment prior "
        "was tightened for sampling stability, which mechanically limits how far partial pooling can depart "
        "from complete pooling. So H2 is a PRIOR-CONSTRAINED test, not a decisive one."))
picture(s, SLD+"h2_pooling.png", In(1.90), max_w=In(10.6), max_h=In(3.5))
_c = tb(s, In(0.95), In(5.48), In(11.4), In(0.4), align=PP_ALIGN.CENTER)
put(_c, "Never the worst in any segment  ·  lowest aggregated error across the small segments "
        "(1.746 vs 1.755 no pooling / 1.757 complete pooling)", 14.5, False, MUTE, 0, first=True,
    align=PP_ALIGN.CENTER)
takeaway(s, "Verdict: partially supported — adaptivity rather than uniform gain, and conditional on a deliberately tight prior.", In(6.05))

# ══════════════════════════════════ 16 H2 MECHANISM
s = slide("The mechanism: shrinkage in proportion to ignorance", kicker="Finding 2b",
 notes=("~1 min. Here is the mechanism in the parameters themselves. The per-segment posterior for the "
        "BG/NBD shape parameter r: small segments have WIDE posteriors pulled toward the global value; the "
        "data-rich UK segment is estimated precisely and sits essentially at its no-pooling value. That is "
        "the classic shrinkage signature — regularisation applied in proportion to how little you know. "
        "Theoretically this is exactly Efron and Morris: shrinkage guarantees improvement in AGGREGATE "
        "error, not a win in every group. So our result is the textbook behaviour, not an anomaly."))
picture(s, FIG+"hierarchical_shrinkage_r.png", In(1.95), max_w=In(8.2), max_h=In(3.95))
takeaway(s, "Efron–Morris guarantees aggregate improvement, not a win in every group — the result is textbook, not anomalous.", In(6.1))

# ══════════════════════════════════ 17 H3
s = slide("H3 — decision-theoretic targeting", kicker="Finding 3",
 notes=("~2 min. H3 predicted that targeting by the posterior probability of clearing the cost would beat "
        "ranking by the point estimate. It does not. The two lines sit on top of each other across every "
        "targeting depth and every cost from £100 to £2,000 — at the headline £600 and 20% depth, £3.82M "
        "versus £3.89M, a 1.7% shortfall. On reflection this is the theoretically EXPECTED result, and "
        "recognising why sharpens the theory. Total captured value is LINEAR in outcomes, and for a linear "
        "objective the posterior mean is a sufficient basis for ranking. The tails carry no extra "
        "information that a linear objective rewards. The probability rule encodes risk aversion — and a "
        "criterion that counts only aggregate value gives no credit for risk aversion. So the finding "
        "DELIMITS the decision-theoretic case rather than undermining it."))
picture(s, SLD+"h3_targeting.png", In(1.95), max_w=In(10.4), max_h=In(3.9))
takeaway(s, "For a LINEAR objective the posterior mean is already sufficient — the posterior's tails earn nothing here.", In(6.1))

# ══════════════════════════════════ 18 ★ PITFALL
s = slide("The pitfall: which posterior?", kicker="Methodological finding ★",
 notes=("~2.5 min — this is the slide I would most like you to remember. Diagnosing WHY the naive rule "
        "fails produced a result more consequential than the hypothesis test. There are two distinct "
        "distributions and both are legitimately called 'the posterior'. The posterior of EXPECTED CLV "
        "reflects only parameter uncertainty — which on a few thousand customers is tiny. So P(CLV > cost) "
        "collapses to 0 or 1 for 96% of customers, as you see on the left. The ranking degenerates into "
        "arbitrary tie-breaking and the rule appears to fail catastrophically — for purely MECHANICAL "
        "reasons that have nothing to do with decision theory. Computed from the posterior PREDICTIVE — the "
        "distribution of what the customer will actually DO — it is graded and usable. The cost of getting "
        "this wrong: hit rate falls from 0.85 to 0.62, wasted spend nearly TRIPLES, £55,040 to £144,738. "
        "A practical diagnostic: inspect the distribution of your probabilities. If most customers sit at "
        "0 or 1, you are using the wrong distribution. This applies to ANY model with distributional "
        "output, including the neural and covariate-rich extensions."))
picture(s, FIG+"prob_expectation_vs_predictive.png", In(1.85), max_w=In(10.2), max_h=In(3.3))
t = tb(s, In(0.95), In(5.28), In(11.4), In(0.7))
put(t, "Getting this wrong:  hit rate 0.85 → 0.62     ·     wasted spend £55,040 → £144,738  (≈ 3×)",
    17, True, ORANGE, 0, first=True, align=PP_ALIGN.CENTER)
takeaway(s, "Decisions about realised outcomes must use the posterior PREDICTIVE — never the posterior of an expectation.", In(6.05))

# ══════════════════════════════════ 19 VERDICTS
s = slide("Summary of the three hypotheses", kicker="Findings in the round",
 notes=("~1.5 min. Three different kinds of answer, and together they form a pattern rather than a mixed "
        "scorecard. The Bayesian treatment delivered DECISIVELY where the quantity of interest is itself a "
        "distribution — uncertainty and latent activity. It delivered ROBUSTNESS, not improvement, where "
        "the structural assumption it relaxes turned out to be largely true of the data. And it delivered "
        "NO advantage where the decision objective is linear enough that a point summary already suffices. "
        "The unifying lesson: the value of a posterior is realised in proportion to how much of it the "
        "question actually uses. That is a more discriminating conclusion than a blanket endorsement of "
        "Bayesian methods would be."))
picture(s, SLD+"verdicts.png", In(1.95), max_w=In(11.0), max_h=In(2.6))
rect(s, In(0.95), In(4.75), In(11.4), In(1.15), SOFT)
t = tb(s, In(1.3), In(4.92), In(10.8), In(0.9), anchor=MSO_ANCHOR.MIDDLE)
put(t, "The value of a posterior is realised in proportion to how much of it the question actually uses.", 19, True, NAVY, 3, first=True)
put(t, "Decisive where the answer is a distribution  ·  robust where structure is already true  ·  neutral where the objective is linear.",
    14, False, MUTE, 0)

# ══════════════════════════════════ 20 SECTION: IMPACT
section("Impact and best practices", "What the field should take from this",
 notes="~10 s.")

# ══════════════════════════════════ 21 IMPACT
s = slide("Impact on the research area", kicker="Contribution",
 notes=("~2 min. Three contributions. ONE — for the BTYD literature: that tradition validates the accuracy "
        "of EXPECTATIONS; I extend validation to the COVERAGE of intervals, an axis it has left untested, "
        "and show that being Bayesian is not by itself sufficient for calibrated uncertainty. TWO — for "
        "hierarchical marketing models: testing both extremes reframes the case for partial pooling as RISK "
        "CONTROL rather than expected accuracy, and shows the pooling question cannot be answered "
        "independently of the prior, which studies should state. THREE — and most transferable — the "
        "expectation-versus-predictive distinction is a general hazard for any model producing "
        "distributional output, including the neural and covariate-rich extensions of customer-base "
        "analysis. Plus the boundary condition: posterior-based decision rules pay only under non-linear "
        "objectives, which the literature advocating such rules does not articulate."))
bullets(s, [
 ("Extends BTYD validation from accuracy to calibration",
  "The tradition validates expectations; coverage of predictive intervals has been left untested. Being Bayesian ≠ being calibrated."),
 ("Reframes hierarchical pooling as risk control, not expected gain",
  "Testing both extremes shows partial pooling buys 'never worst'. And the pooling question is not answerable independently of the prior."),
 ("A transferable methodological warning",
  "Expectation-vs-predictive applies to ANY model with distributional output — including neural and covariate-rich BTYD extensions."),
 ("A boundary condition for decision-theoretic marketing analytics",
  "Posterior-based rules pay only under non-linear objectives — a limit the advocacy literature does not state."),
], top=In(1.95), size=17, gap=9)

# ══════════════════════════════════ 22 BEST PRACTICE
s = slide("Best practices for applied CLV modelling", kicker="Practitioner guidance",
 notes=("~1.5 min. Condensed, actionable guidance. Validate coverage, not just error — a model whose "
        "intervals do not cover is worse than one that admits it has none. Use the predictive distribution "
        "for any statement about realised outcomes, and use the 0/1 pile-up as your diagnostic. Benchmark "
        "supervised models leakage-safely, and then weight the comparison honestly. Test pooling against "
        "both extremes, and report the prior scale, because it bounds what you can conclude. And match the "
        "decision rule to the objective — do not over-engineer: if the objective is linear, rank by expected "
        "value and stop."))
bullets(s, [
 "Validate coverage, not only error — an uncalibrated interval is worse than an honest absence of one",
 "Use the posterior PREDICTIVE for any statement about realised outcomes; diagnose by checking for a 0/1 pile-up",
 "Train supervised baselines leakage-safely — and then weight the comparison for the handicap you imposed",
 "Test pooling against BOTH extremes, and report the between-segment prior scale: it bounds the conclusion",
 "Match the decision rule to the objective — linear objective → rank by expected value and stop",
 "Check sampler geometry first: non-centred parameterisation, prior scales matched to the data's units",
], top=In(1.95), size=17, gap=14)

# ══════════════════════════════════ 23 LIMITATIONS
s = slide("Limitations — and which way they bias the result", kicker="Honest assessment",
 notes=("~1.5 min. I assess each limitation by DIRECTION of bias, not just existence. Stationarity is "
        "violated — we over-predict 20-30% for mid-frequency customers, so absolute CLV is biased UP in the "
        "middle; but the top deciles, where targeting happens, remain calibrated, and the bias hits all "
        "pooling specifications equally so H2 is undisturbed. Single temporal split, no formal tests — the "
        "large H1 margins survive that, the third-decimal H2 differences should be read as descriptive. "
        "And note the two design biases run in OPPOSITE directions: the tight prior biases H2 toward the "
        "null, while the XGBoost inner split biases H1 toward us. So the design errs conservative in one "
        "place and generous in another rather than systematically favouring the Bayesian approach."))
bullets(s, [
 ("Stationarity is violated — 20–30% over-prediction for mid-frequency customers",
  "Biases absolute CLV upward in the middle; top deciles stay calibrated, and all pooling specifications are affected equally."),
 ("A single temporal split, no formal significance tests",
  "Large H1 margins survive this; the third-decimal H2 differences are descriptive patterns, not established effects."),
 ("The two design biases run in OPPOSITE directions",
  "Tight prior → biases H2 toward the null.   XGBoost inner split → biases H1 in our favour.   The design does not systematically flatter the Bayesian model."),
 ("A 40.4-week revenue proxy, not lifetime discounted cash flow",
  "A monotone transformation — rankings and all model comparisons are unaffected."),
], top=In(1.95), size=16.5, gap=8)

# ══════════════════════════════════ 24 OUTLOOK
s = slide("Summary and outlook", kicker="Conclusion",
 notes=("~2 min. To summarise: CLV in non-contractual settings is a problem of reasoning about an "
        "unobservable state. A Bayesian treatment of a generative model delivers accurate and — crucially "
        "— CALIBRATED predictions; partial pooling buys robustness under segment imbalance; and the "
        "posterior earns its keep only where the objective uses it. The broader lesson is that how "
        "confident a model is can matter as much as what it predicts. Looking forward: a prior-sensitivity "
        "analysis is the priority for RQ2; relaxing stationarity and adding covariates are the natural "
        "model extensions; and the real closing of the loop would be a live A/B test rather than a holdout "
        "simulation — moving from prediction to uplift, modelling the causal effect of the intervention "
        "rather than the level of value. Thank you — I'm happy to take questions."))
bullets(s, [
 ("What the thesis establishes",
  "A Bayesian generative treatment gives accurate AND calibrated CLV; pooling buys robustness; the posterior pays only where the objective uses it."),
], top=In(1.95), size=17.5)
rect(s, In(0.95), In(3.1), In(11.4), Pt(1.5), LINE)
t = tb(s, In(0.95), In(3.35), In(11.4), In(0.4))
put(t, "OUTLOOK", 13, True, ORANGE, 8, first=True)
bullets(s, [
 "Prior-sensitivity analysis over the between-segment scale — the priority extension for RQ2",
 "Relax stationarity (time-varying / seasonal) and add a covariate layer to the BG/NBD and Gamma-Gamma parameters",
 "Validate the targeting rule in a live A/B test — moving from prediction to uplift (causal effect, not level)",
], top=In(3.80), size=16.5, gap=13)
takeaway(s, "How confident a model is can matter as much as what it predicts.", In(5.75))

# ══════════════════════════════════ 25 THANKS
s = prs.slides.add_slide(BLANK); _n["i"] += 1
rect(s, 0, 0, W, H, NAVY)
t = tb(s, In(1.4), In(2.75), In(10.5), In(2.0))
put(t, "Thank you", 46, True, WHITE, 10, first=True)
put(t, "I welcome your questions.", 20, False, C(0xBF,0xC9,0xD4), 18)
put(t, "Devansh   ·   Customer Lifetime Value Prediction Using Bayesian Methods", 14, False, C(0x9A,0xA7,0xB5), 0)
rect(s, In(1.4), In(2.35), In(1.6), Pt(3.5), ORANGE)
s.notes_slide.notes_text_frame.text = (
 "BACKUP ANSWERS — why not Pareto/NBD? BG/NBD is the tractable standard (Fader 2005), same predictive "
 "performance, far cheaper. · Why 4 chains/1000 draws? Standard; diagnostics confirmed sufficiency. "
 "· Why weakly-informative half-normal priors? Respect positivity, scales set from data units; prior "
 "predictive checks. · Why is P(alive) AUC only 0.71? Activity is latent and the holdout is finite — a "
 "truly active customer may simply not buy; that caps ANY classifier. Calibration matters more than "
 "sharpness here. · Biggest weakness? The tight between-segment prior constraining H2 — prior sensitivity "
 "is the first thing I would run next.")

os.makedirs("outputs", exist_ok=True)
prs.save(OUT)
print(f"Saved {OUT}  ·  {len(prs.slides.__iter__.__self__._sldIdLst)} slides")
