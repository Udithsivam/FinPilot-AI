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


def test_zero_or_negative_amount_rejected(client, auth_headers):
    assert _add_transaction(client, auth_headers, amount=0).status_code == 422
    assert _add_transaction(client, auth_headers, amount=-50).status_code == 422


def test_empty_category_rejected(client, auth_headers):
    assert _add_transaction(client, auth_headers, category="").status_code == 422


def test_malformed_budget_period_rejected(client, auth_headers):
    # Regression: a malformed period used to be accepted at creation (no
    # format validation) and then crash GET /budgets with a 500, since
    # period_bounds() assumed "YYYY-MM" and blew up on anything else.
    response = client.post(
        "/budgets",
        json={"category": "Groceries", "amount": 1000.0, "period": "not-a-period"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_negative_budget_amount_rejected(client, auth_headers):
    response = client.post(
        "/budgets",
        json={"category": "Groceries", "amount": -500.0, "period": "2026-01"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_budget_matches_transaction_category_case_insensitively(client, auth_headers):
    # Regression (audit G4): budget "Groceries" vs transaction "groceries"
    # used to compute spent=0 due to exact-string SQL equality.
    client.post(
        "/budgets",
        json={"category": "Groceries", "amount": 5000.0, "period": "2026-01"},
        headers=auth_headers,
    )
    _add_transaction(client, auth_headers, category="groceries", amount=1200.0, date="2026-01-05")

    budgets = client.get("/budgets", headers=auth_headers).json()
    assert len(budgets) == 1
    assert budgets[0]["spent"] == 1200.0


def test_budget_matches_transaction_category_ignoring_whitespace(client, auth_headers):
    # Regression (audit G4): surrounding whitespace on either side must
    # not prevent a match.
    client.post(
        "/budgets",
        json={"category": " Groceries ", "amount": 5000.0, "period": "2026-01"},
        headers=auth_headers,
    )
    _add_transaction(client, auth_headers, category="groceries", amount=800.0, date="2026-01-05")

    budgets = client.get("/budgets", headers=auth_headers).json()
    assert len(budgets) == 1
    assert budgets[0]["spent"] == 800.0


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


def _other_user_headers(client):
    client.post(
        "/auth/register",
        json={"email": "user-b@example.com", "password": "supersecret123", "full_name": "User B"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "user-b@example.com", "password": "supersecret123"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_user_cannot_list_or_delete_another_users_transaction(client, auth_headers):
    created = _add_transaction(client, auth_headers).json()
    user_b_headers = _other_user_headers(client)

    listing = client.get("/transactions", headers=user_b_headers).json()
    assert all(t["id"] != created["id"] for t in listing)

    delete_response = client.delete(f"/transactions/{created['id']}", headers=user_b_headers)
    assert delete_response.status_code == 404

    owner_listing = client.get("/transactions", headers=auth_headers).json()
    assert any(t["id"] == created["id"] for t in owner_listing)


def test_user_cannot_list_or_delete_another_users_budget(client, auth_headers):
    created = client.post(
        "/budgets",
        json={"category": "Groceries", "amount": 5000.0, "period": "2026-01"},
        headers=auth_headers,
    ).json()
    user_b_headers = _other_user_headers(client)

    listing = client.get("/budgets", headers=user_b_headers).json()
    assert all(b["id"] != created["id"] for b in listing)

    delete_response = client.delete(f"/budgets/{created['id']}", headers=user_b_headers)
    assert delete_response.status_code == 404

    owner_listing = client.get("/budgets", headers=auth_headers).json()
    assert any(b["id"] == created["id"] for b in owner_listing)


def test_dashboard_analytics(client, auth_headers):
    _add_transaction(client, auth_headers, type="income", category="Salary", amount=50000.0, date="2026-01-01")
    _add_transaction(client, auth_headers, amount=10000.0, date="2026-01-05")

    dashboard = client.get("/analytics/dashboard", headers=auth_headers).json()
    assert dashboard["total_income"] == 50000.0
    assert dashboard["total_expenses"] == 10000.0
    assert dashboard["net_cash_flow"] == 40000.0
    assert dashboard["top_categories"][0]["category"] == "Groceries"
