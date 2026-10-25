"""Domain persistence models for wind actuals and forecasts."""

from django.db import models


class WindActual(models.Model):
    """Actual national wind generation per half-hour from Elexon FUELHH."""

    start_time = models.DateTimeField(
        unique=True,
        db_index=True,
        help_text="Start time of the half-hour settlement period in UTC",
    )
    generation_mw = models.FloatField(
        help_text="National wind generation in MW (no artificial non-negative constraint per CP1381)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wind_actual"
        ordering = ["start_time"]
        verbose_name = "Wind Actual"
        verbose_name_plural = "Wind Actuals"

    def __str__(self) -> str:
        return f"WindActual({self.start_time.isoformat()}: {self.generation_mw} MW)"


class WindForecast(models.Model):
    """National wind generation forecast from Elexon WINDFOR."""

    start_time = models.DateTimeField(
        db_index=True,
        help_text="Target half-hour settlement period in UTC",
    )
    publish_time = models.DateTimeField(
        db_index=True,
        help_text="Timestamp when the forecast was published in UTC",
    )
    generation_mw = models.FloatField(help_text="Forecasted wind generation in MW")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "wind_forecast"
        ordering = ["start_time", "-publish_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["start_time", "publish_time"],
                name="unique_forecast_start_publish",
            )
        ]
        indexes = [
            # Compound index specifically optimized for as-of queries:
            # SELECT DISTINCT ON (start_time) ... WHERE publish_time <= cutoff ORDER BY start_time, publish_time DESC
            models.Index(
                fields=["start_time", "publish_time"],
                name="idx_forecast_start_pub",
            ),
            models.Index(
                fields=["publish_time"],
                name="idx_forecast_publish",
            ),
        ]
        verbose_name = "Wind Forecast"
        verbose_name_plural = "Wind Forecasts"

    def __str__(self) -> str:
        return f"WindForecast(target={self.start_time.isoformat()}, pub={self.publish_time.isoformat()}: {self.generation_mw} MW)"
