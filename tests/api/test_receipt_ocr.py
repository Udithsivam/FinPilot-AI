import io

from PIL import Image, ImageDraw


def _render_receipt_png(lines: list[str]) -> bytes:
    img = Image.new("RGB", (500, 40 * len(lines) + 20), "white")
    draw = ImageDraw.Draw(img)
    y = 10
    for line in lines:
        draw.text((10, y), line, fill="black")
        y += 40
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_receipt_ocr_requires_auth(client):
    image_bytes = _render_receipt_png(["STORE", "Total 100.00"])
    response = client.post(
        "/transactions/receipt-ocr", files={"file": ("receipt.png", image_bytes, "image/png")}
    )
    assert response.status_code == 401


def test_receipt_ocr_extracts_fields_and_suggests_category(client, auth_headers):
    image_bytes = _render_receipt_png(["SWIGGY RESTAURANT", "Grand Total 350.00"])
    response = client.post(
        "/transactions/receipt-ocr",
        files={"file": ("receipt.png", image_bytes, "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["raw_text"]
    assert body["amount"] == 350.0
    assert body["category"]
    assert isinstance(body["prediction_id"], int)


def test_receipt_ocr_rejects_non_image_file(client, auth_headers):
    response = client.post(
        "/transactions/receipt-ocr",
        files={"file": ("notes.txt", b"just some text", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_receipt_ocr_rejects_corrupt_image(client, auth_headers):
    response = client.post(
        "/transactions/receipt-ocr",
        files={"file": ("fake.png", b"not actually a png", "image/png")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_receipt_ocr_persists_prediction_scoped_to_user(client, auth_headers):
    image_bytes = _render_receipt_png(["NETFLIX", "Total 649.00"])
    response = client.post(
        "/transactions/receipt-ocr",
        files={"file": ("receipt.png", image_bytes, "image/png")},
        headers=auth_headers,
    )
    prediction_id = response.json()["prediction_id"]

    history = client.get("/predictions/history", headers=auth_headers).json()
    assert any(p["id"] == prediction_id for p in history)

    client.post(
        "/auth/register",
        json={"email": "other-ocr@example.com", "password": "supersecret123", "full_name": "Other"},
    )
    other_login = client.post(
        "/auth/login", data={"username": "other-ocr@example.com", "password": "supersecret123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    other_history = client.get("/predictions/history", headers=other_headers).json()
    assert not any(p["id"] == prediction_id for p in other_history)
