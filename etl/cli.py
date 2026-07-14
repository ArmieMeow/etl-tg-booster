from __future__ import annotations

import json
import sys
from datetime import date, timedelta

import typer

from etl.config import get_settings, setup_logging
from etl.extract import (
    EXIT_API,
    EXIT_CONFIG,
    EXIT_EMPTY,
    EXIT_OK,
    EmptyResponseError,
    ExtractError,
    default_incremental_range,
    fetch_campaign_stats,
)
from etl.load import fetch_daily_totals, finish_run, start_run, upsert_rows
from etl.validate import validate_rows

app = typer.Typer(
    no_args_is_help=True,
    help="ETL: TG Booster → PostgreSQL",
)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(f"invalid date: {value} (use YYYY-MM-DD)") from exc


@app.command("validate-config")
def validate_config() -> None:
    """Check .env and database connectivity."""
    setup_logging()
    settings = get_settings()

    try:
        settings.validate_for_config_check()
    except ValueError as exc:
        typer.echo(f"Config error: {exc}", err=True)
        raise typer.Exit(EXIT_CONFIG) from exc

    typer.echo("Env OK: DATABASE_URL is set")

    if settings.tg_booster_api_token and settings.tg_booster_api_base_url:
        typer.echo("Env OK: TG Booster API vars are set")
    else:
        typer.echo(
            "Note: TG Booster API token or base URL is not set",
            err=True,
        )

    try:
        import psycopg

        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        typer.echo("Database connection OK")
    except Exception as exc:
        typer.echo(f"Database connection failed: {exc}", err=True)
        raise typer.Exit(EXIT_CONFIG) from exc

    raise typer.Exit(EXIT_OK)


@app.command("extract")
def extract_cmd(
    date_from: str = typer.Option(..., "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(..., "--to", help="End date YYYY-MM-DD"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print JSON to stdout, no DB write"),
) -> None:
    """Extract stats from TG Booster API."""
    setup_logging()
    settings = get_settings()

    try:
        settings.validate_for_run()
    except ValueError as exc:
        typer.echo(f"Config error: {exc}", err=True)
        raise typer.Exit(EXIT_CONFIG) from exc

    d_from = _parse_date(date_from)
    d_to = _parse_date(date_to)

    try:
        rows = fetch_campaign_stats(settings, d_from, d_to)
        valid = validate_rows(rows)
    except ExtractError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_API) from exc
    except EmptyResponseError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_EMPTY) from exc

    if dry_run:
        payload = [row.model_dump(mode="json") for row in valid]
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        raise typer.Exit(EXIT_OK)

    loaded = upsert_rows(settings.database_url, valid)
    typer.echo(f"Loaded {loaded} rows")
    raise typer.Exit(EXIT_OK)


@app.command("run")
def run_cmd(
    date_from: str | None = typer.Option(None, "--from", help="Start date YYYY-MM-DD"),
    date_to: str | None = typer.Option(None, "--to", help="End date YYYY-MM-DD"),
    incremental: bool = typer.Option(False, "--incremental", help="Load recent window only"),
    lookback_days: int = typer.Option(30, "--lookback-days", help="Backfill window if table is empty"),
) -> None:
    """Full pipeline: extract → validate → load."""
    setup_logging()
    settings = get_settings()

    try:
        settings.validate_for_run()
    except ValueError as exc:
        typer.echo(f"Config error: {exc}", err=True)
        raise typer.Exit(EXIT_CONFIG) from exc

    if incremental:
        d_from, d_to = default_incremental_range(settings.database_url)
        mode = "incremental"
    elif date_from and date_to:
        d_from = _parse_date(date_from)
        d_to = _parse_date(date_to)
        mode = "backfill"
    elif date_from or date_to:
        typer.echo("Both --from and --to are required for backfill", err=True)
        raise typer.Exit(EXIT_CONFIG)
    else:
        d_to = date.today()
        d_from = d_to - timedelta(days=lookback_days)
        mode = "default"

    run_id = start_run(
        settings.database_url,
        mode=mode,
        date_from=d_from,
        date_to=d_to,
    )

    try:
        rows = fetch_campaign_stats(settings, d_from, d_to)
        valid = validate_rows(rows)
        if not valid:
            raise EmptyResponseError("all rows were filtered out during validation")
        loaded = upsert_rows(settings.database_url, valid)
        finish_run(settings.database_url, run_id, status="success", rows_loaded=loaded)
        typer.echo(f"Run {run_id}: loaded {loaded} rows ({d_from} -> {d_to})")
        return
    except typer.Exit:
        raise
    except ExtractError as exc:
        finish_run(settings.database_url, run_id, status="error", error_message=str(exc))
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_API) from exc
    except EmptyResponseError as exc:
        finish_run(settings.database_url, run_id, status="empty", error_message=str(exc))
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_EMPTY) from exc
    except Exception as exc:
        finish_run(settings.database_url, run_id, status="error", error_message=str(exc))
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(1) from exc


@app.command("reconcile")
def reconcile_cmd(
    date_from: str = typer.Option(..., "--from", help="Start date YYYY-MM-DD"),
    date_to: str = typer.Option(..., "--to", help="End date YYYY-MM-DD"),
) -> None:
    """Print daily PG totals for comparison with manual TG Booster export."""
    setup_logging()
    settings = get_settings()

    try:
        settings.validate_for_config_check()
    except ValueError as exc:
        typer.echo(f"Config error: {exc}", err=True)
        raise typer.Exit(EXIT_CONFIG) from exc

    d_from = _parse_date(date_from)
    d_to = _parse_date(date_to)

    rows = fetch_daily_totals(settings.database_url, d_from, d_to)
    typer.echo("stat_date,spend,leads,row_count")
    for stat_date, spend, leads, row_count in rows:
        typer.echo(f"{stat_date},{spend:.2f},{leads},{row_count}")

    if not rows:
        typer.echo("No rows in range", err=True)
        raise typer.Exit(EXIT_EMPTY)

    total_spend = sum(r[1] for r in rows)
    total_leads = sum(r[2] for r in rows)
    typer.echo(f"# total_spend={total_spend:.2f} total_leads={total_leads} days={len(rows)}")
    raise typer.Exit(EXIT_OK)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
