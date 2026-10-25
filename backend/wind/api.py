"""Django Ninja API router and endpoints for Wind Forecast Monitor (P5-T01, P5-T02, P5-T03)."""

from datetime import date, time

from ninja import NinjaAPI, Query
from ninja.errors import ValidationError as NinjaValidationError
from pydantic import ValidationError as PydanticValidationError

from config.env import settings
from core.error_handlers import (
    handle_app_error,
    handle_unexpected_error,
    handle_validation_error,
)
from core.errors import AppError, ValidationFailed
from wind.accuracy import AccuracyService
from wind.schemas import (
    AccuracyByHorizonResponse,
    AccuracySummaryResponse,
    ForecastResponse,
    MetaResponse,
)
from wind.selectors import get_as_of_forecast_for_day

api = NinjaAPI(
    title="Wind Forecast Monitor API",
    version="1.0.0",
    description="UK Day-Ahead Wind Forecast and Accuracy Monitoring API for power buyers.",
    urls_namespace="wind_api",
)

# Register standardized error handlers
api.add_exception_handler(AppError, handle_app_error)
api.add_exception_handler(NinjaValidationError, handle_validation_error)
api.add_exception_handler(PydanticValidationError, handle_validation_error)
api.add_exception_handler(Exception, handle_unexpected_error)


def parse_and_validate_cutoff(cutoff_str: str) -> time:
    """Validate and parse HH:MM cutoff string."""
    parts = cutoff_str.strip().split(":")
    if len(parts) != 2:
        raise ValidationFailed(f"Cutoff time must be in HH:MM format (got '{cutoff_str}')")
    try:
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        return time(hour=h, minute=m)
    except ValueError:
        raise ValidationFailed(
            f"Cutoff time must be a valid time between 00:00 and 23:59 (got '{cutoff_str}')"
        ) from None


def validate_date_in_window(d: date, field_name: str) -> None:
    """Validate date falls within ingested data window."""
    if d < settings.data_window_start or d > settings.data_window_end:
        raise ValidationFailed(
            f"{field_name} ({d}) must be within the available data window "
            f"[{settings.data_window_start} to {settings.data_window_end}]."
        )


@api.get("/meta", response=MetaResponse, summary="Metadata, defaults, and attribution")
def get_meta(request):
    """Return available data window bounds, default display windows, and data attribution."""
    return MetaResponse(
        data_window_start=settings.data_window_start,
        data_window_end=settings.data_window_end,
        default_window_start=settings.default_window_start,
        default_window_end=settings.default_window_end,
        default_cutoff_time=settings.default_cutoff_time,
        attribution=(
            "Data sourced from Elexon BMRS (FUELHH wind actuals and WINDFOR forecasts). "
            "Contains BMRS data © Elexon Limited copyright and database right 2026."
        ),
        metric_definitions={
            "bias_mw": "Mean forecast error (Forecast − Actual). Positive = Over-forecast.",
            "mae_mw": "Mean Absolute Error in MW (|Forecast − Actual|).",
            "rmse_mw": "Root Mean Squared Error in MW, penalizing large errors.",
            "p50_abs_error_mw": "Median absolute error (50% of errors are within this MW).",
            "p90_abs_error_mw": "90th percentile absolute error (tail risk benchmark).",
            "p95_abs_error_mw": "95th percentile absolute error (extreme tail risk).",
            "wape_pct": "Weighted Absolute Percentage Error: sum(|error|) / sum(actual) * 100.",
            "p90_over_forecast_mw": "90th percentile of positive over-forecast error (max(Forecast − Actual, 0)).",
        },
    )


@api.get(
    "/forecast",
    response=ForecastResponse,
    summary="Latest forecast available at D-1 cutoff vs actuals (R1)",
)
def get_forecast(
    request,
    delivery_date: date = Query(..., description="Target delivery date (YYYY-MM-DD)"),
    cutoff: str = Query("11:00", description="Cutoff time on D-1 in HH:MM (UTC)"),
):
    """Return 48 half-hour settlement periods with the latest forecast available at cutoff."""
    validate_date_in_window(delivery_date, "delivery_date")
    parsed_cutoff = parse_and_validate_cutoff(cutoff)

    result = get_as_of_forecast_for_day(delivery_date, parsed_cutoff)
    return ForecastResponse(
        delivery_date=result.delivery_date,
        cutoff_time=result.cutoff_time,
        cutoff_datetime=result.cutoff_datetime,
        points=[pt.__dict__ for pt in result.points],
        total_periods=result.total_periods,
        missing_forecast_count=result.missing_forecast_count,
        missing_actual_count=result.missing_actual_count,
    )


@api.get(
    "/accuracy/summary",
    response=AccuracySummaryResponse,
    summary="Accuracy summary for decision-time forecasts (R2)",
)
def get_accuracy_summary(
    request,
    from_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
    cutoff: str = Query("11:00", description="Cutoff time on D-1 in HH:MM (UTC)"),
):
    """Return overall and daily accuracy metrics and empirical risk-adjusted band."""
    start = from_date or settings.default_window_start
    end = to_date or settings.default_window_end

    if start > end:
        raise ValidationFailed(f"from_date ({start}) cannot be after to_date ({end})")

    validate_date_in_window(start, "from_date")
    validate_date_in_window(end, "to_date")
    parsed_cutoff = parse_and_validate_cutoff(cutoff)

    service = AccuracyService()
    result = service.calculate_as_of_summary(start, end, parsed_cutoff)

    return AccuracySummaryResponse(
        start_date=result.start_date,
        end_date=result.end_date,
        cutoff_time=result.cutoff_time,
        overall=result.overall.to_dict() if result.overall else None,
        risk_band=result.risk_band.__dict__ if result.risk_band else None,
        daily=[
            {
                "delivery_date": d.delivery_date,
                "metrics": d.metrics.to_dict() if d.metrics else None,
                "n_pairs": d.n_pairs,
                "n_missing_forecast": d.n_missing_forecast,
                "n_missing_actual": d.n_missing_actual,
            }
            for d in result.daily
        ],
        total_evaluated_periods=result.total_evaluated_periods,
        total_missing_forecasts=result.total_missing_forecasts,
        total_missing_actuals=result.total_missing_actuals,
    )


@api.get(
    "/accuracy/by-horizon",
    response=AccuracyByHorizonResponse,
    summary="Accuracy evaluated across lead-time horizons",
)
def get_accuracy_by_horizon(
    request,
    from_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Return accuracy metrics grouped by forecast lead-time buckets (0-6h, 6-12h, 12-24h, etc.)."""
    start = from_date or settings.default_window_start
    end = to_date or settings.default_window_end

    if start > end:
        raise ValidationFailed(f"from_date ({start}) cannot be after to_date ({end})")

    validate_date_in_window(start, "from_date")
    validate_date_in_window(end, "to_date")

    service = AccuracyService()
    result = service.calculate_by_horizon(start, end)

    return AccuracyByHorizonResponse(
        start_date=result.start_date,
        end_date=result.end_date,
        buckets=[
            {
                "bucket_name": b.bucket_name,
                "min_hours": b.min_hours,
                "max_hours": b.max_hours,
                "avg_lead_time_hours": b.avg_lead_time_hours,
                "metrics": b.metrics.to_dict(),
            }
            for b in result.buckets
        ],
        total_forecasts_evaluated=result.total_forecasts_evaluated,
    )
