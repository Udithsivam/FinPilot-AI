import io

import pytest
from PIL import Image, ImageDraw

from src.ocr.receipt_parser import extract_text, parse_receipt_fields


def _render_receipt_image(lines: list[str]) -> bytes:
    img = Image.new("RGB", (500, 40 * len(lines) + 20), "white")
    draw = ImageDraw.Draw(img)
    y = 10
    for line in lines:
        draw.text((10, y), line, fill="black")
        y += 40
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_parse_receipt_fields_extracts_merchant_and_grand_total():
    text = "SWIGGY RESTAURANT\nOrder #12345\nItem 1     250.00\nSubtotal   250.00\nGrand Total 275.00"
    fields = parse_receipt_fields(text)
    assert fields["merchant"] == "SWIGGY RESTAURANT"
    assert fields["amount"] == 275.00
    assert fields["raw_text"] == text


def test_parse_receipt_fields_prefers_total_over_subtotal():
    text = "STORE\nSubtotal 100.00\nTotal 120.00"
    fields = parse_receipt_fields(text)
    assert fields["amount"] == 120.00


def test_parse_receipt_fields_falls_back_to_largest_number_without_total_keyword():
    text = "STORE\nItem A 50.00\nItem B 75.00"
    fields = parse_receipt_fields(text)
    assert fields["amount"] == 75.00


def test_parse_receipt_fields_extracts_iso_date():
    text = "STORE\nDate: 2026-03-15\nTotal 100.00"
    fields = parse_receipt_fields(text)
    assert fields["date"] == "2026-03-15"


def test_parse_receipt_fields_rejects_implausible_date():
    text = "STORE\nPhone: 99-99-9999\nTotal 100.00"
    fields = parse_receipt_fields(text)
    assert fields["date"] is None


def test_parse_receipt_fields_handles_empty_text():
    fields = parse_receipt_fields("")
    assert fields["merchant"] is None
    assert fields["amount"] is None
    assert fields["date"] is None


def test_extract_text_runs_real_ocr_on_a_rendered_receipt():
    pytest.importorskip("pytesseract")
    image_bytes = _render_receipt_image(["TEST STORE", "Grand Total 199.00"])
    text = extract_text(image_bytes)
    assert "TEST STORE" in text or "TEST" in text.upper()


def test_extract_text_rejects_non_image_bytes():
    with pytest.raises(ValueError):
        extract_text(b"this is not an image")
