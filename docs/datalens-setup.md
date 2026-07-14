# Подключение Yandex DataLens

DataLens не видит `localhost` — для BI нужен PostgreSQL с публичным доступом (VPS, managed-сервис) или туннель.

## Подключение к PostgreSQL

1. [datalens.yandex.cloud](https://datalens.yandex.cloud) → **Создать подключение** → PostgreSQL
2. Укажите host, port, database, user, password из `.env`
3. SSL: выключен (если на сервере нет TLS)
4. **Проверить подключение** → сохранить

## Датасет

1. На странице подключения → **Создать датасет**
2. Источник: представление `mart_campaign_daily`
3. Сохранить

## Чарты (пример)

| Чарт | Тип | Поля |
|------|-----|------|
| Тренд расходов и лидов | Линейный | Ось X: `stat_date` · Ось Y: `SUM(spend)`, `SUM(leads)` |
| Кампании | Таблица | `campaign_name` · `SUM(spend)`, `SUM(leads)`, `AVG(cpl)` |

## Обновление данных

DataLens читает PostgreSQL напрямую. После ETL-загрузки откройте чарт заново или снизьте TTL кеша в настройках подключения.

## Туннель для локальной разработки

Если PostgreSQL доступен только на `localhost`, используйте Cloudflare Tunnel или аналог.
