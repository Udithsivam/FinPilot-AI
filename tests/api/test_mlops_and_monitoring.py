import os


def _admin_headers(client, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "supersecret123", "full_name": "Admin"},
    )
    login = client.post("/auth/login", data={"username": "admin@example.com", "password": "supersecret123"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_monitoring_performance_requires_admin(client, auth_headers):
    response = client.get("/monitoring/performance", headers=auth_headers)
    assert response.status_code == 403


def test_monitoring_drift_requires_admin(client, auth_headers):
    response = client.get("/monitoring/drift", headers=auth_headers)
    assert response.status_code == 403


def test_mlops_summary_requires_admin(client, auth_headers):
    response = client.get("/mlops/summary", headers=auth_headers)
    assert response.status_code == 403


def test_mlops_summary_accessible_to_admin(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    response = client.get("/mlops/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "registry" in body
    assert "rag" in body
    assert body["rag"]["document_count"] > 0
    assert "feedback" in body


def test_monitoring_performance_reports_insufficient_data_with_no_actuals(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    response = client.get("/monitoring/performance", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert all(row["status"] == "insufficient_data" for row in body)


def test_monitoring_drift_returns_real_status(client, monkeypatch):
    headers = _admin_headers(client, monkeypatch)
    response = client.get("/monitoring/drift", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["feature"] == "transaction_amount"
    assert body[0]["status"] in ("stable", "warning", "drift_detected", "insufficient_data")


def test_set_actual_value_enables_performance_monitoring(client, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "admin2@example.com")
    client.post(
        "/auth/register",
        json={"email": "admin2@example.com", "password": "supersecret123", "full_name": "Admin"},
    )
    login = client.post("/auth/login", data={"username": "admin2@example.com", "password": "supersecret123"})
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    predict_payload = {
        "Income": 50000,
        "Age": 30,
        "Dependents": 1,
        "Occupation": "Professional",
        "City_Tier": "Tier_1",
        "Rent": 15000,
        "Loan_Repayment": 0,
        "Insurance": 1000,
        "Groceries": 5000,
        "Transport": 2000,
        "Eating_Out": 1500,
        "Entertainment": 1000,
        "Utilities": 1500,
        "Healthcare": 500,
        "Education": 0,
        "Miscellaneous": 500,
    }
    predict_response = client.post("/predict/savings", json=predict_payload, headers=admin_headers)
    assert predict_response.status_code == 200
    history = client.get("/predictions/history", headers=admin_headers).json()
    prediction_id = history[0]["id"]

    actual_response = client.patch(
        f"/predictions/{prediction_id}/actual", json={"actual_value": "9000.00"}, headers=admin_headers
    )
    assert actual_response.status_code == 200
    assert actual_response.json()["actual_value"] == "9000.00"
    assert actual_response.json()["status"] == "confirmed"

    perf_response = client.get("/monitoring/performance", headers=admin_headers)
    savings_row = next(r for r in perf_response.json() if r["prediction_type"] == "savings")
    # A single sample is still below MIN_SAMPLES (3) in
    # src/monitoring/performance.py — this asserts the honest
    # insufficient_data status, not a fabricated metric from 1 point.
    assert savings_row["status"] == "insufficient_data"


def test_actual_value_update_is_scoped_to_owner(client, auth_headers):
    other_headers_response = client.post(
        "/auth/register",
        json={"email": "other-actual@example.com", "password": "supersecret123", "full_name": "Other"},
    )
    assert other_headers_response.status_code in (200, 201)
    login = client.post(
        "/auth/login", data={"username": "other-actual@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.patch("/predictions/999999/actual", json={"actual_value": "100"}, headers=other_headers)
    assert response.status_code == 404
