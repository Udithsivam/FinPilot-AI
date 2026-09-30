from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.core.config import get_settings
from backend.app.core.rate_limit import _buckets, rate_limit


class FakeRequest:
    def __init__(self, host="1.2.3.4", path="/auth/login"):
        self.client = SimpleNamespace(host=host)
        self.url = SimpleNamespace(path=path)


@pytest.fixture(autouse=True)
def _isolated_rate_limit_state(monkeypatch):
    _buckets.clear()
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_allows_requests_under_the_limit():
    dependency = rate_limit(3).dependency
    request = FakeRequest()
    for _ in range(3):
        dependency(request)


def test_blocks_requests_over_the_limit():
    dependency = rate_limit(3).dependency
    request = FakeRequest()
    for _ in range(3):
        dependency(request)

    with pytest.raises(HTTPException) as exc_info:
        dependency(request)
    assert exc_info.value.status_code == 429


def test_tracks_clients_independently():
    dependency = rate_limit(1).dependency
    dependency(FakeRequest(host="1.1.1.1"))
    dependency(FakeRequest(host="2.2.2.2"))


def test_tracks_routes_independently():
    dependency = rate_limit(1).dependency
    dependency(FakeRequest(path="/auth/login"))
    dependency(FakeRequest(path="/auth/register"))


def test_disabled_via_settings(monkeypatch):
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")
    get_settings.cache_clear()
    dependency = rate_limit(1).dependency
    request = FakeRequest()
    for _ in range(5):
        dependency(request)
