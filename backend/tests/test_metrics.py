"""Unit tests for pure forecast accuracy metrics (P4-T02)."""

import pytest

from wind.metrics import calculate_metrics


def test_metrics_empty_input():
    """Empty inputs should return None."""
    assert calculate_metrics([], []) is None


def test_metrics_length_mismatch():
    """Mismatched array lengths should raise ValueError."""
    with pytest.raises(ValueError, match="Forecasts length .* does not match"):
        calculate_metrics([100.0], [100.0, 200.0])


def test_metrics_single_pair():
    """Single pair calculation."""
    res = calculate_metrics([1200.0], [1000.0])
    assert res is not None
    assert res.count == 1
    assert res.bias_mw == 200.0
    assert res.mae_mw == 200.0
    assert res.rmse_mw == 200.0
    assert res.p50_abs_error_mw == 200.0
    assert res.wape_pct == 20.0  # 200 / 1000 * 100
    assert res.over_forecast_count == 1
    assert res.over_forecast_pct == 100.0
    assert res.under_forecast_count == 0


def test_metrics_hand_calculated_suite():
    """Hand-calculated table test for known values.

    Pairs:
    1: f=1000, a=800  -> error=+200, |error|=200, over=200
    2: f=1500, a=1600 -> error=-100, |error|=100, over=0
    3: f=2000, a=2000 -> error=0,    |error|=0,   over=0
    4: f=3000, a=2600 -> error=+400, |error|=400, over=400
    5: f=2500, a=2700 -> error=-200, |error|=200, over=0

    Total actuals = 800 + 1600 + 2000 + 2600 + 2700 = 9700
    Errors = [+200, -100, 0, +400, -200]
    Abs Errors = [200, 100, 0, 400, 200]
    Mean error (bias) = (200 - 100 + 0 + 400 - 200) / 5 = 300 / 5 = +60.0 MW
    MAE = (200 + 100 + 0 + 400 + 200) / 5 = 900 / 5 = 180.0 MW
    Squared errors = [40000, 10000, 0, 160000, 40000] -> sum = 250000
    Mean squared error = 250000 / 5 = 50000 -> RMSE = sqrt(50000) = 223.61 MW
    Sorted abs errors = [0, 100, 200, 200, 400]
    P50 = 200.0 MW
    WAPE = (900 / 9700) * 100 = 9.28 %
    Over count: 2 (40%)
    Under count: 2 (40%)
    Exact count: 1 (20%)
    """
    f = [1000.0, 1500.0, 2000.0, 3000.0, 2500.0]
    a = [800.0, 1600.0, 2000.0, 2600.0, 2700.0]

    res = calculate_metrics(f, a)
    assert res is not None
    assert res.count == 5
    assert res.bias_mw == 60.0
    assert res.mae_mw == 180.0
    assert res.rmse_mw == 223.61
    assert res.p50_abs_error_mw == 200.0
    assert res.wape_pct == 9.28
    assert res.over_forecast_count == 2
    assert res.over_forecast_pct == 40.0
    assert res.under_forecast_count == 2
    assert res.under_forecast_pct == 40.0
    assert res.exact_count == 1


def test_metrics_zero_and_negative_actuals():
    """WAPE should safely return None when sum of actuals is zero or negative."""
    f = [100.0, 200.0]
    a = [0.0, 0.0]
    res = calculate_metrics(f, a)
    assert res is not None
    assert res.wape_pct is None
    assert res.mae_mw == 150.0
