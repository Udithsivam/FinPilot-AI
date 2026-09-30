def test_register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "supersecret123", "full_name": "Alice"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["email"] == "alice@example.com"

    login_response = client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "supersecret123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"


def test_duplicate_registration_rejected(client):
    payload = {"email": "bob@example.com", "password": "supersecret123", "full_name": "Bob"}
    client.post("/auth/register", json=payload)
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400


def test_login_with_wrong_password_rejected(client):
    client.post(
        "/auth/register",
        json={"email": "carol@example.com", "password": "supersecret123", "full_name": "Carol"},
    )
    response = client.post(
        "/auth/login", data={"username": "carol@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_overlong_password_rejected_at_registration(client):
    # Regression: bcrypt raises ValueError above 72 bytes, which used to
    # surface as an unhandled 500 instead of a clean validation error.
    response = client.post(
        "/auth/register",
        json={"email": "dave@example.com", "password": "x" * 100, "full_name": "Dave"},
    )
    assert response.status_code == 422


def test_overlong_password_rejected_at_login_without_crashing(client):
    client.post(
        "/auth/register",
        json={"email": "erin@example.com", "password": "supersecret123", "full_name": "Erin"},
    )
    response = client.post(
        "/auth/login", data={"username": "erin@example.com", "password": "x" * 100}
    )
    assert response.status_code == 401


def test_too_short_password_rejected_at_registration(client):
    response = client.post(
        "/auth/register",
        json={"email": "frank@example.com", "password": "short", "full_name": "Frank"},
    )
    assert response.status_code == 422


def test_protected_endpoint_requires_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_me_returns_authenticated_user(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
