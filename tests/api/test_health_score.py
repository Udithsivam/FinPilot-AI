def _txn(client, headers, **overrides):
    payload = {"date": "2026-01-15", "amount": 1000.0, "type": "expense", "category": "Groceries", **overrides}
    return client.post("/transactions", json=payload, headers=headers)


def test_health_score_with_no_data_is_all_not_enough_data(client, auth_headers):
    response = client.get("/analytics/health-score", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["score"] is None
    assert all(f["rating"] == "Not Enough Data" for f in body["factors"])


def test_good_savings_rate_scores_well(client, auth_headers):
    _txn(client, auth_headers, type="income", category="Salary", amount=100000.0, date="2026-01-01")
    _txn(client, auth_headers, amount=50000.0, date="2026-01-05")  # 50% savings rate

    body = client.get("/analytics/health-score", headers=auth_headers).json()
    savings_factor = next(f for f in body["factors"] if f["key"] == "savings_rate")
    assert savings_factor["rating"] == "Good"
    assert body["score"] is not None


def test_high_debt_burden_flagged(client, auth_headers):
    _txn(client, auth_headers, type="income", category="Salary", amount=50000.0, date="2026-01-01")
    _txn(client, auth_headers, category="Loan Repayment", amount=20000.0, date="2026-01-05")

    body = client.get("/analytics/health-score", headers=auth_headers).json()
    debt_factor = next(f for f in body["factors"] if f["key"] == "debt_burden")
    assert debt_factor["rating"] == "High"


def test_budget_adherence_reflects_exceeded_budget(client, auth_headers):
    client.post(
        "/budgets", json={"category": "Groceries", "amount": 1000.0, "period": "2026-01"}, headers=auth_headers
    )
    _txn(client, auth_headers, amount=2000.0, date="2026-01-05")

    body = client.get("/analytics/health-score", headers=auth_headers).json()
    budget_factor = next(f for f in body["factors"] if f["key"] == "budget_adherence")
    assert budget_factor["rating"] == "Low"


def test_emergency_reserve_uses_named_goal(client, auth_headers):
    _txn(client, auth_headers, amount=10000.0, date="2026-01-05")
    _txn(client, auth_headers, amount=10000.0, date="2026-02-05")
    client.post(
        "/goals",
        json={"name": "Emergency Fund", "target_amount": 100000.0, "current_amount": 80000.0},
        headers=auth_headers,
    )

    body = client.get("/analytics/health-score", headers=auth_headers).json()
    reserve_factor = next(f for f in body["factors"] if f["key"] == "emergency_reserve")
    assert reserve_factor["rating"] == "Good"
