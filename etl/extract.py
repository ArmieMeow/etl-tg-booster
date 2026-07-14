from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Any

import httpx

from etl.config import Settings
from etl.models import CampaignStatRow, map_report_record

logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_CONFIG = 1
EXIT_API = 2
EXIT_EMPTY = 3

API_DOC = "https://tgbooster.gitbook.io/tgbooster/api/api-metody"


class ExtractError(Exception):
    """Raised when TG Booster API call fails."""


class EmptyResponseError(Exception):
    """Raised when API returns no rows for the requested period."""


class TgBoosterClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.tg_booster_api_token or not settings.tg_booster_api_base_url:
            raise ExtractError("TG Booster API is not configured")
        self.base_url = settings.tg_booster_api_base_url
        self.headers = {
            "Authorization": f"Bearer {settings.tg_booster_api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._client = httpx.Client(timeout=120.0, headers=self.headers)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> TgBoosterClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _post(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = self._client.post(url, json=body or {})
                response.raise_for_status()
                payload = response.json()
                break
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning("API attempt %s failed for %s: %s", attempt, path, exc)
                if attempt == 3:
                    raise ExtractError(f"TG Booster API request failed for {path}: {exc}") from exc
                time.sleep(attempt * 2)
        else:
            raise ExtractError(f"TG Booster API request failed for {path}: {last_error}")

        if not isinstance(payload, dict):
            raise ExtractError(f"unexpected response type from {path}")

        if payload.get("success") is False:
            message = payload.get("message", "unknown API error")
            raise ExtractError(f"TG Booster API error on {path}: {message}")

        return payload

    def fetch_cabinets(self) -> list[dict[str, Any]]:
        payload = self._post("/api/cabinets")
        cabinets = payload.get("cabinets", [])
        if not isinstance(cabinets, list):
            raise ExtractError("invalid cabinets response")
        return [cabinet for cabinet in cabinets if isinstance(cabinet, dict)]

    def fetch_campaigns(
        self,
        cabinet_id: str,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        payload = self._post(
            f"/api/cabinet/{cabinet_id}/companies",
            {
                "filters": {
                    "start_date": date_from.isoformat(),
                    "finish_date": date_to.isoformat(),
                }
            },
        )
        campaigns = payload.get("campaigns", [])
        if not isinstance(campaigns, list):
            raise ExtractError("invalid campaigns response")
        return [campaign for campaign in campaigns if isinstance(campaign, dict)]

    def fetch_cabinet_daily_by_company(
        self,
        cabinet_id: str,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Day x company report in one request (correct per-campaign metrics)."""
        payload = self._post(
            f"/api/cabinet/{cabinet_id}/reports",
            {
                "groups": {
                    "date": {"day": True},
                    "ads": {"company": True},
                },
                "filters": {
                    "dates": [date_from.isoformat(), date_to.isoformat()],
                },
                "metrics": {
                    "views": True,
                    "clicks": True,
                    "joins": True,
                    "spent": True,
                },
            },
        )
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise ExtractError("invalid reports response")
        return [row for row in data if isinstance(row, dict)]

    def fetch_daily_report(
        self,
        cabinet_id: str,
        campaign_id: int,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        payload = self._post(
            f"/api/cabinet/{cabinet_id}/reports",
            {
                "groups": {"date": {"day": True}},
                "filters": {
                    "company": [campaign_id],
                    "dates": [date_from.isoformat(), date_to.isoformat()],
                },
                "metrics": {
                    "views": True,
                    "clicks": True,
                    "joins": True,
                    "spent": True,
                },
            },
        )
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise ExtractError("invalid reports response")
        return [row for row in data if isinstance(row, dict)]


def resolve_cabinet_ids(client: TgBoosterClient, settings: Settings) -> list[tuple[str, str]]:
    """Return (cabinet_id, cabinet_name) for each cabinet to extract."""
    if settings.tg_booster_account_id:
        ids = [part.strip() for part in settings.tg_booster_account_id.split(",") if part.strip()]
        return [(cabinet_id, "") for cabinet_id in ids]

    cabinets = client.fetch_cabinets()
    if not cabinets:
        raise ExtractError("no cabinets returned from /api/cabinets")

    resolved = [(str(cabinet["id"]), cabinet.get("name", "")) for cabinet in cabinets]
    logger.info(
        "using %s cabinet(s): %s",
        len(resolved),
        ", ".join(f"{cabinet_id} ({name})" for cabinet_id, name in resolved),
    )
    return resolved


def _fetch_cabinet_stats(
    client: TgBoosterClient,
    cabinet_id: str,
    date_from: date,
    date_to: date,
) -> list[CampaignStatRow]:
    daily_rows = client.fetch_cabinet_daily_by_company(cabinet_id, date_from, date_to)
    if not daily_rows:
        logger.warning("no stats in cabinet %s for %s -> %s", cabinet_id, date_from, date_to)
        return []

    rows = [
        map_report_record(record, cabinet_id=cabinet_id)
        for record in daily_rows
    ]

    campaigns = {row.campaign_id for row in rows}
    logger.info(
        "extracted %s rows from %s campaigns (cabinet %s)",
        len(rows),
        len(campaigns),
        cabinet_id,
    )
    return rows


def fetch_campaign_stats(
    settings: Settings,
    date_from: date,
    date_to: date,
) -> list[CampaignStatRow]:
    """
    Fetch day x campaign stats via TG Booster API for all configured cabinets.

    Flow: cabinets -> per-cabinet day x company reports (single API call).
    Docs: https://tgbooster.gitbook.io/tgbooster/api/api-metody
    """
    client = TgBoosterClient(settings)
    try:
        cabinets = resolve_cabinet_ids(client, settings)
        rows: list[CampaignStatRow] = []

        for cabinet_id, _cabinet_name in cabinets:
            rows.extend(_fetch_cabinet_stats(client, cabinet_id, date_from, date_to))

        if not rows:
            raise EmptyResponseError(f"no stats returned for {date_from} -> {date_to}")

        logger.info("extracted %s total rows from %s cabinet(s)", len(rows), len(cabinets))
        return rows
    finally:
        client.close()


def default_incremental_range(database_url: str, *, lookback_days: int = 7) -> tuple[date, date]:
    from etl.load import get_max_stat_date

    today = date.today()
    max_date = get_max_stat_date(database_url)
    if max_date is None:
        date_from = today - timedelta(days=lookback_days)
    else:
        date_from = max(max_date - timedelta(days=1), today - timedelta(days=lookback_days))
    return date_from, today
