from pathlib import Path
import pandas as pd


def get_project_root():
    return Path(__file__).resolve().parent.parent


def test_data_folders_exist():
    project_root = get_project_root()

    assert (project_root / "data" / "raw").is_dir()
    assert (project_root / "data" / "processed").is_dir()


def test_csv_datasets_exist():
    project_root = get_project_root()
    data_folder = project_root / "data"

    csv_files = list(data_folder.rglob("*.csv"))

    assert len(csv_files) > 0, "No CSV datasets were found."


def test_csv_datasets_are_readable():
    project_root = get_project_root()
    data_folder = project_root / "data"

    csv_files = list(data_folder.rglob("*.csv"))

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)

        assert not df.empty, (
            f"Dataset is empty: {csv_file.name}"
        )


def test_csv_datasets_have_columns():
    project_root = get_project_root()
    data_folder = project_root / "data"

    csv_files = list(data_folder.rglob("*.csv"))

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)

        assert len(df.columns) > 0, (
            f"Dataset has no columns: {csv_file.name}"
        )