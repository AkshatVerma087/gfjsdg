"""Accuracy service for evaluating forecast performance (P4-T03, P4-T04, P4-T05)."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from wind.metrics import AccuracyMetrics, calculate_metrics
from wind.models import WindActual, WindForecast
from wind.selectors import get_as_of_forecast_for_day


@dataclass(frozen=True)
class DailyAccuracyItem:
    """Accuracy metrics for a single delivery day."""

    delivery_date: date
    metrics: AccuracyMetrics | None
    n_pairs: int
    n_missing_forecast: int
    n_missing_actual: int


@dataclass(frozen=True)
class RiskAdjustedBandConfig:
    """Configuration and empirical parameters for risk-adjusted procurement band."""

    percentile: int  # e.g. 90
    p90_deduction_mw: float  # MW deducted from forecast
    sample_size: int
    description: str


@dataclass(frozen=True)
class AccuracySummaryResult:
    """Summary of forecast accuracy across a date range at decision cutoff."""

    start_date: date
    end_date: date
    cutoff_time: str
    overall: AccuracyMetrics | None
    risk_band: RiskAdjustedBandConfig | None
    daily: list[DailyAccuracyItem]
    total_evaluated_periods: int
    total_missing_forecasts: int
    total_missing_actuals: int


@dataclass(frozen=True)
class HorizonBucketMetrics:
    """Accuracy metrics for a specific forecast lead-time bucket."""

    bucket_name: str  # e.g. "0-6h", "6-12h"
    min_hours: float
    max_hours: float
    avg_lead_time_hours: float
    metrics: AccuracyMetrics


@dataclass(frozen=True)
class AccuracyByHorizonResult:
    """Accuracy evaluated across lead-time horizons."""

    start_date: date
    end_date: date
    buckets: list[HorizonBucketMetrics]
    total_forecasts_evaluated: int


HORIZON_BUCKETS = [
    ("0-6h", 0.0, 6.0),
    ("6-12h", 6.0, 12.0),
    ("12-24h", 12.0, 24.0),
    ("24-48h", 24.0, 48.0),
    ("48h+", 48.0, 1000.0),
]


class AccuracyService:
    """Domain service for calculating forecast accuracy and risk adjustments."""

    def calculate_as_of_summary(
        self,
        start_date: date,
        end_date: date,
        cutoff_time: time = time(11, 0),
    ) -> AccuracySummaryResult:
        """Calculate overall and daily forecast accuracy metrics for as-of decision-time forecasts.

        Args:
            start_date: Start of delivery date range.
            end_date: End of delivery date range.
            cutoff_time: Decision cutoff time on D-1 (default 11:00 GMT).

        Returns:
            AccuracySummaryResult including overall metrics, empirical risk band, and daily breakdowns.
        """
        all_forecasts: list[float] = []
        all_actuals: list[float] = []
        daily_items: list[DailyAccuracyItem] = []

        total_missing_fc = 0
        total_missing_act = 0

        curr = start_date
        while curr <= end_date:
            day_result = get_as_of_forecast_for_day(curr, cutoff_time)
            day_forecasts: list[float] = []
            day_actuals: list[float] = []

            for pt in day_result.points:
                if pt.forecast_mw is not None and pt.actual_mw is not None:
                    day_forecasts.append(pt.forecast_mw)
                    day_actuals.append(pt.actual_mw)
                    all_forecasts.append(pt.forecast_mw)
                    all_actuals.append(pt.actual_mw)

            day_metrics = calculate_metrics(day_forecasts, day_actuals)
            daily_items.append(
                DailyAccuracyItem(
                    delivery_date=curr,
                    metrics=day_metrics,
                    n_pairs=len(day_forecasts),
                    n_missing_forecast=day_result.missing_forecast_count,
                    n_missing_actual=day_result.missing_actual_count,
                )
            )

            total_missing_fc += day_result.missing_forecast_count
            total_missing_act += day_result.missing_actual_count
            curr += timedelta(days=1)

        overall_metrics = calculate_metrics(all_forecasts, all_actuals)

        # Risk-adjusted lower band calculation (P4-T04)
        risk_band = None
        if overall_metrics is not None and overall_metrics.count >= 10:
            risk_band = RiskAdjustedBandConfig(
                percentile=90,
                p90_deduction_mw=overall_metrics.p90_over_forecast_mw,
                sample_size=overall_metrics.count,
                description=(
                    f"Plan on at least (Forecast − {overall_metrics.p90_over_forecast_mw} MW). "
                    "Empirically, actual wind met or exceeded this lower band in 90% of periods."
                ),
            )

        return AccuracySummaryResult(
            start_date=start_date,
            end_date=end_date,
            cutoff_time=cutoff_time.strftime("%H:%M"),
            overall=overall_metrics,
            risk_band=risk_band,
            daily=daily_items,
            total_evaluated_periods=len(all_forecasts),
            total_missing_forecasts=total_missing_fc,
            total_missing_actuals=total_missing_act,
        )

    def calculate_by_horizon(
        self,
        start_date: date,
        end_date: date,
    ) -> AccuracyByHorizonResult:
        """Calculate forecast accuracy metrics partitioned by forecast lead-time horizon (P4-T05).

        Evaluates every forecast published for delivery half-hours between start_date and end_date.
        """
        start_dt = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_dt = datetime.combine(end_date, time.max, tzinfo=UTC)

        # Load all actuals in the delivery window into memory
        actuals_qs = WindActual.objects.filter(
            start_time__gte=start_dt,
            start_time__lte=end_dt,
        ).values("start_time", "generation_mw")
        actuals_map = {a["start_time"]: a["generation_mw"] for a in actuals_qs}

        # Query all forecasts for the delivery window
        forecasts_qs = WindForecast.objects.filter(
            start_time__gte=start_dt,
            start_time__lte=end_dt,
        ).values("start_time", "publish_time", "generation_mw")

        # Bucket pairs by lead time (start_time - publish_time)
        bucket_data = defaultdict(lambda: {"forecasts": [], "actuals": [], "lead_hours": []})

        total_pairs = 0
        for fc in forecasts_qs:
            st = fc["start_time"]
            act_mw = actuals_map.get(st)
            if act_mw is None:
                continue

            lead_hours = (st - fc["publish_time"]).total_seconds() / 3600.0
            if lead_hours < 0:
                continue  # Ignore post-delivery revisions if any

            for name, min_h, max_h in HORIZON_BUCKETS:
                # Rule: [min_h, max_h) except for last bucket [min_h, max_h]
                if (min_h <= lead_hours < max_h) or (max_h >= 1000.0 and lead_hours >= min_h):
                    bucket_data[name]["forecasts"].append(fc["generation_mw"])
                    bucket_data[name]["actuals"].append(act_mw)
                    bucket_data[name]["lead_hours"].append(lead_hours)
                    total_pairs += 1
                    break

        bucket_results: list[HorizonBucketMetrics] = []
        for name, min_h, max_h in HORIZON_BUCKETS:
            data = bucket_data.get(name)
            if data and data["forecasts"]:
                m = calculate_metrics(data["forecasts"], data["actuals"])
                if m is not None:
                    avg_lead = round(float(sum(data["lead_hours"]) / len(data["lead_hours"])), 1)
                    bucket_results.append(
                        HorizonBucketMetrics(
                            bucket_name=name,
                            min_hours=min_h,
                            max_hours=max_h,
                            avg_lead_time_hours=avg_lead,
                            metrics=m,
                        )
                    )

        return AccuracyByHorizonResult(
            start_date=start_date,
            end_date=end_date,
            buckets=bucket_results,
            total_forecasts_evaluated=total_pairs,
        )
