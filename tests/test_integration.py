from pathlib import Path
import pandas as pd


def get_project_root():
    return Path(__file__).resolve().parent.parent


def test_raw_data_integrity():
    project_root = get_project_root()
    raw_folder = project_root / "data" / "raw"

    csv_files = list(raw_folder.glob("*.csv"))

    assert len(csv_files) > 0, "No raw CSV files found."

    for file in csv_files:
        df = pd.read_csv(file)
        assert not df.empty, f"Empty raw dataset: {file.name}"


def test_processed_data_integrity():
    project_root = get_project_root()
    processed_folder = project_root / "data" / "processed"

    csv_files = list(processed_folder.glob("*.csv"))

    assert len(csv_files) > 0, "No processed CSV files found."

    for file in csv_files:
        df = pd.read_csv(file)
        assert not df.empty, f"Empty processed dataset: {file.name}"


def test_raw_and_processed_folders_exist():
    project_root = get_project_root()

    assert (project_root / "data" / "raw").is_dir()
    assert (project_root / "data" / "processed").is_dir()