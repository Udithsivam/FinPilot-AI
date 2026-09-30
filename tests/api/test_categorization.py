def test_categorize_returns_valid_category(client, auth_headers):
    response = client.post(
        "/transactions/categorize",
        json={"merchant": "Swiggy", "description": "Swiggy Order"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category"]
    assert body["subcategory"]
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["model_version"]
    assert isinstance(body["prediction_id"], int)


def test_categorize_low_confidence_for_generic_text(client, auth_headers):
    # A UPI reference string carries no category signal — the model
    # should not be confident about it.
    response = client.post(
        "/transactions/categorize",
        json={"merchant": "", "description": "UPI-1234567890@ybl"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["confidence"] < 0.9


def test_categorize_persists_a_prediction(client, auth_headers):
    client.post(
        "/transactions/categorize",
        json={"merchant": "Netflix", "description": "Netflix Subscription"},
        headers=auth_headers,
    )
    history = client.get("/predictions/history", headers=auth_headers).json()
    assert any(p["prediction_type"] == "categorization" for p in history)


def test_categorize_requires_auth(client):
    response = client.post("/transactions/categorize", json={"merchant": "Swiggy", "description": "Order"})
    assert response.status_code == 401
