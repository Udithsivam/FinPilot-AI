"""Receipt OCR: image -> raw text (Tesseract) -> best-effort structured
fields (merchant, amount, date).

Uses Tesseract (via pytesseract) rather than a deep-learning OCR model
(e.g. EasyOCR): Tesseract is a small, mature, well-understood engine
that needs no GPU and no multi-GB model download, consistent with this
project's stated goal of avoiding unnecessary heavy infrastructure. It
is a separate system binary (not just a pip package) — see README for
install instructions.

Field extraction is deliberately conservative: a field is only
populated when a pattern matches with reasonable confidence, otherwise
it's left as None so the caller (the transaction form) shows it as
blank for the user to fill in, rather than silently guessing wrong.
Receipt OCR is inherently noisy — this never invents a value it isn't
reasonably sure of.
"""

import datetime as dt
import io
import os
import re
import shutil

import pytesseract
from PIL import Image

_DEFAULT_WINDOWS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _configure_tesseract() -> None:
    """Point pytesseract at the Tesseract binary.

    Prefers TESSERACT_CMD if set, then whatever's already on PATH, then
    falls back to Tesseract's default Windows install location (this
    isn't added to PATH by the installer in every configuration).
    """
    configured = os.environ.get("TESSERACT_CMD")
    if configured:
        pytesseract.pytesseract.tesseract_cmd = configured
    elif shutil.which("tesseract") is None and os.path.exists(_DEFAULT_WINDOWS_PATH):
        pytesseract.pytesseract.tesseract_cmd = _DEFAULT_WINDOWS_PATH


_configure_tesseract()


class OCRUnavailableError(Exception):
    """Raised when the Tesseract binary can't be found/run at all —
    distinct from "OCR ran but couldn't confidently extract a field",
    which just leaves that field as None."""


def extract_text(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = image.convert("L")  # grayscale — measurably improves Tesseract accuracy on photos
    except Exception as exc:
        raise ValueError(f"Could not read image: {exc}") from exc

    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError(
            "Tesseract OCR engine not found. Install it and/or set TESSERACT_CMD "
            "to its executable path — see README's OCR section."
        ) from exc


_TOTAL_KEYWORDS_BY_PRIORITY = ["grand total", "total amount", "amount due", "net total", "total"]
_SUBTOTAL_MARKER = "subtotal"
_AMOUNT_RE = re.compile(r"(?:rs\.?|inr|₹|\$)?\s*([\d]{1,3}(?:[,\d]{0,10})?(?:\.\d{1,2})?)", re.IGNORECASE)

_DATE_PATTERNS = [
    (r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", "%Y-%m-%d"),
    (r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b", "%d-%m-%Y"),
    (r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2})\b", "%d-%m-%y"),
]


def _extract_amount(lines: list[str]) -> float | None:
    def amount_in(line: str) -> float | None:
        match = _AMOUNT_RE.search(line)
        if not match:
            return None
        raw = match.group(1).replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            return None
        return value if value > 0 else None

    for keyword in _TOTAL_KEYWORDS_BY_PRIORITY:
        for line in lines:
            lowered = line.lower()
            if keyword in lowered and (keyword != "total" or _SUBTOTAL_MARKER not in lowered):
                amount = amount_in(line)
                if amount is not None:
                    return amount

    # No recognizable "total" line — fall back to the largest currency-
    # like number anywhere on the receipt (a real, common heuristic: the
    # grand total is usually the largest line-item-shaped number), but
    # only as a best-effort guess, never fabricated from nothing.
    candidates = [amount_in(line) for line in lines]
    candidates = [c for c in candidates if c is not None]
    return max(candidates) if candidates else None


def _extract_date(text: str) -> str | None:
    for pattern, fmt in _DATE_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue
        candidate = match.group(0).replace("/", "-")
        try:
            normalized_fmt = fmt.replace("/", "-")
            parsed = dt.datetime.strptime(candidate, normalized_fmt)
            # Reject obviously-wrong OCR misreads (e.g. a phone number
            # mistaken for a date) rather than returning a nonsense date.
            if 2000 <= parsed.year <= dt.date.today().year + 1:
                return parsed.date().isoformat()
        except ValueError:
            continue
    return None


def _extract_merchant(lines: list[str]) -> str | None:
    # Receipts conventionally print the merchant/store name as the first
    # printed line. Skip blank lines and lines that are almost entirely
    # non-alphabetic (OCR noise, separators like "----------").
    for line in lines:
        stripped = line.strip()
        if len(stripped) < 3:
            continue
        letters = sum(1 for c in stripped if c.isalpha())
        if letters / len(stripped) < 0.4:
            continue
        return stripped[:100]
    return None


def parse_receipt_fields(text: str) -> dict:
    lines = [line for line in text.splitlines() if line.strip()]
    return {
        "merchant": _extract_merchant(lines),
        "amount": _extract_amount(lines),
        "date": _extract_date(text),
        "raw_text": text.strip(),
    }
