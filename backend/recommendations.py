"""
Rule-based recommendation engine for SpendSmart.
Analyzes spending patterns and generates actionable savings insights.
"""

import pandas as pd
from backend.analytics import (
    get_category_totals,
    get_weekday_vs_weekend,
    detect_outliers,
    get_subscription_candidates,
    get_merchant_frequency,
)

# Categories that are NOT controllable/avoidable spending.
# The engine should never recommend "reduce P2P Transfer by 20%".
NON_ACTIONABLE = {
    "P2P Transfer", "Social", "Miscellaneous", "Credit",
    "Family Transfer", "Self/Pass-Through Transfer",
    "Large P2P Transfer", "Rent/Business", "Investment",
    "Cash", "Taxes & Fines", "Government",
}


def generate_recommendations(df: pd.DataFrame) -> list[dict]:
    """
    Run all recommendation rules against the transaction data.
    Returns a list of Insight dicts sorted by priority.
    """
    insights = []
    total_spend = df["Amount"].sum()

    # Gather analytics data
    category_totals = get_category_totals(df)
    weekday_weekend = get_weekday_vs_weekend(df)
    outliers = detect_outliers(df)
    subscriptions = get_subscription_candidates(df)
    merchant_freq = get_merchant_frequency(df)

    # Rule 1: High-category cut
    insights.extend(_rule_high_category(category_totals, total_spend))

    # Rule 2: Weekend spending spike
    insights.extend(_rule_weekend_spike(weekday_weekend))

    # Rule 3: Subscription sniffing
    insights.extend(_rule_subscriptions(subscriptions))

    # Rule 4: Merchant concentration
    insights.extend(_rule_merchant_concentration(merchant_freq, total_spend))

    # Rule 5: Outlier alerts
    insights.extend(_rule_outliers(outliers))

    # Rule 6: Travel optimization
    insights.extend(_rule_travel_optimization(df, category_totals))

    # Rule 7: Daily budget awareness
    insights.extend(_rule_daily_budget(df, total_spend))

    # Rule 8: Savings targets (10% and 20%)
    insights.extend(_rule_savings_targets(category_totals, total_spend))

    # Sort by priority: high -> medium -> low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    insights.sort(key=lambda x: priority_order.get(x["priority"], 3))

    return insights


def _rule_high_category(category_totals: list[dict], total_spend: float) -> list[dict]:
    """If a category exceeds 35% of total spend, suggest a 20% cut."""
    insights = []
    for cat in category_totals:
        if cat["category"] in NON_ACTIONABLE:
            continue
        if cat["count"] < 3:
            continue  # Need a pattern, not a one-off
        if cat["percentage"] > 35:
            reduction = cat["total"] * 0.20
            insights.append({
                "title": f"Reduce {cat['category']} spending by 20%",
                "description": (
                    f"{cat['category']} accounts for {cat['percentage']}% of your total spend "
                    f"(₹{cat['total']:,.0f}). Cutting back by 20% could save you significantly."
                ),
                "savings_estimate": round(reduction, 2),
                "icon": "TrendingDown",
                "priority": "high",
                "category": cat["category"],
            })
        elif cat["percentage"] > 25:
            reduction = cat["total"] * 0.15
            insights.append({
                "title": f"Watch your {cat['category']} spending",
                "description": (
                    f"{cat['category']} is {cat['percentage']}% of your budget "
                    f"(₹{cat['total']:,.0f}). A 15% reduction would help."
                ),
                "savings_estimate": round(reduction, 2),
                "icon": "AlertTriangle",
                "priority": "medium",
                "category": cat["category"],
            })
    return insights


def _rule_weekend_spike(weekday_weekend: dict) -> list[dict]:
    """If weekend daily average is 1.5x+ higher than weekday."""
    insights = []
    wd_avg = weekday_weekend["weekday_avg"]
    we_avg = weekday_weekend["weekend_avg"]

    if wd_avg > 0 and we_avg > wd_avg * 1.5:
        spike_pct = round((we_avg / wd_avg - 1) * 100)
        potential_saving = round((we_avg - wd_avg * 1.2) * 8, 2)  # ~8 weekend days/month
        insights.append({
            "title": "Weekend spending is significantly higher",
            "description": (
                f"Your weekend daily average (₹{we_avg:,.0f}) is {spike_pct}% higher "
                f"than weekdays (₹{wd_avg:,.0f}). Setting a weekend budget could help."
            ),
            "savings_estimate": max(potential_saving, 0),
            "icon": "Calendar",
            "priority": "high",
            "category": "General",
        })
    return insights


def _rule_subscriptions(subscriptions: list[dict]) -> list[dict]:
    """Flag recurring subscription-like charges."""
    insights = []
    for sub in subscriptions:
        # Only flag actual subscription-like services (not groceries, etc.)
        if sub["category"] in ("Subscriptions", "Entertainment"):
            insights.append({
                "title": f"Review {sub['merchant']} subscription",
                "description": (
                    f"You're paying ~₹{sub['avg_amount']:,.0f} to {sub['merchant']} "
                    f"({sub['occurrences']} charges detected). "
                    f"Cancel if unused to save ₹{sub['avg_amount']:,.0f}/month."
                ),
                "savings_estimate": round(sub["avg_amount"], 2),
                "icon": "CreditCard",
                "priority": "medium",
                "category": sub["category"],
            })
    return insights


def _rule_merchant_concentration(merchant_freq: list[dict], total_spend: float) -> list[dict]:
    """If a single merchant accounts for >15% of total spend."""
    insights = []
    for m in merchant_freq[:10]:  # Only check top 10 merchants
        pct = (m["total"] / total_spend) * 100
        if m["count"] < 3:
            continue  # Need a pattern, not a one-off
        if pct > 15:
            insights.append({
                "title": f"High spending at {m['merchant']}",
                "description": (
                    f"You spent ₹{m['total']:,.0f} at {m['merchant']} ({pct:.1f}% of total, "
                    f"{m['count']} transactions). Consider cheaper alternatives."
                ),
                "savings_estimate": round(m["total"] * 0.25, 2),
                "icon": "Store",
                "priority": "medium",
                "category": "General",
            })
        elif pct > 10 and m["count"] >= 5:
            insights.append({
                "title": f"Frequent visits to {m['merchant']}",
                "description": (
                    f"You visited {m['merchant']} {m['count']} times, spending ₹{m['total']:,.0f} "
                    f"(avg ₹{m['avg']:,.0f}/visit). Try reducing frequency."
                ),
                "savings_estimate": round(m["avg"] * 2, 2),  # Save ~2 visits worth
                "icon": "MapPin",
                "priority": "low",
                "category": "General",
            })
    return insights


def _rule_outliers(outliers: list[dict]) -> list[dict]:
    """Flag outlier transactions that are unusually high for their category."""
    insights = []
    for o in outliers:
        if o["category"] in NON_ACTIONABLE:
            continue
        insights.append({
            "title": f"Unusual {o['category']} charge: ₹{o['amount']:,.0f}",
            "description": (
                f"₹{o['amount']:,.0f} at {o['merchant']} on {o['date']} is unusually high "
                f"for {o['category']} (typical threshold: ₹{o['threshold']:,.0f}). "
                f"Review if this was necessary."
            ),
            "savings_estimate": round(o["amount"] - o["threshold"], 2),
            "icon": "AlertCircle",
            "priority": "low",
            "category": o["category"],
        })
    return insights


def _rule_travel_optimization(df: pd.DataFrame, category_totals: list[dict]) -> list[dict]:
    """If Travel/Transport has enough trips with high average cost, suggest alternatives."""
    insights = []
    travel_cats = [c for c in category_totals if c["category"].lower() in ("travel", "transport")]

    if travel_cats:
        travel = travel_cats[0]
        avg_trip = travel["total"] / max(travel["count"], 1)

        # Only trigger for genuine commute patterns (3+ trips, avg > ₹150)
        if avg_trip > 150 and travel["count"] >= 3:
            metro_savings = round((avg_trip - 40) * travel["count"] * 0.5, 2)
            insights.append({
                "title": "Consider public transport for regular commute",
                "description": (
                    f"You took {travel['count']} trips averaging ₹{avg_trip:,.0f}/trip. "
                    f"Switching half to Metro/bus (~₹40/trip) could save significantly."
                ),
                "savings_estimate": metro_savings,
                "icon": "Train",
                "priority": "medium",
                "category": travel["category"],
            })
    return insights


def _rule_daily_budget(df: pd.DataFrame, total_spend: float) -> list[dict]:
    """Awareness of daily spending rate and target."""
    insights = []
    date_range_days = (df["Date"].max() - df["Date"].min()).days + 1
    daily_avg = total_spend / max(date_range_days, 1)

    # Suggest a target that's 15% lower
    target_daily = daily_avg * 0.85
    monthly_savings = (daily_avg - target_daily) * 30

    insights.append({
        "title": f"Set a daily spending target of ₹{target_daily:,.0f}",
        "description": (
            f"Your daily average is ₹{daily_avg:,.0f}. Aiming for ₹{target_daily:,.0f}/day "
            f"(15% less) would save ₹{monthly_savings:,.0f}/month."
        ),
        "savings_estimate": round(monthly_savings, 2),
        "icon": "Target",
        "priority": "low",
        "category": "General",
    })
    return insights


def _rule_savings_targets(category_totals: list[dict], total_spend: float) -> list[dict]:
    """Show what 10% and 20% savings look like in concrete terms."""
    insights = []
    # Only use actionable categories for savings targets
    actionable_cats = [c for c in category_totals if c["category"] not in NON_ACTIONABLE]

    for target_pct in [10, 20]:
        target_amount = total_spend * (target_pct / 100)

        # Suggest cuts from top actionable categories
        top_cats = actionable_cats[:3]
        cuts = []
        remaining = target_amount
        for cat in top_cats:
            cut = min(remaining, cat["total"] * 0.25)  # Max 25% cut per category
            if cut > 0:
                cuts.append(f"{cat['category']} (-₹{cut:,.0f})")
                remaining -= cut

        cuts_str = ", ".join(cuts)

        insights.append({
            "title": f"How to save {target_pct}% (₹{target_amount:,.0f}/month)",
            "description": f"Target: ₹{target_amount:,.0f} in savings. Suggested cuts: {cuts_str}.",
            "savings_estimate": round(target_amount, 2),
            "icon": "PiggyBank",
            "priority": "high" if target_pct == 20 else "medium",
            "category": "General",
        })

    return insights
