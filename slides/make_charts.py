"""Presentation-scale charts for the thesis defence deck.
Emphasis colouring (accent vs neutral) + direct value labels, large fonts."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd, os

OUT = "outputs/slides"; os.makedirs(OUT, exist_ok=True)
NAVY, ORANGE, GREY, LGREY = "#2E4057", "#E76F51", "#8C8C8C", "#C9C9C9"
plt.rcParams.update({"font.size": 13, "axes.edgecolor": "#CCCCCC",
                     "axes.labelcolor": "#333333", "text.color": "#222222"})

def clean(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.tick_params(colors="#444444", labelsize=12)

# ───────────────────────── 1. Headline accuracy (two panels, no dual axis)
m = pd.read_csv("outputs/results/metrics_comparison.csv")
# merge in precision@100 so the chart shows the same metric the slide text quotes
_x = pd.read_csv("outputs/results/extra_metrics.csv")[["model", "precision_at_100"]]
m = m.merge(_x, on="model", how="left")
m["top100"] = m["precision_at_100"] * 100         # "how many of the top 100 belong there"
m = m[m.model != "Hierarchical BG/NBD"]           # show pooled Bayesian as "the model"
lbl = {"BG/NBD (Bayesian)": "Bayesian\nBG/NBD+GG", "XGBoost (two-stage)": "XGBoost",
       "RFM Heuristic": "RFM", "Naive (mean)": "Naive"}
m["short"] = m.model.map(lbl)

fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.6))
for ax, col, title, fmt, lower_better in [
    (axes[0], "tx_mae",   "Transaction MAE  (lower is better)", "{:.2f}", True),
    (axes[1], "top100",   "Of the top 100 chosen, how many belong there", "{:.0f}", False)]:
    d = m.sort_values(col, ascending=lower_better)
    cols = [NAVY if s.startswith("Bayesian") else LGREY for s in d.short]
    b = ax.bar(d.short, d[col], color=cols, width=0.62)
    for r, v in zip(b, d[col]):
        ax.text(r.get_x()+r.get_width()/2, v + max(d[col])*0.03, fmt.format(v),
                ha="center", fontsize=13, fontweight="bold",
                color=NAVY if r.get_facecolor()[:3] == tuple(int(NAVY[i:i+2],16)/255 for i in (1,3,5)) else "#555")
    ax.set_title(title, fontsize=14, pad=12, color="#222")
    ax.set_ylim(0, max(d[col])*1.20); ax.set_yticks([]); clean(ax)
    ax.spines["left"].set_visible(False)
fig.tight_layout()
fig.savefig(f"{OUT}/accuracy.png", dpi=170, bbox_inches="tight"); plt.close(fig)

# ───────────────────────── 2. H2 three-way pooling
c = pd.read_csv("outputs/results/country_level_mae.csv")
c = c.set_index("country")
segs = ["Other", "Germany", "France"]           # the small segments H2 is about
n = {"Other": 242, "Germany": 74, "France": 54}
series = [("Complete pooling", "MAE_BG/NBD (Bayesian)", LGREY),
          ("Partial pooling (hierarchical)", "MAE_Hierarchical BG/NBD", NAVY),
          ("No pooling (per segment)", "MAE_No pooling (per segment)", ORANGE)]
x = np.arange(len(segs)); w = 0.26
fig, ax = plt.subplots(figsize=(11.2, 4.8))
for i, (name, col, colr) in enumerate(series):
    vals = [c.loc[s, col] for s in segs]
    b = ax.bar(x + (i-1)*w, vals, w*0.88, label=name, color=colr)
    for r, v in zip(b, vals):
        ax.text(r.get_x()+r.get_width()/2, v+0.03, f"{v:.3f}", ha="center",
                fontsize=11.5, color="#444")
ax.set_xticks(x); ax.set_xticklabels([f"{s}\n(n={n[s]})" for s in segs], fontsize=13)
ax.set_ylabel("Transaction MAE", fontsize=13)
ax.set_ylim(0, 2.9); clean(ax)
ax.legend(frameon=False, fontsize=12, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.16))
fig.tight_layout()
fig.savefig(f"{OUT}/h2_pooling.png", dpi=170, bbox_inches="tight"); plt.close(fig)

# ───────────────────────── 3. H3 targeting: the two rules overlap
t = pd.read_csv("outputs/results/targeting_simulation_bg_nbd_bayesian.csv")
t = t[t.cost_per_customer == 600].sort_values("targeting_depth")
d = t.targeting_depth*100
fig, ax = plt.subplots(figsize=(11.2, 4.8))
ax.plot(d, t.oracle_value/1e6, "--", color=GREY, lw=2, marker="^", ms=7, label="Oracle (perfect foresight)")
ax.plot(d, t.point_estimate_value/1e6, color=NAVY, lw=3, marker="o", ms=9, label="Point estimate  E[CLV]")
ax.plot(d, t.posterior_prob_value/1e6, color=ORANGE, lw=3, marker="s", ms=8, ls=(0,(4,2)), label="Posterior probability  P(CLV>c)")
ax.set_xlabel("Targeting depth (% of customer base)", fontsize=13)
ax.set_ylabel("Cumulative net value (£M)", fontsize=13)
ax.annotate("the two decision rules\nare effectively identical",
            xy=(20, 3.85), xytext=(29, 2.75), fontsize=12.5, color=NAVY, ha="center",
            arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.6))
ax.legend(frameon=False, fontsize=12, loc="lower right"); clean(ax)
fig.tight_layout()
fig.savefig(f"{OUT}/h3_targeting.png", dpi=170, bbox_inches="tight"); plt.close(fig)

# ───────────────────────── 4. Hypothesis verdict summary
fig, ax = plt.subplots(figsize=(11.6, 3.1)); ax.axis("off")
rows = [("H1", "Accuracy + calibrated uncertainty", "SUPPORTED", "#1D7A5F"),
        ("H2", "Partial pooling helps small segments", "PARTIALLY SUPPORTED", "#B8860B"),
        ("H3", "P(CLV>c) targeting beats E[CLV]", "NOT SUPPORTED", "#B3503C")]
for i, (h, txt, verdict, colr) in enumerate(rows):
    y = 0.80 - i*0.30
    ax.add_patch(plt.Rectangle((0.015, y-0.105), 0.075, 0.21, color=NAVY, zorder=2))
    ax.text(0.052, y, h, color="white", fontsize=17, fontweight="bold", ha="center", va="center", zorder=3)
    ax.text(0.115, y, txt, fontsize=15, va="center", color="#222")
    ax.text(0.985, y, verdict, fontsize=14.5, fontweight="bold", color=colr, va="center", ha="right")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
fig.savefig(f"{OUT}/verdicts.png", dpi=170, bbox_inches="tight"); plt.close(fig)

print("wrote:", sorted(os.listdir(OUT)))
