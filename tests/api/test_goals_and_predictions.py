def test_goal_progress_calculation(client, auth_headers):
    client.post(
        "/goals",
        json={"name": "Laptop", "target_amount": 80000.0, "current_amount": 20000.0},
        headers=auth_headers,
    )
    goals = client.get("/goals", headers=auth_headers).json()
    assert len(goals) == 1
    assert goals[0]["progress_pct"] == 25.0


def test_delete_missing_goal_returns_404(client, auth_headers):
    response = client.delete("/goals/999", headers=auth_headers)
    assert response.status_code == 404


def test_negative_target_amount_rejected(client, auth_headers):
    response = client.post(
        "/goals",
        json={"name": "Laptop", "target_amount": -100.0},
        headers=auth_headers,
    )
    assert response.status_code == 422


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


def test_user_cannot_list_or_delete_another_users_goal(client, auth_headers):
    created = client.post(
        "/goals",
        json={"name": "User A's Laptop", "target_amount": 80000.0},
        headers=auth_headers,
    ).json()
    user_b_headers = _other_user_headers(client)

    listing = client.get("/goals", headers=user_b_headers).json()
    assert all(g["id"] != created["id"] for g in listing)

    delete_response = client.delete(f"/goals/{created['id']}", headers=user_b_headers)
    assert delete_response.status_code == 404

    # the resource must still belong to, and be visible/deletable by, its owner
    owner_listing = client.get("/goals", headers=auth_headers).json()
    assert any(g["id"] == created["id"] for g in owner_listing)


VALID_PREDICTION_PAYLOAD = {
    "Income": 50000.0,
    "Age": 30,
    "Dependents": 1,
    "Occupation": "Professional",
    "City_Tier": "Tier_1",
    "Rent": 10000.0,
    "Loan_Repayment": 2000.0,
    "Insurance": 1500.0,
    "Groceries": 5000.0,
    "Transport": 2000.0,
    "Eating_Out": 1500.0,
    "Entertainment": 1500.0,
    "Utilities": 2000.0,
    "Healthcare": 1000.0,
    "Education": 0.0,
    "Miscellaneous": 1000.0,
}


def test_predict_savings_requires_auth(client):
    response = client.post("/predict/savings", json=VALID_PREDICTION_PAYLOAD)
    assert response.status_code == 401


def test_predict_savings_returns_a_number(client, auth_headers):
    response = client.post("/predict/savings", json=VALID_PREDICTION_PAYLOAD, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["predicted_desired_savings"], float)
    assert body["model_type"]
    assert body["model_version"]


def test_predict_savings_rejects_unknown_occupation(client, auth_headers):
    payload = {**VALID_PREDICTION_PAYLOAD, "Occupation": "Astronaut"}
    response = client.post("/predict/savings", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_predict_savings_returns_503_when_model_missing(client, auth_headers, monkeypatch):
    def _raise_missing(*args, **kwargs):
        raise FileNotFoundError("no model artifact")

    monkeypatch.setattr("src.pipeline.predict.load_pipeline", _raise_missing)
    response = client.post("/predict/savings", json=VALID_PREDICTION_PAYLOAD, headers=auth_headers)
    assert response.status_code == 503


def test_predict_savings_includes_real_explanation(client, auth_headers):
    response = client.post("/predict/savings", json=VALID_PREDICTION_PAYLOAD, headers=auth_headers)
    explanation = response.json()["explanation"]
    assert len(explanation) > 0
    for factor in explanation:
        assert factor["feature"]
        assert isinstance(factor["impact"], float)
        assert factor["direction"] in ("positive", "negative")
    # Income should dominate a GradientBoostingRegressor trained on this dataset.
    assert explanation[0]["feature"] == "Income"


def test_predict_savings_persists_to_history(client, auth_headers):
    client.post("/predict/savings", json=VALID_PREDICTION_PAYLOAD, headers=auth_headers)
    history = client.get("/predictions/history", headers=auth_headers).json()
    assert any(p["prediction_type"] == "savings" for p in history)


def test_prediction_history_requires_auth(client):
    response = client.get("/predictions/history")
    assert response.status_code == 401


def test_user_cannot_see_another_users_prediction_history(client, auth_headers):
    client.post("/predict/savings", json=VALID_PREDICTION_PAYLOAD, headers=auth_headers)
    user_b_headers = _other_user_headers(client)
    history = client.get("/predictions/history", headers=user_b_headers).json()
    assert history == []
