"""Domain selectors for querying Wind Forecast Monitor data (R1 - As-of Forecast)."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from wind.models import WindActual, WindForecast


@dataclass(frozen=True)
class HalfHourPoint:
    """A single settlement period's forecast, actual, and timing."""

    settlement_period: int  # 1 to 48
    start_time: datetime
    forecast_mw: float | None
    publish_time: datetime | None
    actual_mw: float | None
    lead_time_hours: float | None  # (start_time - publish_time) in hours


@dataclass(frozen=True)
class DayAheadForecastResult:
    """As-of forecast view for a single delivery day at decision cutoff."""

    delivery_date: date
    cutoff_time: str  # "HH:MM"
    cutoff_datetime: datetime
    points: list[HalfHourPoint]
    total_periods: int
    missing_forecast_count: int
    missing_actual_count: int


def get_as_of_forecast_for_day(
    delivery_date: date,
    cutoff_time: time = time(11, 0),
) -> DayAheadForecastResult:
    """Return the latest wind forecast available at D-1 decision cutoff for each half-hour.

    Args:
        delivery_date: Target delivery date (day D).
        cutoff_time: Decision cutoff time on day D-1 in UTC (default 11:00 GMT).

    Returns:
        DayAheadForecastResult containing 48 settlement periods with the latest eligible
        forecast (publish_time <= cutoff_dt) and actual generation.
    """
    # Decision cutoff on D-1
    cutoff_dt = datetime.combine(delivery_date - timedelta(days=1), cutoff_time, tzinfo=UTC)

    day_start = datetime.combine(delivery_date, time.min, tzinfo=UTC)
    day_end = datetime.combine(delivery_date, time.max, tzinfo=UTC)

    # 1. Fetch all forecasts for delivery day published on or before cutoff
    # Ordered by start_time ASC, publish_time DESC so first record for each start_time is latest
    eligible_forecasts = (
        WindForecast.objects.filter(
            start_time__gte=day_start,
            start_time__lte=day_end,
            publish_time__lte=cutoff_dt,
        )
        .order_by("start_time", "-publish_time")
        .values("start_time", "publish_time", "generation_mw")
    )

    latest_forecast_map: dict[datetime, tuple[float, datetime]] = {}
    for fc in eligible_forecasts:
        st = fc["start_time"]
        if st not in latest_forecast_map:
            latest_forecast_map[st] = (fc["generation_mw"], fc["publish_time"])

    # 2. Fetch actuals for the delivery day
    actuals = WindActual.objects.filter(
        start_time__gte=day_start,
        start_time__lte=day_end,
    ).values("start_time", "generation_mw")
    actuals_map = {a["start_time"]: a["generation_mw"] for a in actuals}

    # 3. Construct 48 half-hour settlement periods
    points: list[HalfHourPoint] = []
    missing_forecasts = 0
    missing_actuals = 0

    for period_idx in range(48):
        st = day_start + timedelta(minutes=30 * period_idx)
        settlement_period = period_idx + 1

        fc_entry = latest_forecast_map.get(st)
        if fc_entry is None and st.minute == 30:
            # Elexon WINDFOR publishes at hourly resolution; the forecast covers both half-hours.
            fc_entry = latest_forecast_map.get(st.replace(minute=0))

        if fc_entry is not None:
            forecast_mw, pub_time = fc_entry
            lead_time_hours = round((st - pub_time).total_seconds() / 3600.0, 2)
        else:
            forecast_mw, pub_time, lead_time_hours = None, None, None
            missing_forecasts += 1

        act_mw = actuals_map.get(st)
        if act_mw is None:
            missing_actuals += 1

        points.append(
            HalfHourPoint(
                settlement_period=settlement_period,
                start_time=st,
                forecast_mw=forecast_mw,
                publish_time=pub_time,
                actual_mw=act_mw,
                lead_time_hours=lead_time_hours,
            )
        )

    return DayAheadForecastResult(
        delivery_date=delivery_date,
        cutoff_time=cutoff_time.strftime("%H:%M"),
        cutoff_datetime=cutoff_dt,
        points=points,
        total_periods=len(points),
        missing_forecast_count=missing_forecasts,
        missing_actual_count=missing_actuals,
    )


def get_as_of_pairs_for_range(
    start_date: date,
    end_date: date,
    cutoff_time: time = time(11, 0),
) -> list[tuple[datetime, float, float, float]]:
    """Return paired (start_time, forecast_mw, actual_mw, lead_time_hours) for a range of dates.

    Only returns points where BOTH forecast and actual are available.
    """
    pairs: list[tuple[datetime, float, float, float]] = []
    curr = start_date
    while curr <= end_date:
        day_res = get_as_of_forecast_for_day(curr, cutoff_time)
        for pt in day_res.points:
            if (
                pt.forecast_mw is not None
                and pt.actual_mw is not None
                and pt.lead_time_hours is not None
            ):
                pairs.append((pt.start_time, pt.forecast_mw, pt.actual_mw, pt.lead_time_hours))
        curr += timedelta(days=1)
    return pairs
