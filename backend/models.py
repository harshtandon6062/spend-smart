"""Pydantic models for SpendSmart API request/response contracts."""

from pydantic import BaseModel


class Transaction(BaseModel):
    """A single spending transaction."""
    date: str
    merchant: str
    amount: float
    category: str


class CategoryTotal(BaseModel):
    """Aggregated spend per category."""
    category: str
    total: float
    percentage: float
    count: int


class DailySpend(BaseModel):
    """Total spend for a single day."""
    date: str
    total: float


class MerchantTotal(BaseModel):
    """Aggregated spend per merchant."""
    merchant: str
    total: float
    count: int


class WeekdayWeekend(BaseModel):
    """Weekday vs weekend spending comparison."""
    weekday_avg: float
    weekend_avg: float
    weekday_total: float
    weekend_total: float
    categories: dict  # {category: {weekday: float, weekend: float}}


class Insight(BaseModel):
    """A single actionable savings recommendation."""
    title: str
    description: str
    savings_estimate: float
    icon: str
    priority: str  # "high" | "medium" | "low"
    category: str


class AnalyticsResponse(BaseModel):
    """Full analytics payload for the dashboard."""
    total_spend: float
    daily_average: float
    transaction_count: int
    date_range: dict  # {start: str, end: str}
    category_totals: list[CategoryTotal]
    daily_spend: list[DailySpend]
    top_merchants: list[MerchantTotal]
    weekday_vs_weekend: WeekdayWeekend


class UploadResponse(BaseModel):
    """Response returned after CSV upload or sample load."""
    analytics: AnalyticsResponse
    recommendations: list[Insight]


class SimulationRequest(BaseModel):
    """What-if simulation input: category -> % reduction."""
    reductions: dict[str, float]


class SimulationResponse(BaseModel):
    """What-if simulation results."""
    original_total: float
    projected_total: float
    total_savings: float
    category_savings: dict[str, float]
