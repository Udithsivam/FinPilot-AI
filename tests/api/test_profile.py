def test_new_user_has_empty_profile(client, auth_headers):
    response = client.get("/users/me/profile", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["user_type"] is None
    assert body["currency"] == "INR"


def test_update_and_read_profile(client, auth_headers):
    update = client.put(
        "/users/me/profile",
        json={"user_type": "Professional", "monthly_income": 60000.0, "currency": "USD"},
        headers=auth_headers,
    )
    assert update.status_code == 200
    assert update.json()["user_type"] == "Professional"

    response = client.get("/users/me/profile", headers=auth_headers)
    body = response.json()
    assert body["user_type"] == "Professional"
    assert body["monthly_income"] == 60000.0
    assert body["currency"] == "USD"


def test_profile_requires_auth(client):
    response = client.get("/users/me/profile")
    assert response.status_code == 401
