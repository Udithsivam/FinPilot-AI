def _other_user_headers(client):
    client.post(
        "/auth/register",
        json={"email": "feedback-user-b@example.com", "password": "supersecret123", "full_name": "User B"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "feedback-user-b@example.com", "password": "supersecret123"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_create_feedback_without_prediction(client, auth_headers):
    response = client.post(
        "/feedback",
        json={"feedback_type": "recommendation_feedback", "corrected_value": "not useful"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["prediction_id"] is None
    assert body["feedback_type"] == "recommendation_feedback"


def test_create_feedback_referencing_own_prediction(client, auth_headers):
    categorize_response = client.post(
        "/transactions/categorize",
        json={"merchant": "Amazon", "description": "Amazon Order"},
        headers=auth_headers,
    )
    prediction_id = categorize_response.json()["prediction_id"]

    response = client.post(
        "/feedback",
        json={
            "prediction_id": prediction_id,
            "feedback_type": "category_correction",
            "corrected_value": "Shopping > Electronics",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["prediction_id"] == prediction_id


def test_feedback_rejects_another_users_prediction_id(client, auth_headers):
    categorize_response = client.post(
        "/transactions/categorize",
        json={"merchant": "Amazon", "description": "Amazon Order"},
        headers=auth_headers,
    )
    prediction_id = categorize_response.json()["prediction_id"]

    user_b_headers = _other_user_headers(client)
    response = client.post(
        "/feedback",
        json={
            "prediction_id": prediction_id,
            "feedback_type": "category_correction",
            "corrected_value": "Food > Restaurants",
        },
        headers=user_b_headers,
    )
    assert response.status_code == 404


def test_feedback_requires_auth(client):
    response = client.post("/feedback", json={"feedback_type": "recommendation_feedback"})
    assert response.status_code == 401
