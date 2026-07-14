from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone

import psycopg

from etl.models import CampaignStatRow

logger = logging.getLogger(__name__)

UPSERT_SQL = """
INSERT INTO raw_campaign_stats (
    stat_date,
    campaign_id,
    campaign_name,
    account_id,
    spend,
    impressions,
    clicks,
    leads,
    source_payload,
    loaded_at
) VALUES (
    %(stat_date)s,
    %(campaign_id)s,
    %(campaign_name)s,
    %(account_id)s,
    %(spend)s,
    %(impressions)s,
    %(clicks)s,
    %(leads)s,
    %(source_payload)s,
    %(loaded_at)s
)
ON CONFLICT (stat_date, campaign_id, account_id) DO UPDATE SET
    campaign_name = EXCLUDED.campaign_name,
    spend = EXCLUDED.spend,
    impressions = EXCLUDED.impressions,
    clicks = EXCLUDED.clicks,
    leads = EXCLUDED.leads,
    source_payload = EXCLUDED.source_payload,
    loaded_at = EXCLUDED.loaded_at
"""


def _row_to_params(row: CampaignStatRow) -> dict:
    return {
        "stat_date": row.stat_date,
        "campaign_id": row.campaign_id,
        "campaign_name": row.campaign_name,
        "account_id": row.account_id,
        "spend": row.spend,
        "impressions": row.impressions,
        "clicks": row.clicks,
        "leads": row.leads,
        "source_payload": json.dumps(row.source_payload) if row.source_payload else None,
        "loaded_at": datetime.now(timezone.utc),
    }


def upsert_rows(database_url: str, rows: list[CampaignStatRow]) -> int:
    if not rows:
        return 0

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(UPSERT_SQL, _row_to_params(row))
        conn.commit()

    logger.info("upserted %s rows", len(rows))
    return len(rows)


def start_run(
    database_url: str,
    *,
    mode: str,
    date_from: date | None,
    date_to: date | None,
) -> int:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO etl_runs (started_at, status, mode, date_from, date_to)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING run_id
                """,
                (datetime.now(timezone.utc), "running", mode, date_from, date_to),
            )
            run_id = cur.fetchone()[0]
        conn.commit()
    return run_id


def finish_run(
    database_url: str,
    run_id: int,
    *,
    status: str,
    rows_loaded: int = 0,
    error_message: str | None = None,
) -> None:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE etl_runs
                SET finished_at = %s,
                    status = %s,
                    rows_loaded = %s,
                    error_message = %s
                WHERE run_id = %s
                """,
                (
                    datetime.now(timezone.utc),
                    status,
                    rows_loaded,
                    error_message,
                    run_id,
                ),
            )
        conn.commit()


def get_max_stat_date(database_url: str) -> date | None:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(stat_date) FROM raw_campaign_stats")
            result = cur.fetchone()[0]
    return result


def fetch_daily_totals(
    database_url: str,
    date_from: date,
    date_to: date,
) -> list[tuple[date, float, int, int]]:
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    stat_date,
                    COALESCE(SUM(spend), 0)::float,
                    COALESCE(SUM(leads), 0)::int,
                    COUNT(*)::int
                FROM raw_campaign_stats
                WHERE stat_date BETWEEN %s AND %s
                GROUP BY stat_date
                ORDER BY stat_date
                """,
                (date_from, date_to),
            )
            return cur.fetchall()
