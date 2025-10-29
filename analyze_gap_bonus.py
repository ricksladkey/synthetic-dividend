"""Analyze gap bonus impact from regenerated research data."""

import pandas as pd

# Load data
df = pd.read_csv("research_phase1_1year_core.csv")

print("=" * 70)
print("GAP BONUS ANALYSIS - Multi-Bracket Fix Impact")
print("=" * 70)
print()

# Transaction counts by asset (sd_n=8 for comparison)
print("Transaction Counts by Asset (sd_n=8):")
print("-" * 70)
sd8 = df[df["sd_n"] == 8][
    ["ticker", "transaction_count", "volatility_alpha_pct", "rebalance_trigger"]
].sort_values("transaction_count", ascending=False)
print(sd8.to_string(index=False))
print()

# Correlation analysis
print("=" * 70)
print("CORRELATION ANALYSIS")
print("=" * 70)
corr_txn_alpha = df["transaction_count"].corr(df["volatility_alpha_pct"])
print(f"Transaction Count vs Volatility Alpha: {corr_txn_alpha:.3f}")
print()

# Group by ticker to see gap frequency patterns
print("Average Metrics by Asset:")
print("-" * 70)
asset_avg = (
    df.groupby("ticker")
    .agg({"transaction_count": "mean", "volatility_alpha_pct": "mean", "rebalance_trigger": "mean"})
    .round(2)
    .sort_values("transaction_count", ascending=False)
)
print(asset_avg)
print()

# Extreme volatility assets (gap bonus leaders)
print("=" * 70)
print("GAP BONUS LEADERS (High Transaction Count)")
print("=" * 70)
high_txn = df[df["transaction_count"] > 200].sort_values("transaction_count", ascending=False)
print(
    high_txn[
        ["ticker", "sd_n", "transaction_count", "volatility_alpha_pct", "rebalance_trigger"]
    ].to_string(index=False)
)
print()

# Theory vs Practice divergence
print("=" * 70)
print("THEORY VS PRACTICE DIVERGENCE")
print("=" * 70)
print()
print("Theoretical expectations (gradual moves only):")
print("  - sd4:  ~4 transactions to double (18.92% brackets)")
print("  - sd8:  ~8 transactions to double (9.05% brackets)")
print("  - sd12: ~12 transactions to double (5.95% brackets)")
print()
print("Actual transaction counts (with gap bonus):")
print()

# Show actual vs theoretical for extreme assets
for ticker in ["MSTR", "ETH-USD", "BTC-USD", "NVDA"]:
    ticker_data = df[df["ticker"] == ticker].sort_values("sd_n")
    if len(ticker_data) > 0:
        print(f"{ticker}:")
        for _, row in ticker_data.iterrows():
            sd_n = int(row["sd_n"])
            actual_txns = int(row["transaction_count"])
            theoretical = sd_n  # Theoretical transactions to double
            multiplier = actual_txns / theoretical if theoretical > 0 else 0
            print(
                f"  sd{sd_n}: {actual_txns:4d} txns (theoretical: {theoretical:2d}, multiplier: {multiplier:5.1f}x)"
            )
        print()

# Volatility alpha vs sd_n relationship
print("=" * 70)
print("VOLATILITY ALPHA vs REBALANCE TRIGGER RELATIONSHIP")
print("=" * 70)
print()
print("For each asset, optimal sd_n (by volatility alpha):")
print("-" * 70)
optimal = df.loc[df.groupby("ticker")["volatility_alpha_pct"].idxmax()]
print(
    optimal[["ticker", "sd_n", "volatility_alpha_pct", "transaction_count"]]
    .sort_values("volatility_alpha_pct", ascending=False)
    .to_string(index=False)
)
print()

# Key insight: relationship may have changed
print("=" * 70)
print("KEY INSIGHTS")
print("=" * 70)
print()
print(f"1. Transaction count strongly correlates with alpha (r={corr_txn_alpha:.3f})")
print()
print("2. Gap bonus multipliers:")
high_vol_avg = df[df["ticker"].isin(["MSTR", "ETH-USD", "BTC-USD"])]["transaction_count"].mean()
low_vol_avg = df[df["ticker"].isin(["SPY", "DIA", "GLD"])]["transaction_count"].mean()
print(f"   - High volatility assets: {high_vol_avg:.0f} avg transactions")
print(f"   - Low volatility assets: {low_vol_avg:.0f} avg transactions")
print(f"   - Multiplier: {high_vol_avg / low_vol_avg:.1f}x")
print()
print("3. Reassessment needed:")
print("   - Old algorithm validated sd_n by gradual moves only")
print("   - Gap bonus makes tighter triggers (higher sd_n) MORE profitable")
print("   - Optimal sd_n may shift UPWARD for volatile assets")
print()
