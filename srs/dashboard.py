
# ATLAS ENTERPRISE OPERATING PLATFORM
# MANAGEMENT DASHBOARD
# Legasis (Pty) Ltd


from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px


# 1. PROJECT DIRECTORIES


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"


# ------------------------------------------------------------
# 2. PAGE CONFIGURATION
# ------------------------------------------------------------

st.set_page_config(
    page_title="Atlas Enterprise Operating Platform",
    page_icon="📊",
    layout="wide"
)



#  DASHBOARD TITLE


st.title("ATLAS ENTERPRISE OPERATING PLATFORM")

st.subheader("Union Management and Performance Dashboard")

st.caption(
    "Legasis (Pty) Ltd | Northern Cape | Synthetic demonstration data"
)

st.divider()

# LOAD DATA


@st.cache_data
def load_csv(file_path):

    if not file_path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)

    except Exception:
        return pd.DataFrame()


def load_data():

    data = {

        "members": load_csv(RAW_DATA_DIR / "members.csv"),

        "dues": load_csv(RAW_DATA_DIR / "dues_transactions.csv"),

        "cases": load_csv(RAW_DATA_DIR / "cases.csv"),

        "events": load_csv(RAW_DATA_DIR / "engagement_events.csv"),

        "branches": load_csv(RAW_DATA_DIR / "branches.csv"),

        "employers": load_csv(RAW_DATA_DIR / "employers.csv")
    }

    return data


data = load_data()

members = data["members"]
dues = data["dues"]
cases = data["cases"]
events = data["events"]
branches = data["branches"]
employers = data["employers"]



# CHECK DATA AVAILABILITY


if members.empty:

    st.error(
        "Members dataset could not be loaded. "
        "Please check the data/raw folder."
    )

    st.stop()



# PREPARE DATA

members = members.copy()

members["status"] = (
    members["status"].astype(str).str.strip().str.lower()
)

if "join_date" in members.columns:

    members["join_date"] = pd.to_datetime(
        members["join_date"],
        errors="coerce"
    )

if "exit_date" in members.columns:

    members["exit_date"] = pd.to_datetime(
        members["exit_date"],
        errors="coerce"
    )

if not dues.empty:

    dues = dues.copy()

    dues["amount_due"] = pd.to_numeric(
        dues["amount_due"], errors="coerce"
    ).fillna(0)

    dues["amount_paid"] = pd.to_numeric(
        dues["amount_paid"], errors="coerce"
    ).fillna(0)



#  SIDEBAR FILTERS


st.sidebar.header("Dashboard Filters")

if "status" in members.columns:

    statuses = sorted(members["status"].dropna().unique())

    selected_status = st.sidebar.multiselect(
        "Membership status",
        statuses,
        default=statuses
    )

    filtered_members = members[
        members["status"].isin(selected_status)
    ]

else:
    filtered_members = members.copy()


if (
    "province" in branches.columns
    and not branches.empty
):

    provinces = sorted(
        branches["province"].dropna().unique()
    )

    selected_province = st.sidebar.multiselect(
        "Province",
        provinces,
        default=provinces
    )

    selected_branch_ids = branches[
        branches["province"].isin(selected_province)
    ]["branch_id"]

    filtered_members = filtered_members[
        filtered_members["branch_id"].isin(selected_branch_ids)
    ]



# MEMBERSHIP OVERVIEW


st.header("1. Membership Overview")

total_members = len(filtered_members)

active_members = int(
    (filtered_members["status"] == "active").sum()
)

lapsed_members = int(
    (filtered_members["status"] == "lapsed").sum()
)

suspended_members = int(
    (filtered_members["status"] == "suspended").sum()
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Members", f"{total_members:,}")

col2.metric("Active Members", f"{active_members:,}")

col3.metric("Lapsed Members", f"{lapsed_members:,}")

col4.metric("Suspended Members", f"{suspended_members:,}")



# MEMBERSHIP STATUS CHART

st.subheader("Membership Status Distribution")

status_counts = (
    filtered_members["status"]
    .value_counts()
    .reset_index()
)

status_counts.columns = ["status", "members"]

if not status_counts.empty:

    fig_status = px.pie(
        status_counts,
        names="status",
        values="members",
        title="Membership by Status",
        hole=0.4
    )

    st.plotly_chart(fig_status, use_container_width=True)


# MEMBERSHIP GROWTH


st.header("2. Membership Growth")

if "join_date" in filtered_members.columns:

    joins = (
        filtered_members.dropna(subset=["join_date"])
        .groupby(
            filtered_members["join_date"].dt.to_period("M")
        )
        .size()
        .reset_index(name="new_members")
    )

    joins.columns = ["period", "new_members"]

    joins["period"] = joins["period"].astype(str)

    if not joins.empty:

        fig_growth = px.line(
            joins,
            x="period",
            y="new_members",
            markers=True,
            title="Monthly New Member Registrations"
        )

        st.plotly_chart(
            fig_growth,
            use_container_width=True
        )

    else:

        st.info("No membership growth data is available.")

else:

    st.info("Membership join dates are unavailable.")


#  DUES COLLECTION OVERVIEW

st.header("3. Membership Dues and Arrears")

if not dues.empty:

    total_due = dues["amount_due"].sum()

    total_paid = dues["amount_paid"].sum()

    arrears = (
        dues["amount_due"] - dues["amount_paid"]
    ).clip(lower=0).sum()

    collection_rate = (
        total_paid / total_due * 100
        if total_due > 0 else 0
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Dues Expected",
        f"R {total_due:,.2f}"
    )

    col2.metric(
        "Total Dues Collected",
        f"R {total_paid:,.2f}"
    )

    col3.metric(
        "Outstanding Arrears",
        f"R {arrears:,.2f}"
    )

    st.metric(
        "Dues Collection Rate",
        f"{collection_rate:.2f}%"
    )

    # Monthly dues performance

    if "period" in dues.columns:

        monthly_dues = dues.groupby("period").agg(
            total_due=("amount_due", "sum"),
            total_paid=("amount_paid", "sum")
        ).reset_index()

        fig_dues = px.bar(
            monthly_dues,
            x="period",
            y=["total_due", "total_paid"],
            barmode="group",
            title="Monthly Dues Expected vs Collected"
        )

        st.plotly_chart(
            fig_dues,
            use_container_width=True
        )

else:

    st.warning("Dues transaction data is unavailable.")



#  CASE MANAGEMENT OVERVIEW


st.header("4. Case Management")

if not cases.empty and "status" in cases.columns:

    case_status = (
        cases["status"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    total_cases = len(cases)

    open_cases = int(
        case_status.isin(
            ["open", "in progress", "escalated"]
        ).sum()
    )

    closed_cases = int(
        (case_status == "closed").sum()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Cases", f"{total_cases:,}")

    col2.metric("Open or Ongoing Cases", f"{open_cases:,}")

    col3.metric("Closed Cases", f"{closed_cases:,}")

    case_chart = (
        case_status.value_counts()
        .reset_index()
    )

    case_chart.columns = ["status", "cases"]

    fig_cases = px.bar(
        case_chart,
        x="status",
        y="cases",
        title="Cases by Status",
        text="cases"
    )

    st.plotly_chart(
        fig_cases,
        use_container_width=True
    )

else:

    st.info("Case management data is unavailable.")

# 13. BRANCH ACTIVITY


st.header("5. Branch Activity")

if not events.empty and not branches.empty:

    branch_activity = events.groupby("branch_id").agg(
        total_events=("event_id", "count"),
        attendance_count=("attended", "sum")
    ).reset_index()

    branch_activity["attendance_rate"] = (
        branch_activity["attendance_count"]
        / branch_activity["total_events"].replace(0, pd.NA)
        * 100
    )

    branch_activity = branch_activity.merge(
        branches[["branch_id", "branch_name"]],
        on="branch_id",
        how="left"
    )

    fig_branch = px.bar(
        branch_activity,
        x="branch_name",
        y="total_events",
        title="Events by Branch",
        text="total_events"
    )

    st.plotly_chart(
        fig_branch,
        use_container_width=True
    )

    st.subheader("Branch Activity Records")

    st.dataframe(
        branch_activity,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("Branch activity data is unavailable.")


# 14. EMPLOYER OVERVIEW

st.header("6. Employer Overview")

if not employers.empty:

    st.metric(
        "Number of Employers",
        f"{len(employers):,}"
    )

    if "sector" in employers.columns:

        sector_counts = (
            employers["sector"]
            .value_counts()
            .reset_index()
        )

        sector_counts.columns = ["sector", "employers"]

        fig_sector = px.pie(
            sector_counts,
            names="sector",
            values="employers",
            title="Employers by Sector"
        )

        st.plotly_chart(
            fig_sector,
            use_container_width=True
        )

else:

    st.info("Employer data is unavailable.")



#DATA TABLES


st.header("7. Dataset Explorer")

selected_dataset = st.selectbox(
    "Choose a dataset to inspect",
    [
        "Members",
        "Dues Transactions",
        "Cases",
        "Engagement Events",
        "Branches",
        "Employers"
    ]
)

dataset_mapping = {
    "Members": filtered_members,
    "Dues Transactions": dues,
    "Cases": cases,
    "Engagement Events": events,
    "Branches": branches,
    "Employers": employers
}

selected_data = dataset_mapping[selected_dataset]

if not selected_data.empty:

    st.dataframe(
        selected_data.head(100),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        f"Showing up to 100 records out of {len(selected_data):,}."
    )

else:

    st.info("No records are available for this dataset.")


#  DASHBOARD FOOTER

st.divider()

st.caption(
    "ATLAS Enterprise Operating Platform | "
    "Legasis (Pty) Ltd | Synthetic demonstration data"
)

st.caption(
    "This dashboard uses synthetic data for development "
    "and demonstration purposes only."
)