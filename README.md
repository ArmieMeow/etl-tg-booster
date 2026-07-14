# ETL: TG Booster → PostgreSQL → DataLens

Пайплайн для автоматизации weekly-отчётности по рекламным кампаниям в Telegram Ads (TG Booster): загрузка из API, валидация, хранение в PostgreSQL, визуализация в Yandex DataLens.

## Задача

На нескольких рекламных проектах еженедельная сводка собиралась вручную — выгрузка из кабинета, Excel, сводные таблицы. Пайплайн заменяет ручной процесс одним источником данных с идемпотентной загрузкой и возможностью сверки с ручной выгрузкой.

## Архитектура

```
TG Booster API  →  Python (extract, validate)  →  PostgreSQL  →  Yandex DataLens
                         ↑
                  CLI / Task Scheduler
```

| Слой | Объект | Назначение |
|------|--------|------------|
| Raw | `raw_campaign_stats` | Статистика кампаний, `source_payload` (JSONB) |
| Mart | `mart_campaign_daily` | View для BI: CPL, CPC, CPM |
| Meta | `etl_runs` | Журнал запусков ETL |

**Гранулярность:** день × кампания × кабинет.  
**Метрики:** spend, impressions, clicks, leads.

## Стек

Python 3.11 · httpx · Pydantic · Typer · PostgreSQL 16 · Docker · Yandex DataLens

## Быстрый старт

### 1. Окружение

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -e ".[dev]"
```

### 2. Конфигурация

```bash
cp .env.example .env
```

Заполните `TG_BOOSTER_API_TOKEN` и `DATABASE_URL` (см. `.env.example`).

### 3. PostgreSQL

```bash
docker compose up -d
python -m etl validate-config
```

Для production PostgreSQL на VPS — см. [`docs/production-postgres.md`](docs/production-postgres.md).

### 4. Загрузка данных

```bash
# Первичная загрузка
python -m etl run --from 2026-06-01 --to 2026-06-30

# Инкремент (последние 7 дней)
python -m etl run --incremental
```

## CLI

| Команда | Описание |
|---------|----------|
| `validate-config` | Проверка `.env` и подключения к БД |
| `run --from DATE --to DATE` | Backfill за период |
| `run --incremental` | Догрузка свежих данных |
| `extract --dry-run` | Extract без записи в БД |
| `reconcile --from DATE --to DATE` | Дневные итоги PG для сверки |

Коды выхода: `0` OK · `1` config/validation · `2` API · `3` empty response.

## Сверка с ручной выгрузкой

Методика и пример сверки за 7 дней — [`docs/reconciliation.md`](docs/reconciliation.md).  
Допустимая погрешность: &lt; 2% по spend и leads.

## Документация

| Файл | Содержание |
|------|------------|
| [`docs/datalens-setup.md`](docs/datalens-setup.md) | Подключение DataLens к PostgreSQL |
| [`docs/production-postgres.md`](docs/production-postgres.md) | PostgreSQL на VPS |
| [`docs/schedule.md`](docs/schedule.md) | Планировщик (cron / Task Scheduler) |
| [`docs/sql-queries.md`](docs/sql-queries.md) | SQL для weekly-отчёта |

## Тесты

```bash
pytest
```

## Структура проекта

```
etl/           # extract, validate, load, CLI
sql/           # DDL, migrations, views
docs/          # setup guides
scripts/       # automation helpers
tests/
```

## Безопасность

- Секреты только в `.env` (в git не попадает)
- В публичной документации не указывайте имена клиентов, кабинетов и production-хосты
