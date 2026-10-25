"""Ingestion service for syncing Elexon BMRS data into the database."""

import logging
from datetime import UTC, date, datetime, time, timedelta

from django.db import transaction

from config.env import settings
from wind.elexon.client import ElexonClient
from wind.models import WindActual, WindForecast

logger = logging.getLogger("wind.ingestion")


class IngestionService:
    """Orchestrates idempotent bulk ingestion of actuals and forecasts."""

    def __init__(self, client: ElexonClient | None = None, batch_size: int = 1000):
        self.client = client or ElexonClient()
        self.batch_size = batch_size

    def ingest_actuals(self, start_date: date, end_date: date) -> int:
        """Fetch and upsert FUELHH wind actuals for the specified date window."""
        logger.info("Starting ingestion of wind actuals from %s to %s", start_date, end_date)
        records = self.client.fetch_actuals(start_date, end_date)
        if not records:
            logger.info("No wind actual records returned for window")
            return 0

        models_to_upsert = [
            WindActual(start_time=r.start_time, generation_mw=r.generation_mw) for r in records
        ]

        with transaction.atomic():
            WindActual.objects.bulk_create(
                models_to_upsert,
                batch_size=self.batch_size,
                update_conflicts=True,
                update_fields=["generation_mw"],
                unique_fields=["start_time"],
            )

        count = len(models_to_upsert)
        logger.info("Successfully upserted %d wind actual records", count)
        return count

    def ingest_forecasts(self, publish_from: datetime, publish_to: datetime) -> int:
        """Fetch and upsert WINDFOR wind forecasts published in the specified window."""
        logger.info(
            "Starting ingestion of wind forecasts published from %s to %s",
            publish_from.isoformat(),
            publish_to.isoformat(),
        )
        records = self.client.fetch_forecasts(publish_from, publish_to)
        if not records:
            logger.info("No wind forecast records returned for window")
            return 0

        models_to_upsert = [
            WindForecast(
                start_time=r.start_time,
                publish_time=r.publish_time,
                generation_mw=r.generation_mw,
            )
            for r in records
        ]

        with transaction.atomic():
            WindForecast.objects.bulk_create(
                models_to_upsert,
                batch_size=self.batch_size,
                update_conflicts=True,
                update_fields=["generation_mw"],
                unique_fields=["start_time", "publish_time"],
            )

        count = len(models_to_upsert)
        logger.info("Successfully upserted %d wind forecast records", count)
        return count

    def ingest_full_window(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, int]:
        """Ingest both actuals and forecasts covering purchase decisions in the window."""
        start = start_date or settings.data_window_start
        end = end_date or settings.data_window_end

        # Ingest actuals for the delivery window
        actuals_count = self.ingest_actuals(start, end)

        # For forecasts, day-ahead decisions on start require forecasts published on D-1.
        # We start publishing window 2 days prior to ensure all cutoff forecasts are present.
        pub_from = datetime.combine(start - timedelta(days=2), time.min, tzinfo=UTC)
        pub_to = datetime.combine(end, time.max, tzinfo=UTC)

        forecasts_count = self.ingest_forecasts(pub_from, pub_to)

        return {
            "actuals_count": actuals_count,
            "forecasts_count": forecasts_count,
        }
