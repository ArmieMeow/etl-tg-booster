# PostgreSQL на VPS (production)

Развёртывание PostgreSQL на VPS для ETL и DataLens.

## На сервере

```bash
# Установка Docker
curl -fsSL https://get.docker.com | sh

mkdir -p /opt/etl-tg-booster/sql
# Скопируйте sql/ и docker-compose.yml (scp или git clone)
```

Создайте `/opt/etl-tg-booster/.env`:

```env
POSTGRES_USER=etl
POSTGRES_PASSWORD=<надёжный-пароль>
POSTGRES_DB=tg_booster
```

```bash
cd /opt/etl-tg-booster
docker compose up -d
docker compose exec -T postgres psql -U etl -d tg_booster < sql/001_init.sql
docker compose exec -T postgres psql -U etl -d tg_booster < sql/002_multi_cabinet_pk.sql
docker compose exec -T postgres psql -U etl -d tg_booster < sql/views.sql
```

## Файрвол

Откройте **TCP 5432** для доступа DataLens и ETL с рабочей машины.

## Запуск ETL с локального ПК

```env
DATABASE_URL=postgresql://etl:<пароль>@<хост-vps>:5432/tg_booster
```

```bash
python -m etl validate-config
python -m etl run --from 2026-06-01 --to 2026-06-30
```
