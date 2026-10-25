"""Pydantic schemas for the Wind Forecast Monitor API (P5-T01)."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class MetaResponse(BaseModel):
    """Metadata describing the data window, defaults, and attribution."""

    data_window_start: date
    data_window_end: date
    default_window_start: date
    default_window_end: date
    default_cutoff_time: str
    attribution: str
    metric_definitions: dict[str, str]


class HalfHourPointSchema(BaseModel):
    """A single half-hour settlement period data point."""

    settlement_period: int = Field(ge=1, le=48)
    start_time: datetime
    forecast_mw: float | None = None
    publish_time: datetime | None = None
    actual_mw: float | None = None
    lead_time_hours: float | None = None


class ForecastResponse(BaseModel):
    """As-of forecast response for a chosen delivery day."""

    delivery_date: date
    cutoff_time: str
    cutoff_datetime: datetime
    points: list[HalfHourPointSchema]
    total_periods: int
    missing_forecast_count: int
    missing_actual_count: int


class MetricsSchema(BaseModel):
    """Forecast accuracy evaluation metrics."""

    count: int
    bias_mw: float
    mae_mw: float
    rmse_mw: float
    p50_abs_error_mw: float
    p90_abs_error_mw: float
    p95_abs_error_mw: float
    wape_pct: float | None = None
    over_forecast_count: int
    over_forecast_pct: float
    under_forecast_count: int
    under_forecast_pct: float
    exact_count: int
    p90_over_forecast_mw: float


class RiskBandSchema(BaseModel):
    """Risk-adjusted procurement band recommendation."""

    percentile: int
    p90_deduction_mw: float
    sample_size: int
    description: str


class DailyAccuracySchema(BaseModel):
    """Daily breakdown of accuracy metrics."""

    delivery_date: date
    metrics: MetricsSchema | None = None
    n_pairs: int
    n_missing_forecast: int
    n_missing_actual: int


class AccuracySummaryResponse(BaseModel):
    """Accuracy summary response for a delivery date range."""

    start_date: date
    end_date: date
    cutoff_time: str
    overall: MetricsSchema | None = None
    risk_band: RiskBandSchema | None = None
    daily: list[DailyAccuracySchema]
    total_evaluated_periods: int
    total_missing_forecasts: int
    total_missing_actuals: int


class HorizonBucketSchema(BaseModel):
    """Accuracy metrics for a forecast horizon bucket."""

    bucket_name: str
    min_hours: float
    max_hours: float
    avg_lead_time_hours: float
    metrics: MetricsSchema


class AccuracyByHorizonResponse(BaseModel):
    """Accuracy by forecast horizon response."""

    start_date: date
    end_date: date
    buckets: list[HorizonBucketSchema]
    total_forecasts_evaluated: int
