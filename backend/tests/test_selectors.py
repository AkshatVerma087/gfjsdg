"""Tests for as-of forecast selector (P4-T01)."""

from datetime import UTC, date, datetime, time

import pytest

from wind.models import WindActual, WindForecast
from wind.selectors import get_as_of_forecast_for_day, get_as_of_pairs_for_range


@pytest.mark.django_db
def test_selector_cutoff_inclusion_and_recency():
    """Selector must pick the latest forecast with publish_time <= cutoff (inclusive)."""
    delivery_date = date(2026, 1, 15)
    t_target = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)

    # Publishes on D-1 (2026-01-14)
    p_0800 = datetime(2026, 1, 14, 8, 0, tzinfo=UTC)
    p_0900 = datetime(2026, 1, 14, 9, 0, tzinfo=UTC)
    p_1000 = datetime(2026, 1, 14, 10, 0, tzinfo=UTC)

    WindForecast.objects.create(start_time=t_target, publish_time=p_0800, generation_mw=5000.0)
    WindForecast.objects.create(start_time=t_target, publish_time=p_0900, generation_mw=5500.0)
    WindForecast.objects.create(start_time=t_target, publish_time=p_1000, generation_mw=6000.0)
    WindActual.objects.create(start_time=t_target, generation_mw=5400.0)

    # 1. Cutoff at 09:00: should pick p_0900 (5500 MW), since publish_time <= cutoff is inclusive
    res_0900 = get_as_of_forecast_for_day(delivery_date, cutoff_time=time(9, 0))
    pt_1400 = next(p for p in res_0900.points if p.start_time == t_target)
    assert pt_1400.forecast_mw == 5500.0
    assert pt_1400.publish_time == p_0900
    assert pt_1400.actual_mw == 5400.0
    assert pt_1400.lead_time_hours == 29.0  # (15th 14:00 - 14th 09:00) = 29 hours

    # 2. Cutoff at 08:59: should pick p_0800 (5000 MW)
    res_0859 = get_as_of_forecast_for_day(delivery_date, cutoff_time=time(8, 59))
    pt_1400_early = next(p for p in res_0859.points if p.start_time == t_target)
    assert pt_1400_early.forecast_mw == 5000.0
    assert pt_1400_early.publish_time == p_0800

    # 3. Cutoff at 07:59: no forecast before cutoff -> None
    res_0759 = get_as_of_forecast_for_day(delivery_date, cutoff_time=time(7, 59))
    pt_1400_none = next(p for p in res_0759.points if p.start_time == t_target)
    assert pt_1400_none.forecast_mw is None
    assert pt_1400_none.publish_time is None
    assert pt_1400_none.actual_mw == 5400.0


@pytest.mark.django_db
def test_selector_returns_48_half_hours_with_boundaries():
    """Selector returns exactly 48 periods, covering 00:00 to 23:30."""
    delivery_date = date(2026, 1, 20)
    d_minus_1_1100 = datetime(2026, 1, 19, 11, 0, tzinfo=UTC)

    # Seed 00:00 and 23:30 boundaries
    t_start = datetime(2026, 1, 20, 0, 0, tzinfo=UTC)
    t_end = datetime(2026, 1, 20, 23, 30, tzinfo=UTC)

    WindForecast.objects.create(
        start_time=t_start, publish_time=d_minus_1_1100, generation_mw=3000.0
    )
    WindForecast.objects.create(start_time=t_end, publish_time=d_minus_1_1100, generation_mw=4500.0)
    WindActual.objects.create(start_time=t_start, generation_mw=3100.0)

    res = get_as_of_forecast_for_day(delivery_date, cutoff_time=time(11, 0))

    assert res.total_periods == 48
    assert len(res.points) == 48
    assert res.points[0].settlement_period == 1
    assert res.points[0].start_time == t_start
    assert res.points[0].forecast_mw == 3000.0
    assert res.points[0].actual_mw == 3100.0

    assert res.points[47].settlement_period == 48
    assert res.points[47].start_time == t_end
    assert res.points[47].forecast_mw == 4500.0
    assert res.points[47].actual_mw is None

    # Missing counts (00:00 covers periods 1 & 2, plus period 48)
    assert res.missing_forecast_count == 45
    assert res.missing_actual_count == 47


@pytest.mark.django_db
def test_get_as_of_pairs_for_range():
    """get_as_of_pairs_for_range returns only paired records across multiple days."""
    d1 = date(2026, 1, 10)
    d2 = date(2026, 1, 11)

    t1 = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)
    p1 = datetime(2026, 1, 9, 11, 0, tzinfo=UTC)
    WindForecast.objects.create(start_time=t1, publish_time=p1, generation_mw=7000.0)
    WindActual.objects.create(start_time=t1, generation_mw=6800.0)

    t2 = datetime(2026, 1, 11, 12, 0, tzinfo=UTC)
    p2 = datetime(2026, 1, 10, 11, 0, tzinfo=UTC)
    WindForecast.objects.create(start_time=t2, publish_time=p2, generation_mw=8000.0)
    WindActual.objects.create(start_time=t2, generation_mw=8200.0)

    pairs = get_as_of_pairs_for_range(d1, d2, cutoff_time=time(11, 0))
    assert len(pairs) == 2
    assert pairs[0][1] == 7000.0
    assert pairs[0][2] == 6800.0
    assert pairs[1][1] == 8000.0
    assert pairs[1][2] == 8200.0
