import pandas as pd


def test_missing_values_are_detected():
    data = pd.DataFrame({
        "member_id": [1, 2, 3],
        "name": ["John", None, "Sarah"]
    })

    assert data.isnull().sum().sum() == 1


def test_duplicate_records_are_detected():
    data = pd.DataFrame({
        "member_id": [1, 2, 2, 3],
        "name": ["John", "Mary", "Mary", "Peter"]
    })

    assert data.duplicated().sum() == 1


def test_invalid_dates_are_detected():
    dates = pd.Series([
        "2026-01-10",
        "2026-02-15",
        "invalid_date"
    ])

    converted_dates = pd.to_datetime(
        dates,
        errors="coerce"
    )

    assert converted_dates.isnull().sum() == 1


def test_invalid_numeric_values_are_detected():
    values = pd.Series(["100", "200", "invalid", "400"])

    converted_values = pd.to_numeric(
        values,
        errors="coerce"
    )

    assert converted_values.isnull().sum() == 1


def test_invalid_categories_are_detected():
    data = pd.DataFrame({
        "status": ["Active", "Inactive", "Unknown"]
    })

    valid_categories = ["Active", "Inactive"]

    invalid_values = ~data["status"].isin(valid_categories)

    assert invalid_values.sum() == 1