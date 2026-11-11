
"""
ATLAS ENTERPRISE OPERATING PLATFORM
Data Cleaning pipeline
"""

from pathlib import Path
import pandas as pd
import numpy as np



# PROJECT PATHS


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_FOLDER = PROJECT_ROOT / "data" / "raw"
PROCESSED_FOLDER = PROJECT_ROOT / "data" / "processed"
REPORT_FOLDER = PROJECT_ROOT / "data" / "reports"

PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
REPORT_FOLDER.mkdir(parents=True, exist_ok=True)



# DATA QUALITY REPORT


cleaning_report = []


def record_report(table_name, original_rows, cleaned_rows,
                  missing_before, missing_after,
                  duplicate_rows, notes):

    cleaning_report.append({
        "table": table_name,
        "original_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "rows_removed": original_rows - cleaned_rows,
        "missing_values_before": missing_before,
        "missing_values_after": missing_after,
        "duplicate_rows_found": duplicate_rows,
        "notes": notes
    })



# STANDARDISE COLUMN NAMES


def standardise_columns(df):

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    return df



# STANDARDISE TEXT VALUES


def standardise_text(df):

    for column in df.select_dtypes(include=["object"]).columns:

        df[column] = df[column].apply(
            lambda value: value.strip()
            if isinstance(value, str)
            else value
        )

        df[column] = df[column].replace("", np.nan)

    return df



#  IDENTIFY DUPLICATE RECORDS


def inspect_duplicates(df):

    duplicate_count = int(df.duplicated().sum())

    # Remove only completely identical rows.
    # Records with the same ID but different information
    # are preserved for investigation.

    df = df.drop_duplicates()

    return df, duplicate_count



# STANDARDISE DATES


DATE_COLUMNS = [
    "join_date",
    "exit_date",
    "paid_date",
    "opened_date",
    "closed_date",
    "event_date",
    "sent_at",
    "timestamp",
    "created_at",
    "closed_at",
    "uploaded_at",
    "received_at",
    "decided_at"
]


def clean_dates(df):

    for column in DATE_COLUMNS:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    # Membership join dates cannot be in the future.
    if "join_date" in df.columns:

        future_dates = df["join_date"] > pd.Timestamp.today()

        df.loc[future_dates, "join_date"] = pd.NaT

    return df



# CLEAN NUMERIC VALUES


NUMERIC_COLUMNS = [
    "amount_due",
    "amount_paid",
    "steward_count",
    "version_number",
    "step_number",
    "max_days",
    "age"
]


def clean_numeric(df):

    for column in NUMERIC_COLUMNS:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df



# 8. STANDARDISE CATEGORIES


def standardise_categories(df):

    category_columns = [
        "status",
        "payment_status",
        "payment_method",
        "employment_type",
        "sector",
        "remittance_cycle",
        "category",
        "outcome",
        "event_type",
        "channel",
        "role",
        "action",
        "document_type",
        "current_step",
        "final_destination",
        "level",
        "approver_role",
        "decision",
        "province"
    ]

    for column in category_columns:

        if column in df.columns:

            df[column] = df[column].apply(
                lambda value: value.lower().strip()
                if isinstance(value, str)
                else value
            )

    return df


#  CHECK REQUIRED IDENTIFIER FIELDS


IDENTIFIER_COLUMNS = [
    "member_id",
    "employer_id",
    "branch_id",
    "region_id",
    "txn_id",
    "case_id",
    "event_id",
    "message_id",
    "log_id",
    "user_id",
    "document_id",
    "step_id"
]


def inspect_identifiers(df):

    duplicate_id_columns = []

    for column in IDENTIFIER_COLUMNS:

        if column in df.columns:

            duplicate_count = int(
                df[column].dropna().duplicated().sum()
            )

            if duplicate_count > 0:

                duplicate_id_columns.append(
                    f"{column}: {duplicate_count} duplicates"
                )

    return duplicate_id_columns


#  CLEAN ONE DATASET

def clean_dataset(file_path):

    table_name = file_path.stem

    print(f"\nCleaning table: {table_name}")

    df = pd.read_csv(file_path, low_memory=False)

    original_rows = len(df)

    missing_before = int(df.isna().sum().sum())

    print(f"Original rows: {original_rows}")

    # Standardise columns and text.
    df = standardise_columns(df)
    df = standardise_text(df)

    # Remove completely identical records only.
    df, duplicate_count = inspect_duplicates(df)

    # Standardise dates and numbers.
    df = clean_dates(df)
    df = clean_numeric(df)

    # Standardise category formatting.
    df = standardise_categories(df)

    # Check IDs without silently deleting records.
    duplicate_ids = inspect_identifiers(df)

    missing_after = int(df.isna().sum().sum())

    # Save cleaned dataset.
    output_path = PROCESSED_FOLDER / f"{table_name}.csv"

    df.to_csv(output_path, index=False)

    notes = "Cleaning completed."

    if duplicate_ids:
        notes += " Duplicate identifiers require investigation: "
        notes += "; ".join(duplicate_ids)

    record_report(
        table_name,
        original_rows,
        len(df),
        missing_before,
        missing_after,
        duplicate_count,
        notes
    )

    print(f"Cleaned rows: {len(df)}")
    print(f"Duplicate rows removed: {duplicate_count}")
    print(f"Missing values before: {missing_before}")
    print(f"Missing values after: {missing_after}")
    print(f"Saved to: {output_path}")



# 11. RUN THE COMPLETE CLEANING PIPELINE


def main():

    print("=" * 60)
    print("ATLAS DATA CLEANING PIPELINE")
    print("=" * 60)

    if not RAW_FOLDER.exists():

        raise FileNotFoundError(
            f"Raw data folder not found: {RAW_FOLDER}"
        )

    csv_files = sorted(RAW_FOLDER.glob("*.csv"))

    if not csv_files:

        raise FileNotFoundError(
            f"No CSV files found in: {RAW_FOLDER}"
        )

    print(f"\nFound {len(csv_files)} CSV datasets.")

    for file_path in csv_files:

        try:

            clean_dataset(file_path)

        except Exception as error:

            print(
                f"ERROR cleaning {file_path.name}: {error}"
            )

            record_report(
                file_path.stem,
                0,
                0,
                0,
                0,
                0,
                f"Cleaning failed: {error}"
            )

    # Save the cleaning report.
    report_df = pd.DataFrame(cleaning_report)

    report_path = (
        REPORT_FOLDER / "data_cleaning_report.csv"
    )

    report_df.to_csv(report_path, index=False)

    print("\n" + "=" * 60)
    print("ATLAS DATA CLEANING SUMMARY")
    print("=" * 60)

    if not report_df.empty:

        print(report_df.to_string(index=False))

    print("\nCleaning pipeline finished.")
    print(f"Processed datasets: {PROCESSED_FOLDER}")
    print(f"Cleaning report: {report_path}")


if __name__ == "__main__":
    main()

