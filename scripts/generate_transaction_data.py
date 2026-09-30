"""Generate a SYNTHETIC transaction-level dataset for training FinPilot's
transaction-categorization model (and any future forecasting/anomaly work).

This is NOT real banking data and must never be presented as such. It
exists because data/raw/data.csv (the existing savings-prediction
dataset) is a cross-sectional financial-profile snapshot with no
transaction rows at all — there is nowhere else in this repository, or
in any dataset evaluated in this project's dataset-research task, that
provides labeled (merchant/description -> category) transaction text.

Deterministic: a fixed random seed means re-running this script
produces byte-identical output (dates are relative to "today" at
generation time, so the specific calendar months covered do shift, but
the relative structure and all amounts/labels do not).

Usage:
    python -m scripts.generate_transaction_data

Outputs:
    data/raw/finpilot_users.csv
    data/raw/finpilot_transactions.csv

Does NOT touch data/raw/data.csv (the existing savings-prediction
dataset, which remains unchanged and is not used by this script).
"""

import calendar
import csv
import datetime as dt
import random
from pathlib import Path

from src.categorization.taxonomy import TAXONOMY

SEED = 7
N_USERS = 40
N_MONTHS = 8

PROJECT_ROOT = Path(__file__).resolve().parents[1]
USERS_PATH = PROJECT_ROOT / "data" / "raw" / "finpilot_users.csv"
TRANSACTIONS_PATH = PROJECT_ROOT / "data" / "raw" / "finpilot_transactions.csv"

USER_TYPES = ["Student", "Professional", "Self_Employed", "Retired", "Homemaker", "Business_Owner"]
CITY_TIERS = ["Tier_1", "Tier_2", "Tier_3"]
FINANCIAL_GOALS = ["Emergency Fund", "New Laptop", "Vacation", "Home Down Payment", "Retirement", "Education Fund"]
PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Cash", "Net Banking"]

# (min, max) monthly income by user type — loose, illustrative bands, not
# derived from any real survey.
INCOME_RANGE_BY_TYPE = {
    "Student": (8_000, 20_000),
    "Professional": (35_000, 150_000),
    "Self_Employed": (25_000, 180_000),
    "Retired": (15_000, 60_000),
    "Homemaker": (0, 25_000),
    "Business_Owner": (40_000, 250_000),
}
AGE_RANGE_BY_TYPE = {
    "Student": (18, 24),
    "Professional": (23, 45),
    "Self_Employed": (25, 55),
    "Retired": (60, 78),
    "Homemaker": (25, 55),
    "Business_Owner": (28, 60),
}

# Words that mark the end of a "brand" prefix in a description template, so
# a merchant name can be derived deterministically instead of guessed.
_MERCHANT_STOPWORDS = {
    "Order", "Bill", "Payment", "Fee", "Purchase", "Subscription", "Booking",
    "Ticket", "Recharge", "Service", "Visit", "Work", "Premium", "Investment",
    "Renewal", "Membership", "Store", "Pump", "Station", "Card",
}


_CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune", "Hyderabad"]


def _add_realistic_noise(description: str, rng: random.Random) -> str:
    """Vary description text the way real transaction records do (reference
    numbers, case, location suffixes) — without this, every transaction in
    a given category has one of only 2-3 possible exact strings, which
    makes text classification trivially easy and inflates accuracy in a
    way that says nothing about how the model would handle real,
    free-form merchant text."""
    roll = rng.random()
    if roll < 0.4:
        return description
    if roll < 0.6:
        return f"{description} Ref{rng.randint(1000, 9999)}"
    if roll < 0.75:
        return description.upper()
    if roll < 0.85:
        return description.lower()
    return f"{description} {rng.choice(_CITIES)}"


_GENERIC_DESCRIPTIONS = [
    "UPI-{n:010d}@ybl",
    "POS TXN {n:06d}",
    "NEFT TRANSFER REF{n:06d}",
    "IMPS-{n:010d}",
    "ACH DEBIT {n:06d}",
    "PAYMENT TO VENDOR {n:04d}",
]


def _finalize_description_and_merchant(clean_description: str, rng: random.Random) -> tuple[str, str]:
    """~18% of the time, replace the description with a generic
    payment-processor-style string (UPI ID, POS code, NEFT reference) that
    carries no category information at all, and clear the merchant too.

    This is deliberate, not a bug: real bank/UPI transaction records are
    full of exactly this kind of opaque line item, and it's the actual
    reason categorization is a real ML problem rather than a keyword
    lookup. Without it, every category here keeps a disjoint, unique
    vocabulary (a supermarket brand never appears under Entertainment,
    etc.), and a text classifier hits 100% trivially — a real, honestly-
    measured number, but one that says nothing about how the model would
    perform on ambiguous real-world text.
    """
    if rng.random() < 0.18:
        template = rng.choice(_GENERIC_DESCRIPTIONS)
        return template.format(n=rng.randint(0, 999_999_999)), ""
    return _add_realistic_noise(clean_description, rng), _merchant_from_description(clean_description)


def _merchant_from_description(description: str) -> str:
    words = description.split()
    for i, word in enumerate(words):
        if word in _MERCHANT_STOPWORDS:
            return " ".join(words[:i]) if i > 0 else description
    return description


# Recurring fixed categories every user has every month, as a fraction of
# monthly income (rent) or a small fixed-ish amount (utilities).
_RECURRING_TEMPLATES = [
    ("Housing", "Rent", 0.28, 0.06),
    ("Utilities", "Electricity", None, None),
    ("Utilities", "Internet", None, None),
    ("Utilities", "Mobile", None, None),
]
_UTILITY_FIXED_RANGE = {"Electricity": (800, 3000), "Internet": (600, 1500), "Mobile": (300, 900)}

# Variable categories: (category, subcategory, per-occurrence amount range,
# typical occurrences per month range).
_VARIABLE_TEMPLATES = [
    ("Groceries", "Supermarket", (1500, 6000), (1, 3)),
    ("Food", "Restaurants", (300, 1800), (0, 3)),
    ("Food", "Food Delivery", (200, 900), (1, 5)),
    ("Transportation", "Fuel", (500, 3000), (0, 3)),
    ("Transportation", "Taxi/Ride Share", (150, 700), (1, 4)),
    ("Entertainment", "Movies", (300, 1200), (0, 2)),
    ("Shopping", "General Shopping", (500, 5000), (0, 3)),
    ("Subscriptions", "Streaming", (150, 700), (1, 1)),
    ("Healthcare", "Medicine", (200, 1500), (0, 2)),
    ("Personal Care", "Salon", (300, 1500), (0, 1)),
]


def _day_in_month(year: int, month: int, day: int) -> dt.date:
    last_day = calendar.monthrange(year, month)[1]
    return dt.date(year, month, min(day, last_day))


def _month_key(months_ago: int) -> tuple[int, int]:
    today = dt.date.today()
    year, month = today.year, today.month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    return year, month


def generate_users(rng: random.Random) -> list[dict]:
    users = []
    for user_id in range(1, N_USERS + 1):
        user_type = rng.choice(USER_TYPES)
        income_lo, income_hi = INCOME_RANGE_BY_TYPE[user_type]
        age_lo, age_hi = AGE_RANGE_BY_TYPE[user_type]
        monthly_income = round(rng.uniform(income_lo, income_hi), 2)
        users.append(
            {
                "user_id": user_id,
                "user_type": user_type,
                "age": rng.randint(age_lo, age_hi),
                "occupation": user_type,
                "city_tier": rng.choice(CITY_TIERS),
                "monthly_income": monthly_income,
                "monthly_budget": round(monthly_income * rng.uniform(0.6, 0.9), 2),
                "currency": "INR",
                "financial_goal": rng.choice(FINANCIAL_GOALS),
            }
        )
    return users


def generate_transactions(users: list[dict], rng: random.Random) -> list[dict]:
    transactions = []
    transaction_id = 1

    for user in users:
        user_id = user["user_id"]
        monthly_income = user["monthly_income"]
        has_loan = rng.random() < 0.4
        has_insurance = rng.random() < 0.5
        # Per-user spending-pattern multiplier per variable category, so
        # different users have genuinely different habits, not just noise
        # around one shared mean.
        category_multiplier = {tpl[0] + tpl[1]: rng.uniform(0.6, 1.6) for tpl in _VARIABLE_TEMPLATES}

        for months_ago in range(N_MONTHS - 1, -1, -1):
            year, month = _month_key(months_ago)

            income_source = "Freelance Income" if user["user_type"] in ("Self_Employed", "Business_Owner") else "Salary"
            transactions.append(
                {
                    "transaction_id": transaction_id,
                    "user_id": user_id,
                    "date": _day_in_month(year, month, 1).isoformat(),
                    "amount": round(monthly_income * rng.uniform(0.95, 1.05), 2),
                    "transaction_type": "income",
                    "category": "Income",
                    "subcategory": income_source,
                    "description": income_source,
                    "merchant": "",
                    "payment_method": "Net Banking",
                    "currency": "INR",
                    "recurring": True,
                }
            )
            transaction_id += 1

            for category, subcategory, income_fraction, fraction_noise in _RECURRING_TEMPLATES:
                if category == "Housing":
                    amount = round(monthly_income * rng.uniform(income_fraction - fraction_noise, income_fraction + fraction_noise), 2)
                else:
                    lo, hi = _UTILITY_FIXED_RANGE[subcategory]
                    amount = round(rng.uniform(lo, hi), 2)
                clean_description = rng.choice(TAXONOMY[category][subcategory])
                description, merchant = _finalize_description_and_merchant(clean_description, rng)
                transactions.append(
                    {
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                        "date": _day_in_month(year, month, rng.randint(1, 5)).isoformat(),
                        "amount": amount,
                        "transaction_type": "expense",
                        "category": category,
                        "subcategory": subcategory,
                        "description": description,
                        "merchant": merchant,
                        "payment_method": rng.choice(PAYMENT_METHODS),
                        "currency": "INR",
                        "recurring": True,
                    }
                )
                transaction_id += 1

            if has_loan:
                clean_description = rng.choice(TAXONOMY["Loan/Debt"]["EMI"])
                description, merchant = _finalize_description_and_merchant(clean_description, rng)
                transactions.append(
                    {
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                        "date": _day_in_month(year, month, 5).isoformat(),
                        "amount": round(monthly_income * rng.uniform(0.1, 0.25), 2),
                        "transaction_type": "expense",
                        "category": "Loan/Debt",
                        "subcategory": "EMI",
                        "description": description,
                        "merchant": merchant,
                        "payment_method": "Net Banking",
                        "currency": "INR",
                        "recurring": True,
                    }
                )
                transaction_id += 1

            if has_insurance:
                clean_description = rng.choice(TAXONOMY["Insurance"]["Health Insurance"])
                description, merchant = _finalize_description_and_merchant(clean_description, rng)
                transactions.append(
                    {
                        "transaction_id": transaction_id,
                        "user_id": user_id,
                        "date": _day_in_month(year, month, 7).isoformat(),
                        "amount": round(rng.uniform(500, 3000), 2),
                        "transaction_type": "expense",
                        "category": "Insurance",
                        "subcategory": "Health Insurance",
                        "description": description,
                        "merchant": merchant,
                        "payment_method": rng.choice(PAYMENT_METHODS),
                        "currency": "INR",
                        "recurring": True,
                    }
                )
                transaction_id += 1

            for category, subcategory, (amt_lo, amt_hi), (occ_lo, occ_hi) in _VARIABLE_TEMPLATES:
                occurrences = rng.randint(occ_lo, occ_hi)
                multiplier = category_multiplier[category + subcategory]
                for _ in range(occurrences):
                    clean_description = rng.choice(TAXONOMY[category][subcategory])
                    description, merchant = _finalize_description_and_merchant(clean_description, rng)
                    amount = round(rng.uniform(amt_lo, amt_hi) * multiplier, 2)
                    transactions.append(
                        {
                            "transaction_id": transaction_id,
                            "user_id": user_id,
                            "date": _day_in_month(year, month, rng.randint(1, 28)).isoformat(),
                            "amount": amount,
                            "transaction_type": "expense",
                            "category": category,
                            "subcategory": subcategory,
                            "description": description,
                            "merchant": merchant,
                            "payment_method": rng.choice(PAYMENT_METHODS),
                            "currency": "INR",
                            "recurring": False,
                        }
                    )
                    transaction_id += 1

    return transactions


def main() -> None:
    rng = random.Random(SEED)
    users = generate_users(rng)
    transactions = generate_transactions(users, rng)

    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(users[0].keys()))
        writer.writeheader()
        writer.writerows(users)

    with open(TRANSACTIONS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(transactions[0].keys()))
        writer.writeheader()
        writer.writerows(transactions)

    print(f"SYNTHETIC data generated (seed={SEED}):")
    print(f"  {USERS_PATH.relative_to(PROJECT_ROOT)}: {len(users)} users")
    print(f"  {TRANSACTIONS_PATH.relative_to(PROJECT_ROOT)}: {len(transactions)} transactions")


if __name__ == "__main__":
    main()
