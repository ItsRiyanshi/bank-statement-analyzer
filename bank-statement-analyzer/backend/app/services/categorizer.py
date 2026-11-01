"""
Rule-based / keyword-based expense categorizer.

Free & local (no LLM API calls needed). Swap `KEYWORD_MAP` lookups for an
embeddings-based classifier later if you want smarter matching -- the
pitch deck mentions this as a "Medium-High feasibility" upgrade path.
"""
from typing import Dict, List

KEYWORD_MAP: Dict[str, List[str]] = {
    "Food & Dining": ["swiggy", "zomato", "restaurant", "cafe", "starbucks", "dominos", "mcdonald", "food"],
    "Groceries": ["bigbasket", "grofers", "blinkit", "dmart", "grocery", "supermarket", "zepto"],
    "Transport": ["uber", "ola", "rapido", "metro", "petrol", "fuel", "irctc", "fastag"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "mall", "shopping"],
    "Bills & Utilities": ["electricity", "water bill", "broadband", "recharge", "airtel", "jio", "vi ", "gas bill"],
    "Rent & Housing": ["rent", "landlord", "housing society", "maintenance"],
    "EMI & Loans": ["emi", "loan", "installment"],
    "Subscriptions": ["netflix", "spotify", "prime video", "hotstar", "youtube premium", "subscription"],
    "Entertainment": ["movie", "bookmyshow", "pvr", "inox", "gaming"],
    "Health": ["pharmacy", "hospital", "clinic", "apollo", "medplus", "doctor"],
    "Education": ["tuition", "course", "udemy", "coursera", "school fee", "college"],
    "Income": ["salary", "credited", "refund", "cashback", "interest earned"],
    "Transfers": ["upi-", "neft", "imps", "rtgs", "transfer"],
}


def categorize(description: str) -> str:
    text = description.lower()
    for category, keywords in KEYWORD_MAP.items():
        if any(kw in text for kw in keywords):
            return category
    return "Other"


def categorize_batch(transactions: List[dict]) -> List[dict]:
    for txn in transactions:
        txn["category"] = categorize(txn["description"])
    return transactions
