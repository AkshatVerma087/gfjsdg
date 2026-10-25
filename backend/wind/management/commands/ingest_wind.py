"""Management command to ingest Elexon BMRS FUELHH actuals and WINDFOR forecasts."""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from config.env import settings
from wind.ingestion import IngestionService


class Command(BaseCommand):
    help = "Ingests national wind actuals (FUELHH) and forecasts (WINDFOR) from Elexon BMRS"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-date",
            "--from",
            dest="from_date",
            type=str,
            default=settings.data_window_start.isoformat(),
            help="Start date in YYYY-MM-DD (defaults to DATA_WINDOW_START)",
        )
        parser.add_argument(
            "--to-date",
            "--to",
            dest="to_date",
            type=str,
            default=settings.data_window_end.isoformat(),
            help="End date in YYYY-MM-DD (defaults to DATA_WINDOW_END)",
        )

    def handle(self, *args, **options):
        try:
            start_date = date.fromisoformat(options["from_date"])
            end_date = date.fromisoformat(options["to_date"])
        except ValueError as exc:
            raise CommandError(f"Invalid date format (must be YYYY-MM-DD): {exc}") from exc

        if start_date > end_date:
            raise CommandError(f"from-date ({start_date}) cannot be after to-date ({end_date})")

        self.stdout.write(
            self.style.NOTICE(f"Ingesting wind data window from {start_date} to {end_date}...")
        )

        service = IngestionService()
        try:
            results = service.ingest_full_window(start_date, end_date)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully completed ingestion:\n"
                    f"  - Actuals (FUELHH WIND): {results['actuals_count']} records\n"
                    f"  - Forecasts (WINDFOR):    {results['forecasts_count']} records"
                )
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Ingestion failed: {exc}"))
            raise CommandError(f"Ingestion failed: {exc}") from exc
