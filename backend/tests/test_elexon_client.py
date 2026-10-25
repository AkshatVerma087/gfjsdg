"""Tests for Elexon BMRS HTTP client using respx (P3-T02)."""

import json
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
import respx

from core.errors import UpstreamUnavailable
from wind.elexon.client import ElexonClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fuelhh_sample():
    with open(FIXTURES_DIR / "elexon_fuelhh_sample.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def windfor_sample():
    with open(FIXTURES_DIR / "elexon_windfor_sample.json", encoding="utf-8") as f:
        return json.load(f)


@respx.mock
def test_fetch_actuals_success(fuelhh_sample):
    """fetch_actuals filters for fuelType=WIND and parses correctly."""
    respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream").respond(
        status_code=200,
        json=fuelhh_sample,
    )

    client = ElexonClient()
    records = client.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    assert len(records) == 2
    assert records[0].generation_mw == 15538.0
    assert records[0].start_time == datetime(2026, 1, 1, 23, 30, tzinfo=UTC)
    assert records[1].generation_mw == 14920.0


@respx.mock
def test_fetch_forecasts_success(windfor_sample):
    """fetch_forecasts parses startTime, publishTime, and generation_mw."""
    respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream").respond(
        status_code=200,
        json=windfor_sample,
    )

    client = ElexonClient()
    records = client.fetch_forecasts(
        datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        datetime(2026, 1, 1, 23, 59, tzinfo=UTC),
    )

    assert len(records) == 3
    assert records[0].generation_mw == 12450.0
    assert records[0].publish_time == datetime(2026, 1, 1, 10, 30, tzinfo=UTC)
    assert records[0].start_time == datetime(2026, 1, 2, 0, 0, tzinfo=UTC)


@respx.mock
def test_retry_on_server_error_then_succeed(fuelhh_sample):
    """Client should retry on 500/503 and succeed when subsequent call returns 200."""
    route = respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream")
    route.side_effect = [
        httpx.Response(503, text="Service Unavailable"),
        httpx.Response(200, json=fuelhh_sample),
    ]

    client = ElexonClient(max_retries=2, backoff_base_seconds=0.01)
    records = client.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    assert len(records) == 2
    assert route.call_count == 2


@respx.mock
def test_retry_exhaustion_raises_upstream_unavailable():
    """Client should raise UpstreamUnavailable after retries are exhausted."""
    route = respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream")
    route.respond(status_code=500, text="Internal Server Error")

    client = ElexonClient(max_retries=2, backoff_base_seconds=0.01)
    with pytest.raises(UpstreamUnavailable) as exc_info:
        client.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    assert "Elexon upstream request failed" in str(exc_info.value)
    assert route.call_count == 3


@respx.mock
def test_malformed_payload_raises_upstream_unavailable():
    """Non-list payload raises UpstreamUnavailable."""
    respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream").respond(
        status_code=200,
        json={"error": "Invalid format"},
    )

    client = ElexonClient(max_retries=0)
    with pytest.raises(UpstreamUnavailable) as exc_info:
        client.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))

    assert "Malformed payload" in str(exc_info.value)


@respx.mock
def test_empty_results_returns_empty_list():
    """Empty list from API returns empty list without error."""
    respx.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream").respond(
        status_code=200,
        json=[],
    )

    client = ElexonClient(max_retries=0)
    records = client.fetch_actuals(date(2026, 1, 1), date(2026, 1, 1))
    assert records == []
