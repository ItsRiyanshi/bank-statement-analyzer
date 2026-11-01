"""
FastAPI app entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

All dependent services (SQLite, Tesseract, PyMuPDF) are free/local.
Google Calendar sync uses Google's free API tier (see services/google_calendar.py).
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, CORS_ORIGIN_REGEX
from app.database import Base, engine
from app import models  # noqa: F401  (ensures models are registered)
from app.routers import upload, transactions, analytics, calendar, budget

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bank Statement Intelligence & Financial Health Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(calendar.router)
app.include_router(budget.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
