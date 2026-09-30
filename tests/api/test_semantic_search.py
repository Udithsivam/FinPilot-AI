def _create_transaction(client, headers, merchant, description, category="Food"):
    return client.post(
        "/transactions",
        json={
            "date": "2026-01-05",
            "amount": 500,
            "type": "expense",
            "category": category,
            "subcategory": None,
            "merchant": merchant,
            "payment_method": "UPI",
            "description": description,
            "is_recurring": False,
        },
        headers=headers,
    )


def test_search_requires_auth(client):
    response = client.get("/transactions/search", params={"q": "food"})
    assert response.status_code == 401


def test_search_returns_matching_transactions(client, auth_headers):
    _create_transaction(client, auth_headers, "Swiggy", "Swiggy Order food delivery")
    _create_transaction(client, auth_headers, "Netflix", "Netflix Subscription", category="Subscriptions")

    response = client.get("/transactions/search", params={"q": "food delivery"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert any(r["merchant"] == "Swiggy" for r in body)
    assert not any(r["merchant"] == "Netflix" for r in body)


def test_search_is_scoped_to_authenticated_user(client, auth_headers):
    _create_transaction(client, auth_headers, "Swiggy", "Swiggy Order food delivery")

    client.post(
        "/auth/register",
        json={"email": "other-search@example.com", "password": "supersecret123", "full_name": "Other User"},
    )
    other_login = client.post(
        "/auth/login", data={"username": "other-search@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.get("/transactions/search", params={"q": "food delivery"}, headers=other_headers)
    assert response.status_code == 200
    assert response.json() == []
