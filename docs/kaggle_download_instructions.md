# Kaggle Dataset Setup

The project is designed around the public **Marketing A/B Testing** dataset on Kaggle, commonly distributed as `control_group.csv` and `test_group.csv`.

1. Download both campaign CSV files from Kaggle.
2. Standardise their columns to the names in `docs/data_dictionary.md`.
3. Add a `campaign_name` column to identify control and test rows.
4. Combine the files as `data/raw/campaign_performance.csv`.
5. Run `python src/analyse_campaigns.py`.

The included generator creates equivalent synthetic records so the complete pipeline can be reviewed without a Kaggle account. Synthetic results must not be presented as real campaign performance.

