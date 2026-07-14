from __future__ import annotations

import logging
from collections.abc import Iterable

from etl.models import CampaignStatRow

logger = logging.getLogger(__name__)


def validate_rows(rows: Iterable[CampaignStatRow]) -> list[CampaignStatRow]:
    """Validate rows; dedupe by (stat_date, campaign_id, account_id), last-wins."""
    accepted: dict[tuple[str, str, str], CampaignStatRow] = {}

    for row in rows:
        account_id = row.account_id or ""
        key = (row.stat_date.isoformat(), row.campaign_id, account_id)

        if row.spend is not None and row.spend < 0:
            logger.warning("skip negative spend: %s", key)
            continue

        accepted[key] = row

    return list(accepted.values())
