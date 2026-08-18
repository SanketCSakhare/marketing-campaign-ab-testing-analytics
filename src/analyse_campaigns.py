"""Validate campaign data and produce A/B testing decision outputs."""

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib"))
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "campaign_performance.csv"
OUTPUT = ROOT / "data" / "processed"
CHARTS = ROOT / "dashboard" / "screenshots"

REQUIRED = {
    "campaign_name", "date", "spend_gbp", "impressions", "reach",
    "website_clicks", "searches", "content_views", "add_to_cart", "purchases",
}


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide KPI inputs while treating zero denominators as undefined."""
    return numerator.div(denominator.where(denominator.ne(0)))


def validate(df: pd.DataFrame) -> None:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df[list(REQUIRED - {"campaign_name", "date"})].isna().any().any():
        raise ValueError("Numeric campaign fields cannot contain null values")
    if (df[list(REQUIRED - {"campaign_name", "date"})] < 0).any().any():
        raise ValueError("Campaign metrics cannot be negative")
    if not (df["purchases"] <= df["add_to_cart"]).all():
        raise ValueError("Purchases cannot exceed add-to-cart events")
    if not (df["add_to_cart"] <= df["content_views"]).all():
        raise ValueError("Add-to-cart events cannot exceed content views")
    if not (df["website_clicks"] <= df["impressions"]).all():
        raise ValueError("Clicks cannot exceed impressions")


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["ctr"] = safe_divide(result["website_clicks"], result["impressions"])
    result["click_to_purchase_rate"] = safe_divide(
        result["purchases"], result["website_clicks"]
    )
    result["cpc_gbp"] = safe_divide(result["spend_gbp"], result["website_clicks"])
    result["cpa_gbp"] = safe_divide(result["spend_gbp"], result["purchases"])
    return result


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    totals = df.groupby("campaign_name", as_index=False).agg(
        days=("date", "nunique"),
        spend_gbp=("spend_gbp", "sum"),
        impressions=("impressions", "sum"),
        reach=("reach", "sum"),
        website_clicks=("website_clicks", "sum"),
        add_to_cart=("add_to_cart", "sum"),
        purchases=("purchases", "sum"),
    )
    totals["ctr"] = safe_divide(totals["website_clicks"], totals["impressions"])
    totals["click_to_purchase_rate"] = safe_divide(
        totals["purchases"], totals["website_clicks"]
    )
    totals["cpc_gbp"] = safe_divide(totals["spend_gbp"], totals["website_clicks"])
    totals["cpa_gbp"] = safe_divide(totals["spend_gbp"], totals["purchases"])
    return totals


def significance(df: pd.DataFrame) -> pd.DataFrame:
    control = df[df["campaign_name"] == "Control Campaign"]
    test = df[df["campaign_name"] == "Test Campaign"]
    rows = []
    for metric in ["ctr", "click_to_purchase_rate", "cpa_gbp"]:
        statistic, p_value = ttest_ind(
            test[metric], control[metric], equal_var=False, nan_policy="omit"
        )
        control_mean = control[metric].mean()
        test_mean = test[metric].mean()
        rows.append(
            {
                "metric": metric,
                "control_mean": control_mean,
                "test_mean": test_mean,
                "relative_change_pct": (test_mean / control_mean - 1) * 100,
                "test_statistic": statistic,
                "p_value": p_value,
                "significant_at_5pct": p_value < 0.05,
            }
        )
    return pd.DataFrame(rows)


def recommendation(summary: pd.DataFrame, tests: pd.DataFrame) -> str:
    indexed = summary.set_index("campaign_name")
    control = indexed.loc["Control Campaign"]
    test = indexed.loc["Test Campaign"]
    cpa_test = tests.set_index("metric").loc["cpa_gbp"]
    conversion_test = tests.set_index("metric").loc["click_to_purchase_rate"]
    conversion_lift = (test["click_to_purchase_rate"] / control["click_to_purchase_rate"] - 1) * 100
    cpa_change = (test["cpa_gbp"] / control["cpa_gbp"] - 1) * 100
    decision = (
        "Scale the test campaign gradually"
        if conversion_test["p_value"] < 0.05 and test["cpa_gbp"] < control["cpa_gbp"]
        else "Keep the control and run a longer test"
    )
    return (
        f"# Experiment Recommendation\n\n"
        f"## Decision\n\n**{decision}.**\n\n"
        f"The test campaign delivered a **{conversion_lift:.1f}%** change in click-to-purchase "
        f"conversion and a **{cpa_change:.1f}%** change in cost per acquisition versus control. "
        f"The conversion p-value was **{conversion_test['p_value']:.4f}** and the CPA p-value was "
        f"**{cpa_test['p_value']:.4f}**.\n\n"
        "## Action\n\nShift 25% of control budget to the test treatment for two weeks, monitor CPA and "
        "conversion daily, and stop the rollout if CPA rises more than 10% above control.\n\n"
        "## Caveat\n\nThe demo data is synthetic and illustrates the analytical workflow. Replace it with "
        "the Kaggle campaign files before using the result as real-world evidence.\n"
    )


def create_charts(summary: pd.DataFrame) -> None:
    CHARTS.mkdir(parents=True, exist_ok=True)
    labels = summary["campaign_name"].str.replace(" Campaign", "", regex=False)
    colors = ["#4263EB", "#0B8F55"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar(labels, summary["click_to_purchase_rate"] * 100, color=colors)
    axes[0].set_title("Click-to-purchase conversion")
    axes[0].set_ylabel("Conversion rate (%)")
    axes[1].bar(labels, summary["cpa_gbp"], color=colors)
    axes[1].set_title("Cost per acquisition")
    axes[1].set_ylabel("GBP per purchase")
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("Campaign experiment: commercial outcome", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(CHARTS / "campaign_experiment_results.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(INPUT, parse_dates=["date"])
    validate(df)
    daily = add_metrics(df)
    summary = summarise(daily)
    tests = significance(daily)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUTPUT / "campaign_daily_metrics.csv", index=False)
    summary.to_csv(OUTPUT / "campaign_summary.csv", index=False)
    tests.to_csv(OUTPUT / "statistical_tests.csv", index=False)
    (ROOT / "docs" / "experiment_recommendation.md").write_text(
        recommendation(summary, tests), encoding="utf-8"
    )
    create_charts(summary)
    print(summary.to_string(index=False))
    print("\nStatistical tests\n", tests.to_string(index=False))


if __name__ == "__main__":
    main()
