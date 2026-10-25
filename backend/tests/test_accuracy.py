"""Tests for AccuracyService (P4-T03, P4-T04, P4-T05)."""

from datetime import UTC, date, datetime, time

import pytest

from wind.accuracy import AccuracyService
from wind.models import WindActual, WindForecast


@pytest.mark.django_db
def test_accuracy_summary_with_seeded_data():
    """Summary service computes overall, daily metrics, and counts missing pairs."""
    d1 = date(2026, 1, 10)
    d2 = date(2026, 1, 11)

    # Delivery Day 1: 2026-01-10
    # Cutoff is 2026-01-09 11:00 UTC
    t1_1 = datetime(2026, 1, 10, 10, 0, tzinfo=UTC)
    p1_1 = datetime(2026, 1, 9, 10, 30, tzinfo=UTC)
    WindForecast.objects.create(start_time=t1_1, publish_time=p1_1, generation_mw=6000.0)
    WindActual.objects.create(start_time=t1_1, generation_mw=5500.0)  # error = +500

    t1_2 = datetime(2026, 1, 10, 10, 30, tzinfo=UTC)
    p1_2 = datetime(2026, 1, 9, 10, 30, tzinfo=UTC)
    WindForecast.objects.create(start_time=t1_2, publish_time=p1_2, generation_mw=7000.0)
    WindActual.objects.create(start_time=t1_2, generation_mw=7200.0)  # error = -200

    # Delivery Day 2: 2026-01-11
    # Cutoff is 2026-01-10 11:00 UTC
    t2_1 = datetime(2026, 1, 11, 12, 0, tzinfo=UTC)
    p2_1 = datetime(2026, 1, 10, 10, 0, tzinfo=UTC)
    WindForecast.objects.create(start_time=t2_1, publish_time=p2_1, generation_mw=8000.0)
    WindActual.objects.create(start_time=t2_1, generation_mw=8000.0)  # error = 0

    service = AccuracyService()
    res = service.calculate_as_of_summary(d1, d2, cutoff_time=time(11, 0))

    assert res.start_date == d1
    assert res.end_date == d2
    assert res.total_evaluated_periods == 3
    assert res.overall is not None
    assert res.overall.count == 3
    # Errors: +500, -200, 0 -> sum = 300 -> mean bias = +100.0 MW
    assert res.overall.bias_mw == 100.0
    # MAE: (500 + 200 + 0) / 3 = 233.33 MW
    assert res.overall.mae_mw == 233.33

    assert len(res.daily) == 2
    assert res.daily[0].delivery_date == d1
    assert res.daily[0].n_pairs == 2
    assert res.daily[1].delivery_date == d2
    assert res.daily[1].n_pairs == 1


@pytest.mark.django_db
def test_risk_adjusted_band_derivation():
    """Risk band is generated when enough samples are present."""
    service = AccuracyService()

    # Seed 12 points for one day to trigger band calculation (sample >= 10)
    d = date(2026, 1, 5)
    cutoff = datetime(2026, 1, 4, 11, 0, tzinfo=UTC)

    for i in range(12):
        st = datetime(2026, 1, 5, i, 0, tzinfo=UTC)
        WindForecast.objects.create(
            start_time=st, publish_time=cutoff, generation_mw=5000.0 + i * 50
        )
        WindActual.objects.create(
            start_time=st, generation_mw=4800.0 + i * 50
        )  # over-forecast by 200 MW

    res = service.calculate_as_of_summary(d, d, cutoff_time=time(11, 0))
    assert res.risk_band is not None
    assert res.risk_band.percentile == 90
    assert res.risk_band.p90_deduction_mw == 200.0
    assert res.risk_band.sample_size == 12
    assert "Plan on at least" in res.risk_band.description


@pytest.mark.django_db
def test_accuracy_by_horizon_bucketing():
    """calculate_by_horizon properly classifies forecasts into lead time buckets."""
    d = date(2026, 1, 15)
    t_target = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
    WindActual.objects.create(start_time=t_target, generation_mw=5000.0)

    # Lead time 4h -> 0-6h bucket
    p_4h = datetime(2026, 1, 15, 8, 0, tzinfo=UTC)
    WindForecast.objects.create(start_time=t_target, publish_time=p_4h, generation_mw=5100.0)

    # Lead time 8h -> 6-12h bucket
    p_8h = datetime(2026, 1, 15, 4, 0, tzinfo=UTC)
    WindForecast.objects.create(start_time=t_target, publish_time=p_8h, generation_mw=5200.0)

    # Lead time 20h -> 12-24h bucket
    p_20h = datetime(2026, 1, 14, 16, 0, tzinfo=UTC)
    WindForecast.objects.create(start_time=t_target, publish_time=p_20h, generation_mw=5300.0)

    service = AccuracyService()
    res = service.calculate_by_horizon(d, d)

    assert res.total_forecasts_evaluated == 3
    bucket_map = {b.bucket_name: b for b in res.buckets}

    assert "0-6h" in bucket_map
    assert bucket_map["0-6h"].metrics.mae_mw == 100.0
    assert bucket_map["0-6h"].avg_lead_time_hours == 4.0

    assert "6-12h" in bucket_map
    assert bucket_map["6-12h"].metrics.mae_mw == 200.0

    assert "12-24h" in bucket_map
    assert bucket_map["12-24h"].metrics.mae_mw == 300.0
