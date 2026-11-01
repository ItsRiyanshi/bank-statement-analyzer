"""
Detects recurring payments (subscriptions, EMIs, rent) by clustering
transactions with similar descriptions and checking whether they repeat
at a roughly fixed interval (monthly / weekly) with a similar amount.

Free, local, pure pandas/numpy -- no ML service required.
"""
from collections import defaultdict
from statistics import mean, pstdev
from typing import List, Dict
import re

# SMS-imported transactions keep the full raw message as their
# description (see extract_transactions_from_sms), which includes the
# transaction date spelled out with a month name, e.g. "...on
# 05-Jun-2026...". Digits alone don't cover that, so without stripping
# month words too, the same recurring charge normalizes to a different
# key every month and recurring detection silently never fires for any
# SMS-derived transaction.
_MONTH_WORDS_RE = re.compile(
    r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)\b"
)


def _normalize_desc(desc: str) -> str:
    # Strip trailing reference numbers / dates so "UPI-NETFLIX-4521" and
    # "UPI-NETFLIX-9981" both normalize to "upi-netflix"
    text = desc.lower()
    text = re.sub(r"\d+", "", text)
    text = _MONTH_WORDS_RE.sub("", text)
    text = re.sub(r"[^a-z\s-]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_recurring(transactions: List[Dict]) -> List[int]:
    """Returns a list of transaction indices that look recurring."""
    groups = defaultdict(list)
    for idx, txn in enumerate(transactions):
        key = _normalize_desc(txn["description"])
        groups[key].append(idx)

    recurring_indices = []
    for key, idxs in groups.items():
        if len(idxs) < 2:
            continue
        amounts = [abs(transactions[i]["amount"]) for i in idxs]
        dates = sorted(transactions[i]["date"] for i in idxs)
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]

        amount_consistent = (pstdev(amounts) / (mean(amounts) or 1)) < 0.15 if len(amounts) > 1 else True
        gap_consistent = any(25 <= g <= 35 for g in gaps) or any(6 <= g <= 8 for g in gaps)

        if amount_consistent and gap_consistent:
            recurring_indices.extend(idxs)

    return recurring_indices
