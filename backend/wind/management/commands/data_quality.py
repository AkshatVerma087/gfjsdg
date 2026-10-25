"""Data quality report command for validating ingested wind data."""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max, Min

from wind.models import WindActual, WindForecast


class Command(BaseCommand):
    help = "Generates data quality report for ingested Wind Actuals and Forecasts"

    def handle(self, *args, **options):
        actuals_count = WindActual.objects.count()
        forecasts_count = WindForecast.objects.count()

        if actuals_count == 0 and forecasts_count == 0:
            self.stderr.write(self.style.ERROR("Database is empty. Please run ingest_wind first."))
            raise CommandError("No wind data found in database.")

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("         WIND DATA QUALITY REPORT"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        # 1. Actuals Overview
        self.stdout.write(
            self.style.SUCCESS(f"\n[ACTUALS - FUELHH WIND] Total Records: {actuals_count}")
        )
        if actuals_count > 0:
            act_agg = WindActual.objects.aggregate(
                min_time=Min("start_time"),
                max_time=Max("start_time"),
                min_mw=Min("generation_mw"),
                max_mw=Max("generation_mw"),
            )
            self.stdout.write(f"  Range: {act_agg['min_time']} to {act_agg['max_time']}")
            self.stdout.write(
                f"  Generation MW Min: {act_agg['min_mw']} MW, Max: {act_agg['max_mw']} MW"
            )

            # Check for negative values
            neg_actuals = WindActual.objects.filter(generation_mw__lt=0).count()
            self.stdout.write(f"  Negative generation count: {neg_actuals}")

            # Check for missing half-hours
            # A full day has 48 settlement periods
            start_date = act_agg["min_time"].date()
            end_date = act_agg["max_time"].date()
            total_days = (end_date - start_date).days + 1
            expected_half_hours = total_days * 48
            gap_count = expected_half_hours - actuals_count
            self.stdout.write(
                f"  Coverage: {total_days} days. Expected half-hours: {expected_half_hours}, Missing: {gap_count}"
            )

        # 2. Forecasts Overview
        self.stdout.write(
            self.style.SUCCESS(f"\n[FORECASTS - WINDFOR] Total Records: {forecasts_count}")
        )
        if forecasts_count > 0:
            fc_agg = WindForecast.objects.aggregate(
                min_target=Min("start_time"),
                max_target=Max("start_time"),
                min_pub=Min("publish_time"),
                max_pub=Max("publish_time"),
                min_mw=Min("generation_mw"),
                max_mw=Max("generation_mw"),
            )
            self.stdout.write(
                f"  Target Half-Hour Range: {fc_agg['min_target']} to {fc_agg['max_target']}"
            )
            self.stdout.write(
                f"  Publish Time Range:     {fc_agg['min_pub']} to {fc_agg['max_pub']}"
            )
            self.stdout.write(
                f"  Forecast MW Min: {fc_agg['min_mw']} MW, Max: {fc_agg['max_mw']} MW"
            )

            # Check negative forecasts
            neg_fc = WindForecast.objects.filter(generation_mw__lt=0).count()
            self.stdout.write(f"  Negative forecast count: {neg_fc}")

            # Distinct target half-hours
            distinct_targets = WindForecast.objects.values("start_time").distinct().count()
            self.stdout.write(f"  Distinct target half-hours covered: {distinct_targets}")

        self.stdout.write(self.style.NOTICE("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("Data quality check completed successfully."))
