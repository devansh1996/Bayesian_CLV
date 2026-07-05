"""H2 check: no-pooling baseline — fit a separate BG/NBD per country segment.

The canonical demonstration of partial pooling is the three-way comparison
complete pooling vs partial pooling vs NO pooling. The thesis currently only
has the first two. Here we fit an independent BetaGeoModel per segment (same
weak data-informed priors for all) and compute per-segment holdout tx MAE.
"""
import warnings, time
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from pymc_marketing.clv import BetaGeoModel
from pymc_marketing.prior import Prior
from src.priors import data_informed_priors
from src.data import CAL_END

customers = pd.read_parquet('data/processed/customers.parquet')
truth = pd.read_parquet('data/processed/holdout_truth.parquet')
holdout = pd.read_parquet('data/processed/holdout_transactions.parquet')
t_future = (holdout['InvoiceDate'].max() - pd.Timestamp(CAL_END)).days / 7.0

pri = data_informed_priors(customers, verbose=False)['bgnbd']
cfg = {f'{n}_prior': Prior('HalfNormal', sigma=float(pri[f'{n}_sigma']))
       for n in ['r', 'alpha', 'a', 'b']}

truth_map = truth.set_index('customer_id')['holdout_transactions'].astype(float)

rows = []
for seg, grp in customers.groupby('country_segment'):
    df = pd.DataFrame({'customer_id': grp['customer_id'].values,
                       'frequency': grp['frequency'].values.astype(float),
                       'recency': grp['recency'].values.astype(float),
                       'T': grp['T'].values.astype(float)})
    t0 = time.time()
    m = BetaGeoModel(data=df, model_config=dict(cfg))
    m.build_model()
    m.fit(draws=1000, tune=1000, chains=4, target_accept=0.9,
          random_seed=42, progressbar=False)
    da = m.expected_purchases(data=df, future_t=float(t_future))
    pred = da.mean(('chain', 'draw')).values
    y = truth_map.loc[grp['customer_id'].values].values
    mae = float(np.mean(np.abs(y - pred)))
    import arviz as az
    rhat = float(az.rhat(m.idata).to_array().max())
    rows.append({'segment': seg, 'n': len(grp), 'MAE_nopool': mae, 'rhat': rhat,
                 'fit_s': round(time.time() - t0, 1)})
    print(f'NOPOOL {seg:16s} n={len(grp):5d} MAE={mae:.4f} rhat={rhat:.3f} '
          f'({rows[-1]["fit_s"]}s)', flush=True)

res = pd.DataFrame(rows)
cm = pd.read_csv('outputs/results/country_level_mae.csv')
merged = cm.merge(res.rename(columns={'segment': 'country'}), on='country')
cols = ['country', 'n_customers', 'MAE_BG/NBD (Bayesian)',
        'MAE_Hierarchical BG/NBD', 'MAE_nopool']
print('\nTHREE-WAY COMPARISON (holdout tx MAE):')
print(merged[cols].rename(columns={
    'MAE_BG/NBD (Bayesian)': 'complete_pool',
    'MAE_Hierarchical BG/NBD': 'partial_pool'}).to_string(index=False))
merged.to_csv('/tmp/h2_threeway.csv', index=False)
