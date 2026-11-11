from pathlib import Path
import pandas as pd

print("ATLAS TEST STARTED")

# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Find the raw data folder
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Find members.csv
file_path = RAW_DATA_DIR / "members.csv"

print("Looking for:", file_path)
print("Does the file exist?", file_path.exists())

if file_path.exists():
    members_df = pd.read_csv(file_path)

    print("\nSUCCESS! MEMBERS DATASET LOADED")
    print("Number of records:", len(members_df))

    print("\nFirst five records:")
    print(members_df.head())
else:
    print("ERROR: members.csv was not found.")