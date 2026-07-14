# SQL-запросы для еженедельного отчёта

Примеры запросов после `python -m etl run --incremental`.

## Последний запуск ETL

```sql
SELECT run_id, finished_at, rows_loaded, mode, status
FROM etl_runs
ORDER BY run_id DESC
LIMIT 1;
```

## Итоги по дням (7 дней)

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

## Итоги по кампаниям (7 дней)

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

## Сверка за период

```sql
SELECT
    stat_date,
    SUM(spend) AS spend,
    SUM(leads) AS leads,
    COUNT(*) AS row_count
FROM raw_campaign_stats
WHERE stat_date BETWEEN :date_from AND :date_to
GROUP BY stat_date
ORDER BY stat_date;
```
