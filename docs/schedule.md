# Schedule — weekly ETL run

## Manual

```bash
python -m etl run --incremental
```

Для local dev с Docker Postgres:

```bash
docker compose up -d
python -m etl run --incremental
```

## Windows Task Scheduler

| Field | Value |
|-------|-------|
| Program | `<project>\.venv\Scripts\python.exe` |
| Arguments | `-m etl run --incremental` |
| Start in | `<project>` |

Wrapper: `scripts/run-incremental.ps1`

```powershell
powershell.exe -ExecutionPolicy Bypass -File "<project>\scripts\run-incremental.ps1"
```

## Linux cron

```cron
0 8 * * 1 cd /path/to/etl-tg-booster && .venv/bin/python -m etl run --incremental >> logs/etl.log 2>&1
```

## Verify last run

```sql
SELECT run_id, finished_at, rows_loaded, mode, status
FROM etl_runs
ORDER BY run_id DESC
LIMIT 5;
```
