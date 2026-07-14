from datetime import date

from etl.models import CampaignStatRow
from etl.validate import validate_rows


def test_negative_spend_skipped():
    rows = [
        CampaignStatRow(stat_date=date(2026, 7, 1), campaign_id="1", spend=-10.0),
        CampaignStatRow(stat_date=date(2026, 7, 1), campaign_id="2", spend=100.0),
    ]
    result = validate_rows(rows)
    assert len(result) == 1
    assert result[0].campaign_id == "2"


def test_duplicate_last_wins():
    rows = [
        CampaignStatRow(stat_date=date(2026, 7, 1), campaign_id="1", spend=10.0),
        CampaignStatRow(stat_date=date(2026, 7, 1), campaign_id="1", spend=99.0),
    ]
    result = validate_rows(rows)
    assert len(result) == 1
    assert result[0].spend == 99.0
