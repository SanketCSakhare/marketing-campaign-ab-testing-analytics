import pandas as pd
import pytest

from src.analyse_campaigns import add_metrics, validate


def valid_row() -> dict:
    return {
        "campaign_name": "Control Campaign", "date": "2019-08-01",
        "spend_gbp": 100, "impressions": 1000, "reach": 800,
        "website_clicks": 100, "searches": 30, "content_views": 25,
        "add_to_cart": 10, "purchases": 5,
    }


def test_metric_calculation():
    result = add_metrics(pd.DataFrame([valid_row()])).iloc[0]
    assert result["ctr"] == pytest.approx(0.1)
    assert result["click_to_purchase_rate"] == pytest.approx(0.05)
    assert result["cpa_gbp"] == pytest.approx(20)


def test_invalid_funnel_is_rejected():
    row = valid_row()
    row["purchases"] = 20
    with pytest.raises(ValueError, match="Purchases"):
        validate(pd.DataFrame([row]))

