from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, field_validator


class CampaignStatRow(BaseModel):
    """Normalized row for PostgreSQL load."""

    stat_date: date
    campaign_id: str
    campaign_name: str | None = None
    account_id: str | None = None
    spend: float | None = None
    impressions: int | None = None
    clicks: int | None = None
    leads: int | None = None
    source_payload: dict[str, Any] | None = None

    @field_validator("campaign_id", mode="before")
    @classmethod
    def campaign_id_to_str(cls, value: Any) -> str:
        if value is None:
            raise ValueError("campaign_id is required")
        return str(value)


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record and record[key] is not None:
            return record[key]
    return None


def map_report_record(
    record: dict[str, Any],
    *,
    campaign_id: str | None = None,
    campaign_name: str | None = None,
    cabinet_id: str,
) -> CampaignStatRow:
    """Map TG Booster /reports row (day or day+company grouping) to CampaignStatRow."""
    stat_date_raw = _first_present(record, "date_day", "date_week", "date")
    if stat_date_raw is None:
        raise ValueError("report row missing date field")

    resolved_campaign_id = campaign_id or _first_present(record, "ads_company_id", "company_id")
    if resolved_campaign_id is None:
        raise ValueError("report row missing campaign/company id")

    resolved_campaign_name = campaign_name or _first_present(
        record, "company_name", "ads_company_name", "campaign_name"
    )

    return CampaignStatRow(
        stat_date=date.fromisoformat(str(stat_date_raw)[:10]),
        campaign_id=str(resolved_campaign_id),
        campaign_name=str(resolved_campaign_name) if resolved_campaign_name is not None else None,
        account_id=cabinet_id,
        spend=_to_float(_first_present(record, "metric_spent", "stat_spent")),
        impressions=_to_int(_first_present(record, "metric_views", "stat_views")),
        clicks=_to_int(_first_present(record, "metric_clicks", "stat_clicks")),
        leads=_to_int(_first_present(record, "metric_joins", "stat_joins")),
        source_payload=record,
    )
