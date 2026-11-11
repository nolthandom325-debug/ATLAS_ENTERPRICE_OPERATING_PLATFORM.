import pandas as pd
from pathlib import Path

from srs.metrics import (
    load_dataset,
    load_all_data,
    prepare_dates,
    calculate_membership_metrics,
    calculate_membership_growth,
    total_members_at_start,
    calculate_dues_metrics,
    calculate_monthly_dues,
    calculate_employer_metrics,
    calculate_case_metrics,
    calculate_branch_activity,
    save_report
)


# 1. TEST DATASET LOADING

def test_load_dataset_function():
    result = load_dataset("members.csv")
    assert isinstance(result, pd.DataFrame)


def test_load_all_data():
    data = load_all_data()

    assert isinstance(data, dict)
    assert "members" in data
    assert "dues" in data
    assert "cases" in data
    assert "events" in data
    assert "branches" in data
    assert "employers" in data


# 2. TEST DATE PREPARATION

def test_prepare_dates():
    data = {
        "members": pd.DataFrame({
            "join_date": ["2025-01-01"],
            "exit_date": ["2025-02-01"]
        }),
        "dues": pd.DataFrame({
            "paid_date": ["2025-01-15"]
        }),
        "cases": pd.DataFrame({
            "opened_date": ["2025-01-01"],
            "closed_date": ["2025-01-10"]
        }),
        "events": pd.DataFrame({
            "event_date": ["2025-01-05"]
        })
    }

    result = prepare_dates(data)

    assert pd.api.types.is_datetime64_any_dtype(
        result["members"]["join_date"]
    )


# 3. TEST MEMBERSHIP METRICS

def test_calculate_membership_metrics():
    members = pd.DataFrame({
        "member_id": [1, 2, 3, 4],
        "status": ["active", "active", "lapsed", "suspended"]
    })

    result = calculate_membership_metrics(members)

    assert result.loc[0, "value"] == 4
    assert result.loc[1, "value"] == 2
    assert result.loc[2, "value"] == 1
    assert result.loc[3, "value"] == 1


def test_membership_metrics_empty_data():
    result = calculate_membership_metrics(pd.DataFrame())

    assert result.empty


# 4. TEST MEMBERSHIP GROWTH

def test_calculate_membership_growth():
    members = pd.DataFrame({
        "join_date": pd.to_datetime([
            "2025-01-01",
            "2025-01-15",
            "2025-02-10"
        ]),
        "exit_date": pd.to_datetime([
            None,
            "2025-02-05",
            None
        ])
    })

    result = calculate_membership_growth(members)

    assert not result.empty
    assert "new_members" in result.columns
    assert "members_exited" in result.columns
    assert "net_growth" in result.columns
    assert "churn_rate_percent" in result.columns


def test_total_members_at_start():
    members = pd.DataFrame({
        "join_date": pd.to_datetime([
            "2024-12-01",
            "2025-01-10"
        ]),
        "exit_date": pd.to_datetime([
            None,
            None
        ])
    })

    periods = pd.PeriodIndex(["2025-01"], freq="M")

    result = total_members_at_start(members, periods)

    assert result == [1]


# 5. TEST DUES METRICS

def test_calculate_dues_metrics():
    dues = pd.DataFrame({
        "amount_due": [100, 200, 300],
        "amount_paid": [100, 150, 200]
    })

    result = calculate_dues_metrics(dues)

    assert result.loc[0, "value"] == 600
    assert result.loc[1, "value"] == 450
    assert result.loc[2, "value"] == 150
    assert result.loc[3, "value"] == 75.0


def test_dues_metrics_empty_data():
    result = calculate_dues_metrics(pd.DataFrame())

    assert result.empty


# 6. TEST MONTHLY DUES

def test_calculate_monthly_dues():
    dues = pd.DataFrame({
        "period": ["2025-01", "2025-01", "2025-02"],
        "txn_id": [1, 2, 3],
        "amount_due": [100, 200, 300],
        "amount_paid": [100, 150, 200]
    })

    result = calculate_monthly_dues(dues)

    assert not result.empty
    assert "total_due" in result.columns
    assert "total_paid" in result.columns
    assert "arrears" in result.columns
    assert "collection_rate_percent" in result.columns

    assert result.loc[0, "total_due"] == 300
    assert result.loc[0, "total_paid"] == 250


# 7. TEST EMPLOYER METRICS

def test_calculate_employer_metrics():
    dues = pd.DataFrame({
        "member_id": [1, 2],
        "amount_due": [100, 200],
        "amount_paid": [100, 150]
    })

    members = pd.DataFrame({
        "member_id": [1, 2],
        "employer_id": [10, 10]
    })

    employers = pd.DataFrame({
        "employer_id": [10],
        "employer_name": ["ABC Company"]
    })

    result = calculate_employer_metrics(
        dues, members, employers
    )

    assert not result.empty
    assert result.loc[0, "total_due"] == 300
    assert result.loc[0, "total_paid"] == 250
    assert result.loc[0, "outstanding_amount"] == 50
    assert "employer_name" in result.columns


# 8. TEST CASE PERFORMANCE

def test_calculate_case_metrics():
    cases = pd.DataFrame({
        "status": ["closed", "open", "closed"],
        "opened_date": pd.to_datetime([
            "2025-01-01",
            "2025-01-05",
            "2025-01-10"
        ]),
        "closed_date": pd.to_datetime([
            "2025-01-11",
            None,
            "2025-01-20"
        ]),
        "outcome": ["won", "pending", "lost"]
    })

    result = calculate_case_metrics(cases)

    assert result.loc[0, "value"] == 3
    assert result.loc[1, "value"] == 1
    assert result.loc[2, "value"] == 2
    assert result.loc[3, "value"] == 10


# 9. TEST BRANCH ACTIVITY

def test_calculate_branch_activity():
    events = pd.DataFrame({
        "branch_id": [1, 1, 2],
        "event_id": [101, 102, 103],
        "attended": [1, 1, 0]
    })

    branches = pd.DataFrame({
        "branch_id": [1, 2],
        "branch_name": ["Durban", "Johannesburg"]
    })

    members = pd.DataFrame({
        "branch_id": [1, 1, 2],
        "status": ["active", "active", "lapsed"]
    })

    result = calculate_branch_activity(
        events, branches, members
    )

    assert len(result) == 2
    assert "attendance_rate_percent" in result.columns
    assert "active_members" in result.columns
    assert "branch_activity_score" in result.columns

    assert result.loc[0, "attendance_rate_percent"] == 100


# 10. TEST REPORT SAVING

def test_save_report(tmp_path, monkeypatch):
    import srs.metrics as metrics

    monkeypatch.setattr(metrics, "REPORTS_DIR", tmp_path)

    sample = pd.DataFrame({
        "metric": ["Total members"],
        "value": [100]
    })

    save_report(sample, "test_report.csv")

    saved_file = tmp_path / "test_report.csv"

    assert saved_file.exists()

    saved_data = pd.read_csv(saved_file)

    assert saved_data.loc[0, "value"] == 100