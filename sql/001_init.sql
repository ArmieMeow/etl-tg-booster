-- Schema: raw layer, mart view, run metadata

CREATE TABLE IF NOT EXISTS raw_campaign_stats (
    stat_date       DATE NOT NULL,
    campaign_id     TEXT NOT NULL,
    campaign_name   TEXT,
    account_id      TEXT NOT NULL,
    spend           NUMERIC(14, 2),
    impressions     BIGINT,
    clicks          BIGINT,
    leads           BIGINT,
    source_payload  JSONB,
    loaded_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (stat_date, campaign_id, account_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_campaign_stats_date
    ON raw_campaign_stats (stat_date DESC);

CREATE INDEX IF NOT EXISTS idx_raw_campaign_stats_account
    ON raw_campaign_stats (account_id);

CREATE TABLE IF NOT EXISTS etl_runs (
    run_id        BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ,
    rows_loaded   INT,
    status        TEXT NOT NULL,
    error_message TEXT,
    mode          TEXT,
    date_from     DATE,
    date_to       DATE
);

CREATE OR REPLACE VIEW mart_campaign_daily AS
SELECT
    stat_date,
    campaign_id,
    campaign_name,
    account_id,
    spend,
    impressions,
    clicks,
    leads,
    CASE WHEN leads > 0 THEN spend / leads END AS cpl,
    CASE WHEN clicks > 0 THEN spend / clicks END AS cpc,
    CASE WHEN impressions > 0 THEN spend / impressions * 1000 END AS cpm
FROM raw_campaign_stats;
