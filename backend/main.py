"""
SpendSmart API — FastAPI backend for personalized spending analysis.
Provides CSV upload, analytics, recommendations, and what-if simulation.
"""

import os
import tempfile
from dotenv import load_dotenv

load_dotenv()  # Load .env for GROQ_API_KEY etc.

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from backend.analytics import parse_and_validate, get_full_analytics, simulate_savings
from backend.recommendations import generate_recommendations
from backend.models import (
    UploadResponse,
    AnalyticsResponse,
    SimulationRequest,
    SimulationResponse,
    Insight,
)

app = FastAPI(
    title="SpendSmart API",
    description="Personalized saving suggestion engine — analyze spending, get insights.",
    version="1.0.0",
)

# CORS — allow all origins (same-domain on Vercel, localhost in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for current session's data
_current_df: pd.DataFrame | None = None


def _set_df(df: pd.DataFrame):
    """Store the current DataFrame in memory."""
    global _current_df
    _current_df = df


def _get_df() -> pd.DataFrame:
    """Retrieve the current DataFrame, or raise 400 if none loaded."""
    if _current_df is None:
        raise HTTPException(
            status_code=400,
            detail="No data loaded. Upload a CSV or load sample data first."
        )
    return _current_df


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "app": "SpendSmart API", "version": "1.0.0"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV or PDF (PhonePe/UPI statement) file.
    Parses, validates, and returns full analytics + recommendations.
    """
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Only CSV and PDF files are supported.")

    try:
        raw_bytes = await file.read()

        if filename.endswith(".pdf"):
            # Use the UPI converter to parse PDF → DataFrame
            df = _parse_pdf_to_df(raw_bytes)
        else:
            # Standard CSV parsing
            content = raw_bytes.decode("utf-8")
            df = parse_and_validate(content)

        _set_df(df)

        analytics = get_full_analytics(df)
        recommendations = generate_recommendations(df)

        return UploadResponse(
            analytics=AnalyticsResponse(**analytics),
            recommendations=[Insight(**r) for r in recommendations],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def _parse_pdf_to_df(pdf_bytes: bytes) -> pd.DataFrame:
    """
    Parse a PhonePe/UPI statement PDF into a pandas DataFrame.
    Uses the upi_converter module to extract and categorize transactions,
    then filters to only spendable (non-excluded DEBIT) transactions.
    """
    from backend.pdf_parser import parse_pdf

    # Write bytes to a temp file for pdfplumber
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        transactions = parse_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)

    # Filter to spendable transactions only
    spendable = [
        t for t in transactions
        if t.txn_type == "DEBIT" and not t.is_excluded
    ]

    if not spendable:
        raise ValueError("No spendable transactions found in PDF. The file may not be a valid UPI statement.")

    # Build DataFrame directly (avoids CSV escaping issues with commas in merchant names)
    rows = [
        {"Date": t.date, "Merchant": t.merchant, "Amount": t.amount, "Category": t.category}
        for t in spendable
    ]

    df = pd.DataFrame(rows)
    df["Merchant"] = df["Merchant"].astype(str).str.strip()
    df["Category"] = df["Category"].astype(str).str.strip()
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Amount", "Date"])
    df = df[df["Amount"] > 0]
    df = df.sort_values("Date").reset_index(drop=True)
    df["DayOfWeek"] = df["Date"].dt.dayofweek
    df["IsWeekend"] = df["DayOfWeek"].isin([5, 6])
    df["DateStr"] = df["Date"].dt.strftime("%Y-%m-%d")

    return df


@app.get("/api/sample", response_model=UploadResponse)
def load_sample():
    """Load the bundled sample dataset and return analytics + recommendations."""
    sample_path = os.path.join(os.path.dirname(__file__), "sample_data.csv")

    if not os.path.exists(sample_path):
        raise HTTPException(status_code=500, detail="Sample data file not found.")

    try:
        with open(sample_path, "r") as f:
            content = f.read()

        df = parse_and_validate(content)
        _set_df(df)

        analytics = get_full_analytics(df)
        recommendations = generate_recommendations(df)

        return UploadResponse(
            analytics=AnalyticsResponse(**analytics),
            recommendations=[Insight(**r) for r in recommendations],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/analytics", response_model=AnalyticsResponse)
def get_analytics():
    """Return analytics for the currently loaded dataset."""
    df = _get_df()
    analytics = get_full_analytics(df)
    return AnalyticsResponse(**analytics)


@app.get("/api/recommendations", response_model=list[Insight])
def get_recommendations():
    """Return recommendations for the currently loaded dataset."""
    df = _get_df()
    recommendations = generate_recommendations(df)
    return [Insight(**r) for r in recommendations]


@app.post("/api/simulate", response_model=SimulationResponse)
def run_simulation(req: SimulationRequest):
    """
    Run a what-if savings simulation.
    Accepts category reduction percentages and returns projected savings.
    """
    df = _get_df()

    # Validate reduction percentages
    for cat, pct in req.reductions.items():
        if pct < 0 or pct > 100:
            raise HTTPException(
                status_code=400,
                detail=f"Reduction for '{cat}' must be between 0 and 100, got {pct}."
            )

    result = simulate_savings(df, req.reductions)
    return SimulationResponse(**result)


@app.get("/api/report/ai")
async def get_ai_report():
    """
    Generate a personalized financial narrative report using Groq LLM.
    Requires data to be loaded first (via upload or sample).
    """
    from backend.ai_report import generate_ai_report

    df = _get_df()
    analytics = get_full_analytics(df)
    recommendations = generate_recommendations(df)

    try:
        report_markdown = await generate_ai_report(analytics, recommendations)
        return {"report": report_markdown}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI report generation failed: {str(e)}"
        )
