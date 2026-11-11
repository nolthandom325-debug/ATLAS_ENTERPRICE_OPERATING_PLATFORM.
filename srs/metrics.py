
# ATLAS ENTERPRISE OPERATING PLATFORM
# BUSINESS METRICS AND PERFORMANCE ANALYSIS
# Legasis (Pty) Ltd


from pathlib import Path
import pandas as pd
import numpy as np


#  PROJECT DIRECTORIES


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)



# 2. LOAD DATASETS


def load_dataset(file_name):

    file_path = RAW_DATA_DIR / file_name

    if not file_path.exists():
        print(f"WARNING: {file_name} was not found.")
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)

    except Exception as error:
        print(f"ERROR loading {file_name}: {error}")
        return pd.DataFrame()



# 3. LOAD ALL REQUIRED DATA


def load_all_data():

    print("\nLoading Atlas datasets...")

    data = {
        "members": load_dataset("members.csv"),
        "dues": load_dataset("dues_transactions.csv"),
        "cases": load_dataset("cases.csv"),
        "events": load_dataset("engagement_events.csv"),
        "branches": load_dataset("branches.csv"),
        "employers": load_dataset("employers.csv")
    }

    for table_name, df in data.items():
        print(f"{table_name}: {len(df)} records loaded")

    return data



#  PREPARE DATE COLUMNS


def prepare_dates(data):

    date_columns = {
        "members": ["join_date", "exit_date"],
        "dues": ["paid_date"],
        "cases": ["opened_date", "closed_date"],
        "events": ["event_date"]
    }

    for table_name, columns in date_columns.items():

        df = data[table_name]

        for column in columns:

            if column in df.columns:
                df[column] = pd.to_datetime(
                    df[column],
                    errors="coerce"
                )

    return data


#  MEMBERSHIP METRICS


def calculate_membership_metrics(members):

    print("\nCalculating membership metrics...")

    if members.empty:
        return pd.DataFrame()

    members["status"] = (
        members["status"].astype(str).str.strip().str.lower()
    )

    total_members = len(members)

    active_members = int(
        (members["status"] == "active").sum()
    )

    lapsed_members = int(
        (members["status"] == "lapsed").sum()
    )

    suspended_members = int(
        (members["status"] == "suspended").sum()
    )

    resigned_members = int(
        (members["status"] == "resigned").sum()
    )

    deceased_members = int(
        (members["status"] == "deceased").sum()
    )

    metrics = {
        "metric": [
            "Total members",
            "Active members",
            "Lapsed members",
            "Suspended members",
            "Resigned members",
            "Deceased members"
        ],
        "value": [
            total_members,
            active_members,
            lapsed_members,
            suspended_members,
            resigned_members,
            deceased_members
        ]
    }

    result = pd.DataFrame(metrics)

    return result



# 6. MONTHLY MEMBERSHIP GROWTH


def calculate_membership_growth(members):

    print("\nCalculating monthly membership growth...")

    if members.empty or "join_date" not in members.columns:
        return pd.DataFrame()

    joins = (
        members.dropna(subset=["join_date"])
        .groupby(members["join_date"].dt.to_period("M"))
        .size()
        .rename("new_members")
    )

    exits = pd.Series(dtype="int64")

    if "exit_date" in members.columns:

        exits = (
            members.dropna(subset=["exit_date"])
            .groupby(members.dropna(subset=["exit_date"])["exit_date"].dt.to_period("M"))
            .size()
            .rename("members_exited")
        )

    monthly = pd.concat([joins, exits], axis=1).fillna(0)

    monthly["new_members"] = monthly["new_members"].astype(int)
    monthly["members_exited"] = monthly["members_exited"].astype(int)

    monthly["net_growth"] = (
        monthly["new_members"] - monthly["members_exited"]
    )

    monthly["opening_members"] = (
        total_members_at_start(members, monthly.index)
    )

    monthly["churn_rate_percent"] = np.where(
        monthly["opening_members"] > 0,
        monthly["members_exited"] /
        monthly["opening_members"] * 100,
        0
    )

    monthly = monthly.reset_index()
    monthly.rename(columns={"index": "period"}, inplace=True)

    monthly["period"] = monthly["period"].astype(str)

    return monthly


def total_members_at_start(members, periods):

    opening_counts = []

    for period in periods:

        month_start = period.start_time

        joined_before = (
            members["join_date"].notna()
            & (members["join_date"] < month_start)
        )

        if "exit_date" in members.columns:

            not_exited = (
                members["exit_date"].isna()
                | (members["exit_date"] >= month_start)
            )

        else:
            not_exited = pd.Series(True, index=members.index)

        opening_counts.append(
            int((joined_before & not_exited).sum())
        )

    return opening_counts
#MEMBERSHIP DUES AND ARREARS


def calculate_dues_metrics(dues):

    print("\nCalculating dues collection metrics...")

    if dues.empty:
        return pd.DataFrame()

    dues["amount_due"] = pd.to_numeric(
        dues["amount_due"], errors="coerce"
    ).fillna(0)

    dues["amount_paid"] = pd.to_numeric(
        dues["amount_paid"], errors="coerce"
    ).fillna(0)

    total_due = dues["amount_due"].sum()
    total_paid = dues["amount_paid"].sum()

    arrears = (dues["amount_due"] - dues["amount_paid"]).clip(lower=0)

    total_arrears = arrears.sum()

    collection_rate = (
        total_paid / total_due * 100
        if total_due > 0 else 0
    )

    arrears_rate = (
        total_arrears / total_due * 100
        if total_due > 0 else 0
    )

    unpaid_transactions = int(
        (dues["amount_paid"] < dues["amount_due"]).sum()
    )

    average_arrears = (
        total_arrears / unpaid_transactions
        if unpaid_transactions > 0 else 0
    )

    result = pd.DataFrame({
        "metric": [
            "Total dues expected",
            "Total dues collected",
            "Total outstanding arrears",
            "Dues collection rate (%)",
            "Arrears rate (%)",
            "Transactions with outstanding dues",
            "Average arrears per outstanding transaction"
        ],
        "value": [
            round(total_due, 2),
            round(total_paid, 2),
            round(total_arrears, 2),
            round(collection_rate, 2),
            round(arrears_rate, 2),
            unpaid_transactions,
            round(average_arrears, 2)
        ]
    })

    return result



# 8. MONTHLY DUES PERFORMANCE


def calculate_monthly_dues(dues):

    print("\nCalculating monthly dues performance...")

    if dues.empty or "period" not in dues.columns:
        return pd.DataFrame()

    dues = dues.copy()

    dues["amount_due"] = pd.to_numeric(
        dues["amount_due"], errors="coerce"
    ).fillna(0)

    dues["amount_paid"] = pd.to_numeric(
        dues["amount_paid"], errors="coerce"
    ).fillna(0)

    monthly = dues.groupby("period").agg(
        total_due=("amount_due", "sum"),
        total_paid=("amount_paid", "sum"),
        transactions=("txn_id", "count")
    ).reset_index()

    monthly["arrears"] = (
        monthly["total_due"] - monthly["total_paid"]
    ).clip(lower=0)

    monthly["collection_rate_percent"] = np.where(
        monthly["total_due"] > 0,
        monthly["total_paid"] / monthly["total_due"] * 100,
        0
    )

    return monthly



# EMPLOYER DUES PERFORMANCE


def calculate_employer_metrics(dues, members, employers):

    print("\nCalculating employer dues performance...")

    if dues.empty or members.empty:
        return pd.DataFrame()

    if "employer_id" not in members.columns:
        return pd.DataFrame()

    employer_dues = dues.merge(
        members[["member_id", "employer_id"]],
        on="member_id",
        how="left"
    )

    employer_dues["amount_due"] = pd.to_numeric(
        employer_dues["amount_due"], errors="coerce"
    ).fillna(0)

    employer_dues["amount_paid"] = pd.to_numeric(
        employer_dues["amount_paid"], errors="coerce"
    ).fillna(0)

    result = employer_dues.groupby("employer_id").agg(
        total_due=("amount_due", "sum"),
        total_paid=("amount_paid", "sum")
    ).reset_index()

    result["outstanding_amount"] = (
        result["total_due"] - result["total_paid"]
    ).clip(lower=0)

    result["collection_rate_percent"] = np.where(
        result["total_due"] > 0,
        result["total_paid"] / result["total_due"] * 100,
        0
    )

    if not employers.empty and "employer_id" in employers.columns:

        result = result.merge(
            employers[["employer_id", "employer_name"]],
            on="employer_id",
            how="left"
        )

    return result



# CASE PERFORMANCE METRICS


def calculate_case_metrics(cases):

    print("\nCalculating case performance metrics...")

    if cases.empty:
        return pd.DataFrame()

    cases = cases.copy()

    cases["status"] = (
        cases["status"].astype(str).str.strip().str.lower()
    )

    total_cases = len(cases)

    open_cases = int(
        cases["status"].isin(["open", "in progress", "escalated"]).sum()
    )

    closed_cases = cases[
        cases["status"] == "closed"
    ].copy()

    resolved_cases = len(closed_cases)

    if (
        not closed_cases.empty
        and "opened_date" in closed_cases.columns
        and "closed_date" in closed_cases.columns
    ):

        resolution_days = (
            closed_cases["closed_date"] -
            closed_cases["opened_date"]
        ).dt.days

        resolution_days = resolution_days.dropna()

        median_resolution_days = (
            resolution_days.median()
            if not resolution_days.empty else 0
        )

    else:
        median_resolution_days = 0

    outcomes = (
        cases["outcome"].astype(str).str.strip().str.lower()
        if "outcome" in cases.columns
        else pd.Series(dtype="object")
    )

    successful_cases = int(
        outcomes.isin(["won", "settled"]).sum()
    )

    decided_cases = int(
        outcomes.isin(["won", "lost", "settled", "withdrawn"]).sum()
    )

    success_rate = (
        successful_cases / decided_cases * 100
        if decided_cases > 0 else 0
    )

    result = pd.DataFrame({
        "metric": [
            "Total cases",
            "Open or ongoing cases",
            "Closed cases",
            "Median case resolution days",
            "Successful cases (won or settled)",
            "Case win and settlement rate (%)"
        ],
        "value": [
            total_cases,
            open_cases,
            resolved_cases,
            round(median_resolution_days, 2),
            successful_cases,
            round(success_rate, 2)
        ]
    })

    return result



# 11. BRANCH ACTIVITY METRICS


def calculate_branch_activity(events, branches, members):

    print("\nCalculating branch activity...")

    if events.empty or branches.empty:
        return pd.DataFrame()

    activity = events.groupby("branch_id").agg(
        total_events=("event_id", "count"),
        attendance_count=("attended", "sum")
    ).reset_index()

    activity["attendance_rate_percent"] = np.where(
        activity["total_events"] > 0,
        activity["attendance_count"] /
        activity["total_events"] * 100,
        0
    )

    activity = branches[
        ["branch_id", "branch_name"]
    ].merge(
        activity,
        on="branch_id",
        how="left"
    )

    activity[["total_events", "attendance_count"]] = (
        activity[["total_events", "attendance_count"]]
        .fillna(0)
    )

    activity["attendance_rate_percent"] = (
        activity["attendance_rate_percent"].fillna(0)
    )

    if not members.empty and "branch_id" in members.columns:

        active = members[
            members["status"].astype(str).str.lower() == "active"
        ]

        active_counts = (
            active.groupby("branch_id")
            .size()
            .rename("active_members")
            .reset_index()
        )

        activity = activity.merge(
            active_counts,
            on="branch_id",
            how="left"
        )

        activity["active_members"] = (
            activity["active_members"].fillna(0)
        )

    else:
        activity["active_members"] = 0

    # This is an attendance-rate indicator, not an overall
    # assessment of branch performance.
    activity["branch_activity_score"] = (
        activity["attendance_rate_percent"].round(2)
    )

    return activity



# 12. SAVE METRICS REPORTS

def save_report(df, file_name):

    if df is not None and not df.empty:

        output_path = REPORTS_DIR / file_name

        df.to_csv(output_path, index=False)

        print("Saved:", output_path)


#
# 13. RUN ALL METRICS


def run_metrics():

    print("\n" + "=" * 70)
    print("ATLAS ENTERPRISE OPERATING PLATFORM")
    print("BUSINESS METRICS ANALYSIS")
    print("=" * 70)

    data = load_all_data()

    data = prepare_dates(data)

    membership = calculate_membership_metrics(
        data["members"]
    )

    growth = calculate_membership_growth(
        data["members"]
    )

    dues = calculate_dues_metrics(
        data["dues"]
    )

    monthly_dues = calculate_monthly_dues(
        data["dues"]
    )

    employers = calculate_employer_metrics(
        data["dues"],
        data["members"],
        data["employers"]
    )

    cases = calculate_case_metrics(
        data["cases"]
    )

    branches = calculate_branch_activity(
        data["events"],
        data["branches"],
        data["members"]
    )

    print("\nSaving reports...")

    save_report(membership, "membership_metrics.csv")
    save_report(growth, "membership_growth.csv")
    save_report(dues, "dues_metrics.csv")
    save_report(monthly_dues, "monthly_dues_metrics.csv")
    save_report(employers, "employer_dues_metrics.csv")
    save_report(cases, "case_metrics.csv")
    save_report(branches, "branch_activity_metrics.csv")

    print("\n" + "=" * 70)
    print("ATLAS METRICS SUMMARY")
    print("=" * 70)

    print("\nMEMBERSHIP METRICS:")
    print(membership.to_string(index=False))

    print("\nDUES METRICS:")
    print(dues.to_string(index=False))

    print("\nCASE METRICS:")
    print(cases.to_string(index=False))

    print("\nBRANCH ACTIVITY:")
    print(branches.head(10).to_string(index=False))

    print("\n" + "=" * 70)
    print("METRICS ANALYSIS COMPLETED")
    print("Reports saved in data/reports/")
    print("=" * 70)


#  PROGRAM ENTRY POINT


if __name__ == "__main__":

    run_metrics()