"""
Flags unusual spending using a simple, explainable z-score approach per
category: if a transaction's amount is more than N standard deviations
away from that category's historical mean, it's flagged as an anomaly.

This is intentionally simple/explainable (per the "Explainable summaries"
requirement) rather than a black-box model.
"""
from collections import defaultdict
from statistics import mean, pstdev
from typing import List, Dict

Z_THRESHOLD = 2.0


def detect_anomalies(transactions: List[Dict]) -> List[int]:
    by_category = defaultdict(list)
    for idx, txn in enumerate(transactions):
        if txn["amount"] < 0:  # only look at expenses
            by_category[txn["category"]].append((idx, abs(txn["amount"])))

    anomaly_indices = []
    for category, items in by_category.items():
        amounts = [a for _, a in items]
        if len(amounts) < 4:
            continue
        mu, sigma = mean(amounts), pstdev(amounts) or 1e-6
        for idx, amt in items:
            z = (amt - mu) / sigma
            if z > Z_THRESHOLD:
                anomaly_indices.append(idx)
    return anomaly_indices
