from datetime import date

from etl.models import map_report_record


def test_map_report_record_with_company_grouping():
    record = {
        "date_day": "2026-07-07",
        "ads_company_id": 65307,
        "company_name": "Campaign A",
        "metric_views": "100",
        "metric_clicks": "5",
        "metric_joins": "2",
        "metric_spent": "10.50",
    }
    row = map_report_record(record, cabinet_id="16159")
    assert row.campaign_id == "65307"
    assert row.campaign_name == "Campaign A"
    assert row.spend == 10.50


def test_map_report_record_from_docs_example():
    record = {
        "date_day": "2023-08-15",
        "metric_views": "871",
        "metric_clicks": "7",
        "metric_joins": "1",
        "metric_spent": "19.93",
    }
    row = map_report_record(
        record,
        campaign_id="912",
        campaign_name="Default",
        cabinet_id="242",
    )
    assert row.stat_date == date(2023, 8, 15)
    assert row.campaign_id == "912"
    assert row.campaign_name == "Default"
    assert row.account_id == "242"
    assert row.impressions == 871
    assert row.clicks == 7
    assert row.leads == 1
    assert row.spend == 19.93
