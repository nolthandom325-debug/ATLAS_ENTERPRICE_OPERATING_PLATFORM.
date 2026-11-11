
# ATLAS ENTERPRISE OPERATING PLATFORM
# DATA VALIDATION SYSTEM
# Legasis (Pty) Ltd


from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. PROJECT DIRECTORIES
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)



# REQUIRED TABLES AND COLUMNS


REQUIRED_COLUMNS = {
    "members": [
        "member_id", "age_band", "join_date", "status",
        "employer_id", "branch_id"
    ],
    "employers": [
        "employer_id", "employer_name", "sector",
        "province", "remittance_cycle"
    ],
    "branches": [
        "branch_id", "branch_name", "region_id",
        "province", "steward_count"
    ],
    "dues_transactions": [
        "txn_id", "member_id", "period",
        "amount_due", "amount_paid", "payment_status"
    ],
    "cases": [
        "case_id", "member_id", "employer_id",
        "category", "opened_date", "status"
    ],
    "engagement_events": [
        "event_id", "member_id", "branch_id",
        "event_type", "event_date", "attended"
    ],
    "communications": [
        "message_id", "member_id", "channel",
        "sent_at", "delivered", "opened_or_replied"
    ],
    "audit_log": [
        "log_id", "user_id", "role",
        "action", "entity", "timestamp"
    ],
    "users": [
        "user_id", "role", "active"
    ],
    "regions": [
        "region_id", "region_name", "province"
    ],
    "documents": [
        "document_id", "document_type", "current_version",
        "status", "current_step", "created_at"
    ],
    "document_versions": [
        "document_id", "version_number", "file_hash",
        "uploaded_by", "uploaded_at"
    ],
    "routing_rules": [
        "document_type", "step_number", "level",
        "approver_role", "max_days"
    ],
    "approval_steps": [
        "step_id", "document_id", "version_number",
        "step_number", "level", "assigned_to", "received_at"
    ]
}


# ------------------------------------------------------------
# 3. PRIMARY KEYS
# ------------------------------------------------------------

PRIMARY_KEYS = {
    "members": ["member_id"],
    "employers": ["employer_id"],
    "branches": ["branch_id"],
    "dues_transactions": ["txn_id"],
    "cases": ["case_id"],
    "engagement_events": ["event_id"],
    "communications": ["message_id"],
    "audit_log": ["log_id"],
    "users": ["user_id"],
    "regions": ["region_id"],
    "documents": ["document_id"],
    "document_versions": ["document_id", "version_number"],
    "routing_rules": ["document_type", "step_number"],
    "approval_steps": ["step_id"]
}


# ------------------------------------------------------------
# 4. ALLOWED VALUES
# ------------------------------------------------------------

ALLOWED_VALUES = {
    "members": {
        "age_band": ["18-24", "25-34", "35-44", "45-54", "55+"],
        "status": ["active", "lapsed", "suspended", "resigned", "deceased"]
    },
    "dues_transactions": {
        "payment_status": ["paid", "partial", "unpaid"]
    },
    "cases": {
        "category": [
            "disciplinary", "unfair dismissal",
            "wage dispute", "health and safety", "other"
        ],
        "status": ["open", "in progress", "closed", "escalated"]
    },
    "communications": {
        "channel": ["SMS", "WhatsApp", "email"]
    },
    "documents": {
        "status": [
            "draft", "submitted", "in review",
            "approved", "rejected", "returned", "closed"
        ]
    },
    "approval_steps": {
        "decision": ["approved", "rejected", "returned", "escalated"]
    }
}


# ------------------------------------------------------------
# 5. LOAD DATASET
# ------------------------------------------------------------

def load_dataset(table_name):

    file_path = RAW_DATA_DIR / f"{table_name}.csv"

    if not file_path.exists():
        return None, f"File not found: {file_path.name}"

    try:
        return pd.read_csv(file_path), None

    except Exception as error:
        return None, str(error)



# 6. CHECK REQUIRED COLUMNS


def validate_columns(df, table_name):

    return [
        column
        for column in REQUIRED_COLUMNS[table_name]
        if column not in df.columns
    ]


# ------------------------------------------------------------
# 7. CHECK DUPLICATE PRIMARY KEYS
# ------------------------------------------------------------

def validate_duplicates(df, table_name):

    keys = PRIMARY_KEYS[table_name]

    return int(df.duplicated(subset=keys).sum())


# ------------------------------------------------------------
# 8. CHECK MISSING VALUES
# ------------------------------------------------------------

def validate_missing_values(df):

    return int(df.isnull().sum().sum())


# ------------------------------------------------------------
# 9. CHECK INVALID CATEGORIES
# ------------------------------------------------------------

def validate_allowed_values(df, table_name):

    invalid_count = 0

    for column, allowed_values in ALLOWED_VALUES.get(table_name, {}).items():

        if column in df.columns:

            invalid_count += int(
                (~df[column].isin(allowed_values) & df[column].notna()).sum()
            )

    return invalid_count


# ------------------------------------------------------------
# 10. CHECK NUMERIC VALUES
# ------------------------------------------------------------

def validate_numeric_values(df, table_name):

    numeric_rules = {
        "dues_transactions": ["amount_due", "amount_paid"],
        "branches": ["steward_count"],
        "documents": ["current_version", "current_step"],
        "document_versions": ["version_number"],
        "routing_rules": ["step_number", "max_days"],
        "approval_steps": ["version_number", "step_number"]
    }

    invalid_count = 0

    for column in numeric_rules.get(table_name, []):

        if column in df.columns:

            values = pd.to_numeric(df[column], errors="coerce")

            invalid_count += int(
                (values.isna() & df[column].notna()).sum()
            )

            invalid_count += int((values < 0).sum())

    return invalid_count


# ------------------------------------------------------------
# 11. CHECK DATE FORMATS
# ------------------------------------------------------------

def validate_dates(df):

    date_columns = [
        "join_date", "exit_date", "paid_date",
        "opened_date", "closed_date", "event_date",
        "sent_at", "timestamp", "created_at",
        "closed_at", "uploaded_at", "received_at",
        "decided_at"
    ]

    invalid_count = 0

    for column in date_columns:

        if column in df.columns:

            original_values = df[column].notna()

            converted = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            invalid_count += int(
                (original_values & converted.isna()).sum()
            )

    return invalid_count


# ------------------------------------------------------------
# 12. CHECK FUTURE JOIN DATES
# ------------------------------------------------------------

def validate_future_join_dates(df, table_name):

    if table_name != "members" or "join_date" not in df.columns:
        return 0

    join_dates = pd.to_datetime(df["join_date"], errors="coerce")

    return int((join_dates > pd.Timestamp.today()).sum())



# VALIDATE ALL DATASETS


def validate_all_datasets():

    print("=" * 75)
    print("ATLAS ENTERPRISE OPERATING PLATFORM")
    print("DATA VALIDATION REPORT")
    print("=" * 75)

    report = []

    for table_name in REQUIRED_COLUMNS:

        print("\nChecking table:", table_name)

        df, error = load_dataset(table_name)

        if df is None:

            report.append({
                "table": table_name,
                "records": 0,
                "missing_columns": "Not checked",
                "duplicate_keys": 0,
                "missing_values": 0,
                "invalid_categories": 0,
                "invalid_numeric_values": 0,
                "invalid_dates": 0,
                "future_join_dates": 0,
                "result": "FILE ERROR",
                "details": error
            })

            print("FILE ERROR:", error)
            continue

        missing_columns = validate_columns(df, table_name)

        if missing_columns:

            report.append({
                "table": table_name,
                "records": len(df),
                "missing_columns": ", ".join(missing_columns),
                "duplicate_keys": 0,
                "missing_values": 0,
                "invalid_categories": 0,
                "invalid_numeric_values": 0,
                "invalid_dates": 0,
                "future_join_dates": 0,
                "result": "MISSING COLUMNS",
                "details": "Other checks skipped"
            })

            print("MISSING COLUMNS:", missing_columns)
            continue

        duplicates = validate_duplicates(df, table_name)
        missing = validate_missing_values(df)
        invalid_categories = validate_allowed_values(df, table_name)
        invalid_numeric = validate_numeric_values(df, table_name)
        invalid_dates = validate_dates(df)
        future_dates = validate_future_join_dates(df, table_name)

        result = (
            "PASS"
            if duplicates == 0
            and invalid_categories == 0
            and invalid_numeric == 0
            and invalid_dates == 0
            and future_dates == 0
            else "REVIEW"
        )

        report.append({
            "table": table_name,
            "records": len(df),
            "missing_columns": "None",
            "duplicate_keys": duplicates,
            "missing_values": missing,
            "invalid_categories": invalid_categories,
            "invalid_numeric_values": invalid_numeric,
            "invalid_dates": invalid_dates,
            "future_join_dates": future_dates,
            "result": result,
            "details": ""
        })

        print("Records:", len(df))
        print("Duplicate keys:", duplicates)
        print("Missing values:", missing)
        print("Invalid categories:", invalid_categories)
        print("Invalid numeric values:", invalid_numeric)
        print("Invalid dates:", invalid_dates)
        print("Future join dates:", future_dates)
        print("Result:", result)

    # --------------------------------------------------------
    # 14. CREATE VALIDATION REPORT
    # --------------------------------------------------------

    report_df = pd.DataFrame(report)

    report_path = REPORTS_DIR / "data_validation_report.csv"

    report_df.to_csv(report_path, index=False)

    print("\n" + "=" * 75)
    print("VALIDATION SUMMARY")
    print("=" * 75)

    if not report_df.empty:

        print("\nTables checked:", len(report_df))
        print("Passed:", (report_df["result"] == "PASS").sum())
        print("Need review:", (report_df["result"] == "REVIEW").sum())
        print("File errors:", (report_df["result"] == "FILE ERROR").sum())

        print("\nFULL SUMMARY:")
        print(report_df.to_string(index=False))

    print("\nReport saved to:")
    print(report_path)

    print("\nDATA VALIDATION COMPLETED")
    print("=" * 75)

    return report_df


# ------------------------------------------------------------
# 15. RUN PROGRAM
# ------------------------------------------------------------

if __name__ == "__main__":

    validation_results = validate_all_datasets()