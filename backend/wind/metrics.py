"""Pure forecast accuracy metric calculation (P4-T02).

Design rules:
1. PURE: No Django models, no ORM, no database or network I/O.
2. Sign convention: error = forecast - actual. Positive = over-forecast.
3. Edge cases: Empty input, single pair, division by zero, all-zero actuals handled safely.
"""

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class AccuracyMetrics:
    """Standard forecast accuracy evaluation metrics."""

    count: int
    bias_mw: float  # Mean (forecast - actual)
    mae_mw: float  # Mean |forecast - actual|
    rmse_mw: float  # sqrt(Mean (forecast - actual)^2)
    p50_abs_error_mw: float  # Median absolute error
    p90_abs_error_mw: float  # 90th percentile absolute error
    p95_abs_error_mw: float  # 95th percentile absolute error
    wape_pct: float | None  # sum(|error|) / sum(actual) * 100 (None if sum(actual) <= 0)
    over_forecast_count: int  # forecast > actual
    over_forecast_pct: float  # % of periods over-forecast
    under_forecast_count: int  # forecast < actual
    under_forecast_pct: float  # % of periods under-forecast
    exact_count: int  # forecast == actual
    p90_over_forecast_mw: float  # 90th percentile of max(forecast - actual, 0)

    def to_dict(self) -> dict:
        return asdict(self)


def calculate_metrics(
    forecasts: list[float] | np.ndarray,
    actuals: list[float] | np.ndarray,
) -> AccuracyMetrics | None:
    """Calculate accuracy metrics from paired forecast and actual generation arrays.

    Args:
        forecasts: Array of forecast generation values in MW.
        actuals: Array of actual generation values in MW (same length as forecasts).

    Returns:
        AccuracyMetrics if count > 0, else None.
    """
    f_arr = np.asarray(forecasts, dtype=np.float64)
    a_arr = np.asarray(actuals, dtype=np.float64)

    if len(f_arr) != len(a_arr):
        raise ValueError(
            f"Forecasts length ({len(f_arr)}) does not match actuals length ({len(a_arr)})"
        )

    n = len(f_arr)
    if n == 0:
        return None

    # Error definitions
    errors = f_arr - a_arr
    abs_errors = np.abs(errors)

    bias = float(np.mean(errors))
    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors**2)))

    # Percentiles of absolute error (using nearest rank / linear interpolation)
    p50 = float(np.percentile(abs_errors, 50))
    p90 = float(np.percentile(abs_errors, 90))
    p95 = float(np.percentile(abs_errors, 95))

    # WAPE: sum(|error|) / sum(actual) * 100
    sum_actuals = float(np.sum(a_arr))
    if sum_actuals > 0:
        wape = float((np.sum(abs_errors) / sum_actuals) * 100.0)
    else:
        wape = None

    # Over / Under forecast distribution
    over_count = int(np.sum(f_arr > a_arr))
    under_count = int(np.sum(f_arr < a_arr))
    exact_count = int(np.sum(f_arr == a_arr))

    over_pct = float(round((over_count / n) * 100.0, 2))
    under_pct = float(round((under_count / n) * 100.0, 2))

    # Empirical over-forecast error (max(f - a, 0)) for risk-adjusted planning band
    over_errors = np.maximum(errors, 0.0)
    p90_over = float(np.percentile(over_errors, 90))

    return AccuracyMetrics(
        count=n,
        bias_mw=round(bias, 2),
        mae_mw=round(mae, 2),
        rmse_mw=round(rmse, 2),
        p50_abs_error_mw=round(p50, 2),
        p90_abs_error_mw=round(p90, 2),
        p95_abs_error_mw=round(p95, 2),
        wape_pct=round(wape, 2) if wape is not None else None,
        over_forecast_count=over_count,
        over_forecast_pct=over_pct,
        under_forecast_count=under_count,
        under_forecast_pct=under_pct,
        exact_count=exact_count,
        p90_over_forecast_mw=round(p90_over, 2),
    )
