"""
Endpoints for uploading bank statements (PDF) or pasted SMS text, running
extraction -> categorization -> recurring/anomaly detection, and saving
everything to the database.
"""
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
import hashlib

from app.database import get_db
from app import models
from app.services.pdf_extractor import extract_transactions_from_pdf, extract_transactions_from_sms
from app.services.categorizer import categorize_batch
from app.services.recurring_detector import detect_recurring
from app.services.anomaly_detector import detect_anomalies

router = APIRouter(prefix="/api/upload", tags=["upload"])


def _persist(db: Session, statement: models.Statement, raw_txns: list):
    raw_txns = categorize_batch(raw_txns)
    recurring_idx = set(detect_recurring(raw_txns))
    for i, t in enumerate(raw_txns):
        t["is_recurring"] = i in recurring_idx
    anomaly_idx = set(detect_anomalies(raw_txns))

    saved = []
    for i, t in enumerate(raw_txns):
        txn = models.Transaction(
            statement_id=statement.id,
            date=t["date"],
            description=t["description"],
            amount=t["amount"],
            category=t["category"],
            is_recurring=i in recurring_idx,
            is_anomaly=i in anomaly_idx,
            raw_text=t.get("raw_text"),
        )
        db.add(txn)
        saved.append(txn)
    db.commit()
    return saved


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")
    content = await file.read()

    content_hash = hashlib.sha256(content).hexdigest()
    existing = (
        db.query(models.Statement)
        .filter(models.Statement.content_hash == content_hash)
        .first()
    )
    if existing:
        raise HTTPException(
            409,
            f"This exact file was already uploaded on "
            f"{existing.uploaded_at:%Y-%m-%d %H:%M} (statement_id={existing.id}). "
            "Skipping to avoid double-counting transactions.",
        )

    statement = models.Statement(
        filename=file.filename,
        source_type="pdf",
        content_hash=content_hash,
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)

    raw_txns, balance_info = extract_transactions_from_pdf(content)
    if not raw_txns:
        raise HTTPException(
            422,
            "No transactions could be parsed from this PDF. The layout may not be "
            "supported yet -- see STATEMENT_PATTERNS in pdf_extractor.py.",
        )

    opening = balance_info.get("opening_balance")
    closing = balance_info.get("closing_balance")
    if closing is None and opening is not None and raw_txns:
        closing = round(float(opening + sum(t.get("amount", 0) for t in raw_txns)), 2)

    statement.opening_balance = opening
    statement.closing_balance = closing
    db.commit()

    saved = _persist(db, statement, raw_txns)
    return {"statement_id": statement.id, "transactions_added": len(saved)}


@router.post("/sms")
async def upload_sms(sms_texts: List[str] = Form(...), db: Session = Depends(get_db)):
    statement = models.Statement(filename="sms_import", source_type="sms")
    db.add(statement)
    db.commit()
    db.refresh(statement)

    raw_txns = extract_transactions_from_sms(sms_texts)
    if not raw_txns:
        raise HTTPException(422, "No transactions could be parsed from the provided SMS text.")
    saved = _persist(db, statement, raw_txns)
    return {"statement_id": statement.id, "transactions_added": len(saved)}