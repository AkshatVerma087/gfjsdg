"""Elexon BMRS API client for FUELHH actuals and WINDFOR forecasts."""

import logging
import random
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from config.env import settings
from core.errors import UpstreamUnavailable

logger = logging.getLogger("wind.elexon")


@dataclass(frozen=True)
class WindActualRecord:
    """Parsed single settlement actual wind generation record."""

    start_time: datetime
    generation_mw: float


@dataclass(frozen=True)
class WindForecastRecord:
    """Parsed single settlement forecast wind generation record."""

    start_time: datetime
    publish_time: datetime
    generation_mw: float


class ElexonClient:
    """Client for Elexon BMRS datasets API with bounded retries and exponential backoff."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
    ):
        self.base_url = (base_url or settings.elexon_base_url).rstrip("/")
        self.timeout = timeout_seconds or settings.elexon_timeout_seconds
        self.max_retries = max_retries
        self.backoff_base = backoff_base_seconds

    def _execute_request_with_retry(self, url: str, params: dict[str, Any]) -> Any:
        """Execute GET request with bounded retries on 429, 5xx, or network errors."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.get(url, params=params)

                    # Check for rate limit or server errors
                    if response.status_code == 429 or response.status_code >= 500:
                        retry_after = response.headers.get("Retry-After")
                        wait_seconds = (
                            float(retry_after)
                            if retry_after
                            else (self.backoff_base * (2**attempt))
                        )
                        wait_seconds += random.uniform(0.05, 0.2)  # Jitter
                        logger.warning(
                            "Elexon upstream returned %s, retrying in %.2fs (attempt %d/%d)",
                            response.status_code,
                            wait_seconds,
                            attempt + 1,
                            self.max_retries,
                        )
                        time.sleep(wait_seconds)
                        continue

                    response.raise_for_status()
                    return response.json()

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                wait_seconds = (self.backoff_base * (2**attempt)) + random.uniform(0.05, 0.2)
                logger.warning(
                    "Network error connecting to Elexon upstream (%s), retrying in %.2fs (attempt %d/%d)",
                    exc,
                    wait_seconds,
                    attempt + 1,
                    self.max_retries,
                )
                time.sleep(wait_seconds)
            except Exception as exc:
                # Other client errors (4xx other than 429) do not retry
                raise UpstreamUnavailable(f"Elexon upstream error: {exc}") from exc

        raise UpstreamUnavailable(
            f"Elexon upstream request failed after {self.max_retries} retries: {last_error}"
        ) from last_error

    def fetch_actuals(self, start_date: date, end_date: date) -> list[WindActualRecord]:
        """Fetch FUELHH wind actuals for a date range, chunked into 7-day windows."""
        url = f"{self.base_url}/datasets/FUELHH/stream"
        records: list[WindActualRecord] = []
        chunk_days = 7

        current_start = start_date
        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=chunk_days - 1), end_date)
            params = {
                "settlementDateFrom": current_start.isoformat(),
                "settlementDateTo": current_end.isoformat(),
            }

            payload = self._execute_request_with_retry(url, params)
            if not isinstance(payload, list):
                raise UpstreamUnavailable(
                    f"Malformed payload from FUELHH endpoint: expected list, got {type(payload)}"
                )

            for item in payload:
                if item.get("fuelType") == "WIND":
                    try:
                        st_raw = item["startTime"].replace("Z", "+00:00")
                        st = datetime.fromisoformat(st_raw).astimezone(UTC)
                        gen = float(item["generation"])
                        records.append(WindActualRecord(start_time=st, generation_mw=gen))
                    except (KeyError, ValueError, TypeError) as parse_err:
                        logger.warning(
                            "Skipping unparseable FUELHH record: %s (%s)", item, parse_err
                        )

            current_start = current_end + timedelta(days=1)

        return records

    def fetch_forecasts(
        self, publish_from: datetime, publish_to: datetime
    ) -> list[WindForecastRecord]:
        """Fetch WINDFOR wind forecasts published between publish_from and publish_to."""
        url = f"{self.base_url}/datasets/WINDFOR/stream"
        records: list[WindForecastRecord] = []
        chunk_days = 3

        current_from = publish_from
        while current_from < publish_to:
            current_to = min(current_from + timedelta(days=chunk_days), publish_to)
            params = {
                "publishDateTimeFrom": current_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": current_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            payload = self._execute_request_with_retry(url, params)
            if not isinstance(payload, list):
                raise UpstreamUnavailable(
                    f"Malformed payload from WINDFOR endpoint: expected list, got {type(payload)}"
                )

            for item in payload:
                try:
                    st_raw = item["startTime"].replace("Z", "+00:00")
                    pt_raw = item["publishTime"].replace("Z", "+00:00")
                    st = datetime.fromisoformat(st_raw).astimezone(UTC)
                    pt = datetime.fromisoformat(pt_raw).astimezone(UTC)
                    gen = float(item["generation"])
                    records.append(
                        WindForecastRecord(
                            start_time=st,
                            publish_time=pt,
                            generation_mw=gen,
                        )
                    )
                except (KeyError, ValueError, TypeError) as parse_err:
                    logger.warning("Skipping unparseable WINDFOR record: %s (%s)", item, parse_err)

            current_from = current_to

        return records
