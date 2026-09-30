def _create_transaction(client, headers, date, amount, ttype="expense", category="Groceries"):
    return client.post(
        "/transactions",
        json={
            "date": date,
            "amount": amount,
            "type": ttype,
            "category": category,
            "subcategory": None,
            "merchant": "Test Merchant",
            "payment_method": "UPI",
            "description": None,
            "is_recurring": False,
        },
        headers=headers,
    )


def test_cash_flow_requires_auth(client):
    response = client.get("/predictions/cash-flow")
    assert response.status_code == 401


def test_cash_flow_rejects_insufficient_history(client, auth_headers):
    response = client.get("/predictions/cash-flow", headers=auth_headers)
    assert response.status_code == 422


def test_cash_flow_returns_prediction_with_sufficient_history(client, auth_headers):
    for date in ["2026-01-01", "2026-02-01"]:
        _create_transaction(client, auth_headers, date, 50000, ttype="income")
    for date in ["2026-01-05", "2026-02-05"]:
        _create_transaction(client, auth_headers, date, 20000)

    response = client.get("/predictions/cash-flow", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["forecast_period"]
    assert isinstance(body["predicted_income"], float)
    assert isinstance(body["predicted_expense"], float)
    assert body["predicted_net_cash_flow"] == body["predicted_income"] - body["predicted_expense"]
    assert body["model_name"]
    assert body["model_version"]


def test_cash_flow_persists_prediction(client, auth_headers):
    for date in ["2026-01-01", "2026-02-01"]:
        _create_transaction(client, auth_headers, date, 50000, ttype="income")
    for date in ["2026-01-05", "2026-02-05"]:
        _create_transaction(client, auth_headers, date, 20000)

    client.get("/predictions/cash-flow", headers=auth_headers)
    history = client.get("/predictions/history", headers=auth_headers).json()
    assert any(p["prediction_type"] == "cash_flow_forecast" for p in history)


def test_cash_flow_is_scoped_to_authenticated_user(client, auth_headers):
    for date in ["2026-01-01", "2026-02-01"]:
        _create_transaction(client, auth_headers, date, 50000, ttype="income")
    for date in ["2026-01-05", "2026-02-05"]:
        _create_transaction(client, auth_headers, date, 20000)

    client.post(
        "/auth/register",
        json={"email": "other-cf@example.com", "password": "supersecret123", "full_name": "Other User"},
    )
    other_login = client.post(
        "/auth/login", data={"username": "other-cf@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.get("/predictions/cash-flow", headers=other_headers)
    assert response.status_code == 422
