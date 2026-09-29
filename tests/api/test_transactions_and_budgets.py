def _add_transaction(client, headers, **overrides):
    payload = {
        "date": "2026-01-15",
        "amount": 1000.0,
        "type": "expense",
        "category": "Groceries",
        **overrides,
    }
    return client.post("/transactions", json=payload, headers=headers)


def test_create_and_list_transactions(client, auth_headers):
    response = _add_transaction(client, auth_headers)
    assert response.status_code == 201

    listing = client.get("/transactions", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_delete_transaction(client, auth_headers):
    created = _add_transaction(client, auth_headers).json()
    delete_response = client.delete(f"/transactions/{created['id']}", headers=auth_headers)
    assert delete_response.status_code == 204
    assert client.get("/transactions", headers=auth_headers).json() == []


def test_delete_missing_transaction_returns_404(client, auth_headers):
    response = client.delete("/transactions/999", headers=auth_headers)
    assert response.status_code == 404


def test_budget_status_tracks_spending(client, auth_headers):
    client.post(
        "/budgets",
        json={"category": "Groceries", "amount": 5000.0, "period": "2026-01"},
        headers=auth_headers,
    )
    _add_transaction(client, auth_headers, amount=4600.0, date="2026-01-05")

    budgets = client.get("/budgets", headers=auth_headers).json()
    assert len(budgets) == 1
    assert budgets[0]["spent"] == 4600.0
    assert budgets[0]["status"] == "approaching_limit"


def test_budget_exceeded_status(client, auth_headers):
    client.post(
        "/budgets",
        json={"category": "Entertainment", "amount": 1000.0, "period": "2026-01"},
        headers=auth_headers,
    )
    _add_transaction(client, auth_headers, category="Entertainment", amount=1500.0, date="2026-01-10")

    budgets = client.get("/budgets", headers=auth_headers).json()
    assert budgets[0]["status"] == "exceeded"
    assert budgets[0]["remaining"] == -500.0


def test_dashboard_analytics(client, auth_headers):
    _add_transaction(client, auth_headers, type="income", category="Salary", amount=50000.0, date="2026-01-01")
    _add_transaction(client, auth_headers, amount=10000.0, date="2026-01-05")

    dashboard = client.get("/analytics/dashboard", headers=auth_headers).json()
    assert dashboard["total_income"] == 50000.0
    assert dashboard["total_expenses"] == 10000.0
    assert dashboard["net_cash_flow"] == 40000.0
    assert dashboard["top_categories"][0]["category"] == "Groceries"
