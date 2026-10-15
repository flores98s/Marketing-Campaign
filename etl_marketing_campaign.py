import pandas as pd

df = pd.read_csv("marketing_campaign_dataset.csv")

print("Shape:", df.shape)
print(df.dtypes)
print(df.head(5).T)

# 1. Missing values and duplicates
print("\nNulls:\n", df.isna().sum())
print("Duplicated rows:", df.duplicated().sum())

# 2. Categorical columns: inspect variants, whitespace, and inconsistent casing
cat_cols = ["Company", "Campaign_Type", "Target_Audience", "Channel_Used",
            "Location", "Language", "Customer_Segment"]
for c in (column for column in cat_cols if column in df.columns):
    print(f"\n{c}: {df[c].nunique()} unique")
    print(df[c].value_counts(dropna=False).head(15))

# 3. Dates
d = pd.to_datetime(df["Date"], errors="coerce")
print("\nDate range:", d.min(), "->", d.max(), "| unparseable:", d.isna().sum())

# 4. Numeric fields that may arrive as text ("$1,234.00", "30 days", "5%")
for c in ["Acquisition_Cost", "Conversion_Rate", "Duration", "ROI"]:
    if c in df.columns:
        print(f"\n{c}: dtype={df[c].dtype} | sample={df[c].head(3).tolist()}")

numeric_columns = [
    column for column in [
        "Acquisition_Cost", "Conversion_Rate", "ROI", "Duration",
        "Clicks", "Impressions", "Engagement_Score"
    ] if column in df.columns
]


def to_numeric(series):
    """Convert formatted text to numbers while preserving numeric columns."""
    if pd.api.types.is_numeric_dtype(series):
        return series
    cleaned = series.astype("string").str.replace(
        r"[^0-9.\-]", "", regex=True
    )
    return pd.to_numeric(cleaned, errors="coerce")


num = df[numeric_columns].apply(to_numeric)
print(num.describe().T)

# 5. Business rules
if {"Clicks", "Impressions"}.issubset(num.columns):
    print("\nClicks > Impressions:", (num["Clicks"] > num["Impressions"]).sum())
if "Engagement_Score" in num.columns:
    print("Engagement outside 1-10:", (~num["Engagement_Score"].between(1, 10)).sum())
print("Negative values:", (num < 0).sum().to_dict())
if "Conversion_Rate" in num.columns:
    print("Conversion_Rate max:", num["Conversion_Rate"].max(),
          "(scale may be 0-1 or 0-100)")