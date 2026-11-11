# ============================================================
# ATLAS ENTERPRISE OPERATING PLATFORM
# COMPLETE DATA DICTIONARY
# Legasis (Pty) Ltd
# ============================================================

data_dictionary = {

    "members": {
        "description": "Stores information about union members.",
        "columns": {
            "member_id": ("UUID", "Primary Key", "Unique member identifier."),
            "age_band": ("VARCHAR", "-", "Age group of the member."),
            "gender": ("VARCHAR", "-", "Gender of the member, where available."),
            "join_date": ("DATE", "-", "Date the member joined the union."),
            "status": ("VARCHAR", "-", "Membership status."),
            "exit_date": ("DATE", "-", "Date membership ended."),
            "exit_reason": ("VARCHAR", "-", "Reason for leaving the union."),
            "employer_id": ("UUID", "Foreign Key", "Links to employers."),
            "branch_id": ("UUID", "Foreign Key", "Links to branches."),
            "occupation": ("VARCHAR", "-", "Member's occupation."),
            "employment_type": ("VARCHAR", "-", "Type of employment."),
            "payment_method": ("VARCHAR", "-", "Method used to pay membership dues.")
        }
    },

    "employers": {
        "description": "Stores information about employers.",
        "columns": {
            "employer_id": ("UUID", "Primary Key", "Unique employer identifier."),
            "employer_name": ("VARCHAR", "-", "Name of the employer."),
            "sector": ("VARCHAR", "-", "Employer industry or sector."),
            "province": ("VARCHAR", "-", "Province where employer operates."),
            "remittance_cycle": ("VARCHAR", "-", "Employer payment cycle.")
        }
    },

    "branches": {
        "description": "Stores union branch information.",
        "columns": {
            "branch_id": ("UUID", "Primary Key", "Unique branch identifier."),
            "branch_name": ("VARCHAR", "-", "Name of the branch."),
            "region_id": ("UUID", "Foreign Key", "Links to regions."),
            "province": ("VARCHAR", "-", "Province of the branch."),
            "steward_count": ("INTEGER", "-", "Number of union stewards.")
        }
    },

    "dues_transactions": {
        "description": "Records monthly membership dues and payments.",
        "columns": {
            "txn_id": ("UUID", "Primary Key", "Unique transaction identifier."),
            "member_id": ("UUID", "Foreign Key", "Links to members."),
            "period": ("VARCHAR", "-", "Month and year of the transaction."),
            "amount_due": ("DECIMAL", "-", "Amount owed by the member in ZAR."),
            "amount_paid": ("DECIMAL", "-", "Amount actually paid in ZAR."),
            "paid_date": ("DATE", "-", "Date payment was received."),
            "payment_status": ("VARCHAR", "-", "Paid, partial or unpaid."),
            "remittance_id": ("UUID", "Foreign Key", "Optional remittance reference.")
        }
    },

    "cases": {
        "description": "Tracks member workplace disputes and union cases.",
        "columns": {
            "case_id": ("UUID", "Primary Key", "Unique case identifier."),
            "member_id": ("UUID", "Foreign Key", "Links to members."),
            "employer_id": ("UUID", "Foreign Key", "Links to employers."),
            "category": ("VARCHAR", "-", "Type of workplace dispute."),
            "opened_date": ("DATE", "-", "Date the case was opened."),
            "closed_date": ("DATE", "-", "Date the case was closed."),
            "status": ("VARCHAR", "-", "Current case status."),
            "outcome": ("VARCHAR", "-", "Final case outcome."),
            "steward_id": ("UUID", "Foreign Key", "Links to users.")
        }
    },

    "engagement_events": {
        "description": "Records member participation in union activities.",
        "columns": {
            "event_id": ("UUID", "Primary Key", "Unique event identifier."),
            "member_id": ("UUID", "Foreign Key", "Links to members."),
            "branch_id": ("UUID", "Foreign Key", "Links to branches."),
            "event_type": ("VARCHAR", "-", "Meeting, campaign, training, march or vote."),
            "event_date": ("DATE", "-", "Date the event took place."),
            "attended": ("BOOLEAN", "-", "Whether the member attended.")
        }
    },

    "communications": {
        "description": "Tracks communications sent to union members.",
        "columns": {
            "message_id": ("UUID", "Primary Key", "Unique message identifier."),
            "member_id": ("UUID", "Foreign Key", "Links to members."),
            "channel": ("VARCHAR", "-", "SMS, WhatsApp or email."),
            "sent_at": ("DATETIME", "-", "Date and time the message was sent."),
            "delivered": ("BOOLEAN", "-", "Whether the message was delivered."),
            "opened_or_replied": ("BOOLEAN", "-", "Whether it was opened or replied to.")
        }
    },

    "audit_log": {
        "description": "Records user activities for accountability and auditing.",
        "columns": {
            "log_id": ("UUID", "Primary Key", "Unique audit log identifier."),
            "user_id": ("UUID", "Foreign Key", "Links to users."),
            "role": ("VARCHAR", "-", "Role of the user performing the action."),
            "action": ("VARCHAR", "-", "Create, update, view, export or delete."),
            "entity": ("VARCHAR", "-", "Record or table affected."),
            "timestamp": ("DATETIME", "-", "Date and time of the action.")
        }
    },

    "users": {
        "description": "Stores system users and their organisational roles.",
        "columns": {
            "user_id": ("UUID", "Primary Key", "Unique user identifier."),
            "role": ("VARCHAR", "-", "Steward, branch, regional, provincial or national officer."),
            "branch_id": ("UUID", "Foreign Key", "Optional link to a branch."),
            "region_id": ("UUID", "Foreign Key", "Optional link to a region."),
            "active": ("BOOLEAN", "-", "Whether the user account is active.")
        }
    },

    "regions": {
        "description": "Stores geographical and organisational regions.",
        "columns": {
            "region_id": ("UUID", "Primary Key", "Unique region identifier."),
            "region_name": ("VARCHAR", "-", "Name of the region."),
            "province": ("VARCHAR", "-", "Province containing the region.")
        }
    },

    "documents": {
        "description": "Tracks documents moving through approval workflows.",
        "columns": {
            "document_id": ("UUID", "Primary Key", "Immutable document identifier."),
            "document_type": ("VARCHAR", "-", "Type of document submitted."),
            "origin_member_id": ("UUID", "Foreign Key", "Optional originating member."),
            "origin_branch_id": ("UUID", "Foreign Key", "Originating branch."),
            "current_version": ("INTEGER", "-", "Current document version."),
            "status": ("VARCHAR", "-", "Current document workflow status."),
            "current_step": ("INTEGER", "-", "Current approval step."),
            "final_destination": ("VARCHAR", "-", "Final approval destination."),
            "created_at": ("DATETIME", "-", "Date and time document was created."),
            "closed_at": ("DATETIME", "-", "Date and time document was closed.")
        }
    },

    "document_versions": {
        "description": "Maintains document version history.",
        "columns": {
            "document_id": ("UUID", "Composite Primary Key / Foreign Key", "Links to documents."),
            "version_number": ("INTEGER", "Composite Primary Key", "Document version number."),
            "file_hash": ("VARCHAR", "-", "Digital fingerprint used to verify file integrity."),
            "uploaded_by": ("UUID", "Foreign Key", "User who uploaded the document."),
            "uploaded_at": ("DATETIME", "-", "Date and time the version was uploaded."),
            "change_note": ("TEXT", "-", "Description of changes made.")
        }
    },

    "routing_rules": {
        "description": "Defines document approval routes and deadlines.",
        "columns": {
            "document_type": ("VARCHAR", "Composite Primary Key", "Type of document being routed."),
            "step_number": ("INTEGER", "Composite Primary Key", "Position in approval sequence."),
            "level": ("VARCHAR", "-", "Branch, region, province or national level."),
            "approver_role": ("VARCHAR", "-", "Role required to approve the document."),
            "max_days": ("INTEGER", "-", "Maximum allowed days for approval.")
        }
    },

    "approval_steps": {
        "description": "Records individual document approval decisions.",
        "columns": {
            "step_id": ("UUID", "Primary Key", "Unique approval step identifier."),
            "document_id": ("UUID", "Foreign Key", "Links to documents."),
            "version_number": ("INTEGER", "Foreign Key", "Version being reviewed."),
            "step_number": ("INTEGER", "-", "Position in the approval sequence."),
            "level": ("VARCHAR", "-", "Organisational approval level."),
            "assigned_to": ("UUID", "Foreign Key", "User assigned to approve the document."),
            "received_at": ("DATETIME", "-", "Date and time approval was received."),
            "decided_at": ("DATETIME", "-", "Date and time a decision was made."),
            "decision": ("VARCHAR", "-", "Approved, rejected, returned or escalated."),
            "comment": ("TEXT", "-", "Comment explaining the decision.")
        }
    }
}


# ============================================================
# DISPLAY THE DATA DICTIONARY
# ============================================================

def display_data_dictionary():

    print("=" * 70)
    print("ATLAS ENTERPRISE OPERATING PLATFORM")
    print("DATA DICTIONARY")
    print("=" * 70)

    print("\nTOTAL TABLES:", len(data_dictionary))

    for table_name, details in data_dictionary.items():

        print("\n" + "=" * 70)
        print("TABLE:", table_name.upper())
        print("DESCRIPTION:", details["description"])
        print("-" * 70)

        print(f"{'COLUMN':<22} {'DATA TYPE':<12} {'KEY':<30} MEANING")
        print("-" * 100)

        for column, information in details["columns"].items():

            data_type, key, meaning = information

            print(
                f"{column:<22} "
                f"{data_type:<12} "
                f"{key:<30} "
                f"{meaning}"
            )

    print("\n" + "=" * 70)
    print("DATA DICTIONARY DISPLAY COMPLETED")
    print("=" * 70)


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    display_data_dictionary()