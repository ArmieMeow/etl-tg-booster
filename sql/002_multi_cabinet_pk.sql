-- Multi-cabinet support: include account_id in primary key
ALTER TABLE raw_campaign_stats
    ALTER COLUMN account_id SET NOT NULL;

ALTER TABLE raw_campaign_stats
    DROP CONSTRAINT IF EXISTS raw_campaign_stats_pkey;

ALTER TABLE raw_campaign_stats
    ADD PRIMARY KEY (stat_date, campaign_id, account_id);
