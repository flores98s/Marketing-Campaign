# Marketing Campaign ETL

A pandas ETL pipeline that extracts the marketing campaign CSV, cleans and validates the data, and produces files ready to load into BigQuery.

## Requirements

- Python 3.9 or newer
- pandas

Install the dependency with:

```bash
pip install pandas
```

## Project Structure

```text
.
├── etl_marketing_campaign.py
├── marketing_campaign_dataset.csv
├── marketing_campaign_clean.csv
├── marketing_campaign_schema.json
└── README.md
```

The script expects `marketing_campaign_dataset.csv` to be in the same directory as `etl_marketing_campaign.py`.

## Run the ETL

From the project directory, run:

```bash
python etl_marketing_campaign.py
```

If you are using the project's virtual environment on Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe .\etl_marketing_campaign.py
```

Custom input and output paths are supported:

```bash
python etl_marketing_campaign.py \
   --input marketing_campaign_dataset.csv \
   --output marketing_campaign_clean.csv \
   --schema-output marketing_campaign_schema.json
```

## ETL Steps

1. Extracts the source CSV and verifies the expected columns.
2. Removes exact duplicate rows.
3. Trims whitespace from text columns.
4. Converts `Duration` from values such as `30 days` to integer days.
5. Converts `Acquisition_Cost` from values such as `$16,174.00` to a numeric value.
6. Converts numeric fields to integer or floating-point values.
7. Converts `Date` to the `YYYY-MM-DD` format used by BigQuery `DATE` columns.
8. Validates nulls, duplicate campaign IDs, negative values, click/impression relationships, and engagement score ranges.
9. Writes the clean CSV and a BigQuery schema JSON file.

The pipeline stops with an error instead of exporting data when a validation rule fails.
Every successful run regenerates and overwrites both output files, so they always belong to the same ETL execution.

## Generated Files

### `marketing_campaign_clean.csv` - upload this file

The transformed dataset. It contains typed, BigQuery-compatible values and keeps the original column names. `Duration` is stored as an integer number of days.

### `marketing_campaign_schema.json` - use this schema during the upload

The explicit BigQuery schema. It can be used with the `bq` command-line tool:

```bash
bq load \
   --source_format=CSV \
   --skip_leading_rows=1 \
   --schema=marketing_campaign_schema.json \
   PROJECT_ID:DATASET_ID.marketing_campaign \
   marketing_campaign_clean.csv
```

Replace `PROJECT_ID` and `DATASET_ID` with your Google Cloud project and BigQuery dataset.

For a manual upload in the BigQuery console:

1. Create or select the destination table.
2. Select `marketing_campaign_clean.csv` as the source file.
3. Set the source format to `CSV` and enable the header-row option.
4. Disable autodetect and enter the fields from `marketing_campaign_schema.json` in the schema editor. For an automatic schema-file load, use the `bq load` command above.
5. Start the load job.

## Expected CSV Columns

The current dataset includes these columns:

- `Campaign_ID`
- `Company`
- `Campaign_Type`
- `Target_Audience`
- `Duration`
- `Channel_Used`
- `Conversion_Rate`
- `Acquisition_Cost`
- `ROI`
- `Location`
- `Language`
- `Clicks`
- `Impressions`
- `Engagement_Score`
- `Customer_Segment`
- `Date`

All listed columns are required. The ETL stops if any expected column is missing.

## Current Dataset Result

When run against the included dataset, the ETL processes 200,000 rows and produces:

- `marketing_campaign_clean.csv` with 200,000 validated rows
- `marketing_campaign_schema.json` with the BigQuery field definitions
- No missing values
- No duplicated campaign IDs
- No invalid dates
- No cases where clicks exceed impressions
- No engagement scores outside the 1-10 range
- No negative numeric values
