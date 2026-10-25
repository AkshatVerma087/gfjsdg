"""Tests for Wind models and ingestion service (P3-T01, P3-T03)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from django.db import IntegrityError, transaction

from wind.elexon.client import WindActualRecord, WindForecastRecord
from wind.ingestion import IngestionService
from wind.models import WindActual, WindForecast


@pytest.mark.django_db
def test_wind_actual_unique_constraint():
    """Duplicate start_time for WindActual must raise IntegrityError."""
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    WindActual.objects.create(start_time=t0, generation_mw=5000.0)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            WindActual.objects.create(start_time=t0, generation_mw=5200.0)


@pytest.mark.django_db
def test_wind_forecast_unique_constraint():
    """Duplicate (start_time, publish_time) for WindForecast must raise IntegrityError."""
    st = datetime(2026, 1, 2, 14, 0, tzinfo=UTC)
    pt = datetime(2026, 1, 1, 11, 0, tzinfo=UTC)
    WindForecast.objects.create(start_time=st, publish_time=pt, generation_mw=6000.0)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            WindForecast.objects.create(start_time=st, publish_time=pt, generation_mw=6100.0)


@pytest.mark.django_db
def test_ingestion_service_idempotence():
    """Running ingestion twice with identical records should update existing rows without duplicating."""
    mock_client = MagicMock()

    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 1, 1, 0, 30, tzinfo=UTC)
    p0 = datetime(2025, 12, 31, 10, 0, tzinfo=UTC)

    mock_client.fetch_actuals.return_value = [
        WindActualRecord(start_time=t0, generation_mw=1000.0),
        WindActualRecord(start_time=t1, generation_mw=1200.0),
    ]
    mock_client.fetch_forecasts.return_value = [
        WindForecastRecord(start_time=t0, publish_time=p0, generation_mw=1050.0),
        WindForecastRecord(start_time=t1, publish_time=p0, generation_mw=1180.0),
    ]

    service = IngestionService(client=mock_client)

    # First run
    res1 = service.ingest_full_window()
    assert res1["actuals_count"] == 2
    assert res1["forecasts_count"] == 2
    assert WindActual.objects.count() == 2
    assert WindForecast.objects.count() == 2

    # Second run with revised values for the same timestamps
    mock_client.fetch_actuals.return_value = [
        WindActualRecord(start_time=t0, generation_mw=1010.0),
        WindActualRecord(start_time=t1, generation_mw=1200.0),
    ]
    res2 = service.ingest_full_window()
    assert res2["actuals_count"] == 2
    assert WindActual.objects.count() == 2
    assert WindForecast.objects.count() == 2

    # Check updated generation_mw
    updated_actual = WindActual.objects.get(start_time=t0)
    assert updated_actual.generation_mw == 1010.0
