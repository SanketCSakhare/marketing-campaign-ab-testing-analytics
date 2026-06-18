-- Campaign scorecard with commercial and funnel KPIs.
SELECT
    campaign_name,
    SUM(spend_gbp) AS spend_gbp,
    SUM(impressions) AS impressions,
    SUM(website_clicks) AS website_clicks,
    SUM(purchases) AS purchases,
    1.0 * SUM(website_clicks) / NULLIF(SUM(impressions), 0) AS ctr,
    1.0 * SUM(purchases) / NULLIF(SUM(website_clicks), 0) AS click_to_purchase_rate,
    SUM(spend_gbp) / NULLIF(SUM(purchases), 0) AS cpa_gbp
FROM campaign_performance
GROUP BY campaign_name;

-- Daily monitoring query for experiment guardrails.
SELECT
    date,
    campaign_name,
    spend_gbp / NULLIF(purchases, 0) AS daily_cpa_gbp,
    1.0 * purchases / NULLIF(website_clicks, 0) AS daily_conversion_rate
FROM campaign_performance
ORDER BY date, campaign_name;

