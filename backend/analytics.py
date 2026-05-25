"""
Analytics engine for SpendSmart.
Uses pandas and numpy to compute spending insights from transaction data.
"""

import pandas as pd
import numpy as np
from io import StringIO


def parse_and_validate(file_content: str) -> pd.DataFrame:
    """
    Parse CSV content and validate required columns.
    Returns a cleaned DataFrame ready for analysis.
    
    Raises ValueError if required columns are missing or data is invalid.
    """
    required_columns = {"Date", "Merchant", "Amount", "Category"}

    try:
        df = pd.read_csv(StringIO(file_content))
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {str(e)}")

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Check required columns (case-insensitive)
    col_map = {}
    for req in required_columns:
        match = [c for c in df.columns if c.lower() == req.lower()]
        if not match:
            raise ValueError(f"Missing required column: '{req}'. Found columns: {list(df.columns)}")
        col_map[req] = match[0]

    # Rename to standardized names
    df = df.rename(columns={v: k for k, v in col_map.items()})
    df = df[["Date", "Merchant", "Amount", "Category"]]

    # Clean data
    df["Merchant"] = df["Merchant"].astype(str).str.strip()
    df["Category"] = df["Category"].astype(str).str.strip()
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Drop rows with invalid amounts or dates
    initial_count = len(df)
    df = df.dropna(subset=["Amount", "Date"])
    df = df[df["Amount"] > 0]
    dropped = initial_count - len(df)

    if len(df) == 0:
        raise ValueError("No valid transactions found after cleaning.")

    if dropped > 0:
        print(f"Dropped {dropped} invalid rows during cleaning.")

    # Sort by date
    df = df.sort_values("Date").reset_index(drop=True)

    # Add helper columns
    df["DayOfWeek"] = df["Date"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["IsWeekend"] = df["DayOfWeek"].isin([5, 6])
    df["DateStr"] = df["Date"].dt.strftime("%Y-%m-%d")

    return df


def get_category_totals(df: pd.DataFrame) -> list[dict]:
    """Aggregate spend per category with percentages."""
    total = df["Amount"].sum()
    grouped = df.groupby("Category").agg(
        total=("Amount", "sum"),
        count=("Amount", "count")
    ).reset_index()
    grouped["percentage"] = (grouped["total"] / total * 100).round(1)
    grouped = grouped.sort_values("total", ascending=False)

    return [
        {
            "category": row["Category"],
            "total": round(row["total"], 2),
            "percentage": row["percentage"],
            "count": int(row["count"]),
        }
        for _, row in grouped.iterrows()
    ]


def get_daily_spend(df: pd.DataFrame) -> list[dict]:
    """Get daily spending totals, filling missing dates with 0."""
    daily = df.groupby("DateStr")["Amount"].sum().reset_index()
    daily.columns = ["date", "total"]

    # Fill in missing dates
    date_range = pd.date_range(df["Date"].min(), df["Date"].max())
    all_dates = pd.DataFrame({"date": date_range.strftime("%Y-%m-%d")})
    daily = all_dates.merge(daily, on="date", how="left").fillna(0)

    return [
        {"date": row["date"], "total": round(row["total"], 2)}
        for _, row in daily.iterrows()
    ]


def get_top_merchants(df: pd.DataFrame, n: int = 5) -> list[dict]:
    """Get top N merchants by total spend."""
    grouped = df.groupby("Merchant").agg(
        total=("Amount", "sum"),
        count=("Amount", "count")
    ).reset_index()
    grouped = grouped.nlargest(n, "total")

    return [
        {
            "merchant": row["Merchant"],
            "total": round(row["total"], 2),
            "count": int(row["count"]),
        }
        for _, row in grouped.iterrows()
    ]


def get_weekday_vs_weekend(df: pd.DataFrame) -> dict:
    """Compare weekday vs weekend spending patterns."""
    weekday_df = df[~df["IsWeekend"]]
    weekend_df = df[df["IsWeekend"]]

    # Count unique weekdays and weekend days in the data
    n_weekdays = max(df[~df["IsWeekend"]]["DateStr"].nunique(), 1)
    n_weekend_days = max(df[df["IsWeekend"]]["DateStr"].nunique(), 1)

    weekday_total = weekday_df["Amount"].sum()
    weekend_total = weekend_df["Amount"].sum()

    # Per-category breakdown
    categories = {}
    for cat in df["Category"].unique():
        cat_weekday = weekday_df[weekday_df["Category"] == cat]["Amount"].sum()
        cat_weekend = weekend_df[weekend_df["Category"] == cat]["Amount"].sum()
        categories[cat] = {
            "weekday": round(cat_weekday / n_weekdays, 2),
            "weekend": round(cat_weekend / n_weekend_days, 2),
        }

    return {
        "weekday_avg": round(weekday_total / n_weekdays, 2),
        "weekend_avg": round(weekend_total / n_weekend_days, 2),
        "weekday_total": round(weekday_total, 2),
        "weekend_total": round(weekend_total, 2),
        "categories": categories,
    }


def detect_outliers(df: pd.DataFrame) -> list[dict]:
    """
    Detect outlier transactions using IQR method per category.
    Returns transactions that are significantly above normal for their category.
    
    Guards against false positives:
    - Minimum absolute threshold of ₹500 (small transactions are never "outliers")
    - Upper bound is at least 2x the category median
    - Capped at top 3 outliers per category (by amount)
    """
    outliers = []

    for cat in df["Category"].unique():
        cat_df = df[df["Category"] == cat]
        if len(cat_df) < 4:
            continue  # Need enough data for IQR

        q1 = cat_df["Amount"].quantile(0.25)
        q3 = cat_df["Amount"].quantile(0.75)
        iqr = q3 - q1
        median = cat_df["Amount"].median()

        # IQR-based threshold
        upper_bound = q3 + 1.5 * iqr

        # Guard: threshold must be at least 2x median and at least ₹500
        upper_bound = max(upper_bound, median * 2, 500)

        cat_outliers = []
        outlier_rows = cat_df[cat_df["Amount"] > upper_bound]
        for _, row in outlier_rows.iterrows():
            cat_outliers.append({
                "date": row["DateStr"],
                "merchant": row["Merchant"],
                "amount": round(row["Amount"], 2),
                "category": cat,
                "threshold": round(upper_bound, 2),
            })

        # Keep only top 3 outliers per category (most extreme)
        cat_outliers.sort(key=lambda x: x["amount"], reverse=True)
        outliers.extend(cat_outliers[:3])

    return outliers


def get_subscription_candidates(df: pd.DataFrame) -> list[dict]:
    """
    Identify recurring subscription-like transactions.
    Criteria: same merchant, ≥2 occurrences, low amount variance (CV < 0.2).
    """
    candidates = []

    merchant_groups = df.groupby("Merchant")
    for merchant, group in merchant_groups:
        if len(group) < 2:
            continue

        amounts = group["Amount"]
        mean_amount = amounts.mean()
        std_amount = amounts.std()

        # Coefficient of variation < 0.2 means very consistent amounts
        if mean_amount > 0 and (std_amount / mean_amount) < 0.2:
            candidates.append({
                "merchant": merchant,
                "avg_amount": round(mean_amount, 2),
                "occurrences": len(group),
                "category": group["Category"].mode().iloc[0],
                "total": round(amounts.sum(), 2),
            })

    return candidates


def get_merchant_frequency(df: pd.DataFrame) -> list[dict]:
    """Get merchant visit frequency, sorted by count."""
    grouped = df.groupby("Merchant").agg(
        count=("Amount", "count"),
        total=("Amount", "sum"),
        avg=("Amount", "mean"),
    ).reset_index()
    grouped = grouped.sort_values("count", ascending=False)

    return [
        {
            "merchant": row["Merchant"],
            "count": int(row["count"]),
            "total": round(row["total"], 2),
            "avg": round(row["avg"], 2),
        }
        for _, row in grouped.iterrows()
    ]


def simulate_savings(df: pd.DataFrame, reductions: dict[str, float]) -> dict:
    """
    Simulate savings by applying percentage reductions per category.
    
    Args:
        reductions: {category_name: reduction_percentage} e.g. {"Food": 20, "Travel": 10}
    
    Returns:
        Simulation results with original, projected, and per-category savings.
    """
    original_total = df["Amount"].sum()
    category_savings = {}

    for cat, pct in reductions.items():
        cat_total = df[df["Category"] == cat]["Amount"].sum()
        savings = cat_total * (pct / 100)
        category_savings[cat] = round(savings, 2)

    total_savings = sum(category_savings.values())

    return {
        "original_total": round(original_total, 2),
        "projected_total": round(original_total - total_savings, 2),
        "total_savings": round(total_savings, 2),
        "category_savings": category_savings,
    }


def get_full_analytics(df: pd.DataFrame) -> dict:
    """Compute all analytics for the dashboard in one call."""
    total_spend = df["Amount"].sum()
    date_range_days = (df["Date"].max() - df["Date"].min()).days + 1

    return {
        "total_spend": round(total_spend, 2),
        "daily_average": round(total_spend / max(date_range_days, 1), 2),
        "transaction_count": len(df),
        "date_range": {
            "start": df["Date"].min().strftime("%Y-%m-%d"),
            "end": df["Date"].max().strftime("%Y-%m-%d"),
        },
        "category_totals": get_category_totals(df),
        "daily_spend": get_daily_spend(df),
        "top_merchants": get_top_merchants(df),
        "weekday_vs_weekend": get_weekday_vs_weekend(df),
    }
