"""
ATLAS DATA SCIENCE PROJECT
 Generate supporting synthetic database tables
"""

import random
import uuid
from pathlib import Path

import pandas as pd
from faker import Faker
from datetime import date

 #PROJECT SETTINGS

RANDOM_SEED = 42
PROVINCE = "Northern Cape"

random.seed(RANDOM_SEED)
faker = Faker()
faker.seed_instance(RANDOM_SEED)



# Create a reproducible ID generator
def generate_id():
    return str(uuid.UUID(int=random.getrandbits(128), version=4))


# Find the main project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_FOLDER = PROJECT_ROOT / "data" / "raw"

# Create the folder if it does not exist
RAW_DATA_FOLDER.mkdir(parents=True, exist_ok=True)


#  GENERATE REGIONS

region_names = [
    "Frances Baard",
    "John Taolo Gaetsewe",
    "Namakwa",
    "Pixley ka Seme",
    "ZF Mgcawu"
]

regions = []

for name in region_names:
    regions.append({
        "region_id": generate_id(),
        "region_name": name,
        "province": PROVINCE
    })

regions_df = pd.DataFrame(regions)


# 3. GENERATE BRANCHES

branches = []

for _, region in regions_df.iterrows():

    for number in range(1, 5):

        branches.append({
            "branch_id": generate_id(),
            "branch_name": f"{region['region_name']} Branch {number:02d}",
            "region_id": region["region_id"],
            "province": PROVINCE,
            "steward_count": random.randint(1, 5)
        })

branches_df = pd.DataFrame(branches)



# GENERATE EMPLOYERS

sectors = [
    "Education",
    "Health",
    "Allied Workers"
]

employers = []

for number in range(1, 31):

    sector = random.choice(sectors)

    employers.append({
        "employer_id": generate_id(),
        "employer_name": f"Synthetic {sector} Employer {number:03d}",
        "sector": sector,
        "province": PROVINCE,
        "remittance_cycle": random.choice(["monthly", "irregular"])
    })

employers_df = pd.DataFrame(employers)



# GENERATE USERS

users = []

# Create stewards and branch officers for each branch
for _, branch in branches_df.iterrows():

    region_id = branch["region_id"]

    for _ in range(int(branch["steward_count"])):

        users.append({
            "user_id": generate_id(),
            "role": "steward",
            "branch_id": branch["branch_id"],
            "region_id": region_id,
            "active": True
        })

    users.append({
        "user_id": generate_id(),
        "role": "branch officer",
        "branch_id": branch["branch_id"],
        "region_id": region_id,
        "active": True
    })


# Create one regional officer for each region
for _, region in regions_df.iterrows():

    users.append({
        "user_id": generate_id(),
        "role": "regional officer",
        "branch_id": None,
        "region_id": region["region_id"],
        "active": True
    })


# Create national officers
for _ in range(2):

    users.append({
        "user_id": generate_id(),
        "role": "national officer",
        "branch_id": None,
        "region_id": None,
        "active": True
    })

users_df = pd.DataFrame(users)



# 6. SAVE THE TABLES AS CSV FILES


# GENERATE 50,000 SYNTHETIC MEMBERS

NUMBER_OF_MEMBERS = 50000

age_bands = ["18-24", "25-34", "35-44", "45-54", "55+"]

occupations = [
    "Nurse",
    "Teacher",
    "Administrator",
    "Cleaner",
    "General Worker",
    "Healthcare Assistant",
    "Clerk"
]

employment_types = ["permanent", "contract", "temporary"]

payment_methods = [
    "stop order",
    "debit order",
    "EFT",
    "cash"
]

member_statuses = [
    "active",
    "lapsed",
    "suspended",
    "resigned",
    "deceased"
]

exit_reasons = [
    "Retirement",
    "Resignation",
    "Dismissal",
    "Non-payment",
    "Other"
]

branch_ids = branches_df["branch_id"].tolist()
employer_ids = employers_df["employer_id"].tolist()

members = []
today = date.today()

for number in range(NUMBER_OF_MEMBERS):

    join_date = faker.date_between(
        start_date=date(2015, 1, 1),
        end_date=today
    )

    status = random.choices(
        member_statuses,
        weights=[75, 8, 5, 10, 2],
        k=1
    )[0]

    exit_date = None
    exit_reason = None

    if status != "active":
        exit_date = faker.date_between(
            start_date=join_date,
            end_date=today
        )
        exit_reason = random.choice(exit_reasons)

    member = {
        "member_id": generate_id(),
        "age_band": random.choice(age_bands),
        "gender": random.choice(["Female", "Male", None]),
        "join_date": join_date,
        "status": status,
        "exit_date": exit_date,
        "exit_reason": exit_reason,
        "employer_id": random.choice(employer_ids),
        "branch_id": random.choice(branch_ids),
        "occupation": random.choice(occupations),
        "employment_type": random.choice(employment_types),
        "payment_method": random.choice(payment_methods)
    }

    members.append(member)

members_df = pd.DataFrame(members)

#  GENERATE MEMBERSHIP DUES TRANSACTIONS


dues_transactions = []

payment_periods = pd.period_range(
    start="2025-01",
    end="2026-10",
    freq="M"
)

for _, member in members_df.iterrows():

    # Generate a payment record for each month
    for period in payment_periods:

        amount_due = 150.00

        # Simulate paid, partial and unpaid contributions
        payment_status = random.choices(
            ["paid", "partial", "unpaid"],
            weights=[75, 15, 10],
            k=1
        )[0]

        if payment_status == "paid":
            amount_paid = amount_due
            paid_date = faker.date_between(
                start_date=period.start_time.date(),
                end_date=period.end_time.date()
            )

        elif payment_status == "partial":
            amount_paid = round(
                random.uniform(20, 149), 2
            )
            paid_date = faker.date_between(
                start_date=period.start_time.date(),
                end_date=period.end_time.date()
            )

        else:
            amount_paid = 0.00
            paid_date = None

        dues_transactions.append({
            "txn_id": generate_id(),
            "member_id": member["member_id"],
            "period": str(period),
            "amount_due": amount_due,
            "amount_paid": amount_paid,
            "paid_date": paid_date,
            "payment_status": payment_status,
            "remittance_id": None
        })

dues_df = pd.DataFrame(dues_transactions)



# 8. GENERATE UNION CASES


case_categories = [
    "Disciplinary",
    "Unfair dismissal",
    "Wage dispute",
    "Health and safety",
    "Other"
]

case_statuses = [
    "Open",
    "In progress",
    "Closed",
    "Escalated"
]

case_outcomes = [
    "Won",
    "Lost",
    "Settled",
    "Withdrawn"
]

cases = []

steward_ids = users_df[
    users_df["role"] == "steward"
]["user_id"].tolist()

for number in range(5000):

    member = members_df.sample(1).iloc[0]

    opened_date = faker.date_between(
        start_date=date(2023, 1, 1),
        end_date=today
    )

    status = random.choice(case_statuses)

    closed_date = None
    outcome = None

    if status == "Closed":
        closed_date = faker.date_between(
            start_date=opened_date,
            end_date=today
        )
        outcome = random.choice(case_outcomes)

    case = {
        "case_id": generate_id(),
        "member_id": member["member_id"],
        "employer_id": member["employer_id"],
        "category": random.choice(case_categories),
        "opened_date": opened_date,
        "closed_date": closed_date,
        "status": status,
        "outcome": outcome,
        "steward_id": random.choice(steward_ids)
    }

    cases.append(case)

cases_df = pd.DataFrame(cases)

# 9. GENERATE MEMBER ENGAGEMENT EVENTS


event_types = [
    "Meeting",
    "Campaign",
    "Training",
    "March",
    "Vote"
]

engagement_events = []

for number in range(10000):

    member = members_df.sample(1).iloc[0]

    event = {
        "event_id": generate_id(),
        "member_id": member["member_id"],
        "branch_id": member["branch_id"],
        "event_type": random.choice(event_types),
        "event_date": faker.date_between(
            start_date=date(2024, 1, 1),
            end_date=today
        ),
        "attended": random.choice([True, False])
    }

    engagement_events.append(event)

engagement_df = pd.DataFrame(engagement_events)



# 10. GENERATE MEMBER COMMUNICATIONS


communication_channels = [
    "SMS",
    "WhatsApp",
    "Email"
]

communications = []

for number in range(10000):

    member = members_df.sample(1).iloc[0]

    sent_at = faker.date_time_between(
        start_date="-2y",
        end_date="now"
    )

    delivered = random.choice([True, False])

    opened_or_replied = (
        random.choice([True, False])
        if delivered else False
    )

    message = {
        "message_id": generate_id(),
        "member_id": member["member_id"],
        "channel": random.choice(communication_channels),
        "sent_at": sent_at,
        "delivered": delivered,
        "opened_or_replied": opened_or_replied
    }

    communications.append(message)

communications_df = pd.DataFrame(communications)


# 11. GENERATE AUDIT LOG


audit_actions = [
    "create",
    "update",
    "view",
    "export",
    "delete"
]

audit_logs = []

for number in range(10000):

    user = users_df.sample(1).iloc[0]

    log = {
        "log_id": generate_id(),
        "user_id": user["user_id"],
        "role": user["role"],
        "action": random.choice(audit_actions),
        "entity": random.choice([
            "member",
            "case",
            "dues",
            "document",
            "communication"
        ]),
        "timestamp": faker.date_time_between(
            start_date="-2y",
            end_date="now"
        )
    }

    audit_logs.append(log)

audit_df = pd.DataFrame(audit_logs)


# --------------------------------------------------
# 12. GENERATE DOCUMENTS
# --------------------------------------------------

document_types = [
    "Membership form",
    "Case file",
    "Dues dispute",
    "Resolution",
    "Report",
    "Request"
]

document_statuses = [
    "Draft",
    "Submitted",
    "In review",
    "Approved",
    "Rejected",
    "Returned",
    "Closed"
]

documents = []

for number in range(3000):

    member = members_df.sample(1).iloc[0]

    created_at = faker.date_time_between(
        start_date="-2y",
        end_date="now"
    )

    status = random.choice(document_statuses)

    closed_at = None

    if status == "Closed":
        closed_at = faker.date_time_between(
            start_date=created_at,
            end_date="now"
        )

    document = {
        "document_id": generate_id(),
        "document_type": random.choice(document_types),
        "origin_member_id": member["member_id"],
        "origin_branch_id": member["branch_id"],
        "current_version": 1,
        "status": status,
        "current_step": random.randint(1, 4),
        "final_destination": random.choice([
            "Branch",
            "Region",
            "Province",
            "National"
        ]),
        "created_at": created_at,
        "closed_at": closed_at
    }

    documents.append(document)

documents_df = pd.DataFrame(documents)

# --------------------------------------------------
# 13. GENERATE DOCUMENT VERSIONS
# --------------------------------------------------

document_versions = []

for _, document in documents_df.iterrows():

    number_of_versions = random.choices(
        [1, 2, 3],
        weights=[70, 20, 10],
        k=1
    )[0]

    for version_number in range(1, number_of_versions + 1):

        version = {
            "document_id": document["document_id"],
            "version_number": version_number,
            "file_hash": faker.sha256(),
            "uploaded_by": random.choice(
                users_df["user_id"].tolist()
            ),
            "uploaded_at": document["created_at"],
            "change_note": (
                "Original upload"
                if version_number == 1
                else "Revised document"
            )
        }

        document_versions.append(version)

document_versions_df = pd.DataFrame(document_versions)


# --------------------------------------------------
# 14. GENERATE DOCUMENT ROUTING RULES
# --------------------------------------------------

routing_rules = []

routing_levels = [
    ("branch", "steward", 3),
    ("region", "regional officer", 5),
    ("province", "provincial officer", 5),
    ("national", "national officer", 7)
]

for document_type in document_types:

    for step_number, (level, role, max_days) in enumerate(
        routing_levels, start=1
    ):

        routing_rules.append({
            "document_type": document_type,
            "step_number": step_number,
            "level": level,
            "approver_role": role,
            "max_days": max_days
        })

routing_rules_df = pd.DataFrame(routing_rules)


# --------------------------------------------------
# 15. GENERATE DOCUMENT APPROVAL STEPS
# --------------------------------------------------

approval_steps = []

approval_decisions = [
    "approved",
    "rejected",
    "returned",
    "escalated"
]

for _, document in documents_df.iterrows():

    document_rules = routing_rules_df[
        routing_rules_df["document_type"]
        == document["document_type"]
    ]

    for _, rule in document_rules.iterrows():

        eligible_users = users_df[
            users_df["role"] == rule["approver_role"]
        ]

        if eligible_users.empty:
            continue

        assigned_user = eligible_users.sample(1).iloc[0]

        received_at = document["created_at"]

        decision = random.choice(approval_decisions)

        decided_at = faker.date_time_between(
            start_date=received_at,
            end_date="now"
        )

        approval_steps.append({
            "step_id": generate_id(),
            "document_id": document["document_id"],
            "version_number": 1,
            "step_number": rule["step_number"],
            "level": rule["level"],
            "assigned_to": assigned_user["user_id"],
            "received_at": received_at,
            "decided_at": decided_at,
            "decision": decision,
            "comment": "Synthetic approval workflow record"
        })

approval_steps_df = pd.DataFrame(approval_steps)


tables = {
    "regions": regions_df,
    "branches": branches_df,
    "employers": employers_df,
    "users": users_df,
    "members":members_df,
    "dues_transactions": dues_df,
    "cases": cases_df,
    "engagement_events": engagement_df,
    "communication": communications_df,
    "audit_log": audit_df,
    "documents": documents_df,
    "document_versions": document_versions_df,
    "routing_rules": routing_rules_df,
    "approval_steps": approval_steps_df

}

for table_name, dataframe in tables.items():

    file_path = RAW_DATA_FOLDER / f"{table_name}.csv"

    dataframe.to_csv(file_path, index=False)

    print(f"{table_name}.csv saved successfully")



# 7. DISPLAY A SUMMARY

print("\nATLAS SUPPORTING DATA SUMMARY")
print("")

for table_name, dataframe in tables.items():
    print(f"{table_name}: {len(dataframe)} records")

print("\nAll supporting tables have been generated.")