# AI-Based Bank Statement Intelligence & Financial Health Analyzer

A full-stack app that turns raw bank statements (PDF/SMS) into spending
insights, a financial health score, recurring-payment/anomaly detection,
and a calendar-aware "Safe-to-Spend" daily budget planner.

Built entirely with **free tools and free-tier services** — no paid APIs
required.

## Stack

| Layer | Tech | Why (free) |
|---|---|---|
| Frontend | React + Vite + Tailwind + Recharts | Open source |
| Backend | Python + FastAPI | Open source |
| Document parsing | PyMuPDF + Tesseract OCR | Open source, local |
| Database | SQLite | File-based, zero cost |
| Calendar sync | Google Calendar API | Free tier for personal use |
| Categorization/forecasting | Rule-based + statistics (pandas/numpy) | No LLM API calls needed |

## Folder structure

```
bank-statement-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── config.py                # env/config loader
│   │   ├── database.py              # SQLAlchemy engine/session
│   │   ├── models.py                # ORM models (Statement, Transaction, CalendarEvent, BudgetPlan)
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── upload.py            # POST /api/upload/pdf, /sms
│   │   │   ├── transactions.py      # CRUD /api/transactions
│   │   │   ├── analytics.py         # /api/analytics/* (summary, health score, recurring, anomalies)
│   │   │   ├── calendar.py          # /api/calendar/* (events, google sync, safe-to-spend)
│   │   │   └── budget.py            # /api/budget/plan (rest-of-month planner)
│   │   └── services/
│   │       ├── pdf_extractor.py     # PyMuPDF + Tesseract OCR + regex parsing
│   │       ├── categorizer.py       # keyword-based expense categorization
│   │       ├── recurring_detector.py# clusters similar txns to find recurring payments
│   │       ├── anomaly_detector.py  # z-score based unusual-spend detection
│   │       ├── health_score.py      # 0-100 explainable financial health score
│   │       ├── forecaster.py        # weekday-average based spend forecasting
│   │       ├── safe_to_spend.py     # daily safe-to-spend calculation
│   │       ├── budget_planner.py    # calendar-aware adaptive day-by-day budget
│   │       ├── google_calendar.py   # Google Calendar API (free tier) integration
│   │       └── summarizer.py        # template-based plain-English summaries
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.jsx / App.jsx
│   │   ├── api/client.js            # axios wrapper for all backend endpoints
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx        # main analytics dashboard
│   │   │   ├── UploadPage.jsx       # PDF upload
│   │   │   └── CalendarPlanner.jsx  # events + day-by-day budget plan
│   │   ├── components/              # HealthScoreGauge, CategoryChart, SpendingTrend,
│   │   │                             # SafeToSpendCard, RecurringPayments, AnomalyAlerts,
│   │   │                             # SummaryPanel, TransactionsTable, UploadStatement,
│   │   │                             # CalendarBudgetPlanner, Navbar
│   │   └── hooks/useTransactions.js # data-fetching hook for the dashboard
│   ├── package.json
│   └── .env.example
└── README.md
```

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Tesseract OCR must also be installed on your system (free):
#   macOS:   brew install tesseract
#   Ubuntu:  sudo apt install tesseract-ocr
#   Windows: https://github.com/UB-Mannheim/tesseract/wiki

cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs are auto-generated at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Visit `http://localhost:5173`.

### 3. (Optional) Google Calendar sync

1. Go to https://console.cloud.google.com/ → create a project (free).
2. Enable the **Google Calendar API**.
3. Create OAuth 2.0 credentials → type "Desktop app" → download JSON.
4. Save it as `backend/credentials.json`.
5. Click "Sync Google Calendar" in the app's Calendar Planner page — a
   browser window will ask you to authorize once; after that a
   `token.json` is cached and no more logins are needed.

## How each pitch-deck feature maps to code

| Feature | Where |
|---|---|
| Extract transactions from PDFs/SMS | `services/pdf_extractor.py` |
| Auto-categorize expenses | `services/categorizer.py` |
| Identify recurring payments | `services/recurring_detector.py` |
| Detect unusual spending | `services/anomaly_detector.py` |
| Monthly spending analytics | `routers/analytics.py` → `/api/analytics/summary` |
| Financial health score | `services/health_score.py` |
| Understandable summaries | `services/summarizer.py` |
| Calendar integration + spend prediction | `services/google_calendar.py`, `services/forecaster.py` |
| Safe-to-Spend predictor | `services/safe_to_spend.py` |
| Adaptive calendar-aware budget planning | `services/budget_planner.py` |

## Notes / next steps

- The PDF regex patterns in `pdf_extractor.py` cover a common layout;
  add more patterns to `STATEMENT_PATTERNS` as you test real statements
  from different banks (this is the "layout-agnostic" upgrade path
  mentioned in the pitch deck).
- All financial data stays local in SQLite — for production, add
  encryption at rest and per-user auth before storing real statements.
- Forecasting is intentionally simple (weekday averages) so it's free,
  fast, and explainable; swap in `statsmodels` (also free) for a proper
  ARIMA model if you want more accuracy.
