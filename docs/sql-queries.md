# SQL snippets for weekly reporting

Use after `python -m etl run --incremental`.

## Last sync

```sql
SELECT run_id, finished_at, rows_loaded, mode, status
FROM etl_runs
ORDER BY run_id DESC
LIMIT 1;
```

## Totals by day (last 7 days)

```sql
SELECT
    stat_date,
    SUM(spend) AS spend,
    SUM(leads) AS leads,
    CASE WHEN SUM(leads) > 0 THEN SUM(spend) / SUM(leads) END AS cpl
FROM raw_campaign_stats
WHERE stat_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY stat_date
ORDER BY stat_date;
```

## Totals by campaign (last 7 days)

```sql
SELECT
    account_id,
    campaign_name,
    SUM(spend) AS spend,
    SUM(leads) AS leads,
    CASE WHEN SUM(leads) > 0 THEN SUM(spend) / SUM(leads) END AS cpl
FROM raw_campaign_stats
WHERE stat_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY account_id, campaign_name
ORDER BY spend DESC;
```

## Reconciliation helper (compare with manual export)

```sql
SELECT
    stat_date,
    SUM(spend) AS spend,
    SUM(leads) AS leads,
    COUNT(*) AS row_count
FROM raw_campaign_stats
WHERE stat_date BETWEEN '2026-07-07' AND '2026-07-13'
GROUP BY stat_date
ORDER BY stat_date;
```

Replace dates with your reconciliation window.
