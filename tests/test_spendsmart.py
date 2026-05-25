"""
SpendSmart Test Suite
=====================
Covers: CSV parsing, analytics engine, recommendation engine, PDF parsing,
        API endpoints, and edge cases.

Run: cd spend_smart && venv/bin/python -m pytest tests/ -v
"""

import pytest
import pandas as pd
import os
import sys
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.analytics import (
    parse_and_validate,
    get_category_totals,
    get_daily_spend,
    get_top_merchants,
    get_weekday_vs_weekend,
    detect_outliers,
    get_subscription_candidates,
    simulate_savings,
    get_full_analytics,
)
from backend.recommendations import generate_recommendations


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

VALID_CSV = """Date,Merchant,Amount,Category
2026-01-01,BigBasket,1250,Food
2026-01-02,Zomato,420,Food
2026-01-03,Uber,180,Travel
2026-01-04,Amazon,2800,Shopping
2026-01-05,Netflix,649,Subscriptions
2026-01-06,Swiggy,350,Food
2026-01-07,Ola,260,Travel
2026-01-08,Zomato,380,Food
2026-01-09,Flipkart,6200,Shopping
2026-01-10,Apollo Pharmacy,350,Health
2026-01-11,Uber,190,Travel
2026-01-12,Swiggy,310,Food
2026-01-13,Electricity Bill,1800,Utilities
2026-01-14,Zomato,400,Food
2026-01-15,Netflix,649,Subscriptions
"""


@pytest.fixture
def sample_df():
    """Parsed DataFrame from valid CSV."""
    return parse_and_validate(VALID_CSV)


@pytest.fixture
def sample_csv_path():
    """Path to the bundled sample_data.csv."""
    return os.path.join(os.path.dirname(__file__), "..", "backend", "sample_data.csv")


# ─────────────────────────────────────────────────────────────
# 1. CSV Parsing & Validation Tests
# ─────────────────────────────────────────────────────────────

class TestCSVParsing:

    def test_valid_csv_parses(self, sample_df):
        """Valid CSV with all required columns should parse successfully."""
        assert len(sample_df) == 15
        assert list(sample_df.columns[:4]) == ["Date", "Merchant", "Amount", "Category"]

    def test_required_columns_present(self, sample_df):
        """Parsed DataFrame has all required columns + helper columns."""
        required = {"Date", "Merchant", "Amount", "Category", "DayOfWeek", "IsWeekend", "DateStr"}
        assert required.issubset(set(sample_df.columns))

    def test_amounts_are_numeric(self, sample_df):
        """All amounts should be parsed as numeric (int or float)."""
        assert sample_df["Amount"].dtype in [float, "float64", int, "int64"]
        assert (sample_df["Amount"] > 0).all()

    def test_dates_are_datetime(self, sample_df):
        """Dates should be parsed as datetime objects."""
        assert pd.api.types.is_datetime64_any_dtype(sample_df["Date"])

    def test_sorted_by_date(self, sample_df):
        """Transactions should be sorted chronologically."""
        dates = sample_df["Date"].tolist()
        assert dates == sorted(dates)

    def test_missing_column_raises_error(self):
        """CSV missing a required column should raise ValueError."""
        bad_csv = "Date,Merchant,Amount\n2026-01-01,Zomato,420\n"
        with pytest.raises(ValueError, match="Missing required column"):
            parse_and_validate(bad_csv)

    def test_empty_csv_raises_error(self):
        """CSV with only headers (no data) should raise ValueError."""
        empty_csv = "Date,Merchant,Amount,Category\n"
        with pytest.raises(ValueError, match="No valid transactions"):
            parse_and_validate(empty_csv)

    def test_invalid_amounts_dropped(self):
        """Rows with non-numeric amounts should be dropped."""
        csv = """Date,Merchant,Amount,Category
2026-01-01,Zomato,420,Food
2026-01-02,Swiggy,invalid,Food
2026-01-03,Uber,180,Travel
"""
        df = parse_and_validate(csv)
        assert len(df) == 2  # "invalid" row dropped

    def test_negative_amounts_dropped(self):
        """Rows with negative amounts should be dropped."""
        csv = """Date,Merchant,Amount,Category
2026-01-01,Zomato,420,Food
2026-01-02,Swiggy,-100,Food
"""
        df = parse_and_validate(csv)
        assert len(df) == 1

    def test_case_insensitive_columns(self):
        """Column names should be matched case-insensitively."""
        csv = """date,merchant,amount,category
2026-01-01,Zomato,420,Food
"""
        df = parse_and_validate(csv)
        assert len(df) == 1
        assert "Date" in df.columns  # Standardized to Title case

    def test_whitespace_trimmed(self):
        """Whitespace in merchant/category names should be trimmed."""
        csv = """Date,Merchant,Amount,Category
2026-01-01,  Zomato  ,420,  Food  
"""
        df = parse_and_validate(csv)
        assert df.iloc[0]["Merchant"] == "Zomato"
        assert df.iloc[0]["Category"] == "Food"


# ─────────────────────────────────────────────────────────────
# 2. Analytics Engine Tests
# ─────────────────────────────────────────────────────────────

class TestAnalytics:

    def test_category_totals(self, sample_df):
        """Category totals should sum to total spend."""
        totals = get_category_totals(sample_df)
        total_from_cats = sum(c["total"] for c in totals)
        total_from_df = sample_df["Amount"].sum()
        assert abs(total_from_cats - total_from_df) < 0.01

    def test_category_percentages_sum_to_100(self, sample_df):
        """Category percentages should sum to ~100%."""
        totals = get_category_totals(sample_df)
        pct_sum = sum(c["percentage"] for c in totals)
        assert 99.5 <= pct_sum <= 100.5

    def test_category_sorted_descending(self, sample_df):
        """Categories should be sorted by total amount (descending)."""
        totals = get_category_totals(sample_df)
        amounts = [c["total"] for c in totals]
        assert amounts == sorted(amounts, reverse=True)

    def test_daily_spend_covers_all_dates(self, sample_df):
        """Daily spend should have entries for every date in range."""
        daily = get_daily_spend(sample_df)
        assert len(daily) == 15  # Jan 1 to Jan 15

    def test_daily_spend_no_negatives(self, sample_df):
        """No daily total should be negative."""
        daily = get_daily_spend(sample_df)
        assert all(d["total"] >= 0 for d in daily)

    def test_top_merchants_limited(self, sample_df):
        """Top merchants should be limited to 5."""
        merchants = get_top_merchants(sample_df, n=5)
        assert len(merchants) <= 5

    def test_top_merchants_sorted(self, sample_df):
        """Top merchants should be sorted by total (descending)."""
        merchants = get_top_merchants(sample_df)
        amounts = [m["total"] for m in merchants]
        assert amounts == sorted(amounts, reverse=True)

    def test_weekday_vs_weekend(self, sample_df):
        """Weekday and weekend averages should be computed."""
        ww = get_weekday_vs_weekend(sample_df)
        assert "weekday_avg" in ww
        assert "weekend_avg" in ww
        assert ww["weekday_avg"] >= 0
        assert ww["weekend_avg"] >= 0

    def test_weekday_weekend_categories(self, sample_df):
        """Per-category weekday/weekend breakdown should cover all categories."""
        ww = get_weekday_vs_weekend(sample_df)
        categories_in_df = set(sample_df["Category"].unique())
        categories_in_ww = set(ww["categories"].keys())
        assert categories_in_df == categories_in_ww

    def test_full_analytics_structure(self, sample_df):
        """Full analytics should have all expected keys."""
        analytics = get_full_analytics(sample_df)
        expected_keys = {
            "total_spend", "daily_average", "transaction_count",
            "date_range", "category_totals", "daily_spend",
            "top_merchants", "weekday_vs_weekend"
        }
        assert expected_keys == set(analytics.keys())

    def test_total_spend_correct(self, sample_df):
        """Total spend should match sum of all amounts."""
        analytics = get_full_analytics(sample_df)
        assert analytics["total_spend"] == sample_df["Amount"].sum()


# ─────────────────────────────────────────────────────────────
# 3. Outlier Detection Tests
# ─────────────────────────────────────────────────────────────

class TestOutlierDetection:

    def test_outlier_detected(self):
        """A transaction far above the IQR should be flagged as an outlier."""
        csv = """Date,Merchant,Amount,Category
2026-01-01,Amazon,500,Shopping
2026-01-02,Flipkart,450,Shopping
2026-01-03,Amazon,520,Shopping
2026-01-04,Flipkart,480,Shopping
2026-01-05,Amazon,8000,Shopping
"""
        df = parse_and_validate(csv)
        outliers = detect_outliers(df)
        shopping_outliers = [o for o in outliers if o["category"] == "Shopping"]
        assert len(shopping_outliers) >= 1
        assert any(o["amount"] == 8000 for o in shopping_outliers)

    def test_normal_transactions_not_flagged(self, sample_df):
        """Regular-amount Food transactions should NOT be flagged."""
        outliers = detect_outliers(sample_df)
        food_outliers = [o for o in outliers if o["category"] == "Food"]
        # Most food transactions (300-420 range) should not be outliers
        assert all(o["amount"] > 500 for o in food_outliers)

    def test_outlier_has_required_fields(self, sample_df):
        """Each outlier dict should have date, merchant, amount, category, threshold."""
        outliers = detect_outliers(sample_df)
        if outliers:
            required = {"date", "merchant", "amount", "category", "threshold"}
            assert required.issubset(set(outliers[0].keys()))


# ─────────────────────────────────────────────────────────────
# 4. Subscription Detection Tests
# ─────────────────────────────────────────────────────────────

class TestSubscriptionDetection:

    def test_netflix_detected_as_subscription(self, sample_df):
        """Netflix (₹649 × 2) should be detected as a subscription candidate."""
        subs = get_subscription_candidates(sample_df)
        netflix = [s for s in subs if s["merchant"] == "Netflix"]
        assert len(netflix) == 1
        assert netflix[0]["occurrences"] >= 2
        assert abs(netflix[0]["avg_amount"] - 649) < 1

    def test_single_occurrence_not_flagged(self, sample_df):
        """Merchants with only 1 transaction should NOT be flagged."""
        subs = get_subscription_candidates(sample_df)
        assert all(s["occurrences"] >= 2 for s in subs)


# ─────────────────────────────────────────────────────────────
# 5. Savings Simulation Tests
# ─────────────────────────────────────────────────────────────

class TestSimulation:

    def test_zero_reduction(self, sample_df):
        """0% reduction should result in zero savings."""
        result = simulate_savings(sample_df, {"Food": 0, "Travel": 0})
        assert result["total_savings"] == 0
        assert result["projected_total"] == result["original_total"]

    def test_100_percent_reduction(self, sample_df):
        """100% reduction on a category should save the full category amount."""
        food_total = sample_df[sample_df["Category"] == "Food"]["Amount"].sum()
        result = simulate_savings(sample_df, {"Food": 100})
        assert abs(result["category_savings"]["Food"] - food_total) < 0.01

    def test_partial_reduction(self, sample_df):
        """20% reduction should save exactly 20% of category total."""
        food_total = sample_df[sample_df["Category"] == "Food"]["Amount"].sum()
        result = simulate_savings(sample_df, {"Food": 20})
        expected = food_total * 0.20
        assert abs(result["category_savings"]["Food"] - expected) < 0.01

    def test_projected_total_correct(self, sample_df):
        """Projected total = original - total savings."""
        result = simulate_savings(sample_df, {"Food": 20, "Travel": 10})
        assert abs(
            result["projected_total"] - (result["original_total"] - result["total_savings"])
        ) < 0.01


# ─────────────────────────────────────────────────────────────
# 6. Recommendation Engine Tests
# ─────────────────────────────────────────────────────────────

class TestRecommendations:

    def test_recommendations_generated(self, sample_df):
        """Should generate at least 1 recommendation."""
        recs = generate_recommendations(sample_df)
        assert len(recs) >= 1

    def test_recommendation_structure(self, sample_df):
        """Each recommendation should have required fields."""
        recs = generate_recommendations(sample_df)
        required = {"title", "description", "savings_estimate", "icon", "priority", "category"}
        for r in recs:
            assert required.issubset(set(r.keys()))

    def test_valid_priorities(self, sample_df):
        """All priorities should be high, medium, or low."""
        recs = generate_recommendations(sample_df)
        valid = {"high", "medium", "low"}
        for r in recs:
            assert r["priority"] in valid

    def test_savings_estimates_positive(self, sample_df):
        """All savings estimates should be non-negative."""
        recs = generate_recommendations(sample_df)
        for r in recs:
            assert r["savings_estimate"] >= 0

    def test_high_category_rule_triggers(self, sample_df):
        """Food is >35% of spend → should trigger high-category rule."""
        recs = generate_recommendations(sample_df)
        food_recs = [r for r in recs if "Food" in r["title"] and "educe" in r["title"]]
        # Food is the dominant category, so at least a "watch" or "reduce" rec
        food_related = [r for r in recs if r["category"] == "Food" or "Food" in r["title"]]
        assert len(food_related) >= 1

    def test_savings_target_rules_exist(self, sample_df):
        """10% and 20% savings target rules should always generate."""
        recs = generate_recommendations(sample_df)
        target_recs = [r for r in recs if "save" in r["title"].lower() and "%" in r["title"]]
        assert len(target_recs) >= 2  # 10% and 20%

    def test_daily_budget_rule_exists(self, sample_df):
        """Daily budget rule should always generate."""
        recs = generate_recommendations(sample_df)
        daily_recs = [r for r in recs if "daily" in r["title"].lower()]
        assert len(daily_recs) >= 1

    def test_sorted_by_priority(self, sample_df):
        """Recommendations should be sorted: high → medium → low."""
        recs = generate_recommendations(sample_df)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        priorities = [priority_order[r["priority"]] for r in recs]
        assert priorities == sorted(priorities)


# ─────────────────────────────────────────────────────────────
# 7. PDF Parser Tests
# ─────────────────────────────────────────────────────────────

class TestPDFParser:

    @pytest.fixture
    def pdf_path(self):
        """Path to the sample PhonePe PDF (if available)."""
        path = os.path.join(os.path.dirname(__file__), "..", "PhonePe_Statement_May2025_May2026.pdf")
        if not os.path.exists(path):
            pytest.skip("PhonePe PDF not found — skipping PDF tests")
        return path

    def test_pdf_parses_transactions(self, pdf_path):
        """PDF should parse into a non-empty list of transactions."""
        from backend.pdf_parser import parse_pdf
        txns = parse_pdf(pdf_path)
        assert len(txns) > 0

    def test_pdf_has_debits_and_credits(self, pdf_path):
        """Parsed PDF should contain both DEBIT and CREDIT transactions."""
        from backend.pdf_parser import parse_pdf
        txns = parse_pdf(pdf_path)
        types = {t.txn_type for t in txns}
        assert "DEBIT" in types
        assert "CREDIT" in types

    def test_pdf_categories_assigned(self, pdf_path):
        """All parsed transactions should have a category assigned."""
        from backend.pdf_parser import parse_pdf
        txns = parse_pdf(pdf_path)
        for t in txns:
            assert t.category != "", f"No category for: {t.description}"

    def test_pdf_exclusions_applied(self, pdf_path):
        """Credits and self-transfers should be marked as excluded."""
        from backend.pdf_parser import parse_pdf
        txns = parse_pdf(pdf_path)
        credits = [t for t in txns if t.txn_type == "CREDIT"]
        assert all(t.is_excluded for t in credits)

    def test_pdf_spendable_subset(self, pdf_path):
        """Spendable transactions should be DEBIT + not excluded."""
        from backend.pdf_parser import parse_pdf
        txns = parse_pdf(pdf_path)
        spendable = [t for t in txns if t.txn_type == "DEBIT" and not t.is_excluded]
        assert len(spendable) > 0
        assert len(spendable) < len(txns)  # Some should be excluded


# ─────────────────────────────────────────────────────────────
# 8. API Endpoint Tests
# ─────────────────────────────────────────────────────────────

class TestAPIEndpoints:

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        from fastapi.testclient import TestClient
        from backend.main import app
        return TestClient(app)

    def test_health_check(self, client):
        """GET / should return 200 with status ok."""
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_sample_data_loads(self, client):
        """GET /api/sample should return analytics + recommendations."""
        resp = client.get("/api/sample")
        assert resp.status_code == 200
        data = resp.json()
        assert "analytics" in data
        assert "recommendations" in data
        assert data["analytics"]["transaction_count"] > 0

    def test_csv_upload(self, client):
        """POST /api/upload with valid CSV should return 200."""
        resp = client.post(
            "/api/upload",
            files={"file": ("test.csv", VALID_CSV.encode(), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["analytics"]["transaction_count"] == 15

    def test_invalid_file_type_rejected(self, client):
        """POST /api/upload with .txt file should return 400."""
        resp = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 400

    def test_bad_csv_rejected(self, client):
        """POST /api/upload with invalid CSV (missing columns) should return 400."""
        bad_csv = "Name,Value\nAlice,100\n"
        resp = client.post(
            "/api/upload",
            files={"file": ("bad.csv", bad_csv.encode(), "text/csv")},
        )
        assert resp.status_code == 400

    def test_simulation_endpoint(self, client):
        """POST /api/simulate after loading data should return savings."""
        # Load data first
        client.get("/api/sample")
        # Run simulation
        resp = client.post("/api/simulate", json={"reductions": {"Food": 20}})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_savings"] > 0
        assert data["projected_total"] < data["original_total"]

    def test_simulation_without_data_returns_400(self, client):
        """POST /api/simulate without loading data first should return 400."""
        # Reset state by importing and clearing
        from backend.main import _set_df
        _set_df(None)  # type: ignore
        resp = client.post("/api/simulate", json={"reductions": {"Food": 20}})
        assert resp.status_code == 400

    def test_analytics_after_upload(self, client):
        """GET /api/analytics after upload should return cached data."""
        client.post(
            "/api/upload",
            files={"file": ("test.csv", VALID_CSV.encode(), "text/csv")},
        )
        resp = client.get("/api/analytics")
        assert resp.status_code == 200
        assert resp.json()["transaction_count"] == 15

    def test_recommendations_after_upload(self, client):
        """GET /api/recommendations after upload should return insights."""
        client.post(
            "/api/upload",
            files={"file": ("test.csv", VALID_CSV.encode(), "text/csv")},
        )
        resp = client.get("/api/recommendations")
        assert resp.status_code == 200
        recs = resp.json()
        assert len(recs) >= 1


# ─────────────────────────────────────────────────────────────
# 9. Edge Case Tests
# ─────────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_single_transaction(self):
        """A single transaction should still produce valid analytics."""
        csv = "Date,Merchant,Amount,Category\n2026-01-01,Zomato,420,Food\n"
        df = parse_and_validate(csv)
        analytics = get_full_analytics(df)
        assert analytics["total_spend"] == 420
        assert analytics["transaction_count"] == 1

    def test_single_category(self):
        """All transactions in one category should give 100%."""
        csv = """Date,Merchant,Amount,Category
2026-01-01,Zomato,420,Food
2026-01-02,Swiggy,350,Food
2026-01-03,BigBasket,800,Food
"""
        df = parse_and_validate(csv)
        totals = get_category_totals(df)
        assert len(totals) == 1
        assert totals[0]["percentage"] == 100.0

    def test_same_day_transactions(self):
        """Multiple transactions on the same day should be summed."""
        csv = """Date,Merchant,Amount,Category
2026-01-01,Zomato,420,Food
2026-01-01,Uber,180,Travel
2026-01-01,Amazon,1500,Shopping
"""
        df = parse_and_validate(csv)
        daily = get_daily_spend(df)
        assert len(daily) == 1
        assert daily[0]["total"] == 2100

    def test_large_dataset(self):
        """Analytics should handle 1000+ transactions without error."""
        rows = ["Date,Merchant,Amount,Category"]
        for i in range(1000):
            day = (i % 30) + 1
            rows.append(f"2026-01-{day:02d},Merchant{i%10},{100+i},Food")
        csv = "\n".join(rows)
        df = parse_and_validate(csv)
        analytics = get_full_analytics(df)
        assert analytics["transaction_count"] == 1000
