def _create_transaction(client, headers, date, amount, category="Groceries"):
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
            "is_recurring": False,
        },
        headers=headers,
    )


def test_anomalies_requires_auth(client):
    response = client.get("/analytics/anomalies")
    assert response.status_code == 401


def test_anomalies_empty_for_new_user(client, auth_headers):
    response = client.get("/analytics/anomalies", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_anomalies_flags_outlier_and_is_scoped_to_user(client, auth_headers):
    for i in range(1, 8):
        _create_transaction(client, auth_headers, f"2026-01-{i:02d}", 500 + i)
    _create_transaction(client, auth_headers, "2026-01-20", 15000)

    response = client.get("/analytics/anomalies", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert any(a["amount"] == 15000 for a in body)

    client.post(
        "/auth/register",
        json={"email": "other-anom@example.com", "password": "supersecret123", "full_name": "Other User"},
    )
    other_login = client.post(
        "/auth/login", data={"username": "other-anom@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    other_response = client.get("/analytics/anomalies", headers=other_headers)
    assert other_response.status_code == 200
    assert other_response.json() == []
