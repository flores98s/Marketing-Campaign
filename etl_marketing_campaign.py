import argparse
import json
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = [
    "Campaign_ID",
    "Company",
    "Campaign_Type",
    "Target_Audience",
    "Duration",
    "Channel_Used",
    "Conversion_Rate",
    "Acquisition_Cost",
    "ROI",
    "Location",
    "Language",
    "Clicks",
    "Impressions",
    "Engagement_Score",
    "Customer_Segment",
    "Date",
]

TEXT_COLUMNS = [
    "Company",
    "Campaign_Type",
    "Target_Audience",
    "Channel_Used",
    "Location",
    "Language",
    "Customer_Segment",
]

BIGQUERY_SCHEMA = [
    {"name": "Campaign_ID", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "Company", "type": "STRING", "mode": "REQUIRED"},
    {"name": "Campaign_Type", "type": "STRING", "mode": "REQUIRED"},
    {"name": "Target_Audience", "type": "STRING", "mode": "REQUIRED"},
    {"name": "Duration", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "Channel_Used", "type": "STRING", "mode": "REQUIRED"},
    {"name": "Conversion_Rate", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "Acquisition_Cost", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "ROI", "type": "FLOAT", "mode": "REQUIRED"},
    {"name": "Location", "type": "STRING", "mode": "REQUIRED"},
    {"name": "Language", "type": "STRING", "mode": "REQUIRED"},
    {"name": "Clicks", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "Impressions", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "Engagement_Score", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "Customer_Segment", "type": "STRING", "mode": "REQUIRED"},
    {"name": "Date", "type": "DATE", "mode": "REQUIRED"},
]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Clean the marketing campaign CSV and create BigQuery-ready files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("marketing_campaign_dataset.csv"),
        help="Source CSV path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("marketing_campaign_clean.csv"),
        help="Clean CSV output path.",
    )
    parser.add_argument(
        "--schema-output",
        type=Path,
        default=Path("marketing_campaign_schema.json"),
        help="BigQuery schema JSON output path.",
    )
    return parser.parse_args()


def to_numeric(series):
    """Convert formatted text such as currency or durations to numbers."""
    if pd.api.types.is_numeric_dtype(series):
        return series
    cleaned = series.astype("string").str.replace(
        r"[^0-9.\-]", "", regex=True
    )
    return pd.to_numeric(cleaned, errors="coerce")


def extract(input_path):
    """Read the source CSV and verify the expected columns are available."""
    df = pd.read_csv(input_path)
    missing_columns = [column for column in EXPECTED_COLUMNS if column not in df]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    return df[EXPECTED_COLUMNS].copy()


def transform(df):
    """Clean text, numeric values, dates, and duration units for BigQuery."""
    for column in TEXT_COLUMNS:
        df[column] = df[column].astype("string").str.strip()

    df["Duration"] = to_numeric(df["Duration"]).astype("Int64")
    df["Acquisition_Cost"] = to_numeric(df["Acquisition_Cost"])
    for column in [
        "Campaign_ID",
        "Clicks",
        "Impressions",
        "Engagement_Score",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")
    for column in ["Conversion_Rate", "ROI"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


def validate(df):
    """Raise an error when records violate schema or business rules."""
    required_columns = [
        column for column in EXPECTED_COLUMNS if column != "Campaign_ID"
    ] + ["Campaign_ID"]
    null_counts = df[required_columns].isna().sum()
    null_counts = null_counts[null_counts > 0]
    if not null_counts.empty:
        raise ValueError(f"Null values found: {null_counts.to_dict()}")

    duplicate_ids = df["Campaign_ID"].duplicated().sum()
    if duplicate_ids:
        raise ValueError(f"Duplicated Campaign_ID values found: {duplicate_ids}")

    if (df["Clicks"] > df["Impressions"]).any():
        raise ValueError("Some rows have more clicks than impressions")
    if (~df["Engagement_Score"].between(1, 10)).any():
        raise ValueError("Some engagement scores are outside the 1-10 range")

    numeric_columns = [
        "Duration",
        "Conversion_Rate",
        "Acquisition_Cost",
        "ROI",
        "Clicks",
        "Impressions",
        "Engagement_Score",
    ]
    negative_counts = (df[numeric_columns] < 0).sum()
    negative_counts = negative_counts[negative_counts > 0]
    if not negative_counts.empty:
        raise ValueError(f"Negative values found: {negative_counts.to_dict()}")


def load(df, output_path, schema_path):
    """Write the cleaned CSV and the schema used to load it into BigQuery."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, date_format="%Y-%m-%d")
    schema_path.write_text(
        json.dumps(BIGQUERY_SCHEMA, indent=2), encoding="utf-8"
    )


def main():
    args = parse_arguments()
    raw_df = extract(args.input)
    print(f"Extracted {len(raw_df):,} rows from {args.input}")

    duplicate_rows = raw_df.duplicated().sum()
    if duplicate_rows:
        raw_df = raw_df.drop_duplicates().copy()
        print(f"Removed {duplicate_rows:,} exact duplicate rows")

    clean_df = transform(raw_df)
    validate(clean_df)
    load(clean_df, args.output, args.schema_output)

    print(f"Loaded {len(clean_df):,} validated rows into {args.output}")
    print(f"BigQuery schema written to {args.schema_output}")


if __name__ == "__main__":
    main()