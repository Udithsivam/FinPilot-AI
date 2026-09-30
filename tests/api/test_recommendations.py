def _txn(client, headers, **overrides):
    payload = {"date": "2026-01-15", "amount": 1000.0, "type": "expense", "category": "Groceries", **overrides}
    return client.post("/transactions", json=payload, headers=headers)


def test_recommendations_empty_with_no_data(client, auth_headers):
    response = client.get("/analytics/recommendations", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_recommendations_flag_exceeded_budget(client, auth_headers):
    client.post(
        "/budgets", json={"category": "Groceries", "amount": 1000.0, "period": "2026-01"}, headers=auth_headers
    )
    _txn(client, auth_headers, amount=2000.0, date="2026-01-05")

    recs = client.get("/analytics/recommendations", headers=auth_headers).json()
    assert any(r["type"] == "budget_adjustment" and r["priority"] == "high" for r in recs)
    assert "Groceries" in recs[0]["evidence"]


def test_recommendations_flag_category_increase(client, auth_headers):
    _txn(client, auth_headers, amount=1000.0, date="2026-01-05")
    _txn(client, auth_headers, amount=2000.0, date="2026-02-05")

    recs = client.get("/analytics/recommendations", headers=auth_headers).json()
    assert any(r["type"] == "category_review" for r in recs)


def test_recommendations_flag_savings_rate_drop(client, auth_headers):
    client.post(
        "/transactions",
        json={"date": "2026-01-01", "amount": 50000.0, "type": "income", "category": "Salary"},
        headers=auth_headers,
    )
    _txn(client, auth_headers, amount=5000.0, date="2026-01-05")  # 90% savings rate
    client.post(
        "/transactions",
        json={"date": "2026-02-01", "amount": 50000.0, "type": "income", "category": "Salary"},
        headers=auth_headers,
    )
    _txn(client, auth_headers, amount=40000.0, date="2026-02-05")  # 20% savings rate

    recs = client.get("/analytics/recommendations", headers=auth_headers).json()
    assert any(r["type"] == "expense_reduction" for r in recs)


def test_recommendations_flag_high_recurring_share(client, auth_headers):
    _txn(client, auth_headers, amount=10000.0, date="2026-01-05", is_recurring=True, category="Rent")
    _txn(client, auth_headers, amount=1000.0, date="2026-01-06", is_recurring=False, category="Entertainment")

    recs = client.get("/analytics/recommendations", headers=auth_headers).json()
    assert any(r["type"] == "recurring_review" for r in recs)


def test_recommendations_requires_auth(client):
    response = client.get("/analytics/recommendations")
    assert response.status_code == 401
