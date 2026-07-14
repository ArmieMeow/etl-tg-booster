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
