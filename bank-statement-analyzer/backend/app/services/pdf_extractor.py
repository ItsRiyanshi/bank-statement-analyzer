import re
import io
from datetime import date
from typing import List, Dict, Optional, Tuple

import fitz
import pytesseract
from PIL import Image


# ============================================================
# DATE PARSING
# ============================================================

MONTH_LOOKUP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_MONTH_RE = "|".join(
    sorted(MONTH_LOOKUP.keys(), key=len, reverse=True)
)


DATE_TOKEN_PATTERNS = [
    (
        re.compile(
            r"^(\d{4})[/\-.]+(\d{1,2})[/\-.]+(\d{1,2})$"
        ),
        "ymd",
    ),
    (
        re.compile(
            r"^(\d{1,2})[/\-.]+(\d{1,2})[/\-.]+(\d{2,4})$"
        ),
        "dmy",
    ),
    (
        re.compile(
            rf"^(\d{{1,2}})(?:st|nd|rd|th)?"
            rf"[\s\-,]*({_MONTH_RE})"
            rf"[\s\-,]*(\d{{2,4}})$",
            re.IGNORECASE,
        ),
        "d_mon_y",
    ),
    (
        re.compile(
            rf"^({_MONTH_RE})[\s\-,]+"
            rf"(\d{{1,2}})(?:st|nd|rd|th)?"
            rf"[\s,]+(\d{{2,4}})$",
            re.IGNORECASE,
        ),
        "mon_d_y",
    ),
]


DATE_SEARCH_PATTERNS = [
    (
        re.compile(
            r"(\d{4})[/\-.]+(\d{1,2})[/\-.]+(\d{1,2})"
        ),
        "ymd",
    ),
    (
        re.compile(
            r"(\d{1,2})[/\-.]+(\d{1,2})[/\-.]+(\d{2,4})"
        ),
        "dmy",
    ),
    (
        re.compile(
            rf"(\d{{1,2}})(?:st|nd|rd|th)?"
            rf"[\s\-,]*({_MONTH_RE})"
            rf"[\s\-,]*(\d{{2,4}})",
            re.IGNORECASE,
        ),
        "d_mon_y",
    ),
    (
        re.compile(
            rf"({_MONTH_RE})[\s\-,]+"
            rf"(\d{{1,2}})(?:st|nd|rd|th)?"
            rf"[\s,]+(\d{{2,4}})",
            re.IGNORECASE,
        ),
        "mon_d_y",
    ),
]


def _normalize_year(year: int) -> int:
    if year < 100:
        return 2000 + year if year < 70 else 1900 + year
    return year


def _build_date(
    kind: str,
    groups: Tuple[str, ...]
) -> Optional[date]:

    try:
        if kind == "ymd":
            year = int(groups[0])
            month = int(groups[1])
            day = int(groups[2])

        elif kind == "dmy":
            day = int(groups[0])
            month = int(groups[1])
            year = int(groups[2])

        elif kind == "d_mon_y":
            day = int(groups[0])
            month = MONTH_LOOKUP.get(groups[1].lower())
            year = int(groups[2])

        elif kind == "mon_d_y":
            month = MONTH_LOOKUP.get(groups[0].lower())
            day = int(groups[1])
            year = int(groups[2])

        else:
            return None

        if not month:
            return None

        year = _normalize_year(year)

        return date(year, month, day)

    except (ValueError, TypeError):
        return None


def _parse_date_token(token: str) -> Optional[date]:

    token = token.strip()

    for pattern, kind in DATE_TOKEN_PATTERNS:

        match = pattern.match(token)

        if match:
            parsed = _build_date(
                kind,
                match.groups()
            )

            if parsed:
                return parsed

    return None


def _find_date_in_text(text: str) -> Optional[date]:

    for pattern, kind in DATE_SEARCH_PATTERNS:

        match = pattern.search(text)

        if match:
            parsed = _build_date(
                kind,
                match.groups()
            )

            if parsed:
                return parsed

    return None


def _parse_date(raw: str) -> Optional[date]:
    return _parse_date_token(raw)


# ============================================================
# AMOUNT PARSING
# ============================================================

CURRENCY_PREFIX = r"(?:₹|Rs\.?|INR)\s?"

AMOUNT_CORE = r"[\d,]+(?:\.\d{1,2})?"

AMOUNT_RE = (
    rf"(?:{CURRENCY_PREFIX})?"
    rf"(?P<amount>{AMOUNT_CORE})"
)

_AMOUNT_TOKEN_RE = re.compile(
    rf"^(?:{CURRENCY_PREFIX})?"
    rf"({AMOUNT_CORE})$"
)


def _to_float(raw_amount: str) -> float:

    return float(
        raw_amount
        .replace(",", "")
        .replace("₹", "")
        .strip()
    )


def _is_amount_token(token: str) -> bool:

    return bool(
        _AMOUNT_TOKEN_RE.match(
            token.strip()
        )
    )


def _amount_value(token: str) -> Optional[float]:

    match = _AMOUNT_TOKEN_RE.match(
        token.strip()
    )

    if not match:
        return None

    return _to_float(match.group(1))


def _is_empty_column(token: str) -> bool:

    token = token.strip()

    return (
        token in ("", "-", "--", "—")
        or (
            _is_amount_token(token)
            and _amount_value(token) == 0
        )
    )


# ============================================================
# CREDIT / DEBIT KEYWORDS
# ============================================================

DEBIT_KEYWORDS = [
    "debit",
    "debited",
    "withdrawn",
    "withdrawal",
    "spent",
    "paid",
    "purchase",
    "sent",
    "dr",
    "emi",
    "bill payment",
    "premium",
    "rent",
    "grocery",
    "electricity",
    "food",
    "shopping",
    "fuel",
    "restaurant",
    "pharmacy",
    "mobile",
    "netflix",
]

CREDIT_KEYWORDS = [
    "credit",
    "credited",
    "deposited",
    "deposit",
    "received",
    "refund",
    "refunded",
    "cr",
    "salary",
    "cashback",
    "interest earned",
    "interest credit",
    "reversal",
    "bonus",
]


def _contains_keyword(text: str, keywords: List[str]) -> bool:
    """
    Whole-word keyword match. Plain substring checks (`kw in text`) let
    short tokens like "cr"/"dr" match inside unrelated words -- e.g.
    "Netflix Subscription" contains "cr" (subs-CR-iption) and "Address
    Update" contains "dr" (ad-DR-ess) -- silently flipping the
    credit/debit direction. Word boundaries prevent that.
    """

    for keyword in keywords:

        if re.search(
            rf"\b{re.escape(keyword)}\b",
            text,
            re.IGNORECASE,
        ):
            return True

    return False


# ============================================================
# STATEMENT PATTERNS
# ============================================================

_DATE_GRP = (
    r"(?P<date>"
    r"\d{1,2}[/\-.]+\d{1,2}[/\-.]+\d{2,4}"
    r"|"
    r"\d{4}[/\-.]+\d{1,2}[/\-.]+\d{1,2}"
    r"|"
    rf"\d{{1,2}}(?:st|nd|rd|th)?"
    rf"[\s\-,]*(?:{_MONTH_RE})"
    rf"[\s\-,]*\d{{2,4}}"
    r"|"
    rf"(?:{_MONTH_RE})"
    rf"[\s\-,]+\d{{1,2}}"
    rf"(?:st|nd|rd|th)?"
    rf"[\s,]+\d{{2,4}}"
    r")"
)

_TOKEN_OR_DASH = rf"(?:{AMOUNT_CORE}|-{{1,2}}|—)"


# ============================================================
# MATCH STATEMENT LINE
# ============================================================

def _match_statement_line(
    line: str
) -> Optional[Dict]:

    line = line.strip()

    # --------------------------------------------------------
    # Date + Description + Transaction Amount + Balance
    # --------------------------------------------------------

    two_amount_pattern = re.compile(
        rf"^{_DATE_GRP}\s+"
        rf"(?P<desc>.*?)\s+"
        rf"(?P<amount1>{AMOUNT_CORE})\s+"
        rf"(?P<balance>{AMOUNT_CORE})"
        rf"(?:\s+\S.*)?$",
        re.IGNORECASE,
    )

    match = two_amount_pattern.match(line)

    if match:

        groups = match.groupdict()

        parsed_date = _parse_date_token(
            groups["date"]
        )

        if parsed_date:

            description = groups["desc"].strip()

            amount = _to_float(
                groups["amount1"]
            )

            # Determine credit/debit from description
            lower_desc = description.lower()

            if _contains_keyword(
                lower_desc, CREDIT_KEYWORDS
            ):
                drcr = "Cr"

            elif _contains_keyword(
                lower_desc, DEBIT_KEYWORDS
            ):
                drcr = "Dr"

            else:
                drcr = None

            return {
                "date": parsed_date,
                "description": description,
                "amount": amount,
                "drcr": drcr,
                "raw_text": line,
                "balance": _amount_value(groups["balance"]),
            }

    # --------------------------------------------------------
    # Date + Debit + Credit + Balance
    # --------------------------------------------------------

    three_column_pattern = re.compile(
        rf"^{_DATE_GRP}\s+"
        rf"(?P<desc>.+?)\s+"
        rf"(?P<debit>{_TOKEN_OR_DASH})\s+"
        rf"(?P<credit>{_TOKEN_OR_DASH})\s+"
        rf"(?P<balance>{AMOUNT_CORE})"
        rf"(?:\s+\S.*)?$",
        re.IGNORECASE,
    )

    match = three_column_pattern.match(line)

    if match:

        groups = match.groupdict()

        parsed_date = _parse_date_token(
            groups["date"]
        )

        if not parsed_date:
            return None

        description = groups["desc"].strip()

        debit = (
            None
            if _is_empty_column(groups["debit"])
            else _amount_value(groups["debit"])
        )

        credit = (
            None
            if _is_empty_column(groups["credit"])
            else _amount_value(groups["credit"])
        )

        if debit is not None:

            return {
                "date": parsed_date,
                "description": description,
                "amount": debit,
                "drcr": "Dr",
                "raw_text": line,
                "balance": _amount_value(groups["balance"]),
            }

        if credit is not None:

            return {
                "date": parsed_date,
                "description": description,
                "amount": credit,
                "drcr": "Cr",
                "raw_text": line,
                "balance": _amount_value(groups["balance"]),
            }

    # --------------------------------------------------------
    # Date + Dr/Cr + Description + Amount
    # --------------------------------------------------------

    drcr_pattern = re.compile(
        rf"^{_DATE_GRP}\s+"
        rf"(?P<drcr>Dr|Cr|Debit|Credit)\s+"
        rf"(?P<desc>.+?)\s+"
        rf"{AMOUNT_RE}"
        rf"(?:\s+\S.*)?$",
        re.IGNORECASE,
    )

    match = drcr_pattern.match(line)

    if match:

        groups = match.groupdict()

        parsed_date = _parse_date_token(
            groups["date"]
        )

        if not parsed_date:
            return None

        return {
            "date": parsed_date,
            "description": groups["desc"].strip(),
            "amount": _to_float(
                groups["amount"]
            ),
            "drcr": groups["drcr"],
            "raw_text": line,
        }

    # --------------------------------------------------------
    # Date + Description + Signed Amount
    # --------------------------------------------------------

    signed_pattern = re.compile(
        rf"^{_DATE_GRP}\s+"
        rf"(?P<desc>.+?)\s+"
        rf"(?P<sign>[+-])\s?"
        rf"{AMOUNT_RE}"
        rf"(?:\s+\S.*)?$",
        re.IGNORECASE,
    )

    match = signed_pattern.match(line)

    if match:

        groups = match.groupdict()

        parsed_date = _parse_date_token(
            groups["date"]
        )

        if not parsed_date:
            return None

        amount = _to_float(
            groups["amount"]
        )

        if groups["sign"] == "-":
            drcr = "Dr"
        else:
            drcr = "Cr"

        return {
            "date": parsed_date,
            "description": groups["desc"].strip(),
            "amount": amount,
            "drcr": drcr,
            "raw_text": line,
        }

    # --------------------------------------------------------
    # Date + Description + Amount
    # --------------------------------------------------------

    single_amount_pattern = re.compile(
        rf"^{_DATE_GRP}\s+"
        rf"(?P<desc>.+?)\s+"
        rf"{AMOUNT_RE}"
        rf"\s*(?P<drcr>Dr|Cr|Debit|Credit)?\s*$",
        re.IGNORECASE,
    )

    match = single_amount_pattern.match(line)

    if match:

        groups = match.groupdict()

        parsed_date = _parse_date_token(
            groups["date"]
        )

        if not parsed_date:
            return None

        return {
            "date": parsed_date,
            "description": groups["desc"].strip(),
            "amount": _to_float(
                groups["amount"]
            ),
            "drcr": groups.get("drcr"),
            "raw_text": line,
        }

    return None


# ============================================================
# INFER SIGN
# ============================================================

def _infer_sign(
    amount: float,
    drcr: Optional[str],
    description: str
) -> float:

    if drcr:

        drcr_lower = drcr.lower()

        if drcr_lower.startswith(
            ("cr", "credit")
        ):
            return abs(amount)

        return -abs(amount)

    text = description.lower()

    if _contains_keyword(text, CREDIT_KEYWORDS):
        return abs(amount)

    if _contains_keyword(text, DEBIT_KEYWORDS):
        return -abs(amount)

    return -abs(amount)


# ============================================================
# COLUMN FALLBACK
# ============================================================

_COLUMN_SPLIT_RE = re.compile(
    r"\s{2,}|\t+"
)


def _parse_line_by_columns(
    line: str
) -> Optional[Dict]:

    tokens = [
        token.strip()
        for token in _COLUMN_SPLIT_RE.split(
            line.strip()
        )
        if token.strip()
    ]

    if len(tokens) < 3:
        return None

    date_index = None
    parsed_date = None

    for i, token in enumerate(tokens[:4]):

        parsed = _parse_date_token(token)

        if parsed:

            date_index = i
            parsed_date = parsed
            break

    if parsed_date is None:
        return None

    remaining = tokens[
        date_index + 1:
    ]

    amount_tokens = []

    cursor = len(remaining) - 1

    while (
        cursor >= 0
        and _is_amount_token(
            remaining[cursor]
        )
        and len(amount_tokens) < 3
    ):

        amount_tokens.insert(
            0,
            remaining[cursor]
        )

        cursor -= 1

    if not amount_tokens:
        return None

    description = " ".join(
        remaining[:cursor + 1]
    ).strip()

    if not description:
        return None

    if len(amount_tokens) >= 2:

        amount = _amount_value(
            amount_tokens[-2]
        )

    else:

        amount = _amount_value(
            amount_tokens[0]
        )

    if amount is None:
        return None

    text = description.lower()

    drcr = None

    if _contains_keyword(text, CREDIT_KEYWORDS):
        drcr = "Cr"

    elif _contains_keyword(text, DEBIT_KEYWORDS):
        drcr = "Dr"

    return {
        "date": parsed_date,
        "description": description,
        "amount": amount,
        "drcr": drcr,
        "raw_text": line,
    }


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def _extract_text_native(
    pdf_bytes: bytes
) -> List[str]:

    doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    lines = []

    for page in doc:

        text = page.get_text("text")

        # OCR fallback for scanned pages with minimal native text
        if len(text.strip()) < 20:
            try:
                pix = page.get_pixmap(dpi=200)
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(image)
                if ocr_text and ocr_text.strip():
                    text = ocr_text
            except (pytesseract.TesseractNotFoundError, Exception):
                # Tesseract OCR system binary is not installed or available on this host.
                # Gracefully retain whatever text PyMuPDF extracted natively.
                pass

        for line in text.split("\n"):

            # Replace pipe delimiters with space for table alignment
            line = line.replace("|", " ").strip()

            if line:
                lines.append(line)

    doc.close()

    return lines


# ============================================================
# DATE LINE DETECTION
# ============================================================

def _line_starts_with_date(
    line: str
) -> bool:

    line = line.strip()

    if _parse_date_token(line):
        return True

    patterns = [

        r"^\d{1,2}[/\-.]+\d{1,2}[/\-.]+\d{2,4}(?:\s|$)",

        r"^\d{4}[/\-.]+\d{1,2}[/\-.]+\d{1,2}(?:\s|$)",

        rf"^\d{{1,2}}(?:st|nd|rd|th)?"
        rf"[\s\-,]*(?:{_MONTH_RE})"
        rf"[\s\-,]*\d{{2,4}}(?:\s|$)",

        rf"^(?:{_MONTH_RE})"
        rf"[\s\-,]+\d{{1,2}}"
        rf"(?:st|nd|rd|th)?"
        rf"[\s,]+\d{{2,4}}(?:\s|$)",
    ]

    return any(
        re.match(
            pattern,
            line,
            re.IGNORECASE
        )
        for pattern in patterns
    )


# ============================================================
# MULTI-LINE ROW RECONSTRUCTION
# ============================================================

def _merge_multiline_rows(
    lines: List[str]
) -> List[str]:

    merged = []

    current = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # New transaction row
        if _line_starts_with_date(line):

            if current:

                merged.append(
                    " ".join(current)
                )

            current = [line]

        else:

            if current:

                current.append(line)

    if current:

        merged.append(
            " ".join(current)
        )

    return merged


# ============================================================
# MAIN PDF EXTRACTION
# ============================================================

def extract_transactions_from_pdf(
    pdf_bytes: bytes
) -> Tuple[List[Dict], Dict[str, Optional[float]]]:

    raw_lines = _extract_text_native(
        pdf_bytes
    )

    # Reconstruct rows split across multiple lines
    lines = _merge_multiline_rows(
        raw_lines
    )

    transactions = []

    opening_balance = None
    closing_balance = None

    for line in lines:

        parsed = (
            _match_statement_line(line)
            or _parse_line_by_columns(line)
        )

        if not parsed:
            continue

        description = parsed[
            "description"
        ].strip()

        # ----------------------------------------------------
        # Do NOT treat Opening Balance as a transaction, but do
        # capture its value as the statement's starting balance.
        # ----------------------------------------------------

        if description.lower() in {
            "opening balance",
            "closing balance",
            "balance brought forward",
            "brought forward",
        }:

            if opening_balance is None:
                opening_balance = parsed["amount"]

            continue

        # Track the running balance printed on each row (if this
        # bank's layout includes one) so we know the true final
        # balance, not just the net of parsed transaction amounts.
        row_balance = parsed.get("balance")

        if row_balance is not None:
            closing_balance = row_balance

        amount = _infer_sign(
            parsed["amount"],
            parsed.get("drcr"),
            description
        )

        transactions.append(
            {
                "date": parsed["date"],
                "description": description,
                "amount": amount,
                "raw_text": parsed["raw_text"],
            }
        )

    balance_info = {
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
    }

    return transactions, balance_info


# ============================================================
# SMS PARSING
# ============================================================

_SMS_CURRENCY_AMOUNT_RE = re.compile(
    rf"{CURRENCY_PREFIX}"
    rf"({AMOUNT_CORE})",
    re.IGNORECASE
)

_SMS_BARE_AMOUNT_RE = re.compile(
    r"(?<![\w/\-.])"
    r"(\d{2,}(?:,\d{2,3})*(?:\.\d{1,2})?)"
    r"(?![\w/\-])"
)


def extract_transactions_from_sms(
    sms_texts: List[str]
) -> List[Dict]:

    transactions = []

    for sms in sms_texts:

        text = sms.strip()

        if not text:
            continue

        amount_match = (
            _SMS_CURRENCY_AMOUNT_RE.search(text)
            or _SMS_BARE_AMOUNT_RE.search(text)
        )

        if not amount_match:
            continue

        amount = _to_float(
            amount_match.group(1)
        )

        parsed_date = _find_date_in_text(
            text
        )

        if not parsed_date:
            continue

        lower_text = text.lower()

        direction = None

        if _contains_keyword(lower_text, CREDIT_KEYWORDS):
            direction = "credit"

        elif _contains_keyword(lower_text, DEBIT_KEYWORDS):
            direction = "debit"

        if direction == "credit":

            amount = abs(amount)

        else:

            amount = -abs(amount)

        transactions.append(
            {
                "date": parsed_date,
                "description": text[:120],
                "amount": amount,
                "raw_text": text,
            }
        )

    return transactions