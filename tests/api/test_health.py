def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_metrics_endpoint_exposed(client):
    response = client.get("/metrics")
    assert response.status_code == 200


def test_cors_headers_present_for_cross_origin_request(client):
    # Regression: without CORSMiddleware, a frontend served from a
    # different origin than the API (any real production deployment)
    # would have every request silently blocked by the browser.
    response = client.get("/health", headers={"Origin": "https://app.example.com"})
    assert response.headers.get("access-control-allow-origin") == "*"
