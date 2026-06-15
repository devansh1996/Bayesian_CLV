
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
 
# ──────────────────────────────────────────────────────────────────────────────
# PATHS & CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
 
RAW_PATH       = Path("data/raw/online_retail_II.xlsx")
PROCESSED_DIR  = Path("data/processed")
 
# Calibration window ends here; everything from this date onward is holdout
CAL_END = "2011-03-01"
 
# StockCodes that represent fees / operational charges, not real product purchases
NON_PRODUCT_CODES = {
    "POST",        # postage
    "DOT",         # dotcom postage
    "M",           # manual entry
    "AMAZONFEE",   # amazon fee
    "BANK CHARGES",
    "C2",          # carriage
    "D",           # discount
    "CRUK",        # charity donation
    "S",           # sample
    "PADS",        # pads to match delivery
}
 
# Countries with fewer customers than this threshold get collapsed into "Other"
MIN_COUNTRY_CUSTOMERS = 30
 
 
# ──────────────────────────────────────────────────────────────────────────────
# 1. LOADING
# ──────────────────────────────────────────────────────────────────────────────
 
def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """
    Load both annual sheets from the UCI Online Retail II xlsx and concatenate.
 
    The dataset spans two sheets:
        - "Year 2009-2010"
        - "Year 2010-2011"
 
    Parameters
    ----------
    path : Path to the xlsx file (default: data/raw/online_retail_II.xlsx)
 
    Returns
    -------
    pd.DataFrame — raw concatenated transactions, columns stripped of whitespace
    """
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Dataset not found at '{path}'.\n"
            "Download from: https://archive.ics.uci.edu/dataset/502/online+retail+ii\n"
            "and place it at data/raw/online_retail_II.xlsx"
        )
 
    print(f"Loading {path} ...")
    df1 = pd.read_excel(path, sheet_name="Year 2009-2010")
    df2 = pd.read_excel(path, sheet_name="Year 2010-2011")
 
    df = pd.concat([df1, df2], ignore_index=True)
    df.columns = df.columns.str.strip()
 
    print(f"  Loaded {len(df):,} rows across both sheets")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Date range: {df['InvoiceDate'].min()} → {df['InvoiceDate'].max()}")
    print(f"  Unique customers (raw): {df['Customer ID'].nunique():,}")
 
    return df
 
 
# ──────────────────────────────────────────────────────────────────────────────
# 2. CLEANING
# ──────────────────────────────────────────────────────────────────────────────
 
def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning steps to raw transaction data.
 
    Steps applied in order:
        1. Drop rows missing Customer ID
        2. Remove cancellations  (InvoiceNo starts with 'C')
        3. Remove non-product stock codes (fees, postage, donations, etc.)
        4. Remove zero or negative quantities and prices
        5. Compute line-level Revenue = Quantity × Price
        6. Parse InvoiceDate to datetime
 
    Parameters
    ----------
    df : raw DataFrame from load_raw()
 
    Returns
    -------
    pd.DataFrame — cleaned transactions, reset index
    """
    n_raw = len(df)
    report = {}
 
    # ── Step 1: Missing Customer ID ──
    mask = df["Customer ID"].isna()
    report["missing_customer_id"] = mask.sum()
    df = df[~mask].copy()
    df["Customer ID"] = df["Customer ID"].astype(int)
 
    # ── Step 2: Cancellations ──
    df["Invoice"] = df["Invoice"].astype(str)
    mask = df["Invoice"].str.startswith("C")
    report["cancellations"] = mask.sum()
    df = df[~mask]
 
    # ── Step 3: Non-product stock codes ──
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    mask = df["StockCode"].isin(NON_PRODUCT_CODES)
    report["non_product_codes"] = mask.sum()
    df = df[~mask]
 
    # ── Step 4: Negative / zero qty or price ──
    mask = ~((df["Quantity"] > 0) & (df["Price"] > 0))
    report["neg_or_zero"] = mask.sum()
    df = df[~mask]
 
    # ── Step 5: Revenue ──
    df["Revenue"] = df["Quantity"] * df["Price"]
 
    # ── Step 6: Parse dates ──
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
 
    n_clean = len(df)
    n_removed = n_raw - n_clean
 
    print("\nCleaning report:")
    print(f"  Raw rows:                {n_raw:>10,}")
    for label, count in report.items():
        print(f"  - {label:<24} {count:>10,}  ({count/n_raw:.1%})")
    print(f"  ─────────────────────────────────────")
    print(f"  Clean rows:              {n_clean:>10,}  ({n_clean/n_raw:.1%} retained)")
    print(f"  Unique customers:        {df['Customer ID'].nunique():>10,}")
    print(f"  Unique products:         {df['StockCode'].nunique():>10,}")
 
    return df.reset_index(drop=True)
 
 
# ──────────────────────────────────────────────────────────────────────────────
# 3. TEMPORAL SPLIT
# ──────────────────────────────────────────────────────────────────────────────
 
def temporal_split(
    df: pd.DataFrame,
    cal_end: str = CAL_END,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split clean transaction data into calibration and holdout periods.
 
    The split is exclusive: calibration contains all transactions
    strictly before cal_end; holdout contains cal_end and later.
 
    Parameters
    ----------
    df      : cleaned transaction DataFrame from clean_transactions()
    cal_end : first date of holdout period (string, e.g. "2011-03-01")
 
    Returns
    -------
    cal     : calibration period transactions
    holdout : holdout period transactions
    """
    cal_end_dt = pd.Timestamp(cal_end)
 
    cal     = df[df["InvoiceDate"] <  cal_end_dt].copy()
    holdout = df[df["InvoiceDate"] >= cal_end_dt].copy()
 
    cal_cust     = cal["Customer ID"].nunique()
    holdout_cust = holdout["Customer ID"].nunique()
    overlap      = len(set(cal["Customer ID"]) & set(holdout["Customer ID"]))
 
    print(f"\nTemporal split at {cal_end}:")
    print(f"  Calibration : {cal['InvoiceDate'].min().date()} → {cal['InvoiceDate'].max().date()}"
          f"  ({len(cal):,} rows, {cal_cust:,} customers)")
    print(f"  Holdout     : {holdout['InvoiceDate'].min().date()} → {holdout['InvoiceDate'].max().date()}"
          f"  ({len(holdout):,} rows, {holdout_cust:,} customers)")
    print(f"  Overlap     : {overlap:,} customers appear in both periods ({overlap/cal_cust:.1%} of cal)")
 
    return cal, holdout
 
 
# ──────────────────────────────────────────────────────────────────────────────
# 4. CUSTOMER-LEVEL AGGREGATION  (RFM + BG/NBD inputs)
# ──────────────────────────────────────────────────────────────────────────────
 
def aggregate_customers(
    cal: pd.DataFrame,
    time_unit: str = "W",
) -> pd.DataFrame:
    """
    Aggregate calibration transactions to customer-level summary statistics
    required as inputs for the BG/NBD and Gamma-Gamma models.
 
    BG/NBD requires per-customer:
        frequency      : number of repeat purchases (total purchases - 1)
        recency        : weeks from first to last purchase
        T              : weeks from first purchase to end of calibration window
        monetary_value : mean revenue per repeat transaction (excludes first)
 
    Additional columns for EDA / baselines:
        n_purchases    : total invoice count
        total_revenue  : sum of all invoice revenues
        first_purchase : date of first invoice
        last_purchase  : date of last (most recent) invoice
        country        : most frequent country across invoices
 
    Parameters
    ----------
    cal       : calibration transactions from temporal_split()
    time_unit : time unit for recency/T (default "W" = weeks)
                Use "D" for days if you want daily granularity.
 
    Returns
    -------
    pd.DataFrame — one row per customer
    """
    # Use one day after last observed transaction as the observation end point.
    # This is more robust than using CAL_END directly in case the data
    # doesn't reach all the way to the split date.
    cal_end_obs = cal["InvoiceDate"].max() + pd.Timedelta(days=1)
 
    # ── Invoice-level aggregation ──
    # Collapse line items → one row per (customer, invoice)
    invoices = (
        cal
        .groupby(["Customer ID", "Invoice"])
        .agg(
            invoice_date    = ("InvoiceDate", "min"),
            invoice_revenue = ("Revenue",     "sum"),
            country         = ("Country",     "first"),
        )
        .reset_index()
    )
 
    # ── Customer-level loop ──
    customers = []
    for cid, grp in invoices.groupby("Customer ID"):
        grp           = grp.sort_values("invoice_date")
        first_purchase = grp["invoice_date"].min()
        last_purchase  = grp["invoice_date"].max()
        n_purchases    = len(grp)
 
        # BG/NBD frequency = repeat purchases (first purchase is not a repeat)
        frequency = n_purchases - 1
 
        # Recency: weeks from first to last purchase
        recency = (last_purchase - first_purchase) / np.timedelta64(1, time_unit)
 
        # T: weeks from first purchase to end of calibration window
        T = (cal_end_obs - first_purchase) / np.timedelta64(1, time_unit)
 
        # Monetary value: mean revenue per REPEAT transaction.
        # The first transaction is excluded (standard Gamma-Gamma convention)
        # because it conflates acquisition behavior with repeat spend.
        if frequency > 0:
            monetary_value = grp.iloc[1:]["invoice_revenue"].mean()
        else:
            monetary_value = 0.0
 
        customers.append({
            "customer_id"   : cid,
            "frequency"     : frequency,
            "recency"       : recency,
            "T"             : T,
            "monetary_value": monetary_value,
            "n_purchases"   : n_purchases,
            "total_revenue" : grp["invoice_revenue"].sum(),
            "first_purchase": first_purchase,
            "last_purchase" : last_purchase,
            "country"       : grp["country"].mode().iloc[0],
        })
 
    cust_df = pd.DataFrame(customers)
 
    # Sanity check: recency must never exceed T
    assert (cust_df["recency"] <= cust_df["T"] + 1e-6).all(), \
        "Data integrity error: recency > T for some customers"
 
    repeat = cust_df[cust_df["frequency"] > 0]
    print(f"\nCustomer aggregation (time unit = '{time_unit}'):")
    print(f"  Total customers:          {len(cust_df):>8,}")
    print(f"  Repeat purchasers:        {len(repeat):>8,}  ({len(repeat)/len(cust_df):.1%})")
    print(f"  One-time purchasers:      {(cust_df['frequency']==0).sum():>8,}")
    print(f"  Mean frequency:           {cust_df['frequency'].mean():>8.2f}")
    print(f"  Median T ({time_unit}):          {cust_df['T'].median():>8.1f}")
    print(f"  Mean monetary (repeaters): £{repeat['monetary_value'].mean():>7.2f}")
 
    return cust_df
 
 
# ──────────────────────────────────────────────────────────────────────────────
# 5. COUNTRY SEGMENTATION
# ──────────────────────────────────────────────────────────────────────────────
 
def collapse_countries(
    cust_df: pd.DataFrame,
    min_customers: int = MIN_COUNTRY_CUSTOMERS,
) -> pd.DataFrame:
    """
    Collapse low-volume countries into an "Other" segment.
 
    Countries with fewer than min_customers customers are merged into "Other"
    to avoid near-empty segments in the hierarchical model.
 
    Adds column: country_segment
 
    Parameters
    ----------
    cust_df       : customer DataFrame from aggregate_customers()
    min_customers : minimum customers to keep a country as its own segment
 
    Returns
    -------
    pd.DataFrame — same as input with additional 'country_segment' column
    """
    counts = cust_df["country"].value_counts()
    keep   = counts[counts >= min_customers].index.tolist()
 
    cust_df = cust_df.copy()
    cust_df["country_segment"] = cust_df["country"].where(
        cust_df["country"].isin(keep), other="Other"
    )
 
    n_collapsed = len(counts) - len(keep)
    print(f"\nCountry segmentation (min={min_customers} customers):")
    print(f"  Original countries: {len(counts)}")
    print(f"  Kept as named:      {len(keep)}  (collapsed {n_collapsed} into 'Other')")
    print(f"\n  Segment counts:")
    print(cust_df["country_segment"].value_counts().to_string())
 
    return cust_df
 
 
# ──────────────────────────────────────────────────────────────────────────────
# 6. HOLDOUT GROUND TRUTH
# ──────────────────────────────────────────────────────────────────────────────
 
def compute_holdout_truth(
    holdout: pd.DataFrame,
    cal_customers: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute ground-truth holdout metrics for each calibration customer.
 
    Customers who made no purchases in the holdout period receive zeros
    (left join from calibration customer list).
 
    Returns
    -------
    pd.DataFrame with columns:
        customer_id          : customer identifier
        holdout_transactions : unique invoices in holdout period
        holdout_spend        : total revenue in holdout period
        is_active            : 1 if customer made at least one holdout purchase
    """
    # Collapse holdout to one row per (customer, invoice)
    holdout_invoices = (
        holdout
        .groupby(["Customer ID", "Invoice"])
        .agg(invoice_revenue=("Revenue", "sum"))
        .reset_index()
    )
 
    holdout_agg = (
        holdout_invoices
        .groupby("Customer ID")
        .agg(
            holdout_transactions = ("Invoice",         "nunique"),
            holdout_spend        = ("invoice_revenue", "sum"),
        )
        .reset_index()
        .rename(columns={"Customer ID": "customer_id"})
    )
 
    # Left join: calibration customers not in holdout get zeros
    truth = cal_customers[["customer_id"]].merge(
        holdout_agg, on="customer_id", how="left"
    )
    truth["holdout_transactions"] = truth["holdout_transactions"].fillna(0).astype(int)
    truth["holdout_spend"]        = truth["holdout_spend"].fillna(0.0)
    truth["is_active"]            = (truth["holdout_transactions"] > 0).astype(int)
 
    print(f"\nHoldout ground truth ({len(truth):,} calibration customers):")
    print(f"  Active in holdout:        {truth['is_active'].sum():>8,}  ({truth['is_active'].mean():.1%})")
    print(f"  Inactive in holdout:      {(truth['is_active']==0).sum():>8,}")
    print(f"  Mean holdout transactions:{truth['holdout_transactions'].mean():>8.2f}")
    print(f"  Mean holdout spend:       £{truth['holdout_spend'].mean():>7.2f}")
    print(f"  Total holdout revenue:    £{truth['holdout_spend'].sum():>,.0f}")
 
    return truth
 
 
# ──────────────────────────────────────────────────────────────────────────────
# 7. FULL PIPELINE
# ──────────────────────────────────────────────────────────────────────────────
 
def run_pipeline(
    raw_path: Path = RAW_PATH,
    cal_end: str = CAL_END,
    time_unit: str = "W",
    min_country_customers: int = MIN_COUNTRY_CUSTOMERS,
    save: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Run the full data preparation pipeline end-to-end.
 
    Steps:
        1. load_raw()
        2. clean_transactions()
        3. temporal_split()
        4. aggregate_customers()
        5. collapse_countries()
        6. compute_holdout_truth()
        7. Save processed files to data/processed/ (if save=True)
 
    Parameters
    ----------
    raw_path              : path to the xlsx dataset
    cal_end               : calibration end date string
    time_unit             : time unit for RFM ("W" = weeks, "D" = days)
    min_country_customers : threshold for country collapsing
    save                  : whether to write parquet files to disk
 
    Returns
    -------
    df        : full cleaned transactions
    cal       : calibration transactions
    holdout   : holdout transactions
    customers : customer-level RFM features (calibration window)
    truth     : holdout ground truth per customer
    """
    print("=" * 60)
    print("RUNNING DATA PIPELINE")
    print("=" * 60)
 
    # Load & clean
    df = load_raw(raw_path)
    df = clean_transactions(df)
 
    # Split
    cal, holdout = temporal_split(df, cal_end=cal_end)
 
    # Aggregate
    customers = aggregate_customers(cal, time_unit=time_unit)
    customers = collapse_countries(customers, min_customers=min_country_customers)
 
    # Holdout truth
    truth = compute_holdout_truth(holdout, customers)
 
    # Save
    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        cal.to_parquet(      PROCESSED_DIR / "cal_transactions.parquet",  index=False)
        holdout.to_parquet(  PROCESSED_DIR / "holdout_transactions.parquet", index=False)
        customers.to_parquet(PROCESSED_DIR / "customers.parquet",          index=False)
        truth.to_parquet(    PROCESSED_DIR / "holdout_truth.parquet",      index=False)
        print(f"\n✓ Saved 4 parquet files to {PROCESSED_DIR}/")
 
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
 
    return df, cal, holdout, customers, truth
 
 
# ──────────────────────────────────────────────────────────────────────────────
# CONVENIENCE LOADERS  (use in notebooks after pipeline has run once)
# ──────────────────────────────────────────────────────────────────────────────
 
def load_processed(
    processed_dir: Path = PROCESSED_DIR,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load pre-processed parquet files saved by run_pipeline().
 
    Faster than re-running the full pipeline in every notebook session.
 
    Returns
    -------
    cal, holdout, customers, truth
    """
    cal       = pd.read_parquet(processed_dir / "cal_transactions.parquet")
    holdout   = pd.read_parquet(processed_dir / "holdout_transactions.parquet")
    customers = pd.read_parquet(processed_dir / "customers.parquet")
    truth     = pd.read_parquet(processed_dir / "holdout_truth.parquet")
 
    print(f"Loaded from {processed_dir}:")
    print(f"  cal:       {len(cal):,} rows")
    print(f"  holdout:   {len(holdout):,} rows")
    print(f"  customers: {len(customers):,} rows")
    print(f"  truth:     {len(truth):,} rows")
 
    return cal, holdout, customers, truth
 
 
# ──────────────────────────────────────────────────────────────────────────────
 
if __name__ == "__main__":
    run_pipeline()