"""Generate reproducible campaign-level demo data matching the Kaggle schema."""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


def make_campaign(name: str, days: int, seed: int, lift: float) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2019-08-01", periods=days, freq="D")
    impressions = rng.integers(70_000, 125_000, days)
    reach = (impressions * rng.uniform(0.72, 0.89, days)).astype(int)
    clicks = rng.binomial(impressions, 0.048 * lift)
    searches = rng.binomial(clicks, 0.205 * lift)
    views = rng.binomial(searches, 0.74)
    cart = rng.binomial(views, 0.46 * lift)
    purchases = rng.binomial(cart, 0.34 * lift)
    spend = impressions * rng.uniform(0.035, 0.052, days) * (1.04 if name == "Test Campaign" else 1)
    return pd.DataFrame(
        {
            "campaign_name": name,
            "date": dates,
            "spend_gbp": spend.round(2),
            "impressions": impressions,
            "reach": reach,
            "website_clicks": clicks,
            "searches": searches,
            "content_views": views,
            "add_to_cart": cart,
            "purchases": purchases,
        }
    )


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    control = make_campaign("Control Campaign", 30, 42, 1.00)
    test = make_campaign("Test Campaign", 30, 84, 1.13)
    pd.concat([control, test], ignore_index=True).to_csv(
        RAW_DIR / "campaign_performance.csv", index=False
    )
    print("Created data/raw/campaign_performance.csv with 60 campaign-day records.")


if __name__ == "__main__":
    main()

