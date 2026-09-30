import random

from scripts.generate_transaction_data import generate_transactions, generate_users


def test_generator_is_deterministic():
    users_a = generate_users(random.Random(7))
    transactions_a = generate_transactions(users_a, random.Random(7))

    users_b = generate_users(random.Random(7))
    transactions_b = generate_transactions(users_b, random.Random(7))

    assert users_a == users_b
    assert transactions_a == transactions_b


def test_generated_amounts_are_positive():
    users = generate_users(random.Random(7))
    transactions = generate_transactions(users, random.Random(7))
    assert all(t["amount"] > 0 for t in transactions)


def test_every_expense_has_a_valid_category_and_subcategory():
    from src.categorization.taxonomy import TAXONOMY

    users = generate_users(random.Random(7))
    transactions = generate_transactions(users, random.Random(7))
    expenses = [t for t in transactions if t["transaction_type"] == "expense"]
    assert len(expenses) > 0
    for t in expenses:
        assert t["category"] in TAXONOMY
        assert t["subcategory"] in TAXONOMY[t["category"]]


def test_income_transactions_have_no_category_from_taxonomy():
    users = generate_users(random.Random(7))
    transactions = generate_transactions(users, random.Random(7))
    incomes = [t for t in transactions if t["transaction_type"] == "income"]
    assert len(incomes) > 0
    assert all(t["category"] == "Income" for t in incomes)


def test_generates_multiple_users_and_months_of_history():
    users = generate_users(random.Random(7))
    transactions = generate_transactions(users, random.Random(7))
    assert len(users) >= 10
    distinct_months = {t["date"][:7] for t in transactions}
    assert len(distinct_months) >= 6
