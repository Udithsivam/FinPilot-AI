def _create_transaction(client, headers, date, amount, category="Groceries", is_recurring=False):
    return client.post(
        "/transactions",
        json={
            "date": date,
            "amount": amount,
            "type": "expense",
            "category": category,
            "subcategory": None,
            "merchant": "Test Merchant",
            "payment_method": "UPI",
            "description": None,
            "is_recurring": is_recurring,
        },
        headers=headers,
    )


def test_forecast_requires_auth(client):
    response = client.get("/predictions/expenses")
    assert response.status_code == 401


def test_forecast_rejects_insufficient_history(client, auth_headers):
    # A brand-new user has zero transactions — nowhere near the two
    # distinct calendar months of expense history the model needs.
    response = client.get("/predictions/expenses", headers=auth_headers)
    assert response.status_code == 422


def test_forecast_returns_prediction_with_sufficient_history(client, auth_headers):
    for date in ["2026-01-05", "2026-01-20"]:
        _create_transaction(client, auth_headers, date, 2000)
    for date in ["2026-02-05", "2026-02-20"]:
        _create_transaction(client, auth_headers, date, 2500)

    response = client.get("/predictions/expenses", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["forecast_period"]
    assert isinstance(body["predicted_expense"], float)
    assert isinstance(body["baseline_comparison"], float)
    assert body["model_name"]
    assert body["model_version"]
    assert isinstance(body["prediction_id"], int)


def test_forecast_persists_prediction(client, auth_headers):
    for date in ["2026-01-05", "2026-02-05"]:
        _create_transaction(client, auth_headers, date, 1800)

    client.get("/predictions/expenses", headers=auth_headers)
    history = client.get("/predictions/history", headers=auth_headers).json()
    assert any(p["prediction_type"] == "expense_forecast" for p in history)


def test_forecast_is_scoped_to_the_authenticated_user(client, auth_headers):
    for date in ["2026-01-05", "2026-02-05"]:
        _create_transaction(client, auth_headers, date, 1800)

    client.post(
        "/auth/register",
        json={"email": "other@example.com", "password": "supersecret123", "full_name": "Other User"},
    )
    other_login = client.post(
        "/auth/login", data={"username": "other@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.get("/predictions/expenses", headers=other_headers)
    # The other user has no transactions of their own — the first user's
    # history must not leak into their forecast.
    assert response.status_code == 422
