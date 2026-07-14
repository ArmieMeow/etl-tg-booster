# ETL: TG Booster → PostgreSQL → DataLens

Пайплайн для автоматизации еженедельной отчётности по рекламным кампаниям в Telegram Ads (TG Booster): загрузка из API, валидация, хранение в PostgreSQL, визуализация в Yandex DataLens.

## Задача

На нескольких рекламных проектах еженедельная сводка собиралась вручную — выгрузка из кабинета, Excel, сводные таблицы. Пайплайн заменяет ручной процесс одним источником данных с идемпотентной загрузкой и возможностью сверки с ручной выгрузкой.

## Архитектура

```
TG Booster API  →  Python (extract, validate, load)  →  PostgreSQL  →  Yandex DataLens
                         ↑
                  CLI / планировщик
```

| Слой | Объект | Назначение |
|------|--------|------------|
| Raw | `raw_campaign_stats` | Статистика кампаний, сырой JSON в `source_payload` |
| Mart | `mart_campaign_daily` | Представление для BI: CPL, CPC, CPM |
| Meta | `etl_runs` | Журнал запусков ETL |

**Гранулярность:** день × кампания × кабинет.  
**Метрики:** расход, показы, клики, лиды.

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

Для production PostgreSQL на VPS — [`docs/production-postgres.md`](docs/production-postgres.md).

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
| `run --from DATE --to DATE` | Загрузка за период |
| `run --incremental` | Инкрементальная догрузка |
| `extract --dry-run` | Извлечение без записи в БД |
| `reconcile --from DATE --to DATE` | Дневные итоги для сверки |

Коды выхода: `0` — успех · `1` — конфигурация/валидация · `2` — ошибка API · `3` — пустой ответ.

## Сверка с ручной выгрузкой

Методика и пример сверки за 7 дней — [`docs/reconciliation.md`](docs/reconciliation.md).  
Допустимая погрешность: < 2% по расходу и лидам.

## Документация

| Файл | Содержание |
|------|------------|
| [`docs/datalens-setup.md`](docs/datalens-setup.md) | Подключение DataLens к PostgreSQL |
| [`docs/production-postgres.md`](docs/production-postgres.md) | PostgreSQL на VPS |
| [`docs/schedule.md`](docs/schedule.md) | Планировщик (cron / Windows) |
| [`docs/sql-queries.md`](docs/sql-queries.md) | SQL для еженедельного отчёта |

## Тесты

```bash
pytest
```

## Структура проекта

```
etl/           # извлечение, валидация, загрузка, CLI
sql/           # DDL, миграции, представления
docs/          # инструкции
scripts/       # скрипты автоматизации
tests/
```
