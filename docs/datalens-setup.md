# DataLens setup

Yandex DataLens не видит `localhost` — для BI нужен PostgreSQL с публичным доступом (VPS, managed DB) или туннель.

## Подключение PostgreSQL

1. [datalens.yandex.cloud](https://datalens.yandex.cloud) → **Создать подключение** → PostgreSQL
2. Заполните host, port, database, user, password из вашего `.env`
3. SSL: Off (для MVP на VPS с self-managed Postgres)
4. **Проверить подключение** → сохранить

## Датасет

1. На странице подключения → **Создать датасет**
2. Источник: view `mart_campaign_daily`
3. Сохранить

## Чарты (пример)

| Чарт | Тип | Поля |
|------|-----|------|
| Тренд | Линейный | X: `stat_date` · Y: `SUM(spend)`, `SUM(leads)` |
| Кампании | Таблица | `campaign_name` · `SUM(spend)`, `SUM(leads)`, `AVG(cpl)` |

## Обновление данных

PostgreSQL подключается напрямую — отдельной кнопки «обновить данные» на датасете нет.  
Если чарт показывает старые цифры: откройте чарт → **Редактировать** → **Сохранить** (сброс кеша), или уменьшите TTL в настройках кеширования подключения.

## Local dev fallback

Для локального Docker Postgres можно использовать Cloudflare Tunnel или ngrok TCP (ngrok free tier может требовать карту).
