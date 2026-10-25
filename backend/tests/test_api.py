"""Integration tests for Wind Forecast Monitor API endpoints (P5-T04)."""

from datetime import UTC, datetime

import pytest
from django.test import Client

from wind.models import WindActual, WindForecast


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def seeded_data():
    """Seed test data for Jan 10-11."""
    st = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)
    pt = datetime(2026, 1, 9, 10, 0, tzinfo=UTC)

    WindActual.objects.create(start_time=st, generation_mw=6000.0)
    WindForecast.objects.create(start_time=st, publish_time=pt, generation_mw=6500.0)


@pytest.mark.django_db
def test_meta_endpoint(client):
    """GET /api/v1/meta returns valid metadata, attribution, and definitions."""
    res = client.get("/api/v1/meta")
    assert res.status_code == 200
    data = res.json()
    assert "data_window_start" in data
    assert "attribution" in data
    assert "Elexon BMRS" in data["attribution"]
    assert "metric_definitions" in data
    assert "bias_mw" in data["metric_definitions"]


@pytest.mark.django_db
def test_forecast_endpoint_success(client, seeded_data):
    """GET /api/v1/forecast returns 48 half-hour points for valid delivery date."""
    res = client.get("/api/v1/forecast?delivery_date=2026-01-10&cutoff=11:00")
    assert res.status_code == 200
    data = res.json()
    assert data["delivery_date"] == "2026-01-10"
    assert data["cutoff_time"] == "11:00"
    assert data["total_periods"] == 48
    assert len(data["points"]) == 48

    # Find the seeded point
    pt = next(p for p in data["points"] if p["start_time"].startswith("2026-01-10T12:00"))
    assert pt["forecast_mw"] == 6500.0
    assert pt["actual_mw"] == 6000.0
    assert pt["lead_time_hours"] == 26.0


@pytest.mark.django_db
def test_forecast_endpoint_validation_errors(client):
    """GET /api/v1/forecast returns 422 for invalid date, out-of-range date, or invalid cutoff."""
    # 1. Missing delivery_date
    res1 = client.get("/api/v1/forecast")
    assert res1.status_code == 422
    assert res1.json()["error"]["code"] == "VALIDATION_FAILED"

    # 2. Out of window delivery_date
    res2 = client.get("/api/v1/forecast?delivery_date=2020-01-01")
    assert res2.status_code == 422
    assert "must be within the available data window" in res2.json()["error"]["message"]

    # 3. Invalid cutoff time
    res3 = client.get("/api/v1/forecast?delivery_date=2026-01-10&cutoff=99:99")
    assert res3.status_code == 422
    assert "Cutoff time must be a valid time" in res3.json()["error"]["message"]


@pytest.mark.django_db
def test_accuracy_summary_endpoint(client, seeded_data):
    """GET /api/v1/accuracy/summary returns overall and daily metrics."""
    res = client.get(
        "/api/v1/accuracy/summary?from_date=2026-01-10&to_date=2026-01-10&cutoff=11:00"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["start_date"] == "2026-01-10"
    assert data["end_date"] == "2026-01-10"
    assert data["total_evaluated_periods"] == 1
    assert data["overall"]["bias_mw"] == 500.0
    assert data["overall"]["mae_mw"] == 500.0
    assert len(data["daily"]) == 1


@pytest.mark.django_db
def test_accuracy_summary_date_inversion_error(client):
    """GET /api/v1/accuracy/summary returns 422 when from_date > to_date."""
    res = client.get("/api/v1/accuracy/summary?from_date=2026-01-20&to_date=2026-01-10")
    assert res.status_code == 422
    assert "cannot be after" in res.json()["error"]["message"]


@pytest.mark.django_db
def test_accuracy_by_horizon_endpoint(client, seeded_data):
    """GET /api/v1/accuracy/by-horizon returns lead time buckets."""
    res = client.get("/api/v1/accuracy/by-horizon?from_date=2026-01-10&to_date=2026-01-10")
    assert res.status_code == 200
    data = res.json()
    assert "buckets" in data
    assert data["total_forecasts_evaluated"] >= 1


@pytest.mark.django_db
def test_request_id_header_returned(client):
    """Custom X-Request-ID should be echoed back on all responses."""
    custom_id = "test-req-id-12345"
    res = client.get("/api/v1/meta", HTTP_X_REQUEST_ID=custom_id)
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_id
