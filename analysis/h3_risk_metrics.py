"""H3 check: risk-sensitive decision metrics for the targeting rules.

The current sim scores TOTAL realised net value — a risk-neutral objective for
which posterior-mean ranking is near-optimal, so P(CLV>c) cannot win by design.
The posterior's decision value should appear on risk-sensitive metrics:
  - hit rate      : fraction of targeted customers whose realised value > cost
  - wasted spend  : sum over targeted of max(cost - realised, 0)  (downside loss)
  - downside-penalised profit : net value - wasted spend (lambda = 1)
"""
import warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from src.models import (load_bgnbd, load_gamma_gamma, predict_transactions,
                        predict_spend, compute_clv_posterior)
from src.data import CAL_END

customers = pd.read_parquet('data/processed/customers.parquet')
truth = pd.read_parquet('data/processed/holdout_truth.parquet')
holdout = pd.read_parquet('data/processed/holdout_transactions.parquet')
t_future = (holdout['InvoiceDate'].max() - pd.Timestamp(CAL_END)).days / 7.0
y = truth.set_index('customer_id').loc[customers['customer_id'].values,
                                       'holdout_spend'].values.astype(float)

bg = load_bgnbd('bgnbd_standard')
gg = load_gamma_gamma('gamma_gamma')
tx = predict_transactions(bg, customers, t_future=t_future, n_samples=1000)
spend, mask = predict_spend(gg, customers, n_samples=1000)
clv = compute_clv_posterior(tx, spend, mask)
clv_mean = clv.mean(axis=0)
n = len(y)
print(f'CLV posterior {clv.shape}; mean £{clv_mean.mean():.0f}', flush=True)

rows = []
for c in [100.0, 300.0, 600.0, 1200.0, 2000.0]:
    p_above = (clv > c).mean(axis=0)
    for depth in [0.10, 0.20]:
        k = int(np.ceil(depth * n))
        for rule, order in [('point', np.argsort(clv_mean)[::-1]),
                            ('prob',  np.argsort(p_above)[::-1])]:
            top = order[:k]
            yt = y[top]
            rows.append({
                'cost': c, 'depth': depth, 'rule': rule,
                'hit_rate': float((yt > c).mean()),
                'wasted_spend': float(np.maximum(c - yt, 0).sum()),
                'net_value': float((yt - c).sum()),
                'downside_pen_profit': float((yt - c).sum()
                                             - np.maximum(c - yt, 0).sum()),
            })

df = pd.DataFrame(rows)
piv = df.pivot_table(index=['cost', 'depth'], columns='rule',
                     values=['hit_rate', 'wasted_spend', 'net_value'])
pd.set_option('display.width', 200)
print(piv.round(3).to_string())
df.to_csv('/tmp/h3_risk_metrics.csv', index=False)

print('\nprob-rule advantage (positive = prob rule better):')
for (c, d), g in df.groupby(['cost', 'depth']):
    gp = g.set_index('rule')
    print(f'  cost={int(c):5d} depth={d:.2f}  '
          f'hit_rate: {gp.loc["prob","hit_rate"]-gp.loc["point","hit_rate"]:+.3f}  '
          f'wasted_spend saved: £{gp.loc["point","wasted_spend"]-gp.loc["prob","wasted_spend"]:+,.0f}')

# ── PREDICTIVE version: P(realized CLV > c) via posterior predictive ─────────
print('\n===== PREDICTIVE CLV (Poisson count noise) =====', flush=True)
rng = np.random.default_rng(7)
clv_pred = rng.poisson(np.clip(tx, 0, None)).astype(float)
full_spend = np.empty_like(tx)
full_spend[:, mask] = spend
full_spend[:, ~mask] = spend.mean()
clv_pred = clv_pred * full_spend
print('sat check: frac customers with P(pred>600)>0.99:',
      float(((clv_pred > 600).mean(axis=0) > 0.99).mean()))

rows2 = []
for c in [100.0, 300.0, 600.0, 1200.0, 2000.0]:
    p_above = (clv_pred > c).mean(axis=0)
    for depth in [0.10, 0.20]:
        k = int(np.ceil(depth * n))
        for rule, order in [('point', np.argsort(clv_mean)[::-1]),
                            ('prob',  np.argsort(p_above)[::-1])]:
            top = order[:k]; yt = y[top]
            rows2.append({'cost': c, 'depth': depth, 'rule': rule,
                          'hit_rate': float((yt > c).mean()),
                          'wasted_spend': float(np.maximum(c - yt, 0).sum()),
                          'net_value': float((yt - c).sum())})
df2 = pd.DataFrame(rows2)
print('\nprob-rule advantage with PREDICTIVE distribution:')
for (c, d), g in df2.groupby(['cost', 'depth']):
    gp = g.set_index('rule')
    print(f'  cost={int(c):5d} depth={d:.2f}  '
          f'hit_rate: {gp.loc["prob","hit_rate"]-gp.loc["point","hit_rate"]:+.3f}  '
          f'wasted saved: £{gp.loc["point","wasted_spend"]-gp.loc["prob","wasted_spend"]:+,.0f}  '
          f'net delta: £{gp.loc["prob","net_value"]-gp.loc["point","net_value"]:+,.0f}')
df2.to_csv('/tmp/h3_risk_predictive.csv', index=False)
