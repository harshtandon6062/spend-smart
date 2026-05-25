"""
AI Report Generator for SpendSmart.
Uses Groq's LLM API to produce a personalized, narrative financial report.
"""

import os
import httpx

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


async def generate_ai_report(analytics: dict, recommendations: list[dict]) -> str:
    """
    Send analytics + recommendations to Groq LLM and get back
    a well-structured, personalized financial narrative report.
    """
    # Build the data summary for the prompt
    cat_lines = "\n".join(
        f"  - {c['category']}: ₹{c['total']:,.0f} ({c['percentage']}%, {c['count']} txns)"
        for c in analytics["category_totals"]
    )

    merchant_lines = "\n".join(
        f"  - {m['merchant']}: ₹{m['total']:,.0f} ({m['count']} visits)"
        for m in analytics["top_merchants"]
    )

    rec_lines = "\n".join(
        f"  - [{r['priority'].upper()}] {r['title']}: {r['description']} "
        f"(Est. savings: ₹{r['savings_estimate']:,.0f})"
        for r in recommendations
    )

    ww = analytics["weekday_vs_weekend"]

    prompt = f"""You are a personal finance advisor writing a professional financial report for a user. 
You have been given their complete spending data and analytics. Write a comprehensive, personalized report.

## USER'S SPENDING DATA

**Period**: {analytics['date_range']['start']} to {analytics['date_range']['end']}
**Total Spend**: ₹{analytics['total_spend']:,.0f}
**Daily Average**: ₹{analytics['daily_average']:,.0f}
**Total Transactions**: {analytics['transaction_count']}
**Weekday Avg/Day**: ₹{ww['weekday_avg']:,.0f}
**Weekend Avg/Day**: ₹{ww['weekend_avg']:,.0f}

### Category Breakdown:
{cat_lines}

### Top Merchants:
{merchant_lines}

### System-Generated Recommendations:
{rec_lines}

## INSTRUCTIONS

Write a **personalized financial health report** in markdown with these sections:

1. **Executive Summary** (2-3 sentences — overall financial health verdict)
2. **Spending Profile** (analyze their category distribution — what stands out, what's healthy, what's concerning)
3. **Key Patterns Detected** (weekend vs weekday behavior, merchant habits, any concentration risks)
4. **Top 3 Actionable Recommendations** (specific, numbered, with estimated monthly savings in ₹ — be concrete, not generic)
5. **30-Day Challenge** (one specific, measurable challenge they can start today)

RULES:
- Use ₹ for all currency, Indian context (UPI, metro, Swiggy, etc.)
- Be direct and specific — reference actual numbers from their data
- Keep it under 500 words
- Use a warm but professional tone — like a smart friend who's good with money
- Do NOT use generic advice. Every sentence should reference THEIR specific data.
- Use markdown headers (##), bold, and bullet points for readability
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a concise, data-driven personal finance advisor. You write clear, actionable reports referencing specific numbers from the user's data. Output in clean markdown."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GROQ_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]
