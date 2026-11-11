# ============================================================
# ATLAS ENTERPRISE OPERATING PLATFORM
# DOCUMENT ROUTING AND INTEGRITY CHECKS
# Legasis (Pty) Ltd
# ============================================================

from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. PROJECT DIRECTORIES
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# 2. LOAD DATASETS
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# 3. LOAD ROUTING DATA
# ------------------------------------------------------------

def load_routing_data():

    print("\nLoading document routing datasets...")

    data = {
        "documents": load_dataset("documents.csv"),
        "approval_steps": load_dataset("approval_steps.csv"),
        "routing_rules": load_dataset("routing_rules.csv"),
        "document_versions": load_dataset("document_versions.csv"),
        "users": load_dataset("users.csv")
    }

    for table_name, df in data.items():
        print(f"{table_name}: {len(df)} records loaded")

    return data


# ------------------------------------------------------------
# 4. CHECK REQUIRED COLUMNS
# ------------------------------------------------------------

REQUIRED_COLUMNS = {

    "documents": [
        "document_id",
        "document_type",
        "current_version",
        "status",
        "current_step",
        "final_destination",
        "created_at",
        "closed_at"
    ],

    "approval_steps": [
        "step_id",
        "document_id",
        "version_number",
        "step_number",
        "level",
        "assigned_to",
        "received_at",
        "decided_at",
        "decision"
    ],

    "routing_rules": [
        "document_type",
        "step_number",
        "level",
        "approver_role",
        "max_days"
    ],

    "document_versions": [
        "document_id",
        "version_number",
        "file_hash",
        "uploaded_by",
        "uploaded_at"
    ],

    "users": [
        "user_id",
        "role",
        "active"
    ]
}


def check_required_columns(data):

    print("\nChecking required routing columns...")

    results = {}

    for table_name, required in REQUIRED_COLUMNS.items():

        df = data[table_name]

        if df.empty:
            results[table_name] = False
            print(f"{table_name}: EMPTY OR MISSING")
            continue

        missing = [
            column for column in required
            if column not in df.columns
        ]

        if missing:
            results[table_name] = False
            print(f"{table_name}: Missing columns {missing}")

        else:
            results[table_name] = True
            print(f"{table_name}: All required columns found")

    return results


# ------------------------------------------------------------
# 5. PREPARE DATE COLUMNS
# ------------------------------------------------------------

def prepare_routing_dates(data):

    date_columns = {

        "documents": ["created_at", "closed_at"],

        "approval_steps": [
            "received_at",
            "decided_at"
        ],

        "document_versions": [
            "uploaded_at"
        ]
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


# ------------------------------------------------------------
# 6. CHECK ORPHAN APPROVAL STEPS
# ------------------------------------------------------------

def check_orphan_approval_steps(documents, approvals):

    print("\nChecking orphan approval steps...")

    if documents.empty or approvals.empty:
        return pd.DataFrame()

    document_ids = set(documents["document_id"].dropna())

    orphan_steps = approvals[
        ~approvals["document_id"].isin(document_ids)
    ].copy()

    if not orphan_steps.empty:
        orphan_steps["issue"] = "Approval step has no matching document"

    print("Orphan approval steps:", len(orphan_steps))

    return orphan_steps


# ------------------------------------------------------------
# 7. CHECK DOCUMENTS WITHOUT APPROVAL STEPS
# ------------------------------------------------------------

def check_documents_without_steps(documents, approvals):

    print("\nChecking documents without approval steps...")

    if documents.empty:
        return pd.DataFrame()

    documents_with_steps = set(
        approvals["document_id"].dropna()
    ) if not approvals.empty else set()

    missing_steps = documents[
        ~documents["document_id"].isin(documents_with_steps)
    ].copy()

    missing_steps["issue"] = "Document has no approval steps"

    print("Documents without approval steps:", len(missing_steps))

    return missing_steps


# ------------------------------------------------------------
# 8. CHECK APPROVAL SEQUENCE
# ------------------------------------------------------------

def check_approval_sequence(documents, approvals, rules):

    print("\nChecking approval sequences...")

    issues = []

    if documents.empty or approvals.empty or rules.empty:
        return pd.DataFrame()

    for _, document in documents.iterrows():

        document_id = document["document_id"]
        document_type = document["document_type"]

        expected = rules[
            rules["document_type"] == document_type
        ].copy()

        actual = approvals[
            approvals["document_id"] == document_id
        ].copy()

        if expected.empty:
            issues.append({
                "document_id": document_id,
                "issue": "No routing rule exists for document type"
            })
            continue

        expected = expected.sort_values("step_number")
        actual = actual.sort_values("step_number")

        expected_steps = expected["step_number"].tolist()
        actual_steps = actual["step_number"].tolist()

        # Detect approval steps that do not exist in the route.
        unexpected = [
            step for step in actual_steps
            if step not in expected_steps
        ]

        if unexpected:
            issues.append({
                "document_id": document_id,
                "issue": f"Unexpected approval steps: {unexpected}"
            })

        # Detect missing steps in a completed route.
        if str(document.get("status", "")).lower() in [
            "approved", "closed"
        ]:

            missing = [
                step for step in expected_steps
                if step not in actual_steps
            ]

            if missing:
                issues.append({
                    "document_id": document_id,
                    "issue": f"Completed document is missing steps: {missing}"
                })

        # Check that completed steps follow the required order.
        decided = actual[
            actual["decision"].astype(str).str.lower().eq("approved")
        ]

        decided_steps = decided["step_number"].tolist()

        if decided_steps != sorted(decided_steps):

            issues.append({
                "document_id": document_id,
                "issue": "Approval steps are not in sequence"
            })

    print("Sequence issues:", len(issues))

    return pd.DataFrame(issues)


# ------------------------------------------------------------
# 9. CHECK WRONG APPROVAL LEVELS
# ------------------------------------------------------------

def check_approval_levels(approvals, rules):

    print("\nChecking approval levels...")

    issues = []

    if approvals.empty or rules.empty:
        return pd.DataFrame()

    for _, approval in approvals.iterrows():

        matching_rule = rules[
            (rules["step_number"] == approval["step_number"])
            & (
                rules["document_type"]
                == get_document_type(
                    approval["document_id"],
                    None
                )
            )
        ]

        # Document type is checked in the main route check.
        # This function checks the level against matching
        # step numbers for each available rule.

        if matching_rule.empty:
            continue

        matching_levels = (
            matching_rule["level"].astype(str).str.lower().tolist()
        )

        actual_level = str(approval["level"]).lower()

        if actual_level not in matching_levels:

            issues.append({
                "document_id": approval["document_id"],
                "step_number": approval["step_number"],
                "issue": "Approval level does not match routing rule"
            })

    print("Approval level issues:", len(issues))

    return pd.DataFrame(issues)


def get_document_type(document_id, documents):

    if documents is None or documents.empty:
        return None

    matching = documents[
        documents["document_id"] == document_id
    ]

    if matching.empty:
        return None

    return matching.iloc[0]["document_type"]


# ------------------------------------------------------------
# 10. CHECK ASSIGNED USERS
# ------------------------------------------------------------

def check_assigned_users(approvals, users):

    print("\nChecking assigned approval users...")

    issues = []

    if approvals.empty:
        return pd.DataFrame()

    if users.empty:
        return pd.DataFrame([{
            "issue": "Users dataset is empty; assignments cannot be checked"
        }])

    valid_users = set(users["user_id"].dropna())

    active_users = set(
        users.loc[
            users["active"].astype(str).str.lower().isin(
                ["true", "1", "yes"]
            ),
            "user_id"
        ].dropna()
    )

    for _, approval in approvals.iterrows():

        assigned_to = approval["assigned_to"]

        if pd.isna(assigned_to) or assigned_to not in valid_users:

            issues.append({
                "document_id": approval["document_id"],
                "step_number": approval["step_number"],
                "issue": "Assigned user does not exist"
            })

        elif assigned_to not in active_users:

            issues.append({
                "document_id": approval["document_id"],
                "step_number": approval["step_number"],
                "issue": "Assigned user is not active"
            })

    print("Assignment issues:", len(issues))

    return pd.DataFrame(issues)


# ------------------------------------------------------------
# 11. CHECK OVERDUE APPROVALS
# ------------------------------------------------------------

def check_overdue_approvals(approvals, rules):

    print("\nChecking overdue approvals...")

    if approvals.empty or rules.empty:
        return pd.DataFrame()

    current_time = pd.Timestamp.now()

    pending = approvals[
        approvals["decision"].isna()
        | approvals["decision"].astype(str).str.strip().str.lower().isin(
            ["", "pending", "nan"]
        )
    ].copy()

    if pending.empty:
        return pd.DataFrame()

    pending = pending.merge(
        rules[["step_number", "level", "max_days"]],
        on=["step_number", "level"],
        how="left",
        suffixes=("", "_rule")
    )

    pending["received_at"] = pd.to_datetime(
        pending["received_at"],
        errors="coerce"
    )

    pending["max_days"] = pd.to_numeric(
        pending["max_days"],
        errors="coerce"
    )

    pending["days_waiting"] = (
        current_time - pending["received_at"]
    ).dt.days

    pending["overdue"] = (
        pending["days_waiting"] > pending["max_days"]
    )

    overdue = pending[
        pending["overdue"] == True
    ].copy()

    overdue["issue"] = "Approval has exceeded its allowed time"

    print("Overdue approvals:", len(overdue))

    return overdue


# ------------------------------------------------------------
# 12. CHECK DOCUMENT VERSION INTEGRITY
# ------------------------------------------------------------

def check_document_versions(documents, versions):

    print("\nChecking document versions...")

    issues = []

    if documents.empty or versions.empty:
        return pd.DataFrame()

    for _, document in documents.iterrows():

        document_id = document["document_id"]

        matching_versions = versions[
            versions["document_id"] == document_id
        ]

        if matching_versions.empty:

            issues.append({
                "document_id": document_id,
                "issue": "Document has no version history"
            })

            continue

        current_version = document["current_version"]

        version_numbers = matching_versions["version_number"].tolist()

        if current_version not in version_numbers:

            issues.append({
                "document_id": document_id,
                "issue": "Current document version is missing"
            })

    print("Version issues:", len(issues))

    return pd.DataFrame(issues)


# ------------------------------------------------------------
# 13. CHECK DUPLICATE FILE HASHES
# ------------------------------------------------------------

def check_duplicate_file_hashes(versions):

    print("\nChecking duplicate file hashes...")

    if versions.empty or "file_hash" not in versions.columns:
        return pd.DataFrame()

    valid_hashes = versions[
        versions["file_hash"].notna()
        & (versions["file_hash"].astype(str).str.strip() != "")
    ]

    hash_counts = (
        valid_hashes.groupby("file_hash")["document_id"]
        .nunique()
    )

    duplicate_hashes = hash_counts[
        hash_counts > 1
    ].index

    duplicates = valid_hashes[
        valid_hashes["file_hash"].isin(duplicate_hashes)
    ].copy()

    if not duplicates.empty:
        duplicates["issue"] = "Same file hash used by different documents"

    print("Duplicate file hash records:", len(duplicates))

    return duplicates


# ------------------------------------------------------------
# 14. CHECK CLOSED DOCUMENTS
# ------------------------------------------------------------

def check_closed_documents(documents, approvals):

    print("\nChecking closed documents...")

    issues = []

    if documents.empty:
        return pd.DataFrame()

    for _, document in documents.iterrows():

        if str(document["status"]).strip().lower() != "closed":
            continue

        document_id = document["document_id"]

        if pd.isna(document["closed_at"]):

            issues.append({
                "document_id": document_id,
                "issue": "Closed document has no closing date"
            })

        matching = approvals[
            approvals["document_id"] == document_id
        ] if not approvals.empty else pd.DataFrame()

        if matching.empty:

            issues.append({
                "document_id": document_id,
                "issue": "Closed document has no approval history"
            })

            continue

        decisions = (
            matching["decision"].astype(str).str.strip().str.lower()
        )

        if "approved" not in decisions.values:

            issues.append({
                "document_id": document_id,
                "issue": "Closed document has no approved step"
            })

    print("Closed document issues:", len(issues))

    return pd.DataFrame(issues)


# ------------------------------------------------------------
# 15. CHECK DUPLICATE APPROVAL STEPS
# ------------------------------------------------------------

def check_duplicate_approval_steps(approvals):

    print("\nChecking duplicate approval steps...")

    if approvals.empty:
        return pd.DataFrame()

    duplicates = approvals[
        approvals.duplicated(
            subset=[
                "document_id",
                "version_number",
                "step_number"
            ],
            keep=False
        )
    ].copy()

    if not duplicates.empty:
        duplicates["issue"] = "Duplicate approval step for document version"

    print("Duplicate approval steps:", len(duplicates))

    return duplicates


# ------------------------------------------------------------
# 16. SAVE INDIVIDUAL REPORTS
# ------------------------------------------------------------

def save_report(df, file_name):

    if df is not None and not df.empty:

        output_path = REPORTS_DIR / file_name

        df.to_csv(output_path, index=False)

        print("Report saved:", output_path)


# ------------------------------------------------------------
# 17. RUN DOCUMENT ROUTING CHECKS
# ------------------------------------------------------------

def run_document_routing_checks():

    print("\n" + "=" * 75)
    print("ATLAS ENTERPRISE OPERATING PLATFORM")
    print("DOCUMENT ROUTING INTEGRITY REPORT")
    print("=" * 75)

    data = load_routing_data()

    column_results = check_required_columns(data)

    if not all(column_results.values()):

        print("\nROUTING CHECKS STOPPED.")
        print("One or more datasets are empty or missing required columns.")
        print("Check the messages above before continuing.")

        return

    data = prepare_routing_dates(data)

    documents = data["documents"]
    approvals = data["approval_steps"]
    rules = data["routing_rules"]
    versions = data["document_versions"]
    users = data["users"]

    # Run all integrity checks.

    orphan_steps = check_orphan_approval_steps(
        documents, approvals
    )

    documents_without_steps = check_documents_without_steps(
        documents, approvals
    )

    sequence_issues = check_approval_sequence(
        documents, approvals, rules
    )

    level_issues = check_approval_levels(
        approvals, rules
    )

    assignment_issues = check_assigned_users(
        approvals, users
    )

    overdue_approvals = check_overdue_approvals(
        approvals, rules
    )

    version_issues = check_document_versions(
        documents, versions
    )

    duplicate_hashes = check_duplicate_file_hashes(
        versions
    )

    closed_document_issues = check_closed_documents(
        documents, approvals
    )

    duplicate_steps = check_duplicate_approval_steps(
        approvals
    )

    # Save individual reports.

    save_report(orphan_steps, "orphan_approval_steps.csv")

    save_report(
        documents_without_steps,
        "documents_without_approval_steps.csv"
    )

    save_report(sequence_issues, "approval_sequence_issues.csv")

    save_report(level_issues, "approval_level_issues.csv")

    save_report(assignment_issues, "approval_assignment_issues.csv")

    save_report(overdue_approvals, "overdue_approvals.csv")

    save_report(version_issues, "document_version_issues.csv")

    save_report(duplicate_hashes, "duplicate_file_hashes.csv")

    save_report(
        closed_document_issues,
        "closed_document_issues.csv"
    )

    save_report(duplicate_steps, "duplicate_approval_steps.csv")

    # Create overall summary.

    report_summary = pd.DataFrame({

        "check": [
            "Orphan approval steps",
            "Documents without approval steps",
            "Approval sequence issues",
            "Approval level issues",
            "Assignment issues",
            "Overdue approvals",
            "Document version issues",
            "Duplicate file hashes",
            "Closed document issues",
            "Duplicate approval steps"
        ],

        "issues_found": [
            len(orphan_steps),
            len(documents_without_steps),
            len(sequence_issues),
            len(level_issues),
            len(assignment_issues),
            len(overdue_approvals),
            len(version_issues),
            len(duplicate_hashes),
            len(closed_document_issues),
            len(duplicate_steps)
        ]
    })

    summary_path = REPORTS_DIR / "document_routing_summary.csv"

    report_summary.to_csv(summary_path, index=False)

    # Display final results.

    print("\n" + "=" * 75)
    print("DOCUMENT ROUTING SUMMARY")
    print("=" * 75)

    print(report_summary.to_string(index=False))

    total_issues = int(report_summary["issues_found"].sum())

    print("\nTotal issues found:", total_issues)

    if total_issues == 0:
        print("ROUTING STATUS: NO ISSUES DETECTED")
    else:
        print("ROUTING STATUS: REVIEW REQUIRED")

    print("\nSummary saved to:", summary_path)

    print("\nDOCUMENT ROUTING CHECKS COMPLETED")

    print("=" * 75)



#  PROGRAM ENTRY POINT


if __name__ == "__main__":

    run_document_routing_checks()