# Планировщик: еженедельный запуск ETL

## Ручной запуск

```bash
python -m etl run --incremental
```

Для локальной разработки с Docker PostgreSQL:

```bash
docker compose up -d
python -m etl run --incremental
```

## Windows: Планировщик заданий

| Поле | Значение |
|------|----------|
| Программа | `<путь-к-проекту>\.venv\Scripts\python.exe` |
| Аргументы | `-m etl run --incremental` |
| Рабочая папка | `<путь-к-проекту>` |

Обёртка с логированием: `scripts/run-incremental.ps1`

```powershell
powershell.exe -ExecutionPolicy Bypass -File "<путь-к-проекту>\scripts\run-incremental.ps1"
```

## Linux: cron

```cron
0 8 * * 1 cd /path/to/etl-tg-booster && .venv/bin/python -m etl run --incremental >> logs/etl.log 2>&1
```

Понедельник 08:00 — пример для еженедельного отчёта. Для ежедневной догрузки используйте `0 8 * * *`.

## Проверка последнего запуска

```sql
SELECT run_id, finished_at, rows_loaded, mode, status
FROM etl_runs
ORDER BY run_id DESC
LIMIT 5;
```
