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


def test_chat_requires_auth(client):
    response = client.post("/ai/chat", json={"question": "What is an emergency fund?"})
    assert response.status_code == 401


def test_chat_answers_general_knowledge_question_with_citation(client, auth_headers):
    response = client.post("/ai/chat", json={"question": "What is an emergency fund?"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "emergency fund" in body["answer"].lower() or len(body["sources"]) > 0
    assert len(body["sources"]) > 0
    assert any(s["document_id"] == "emergency_fund" for s in body["sources"])
    assert body["provider"]


def test_chat_includes_real_user_data_for_spending_question(client, auth_headers):
    _create_transaction(client, auth_headers, "2026-01-01", 50000, ttype="income")
    _create_transaction(client, auth_headers, "2026-01-05", 5000, category="Groceries")

    response = client.post(
        "/ai/chat", json={"question": "What did I spend the most on this month?"}, headers=auth_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["user_facts"]) > 0
    assert any("Groceries" in fact or "income" in fact.lower() for fact in body["user_facts"])


def test_chat_is_scoped_to_authenticated_user(client, auth_headers):
    _create_transaction(client, auth_headers, "2026-01-01", 50000, ttype="income")
    _create_transaction(client, auth_headers, "2026-01-05", 99999, category="Entertainment")

    client.post(
        "/auth/register",
        json={"email": "other-chat@example.com", "password": "supersecret123", "full_name": "Other User"},
    )
    other_login = client.post(
        "/auth/login", data={"username": "other-chat@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.post(
        "/ai/chat", json={"question": "What did I spend the most on this month?"}, headers=other_headers
    )
    assert response.status_code == 200
    body = response.json()
    assert not any("99999" in fact or "Entertainment" in fact for fact in body["user_facts"])
