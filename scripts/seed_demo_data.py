"""Seed a demo user with realistic, clearly-SYNTHETIC financial data.

This is for local demo/review purposes only — nothing here is real
financial data, and this script must never run against a production
database. It talks to the running FastAPI backend over HTTP using the
same public API a real client would use (no direct DB writes, no
bypassing validation), so the seeded data is guaranteed to be exactly
as valid as anything a real user could create.

Usage:
    python -m scripts.seed_demo_data
    python -m scripts.seed_demo_data --base-url http://127.0.0.1:8000

Deterministic: uses a fixed random seed, so re-running produces the same
transaction amounts (dates always end at the current month, so which
calendar months are covered does shift with time).
"""

import argparse
import calendar
import datetime as dt
import random
import sys

import requests

DEMO_EMAIL = "demo@finpilot.ai"
DEMO_PASSWORD = "DemoPass123!"
DEMO_NAME = "Demo User"

SEED = 42


def _month_key(months_ago: int) -> tuple[int, int]:
    today = dt.date.today()
    year, month = today.year, today.month - months_ago
    while month <= 0:
        month += 12
        year -= 1
    return year, month


def _day_in_month(year: int, month: int, day: int) -> str:
    last_day = calendar.monthrange(year, month)[1]
    return dt.date(year, month, min(day, last_day)).isoformat()


def _register_and_login(base_url: str) -> str:
    session = requests.Session()
    register_response = session.post(
        f"{base_url}/auth/register",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD, "full_name": DEMO_NAME},
    )
    if register_response.status_code not in (201, 400):
        register_response.raise_for_status()
    if register_response.status_code == 201:
        print(f"Created demo user {DEMO_EMAIL}")
    else:
        print(f"Demo user {DEMO_EMAIL} already exists, reusing it")

    login_response = session.post(
        f"{base_url}/auth/login",
        data={"username": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    login_response.raise_for_status()
    return login_response.json()["access_token"]


def seed(base_url: str) -> None:
    rng = random.Random(SEED)
    token = _register_and_login(base_url)
    headers = {"Authorization": f"Bearer {token}"}

    requests.put(
        f"{base_url}/users/me/profile",
        json={"user_type": "Professional", "monthly_income": 75000, "currency": "INR"},
        headers=headers,
    ).raise_for_status()

    # 3 months of transactions, oldest to newest, with Groceries rising
    # month-over-month (demonstrates the "spending increased" insight) and
    # a >=20% savings rate every month (demonstrates the savings streak
    # insight and a "Good" Financial Health savings-rate factor).
    groceries_by_month = [6000, 7200, 9500]  # +20%, then +32%
    for i, months_ago in enumerate((2, 1, 0)):
        year, month = _month_key(months_ago)
        rows = [
            {"date": _day_in_month(year, month, 1), "amount": 75000, "type": "income", "category": "Salary"},
            {
                "date": _day_in_month(year, month, 3),
                "amount": 20000,
                "type": "expense",
                "category": "Rent",
                "is_recurring": True,
            },
            {
                "date": _day_in_month(year, month, 5),
                "amount": groceries_by_month[i],
                "type": "expense",
                "category": "Groceries",
            },
            {
                "date": _day_in_month(year, month, 10),
                "amount": round(rng.uniform(1500, 3500), 2),
                "type": "expense",
                "category": "Eating Out",
            },
            {
                "date": _day_in_month(year, month, 14),
                "amount": round(rng.uniform(1000, 2000), 2),
                "type": "expense",
                "category": "Entertainment",
            },
            {
                "date": _day_in_month(year, month, 18),
                "amount": round(rng.uniform(2000, 3000), 2),
                "type": "expense",
                "category": "Transport",
            },
            {
                "date": _day_in_month(year, month, 20),
                "amount": round(rng.uniform(2500, 3500), 2),
                "type": "expense",
                "category": "Utilities",
            },
        ]
        for row in rows:
            requests.post(f"{base_url}/transactions", json=row, headers=headers).raise_for_status()

    current_year, current_month = _month_key(0)
    current_period = f"{current_year:04d}-{current_month:02d}"
    budgets = [
        {"category": "Groceries", "amount": 8000, "period": current_period},
        {"category": "Eating Out", "amount": 3000, "period": current_period},
        {"category": "Entertainment", "amount": 2500, "period": current_period},
    ]
    for budget in budgets:
        requests.post(f"{base_url}/budgets", json=budget, headers=headers).raise_for_status()

    goals = [
        {"name": "Emergency Fund", "target_amount": 300000, "current_amount": 135000},
        {"name": "New Laptop", "target_amount": 90000, "current_amount": 32000},
    ]
    for goal in goals:
        requests.post(f"{base_url}/goals", json=goal, headers=headers).raise_for_status()

    print(f"\nSeeded {len(groceries_by_month) * 7} transactions, {len(budgets)} budgets, {len(goals)} goals.")
    print("\nDemo login:")
    print(f"  email:    {DEMO_EMAIL}")
    print(f"  password: {DEMO_PASSWORD}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    try:
        seed(args.base_url)
    except requests.ConnectionError:
        print(f"Could not reach the backend at {args.base_url} — is it running?", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
