# 💰 SpendSmart — Personalized Saving Suggestion Engine

A full-stack application that analyzes your spending data (CSV or PhonePe/UPI PDF statements) and generates **actionable, data-driven savings recommendations** with estimated monthly impact.

Built for the **Fiserv Hackathon 2026** (Stage 2).

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📊 **Smart Analytics** | Category breakdown, daily trends, top merchants, weekday vs weekend patterns |
| 💡 **8-Rule Recommendation Engine** | High-category cuts, weekend spikes, subscription sniffing, outlier detection (IQR), merchant concentration, travel optimization, daily budget, savings targets |
| 🎚️ **What-If Simulator** | Adjust category spending with sliders and see projected monthly savings in real-time |
| 💰 **Budget Planner** | Set per-category budgets with live progress bars |
| 📄 **PDF Report Export** | Clean, structured financial report (not a screenshot) |
| 📱 **PhonePe PDF Upload** | Directly upload UPI statement PDFs — auto-categorized into 17 spending categories |
| 🧪 **57 Automated Tests** | Full pytest suite: unit → integration → API → edge cases |

---

## 🏗️ Architecture

```
┌─────────────────────────┐      ┌──────────────────────────┐
│   React Frontend (:5173)│◄────►│  FastAPI Backend (:8000)  │
│   Vite + Chart.js       │ REST │  pandas + numpy           │
│   react-chartjs-2       │ API  │  pdfplumber               │
└─────────────────────────┘      └──────────────────────────┘
```

**Backend (Python)**
- `analytics.py` — pandas aggregations, IQR outlier detection, subscription sniffing
- `recommendations.py` — 8-rule recommendation engine with priority sorting
- `pdf_parser.py` — PhonePe/UPI PDF → categorized transactions (17 categories)
- `main.py` — FastAPI with 5 REST endpoints + CORS

**Frontend (React)**
- Interactive dashboard with 4 Chart.js visualizations
- Premium dark-mode UI with glassmorphism design
- Real-time savings simulator with debounced API calls
- Structured PDF report generation (jsPDF + html2canvas)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd spend_smart
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

### Run Tests
```bash
source venv/bin/activate
python -m pytest tests/ -v
```

---

## 📁 Project Structure

```
spend_smart/
├── backend/
│   ├── main.py              # FastAPI app (5 endpoints)
│   ├── analytics.py         # pandas analytics engine
│   ├── recommendations.py   # 8-rule recommendation engine
│   ├── pdf_parser.py        # PhonePe PDF → CSV converter
│   ├── models.py            # Pydantic request/response models
│   ├── sample_data.csv      # 70 demo transactions
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React components (12 files)
│   │   ├── services/api.js  # axios API layer
│   │   ├── utils/formatters.js
│   │   ├── App.jsx
│   │   └── index.css        # Design system
│   ├── package.json
│   └── vite.config.js       # API proxy config
├── tests/
│   └── test_spendsmart.py   # 57 pytest test cases
└── README.md
```

---

## 🧪 Testing

**57 tests across 9 categories — 100% pass rate**

| Layer | Tests | Covers |
|-------|-------|--------|
| Unit | 31 | CSV parsing, IQR outliers, subscription detection, simulation math |
| Integration | 12 | Recommendation rules, analytics pipeline |
| API | 9 | All 5 endpoints, error handling |
| Edge Cases | 5 | Single transaction, 1000+ rows, bad data |

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/api/upload` | Upload CSV or PDF file |
| `GET` | `/api/sample` | Load demo dataset |
| `GET` | `/api/analytics` | Get analytics for loaded data |
| `GET` | `/api/recommendations` | Get savings recommendations |
| `POST` | `/api/simulate` | Run what-if savings simulation |

Swagger docs: **http://localhost:8000/docs**

---

## 🎯 Hackathon Scoring Alignment

| Criteria | Weight | How We Address It |
|----------|--------|-------------------|
| Insight Quality | 40% | 8-rule engine, IQR outliers, subscription sniffing, weekday/weekend patterns |
| Visualization | 30% | 4 interactive charts, premium dark UI, PDF reports |
| Logic & Accuracy | 20% | pandas/numpy analytics, simulation math, 57 automated tests |
| Code Quality | 10% | Clean separation, type hints, docstrings, modular architecture |

---

## 👨‍💻 Tech Stack

**Backend:** Python, FastAPI, pandas, numpy, pdfplumber  
**Frontend:** React, Vite, Chart.js, axios, jsPDF  
**Testing:** pytest, FastAPI TestClient
