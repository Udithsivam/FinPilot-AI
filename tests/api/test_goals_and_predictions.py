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
    assert isinstance(response.json()["predicted_desired_savings"], float)


def test_predict_savings_rejects_unknown_occupation(client, auth_headers):
    payload = {**VALID_PREDICTION_PAYLOAD, "Occupation": "Astronaut"}
    response = client.post("/predict/savings", json=payload, headers=auth_headers)
    assert response.status_code == 422
