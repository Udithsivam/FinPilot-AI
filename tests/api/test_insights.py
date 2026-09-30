def _txn(client, headers, **overrides):
    payload = {"date": "2026-01-15", "amount": 1000.0, "type": "expense", "category": "Groceries", **overrides}
    return client.post("/transactions", json=payload, headers=headers)


def test_insights_empty_with_no_history(client, auth_headers):
    response = client.get("/analytics/insights", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_insights_flags_category_increase(client, auth_headers):
    _txn(client, auth_headers, amount=1000.0, date="2026-01-05")
    _txn(client, auth_headers, amount=2000.0, date="2026-02-05")

    insights = client.get("/analytics/insights", headers=auth_headers).json()
    assert any(i["tone"] == "warning" and "Groceries" in i["title"] for i in insights)


def test_insights_flags_category_decrease(client, auth_headers):
    _txn(client, auth_headers, amount=2000.0, date="2026-01-05")
    _txn(client, auth_headers, amount=1000.0, date="2026-02-05")

    insights = client.get("/analytics/insights", headers=auth_headers).json()
    assert any(i["tone"] == "success" and "Groceries" in i["title"] for i in insights)


def test_insights_ignores_small_category_changes(client, auth_headers):
    _txn(client, auth_headers, amount=1000.0, date="2026-01-05")
    _txn(client, auth_headers, amount=1050.0, date="2026-02-05")  # +5%, below threshold

    insights = client.get("/analytics/insights", headers=auth_headers).json()
    assert insights == []


def test_insights_flags_savings_streak(client, auth_headers):
    for month in ("2026-01", "2026-02", "2026-03"):
        client.post(
            "/transactions",
            json={"date": f"{month}-01", "amount": 50000.0, "type": "income", "category": "Salary"},
            headers=auth_headers,
        )
        _txn(client, auth_headers, amount=20000.0, date=f"{month}-05")  # 60% savings rate each month

    insights = client.get("/analytics/insights", headers=auth_headers).json()
    assert any("savings streak" in i["title"].lower() for i in insights)


def test_insights_requires_auth(client):
    response = client.get("/analytics/insights")
    assert response.status_code == 401
