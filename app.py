import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime

# -------------------------------------------------
# PAGE CONFIG (Mobile Friendly)
# -------------------------------------------------
st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💸",
    layout="centered"
)

# -------------------------------------------------
# SUPABASE (SECURE – FROM STREAMLIT SECRETS)
# -------------------------------------------------
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -------------------------------------------------
# DATABASE FUNCTIONS
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_data(month: int, year: int) -> pd.DataFrame:
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"

    response = (
        supabase.table("expenses")
        .select("*")
        .gte("date", start_date)
        .lte("date", end_date)
        .execute()
    )

    df = pd.DataFrame(response.data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def add_entry(entry: dict):
    supabase.table("expenses").insert(entry).execute()
    st.cache_data.clear()


def delete_entry(entry_id: int):
    supabase.table("expenses").delete().eq("id", entry_id).execute()
    st.cache_data.clear()

# -------------------------------------------------
# APP HEADER
# -------------------------------------------------
st.title("💸 Smart Expense Tracker")
st.caption("Simple • Secure • Mobile-Optimized")

# -------------------------------------------------
# MONTH / YEAR FILTER
# -------------------------------------------------
today = datetime.now()
col1, col2 = st.columns(2)

with col1:
    month = st.selectbox(
        "Month",
        list(range(1, 13)),
        index=today.month - 1
    )

with col2:
    year = st.selectbox(
        "Year",
        list(range(2022, today.year + 2)),
        index=2 if today.year >= 2024 else 0
    )

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
with st.spinner("Loading financial data..."):
    df = load_data(month, year)

# -------------------------------------------------
# ADD ENTRY FORM (MOBILE FRIENDLY)
# -------------------------------------------------
with st.expander("➕ Add Income / Expense / Savings"):
    with st.form("add_entry_form", clear_on_submit=True):

        date = st.date_input("Date", today)

        entry_type = st.radio(
            "Type",
            ["Income", "Expense", "Savings"],
            horizontal=True
        )

        category_map = {
            "Income": ["Salary", "Bonus", "Interest", "Other"],
            "Expense": [
                "Food", "Groceries", "Transport", "Rent",
                "Bills", "Utilities", "Health Care",
                "Shopping", "Entertainment", "Other"
            ],
            "Savings": ["Emergency Fund", "Investments", "FD / RD"]
        }

        category = st.selectbox("Category", category_map[entry_type])

        amount = st.number_input(
            "Amount (₹)",
            min_value=1.0,
            step=100.0,
            format="%.2f"
        )

        submit = st.form_submit_button("Add Entry")

        if submit:
            try:
                add_entry({
                    "date": str(date),
                    "type": entry_type,
                    "category": category,
                    "amount": amount
                })
                st.success("Entry added successfully ✅")
            except Exception:
                st.error("Failed to add entry ❌")

# -------------------------------------------------
# ACCOUNTING SUMMARY
# -------------------------------------------------
st.subheader("📘 Monthly Summary")

if df.empty:
    st.info("No records found for this month.")
    st.stop()

income = df[df["type"] == "Income"]["amount"].sum()
expenses = df[df["type"] == "Expense"]["amount"].sum()
savings = df[df["type"] == "Savings"]["amount"].sum()
net_balance = income - expenses - savings

colA, colB, colC, colD = st.columns(4)

colA.metric("Income", f"₹{income:,.0f}")
colB.metric("Expenses", f"₹{expenses:,.0f}")
colC.metric("Savings", f"₹{savings:,.0f}")
colD.metric(
    "Net Balance",
    f"₹{net_balance:,.0f}",
    delta="Surplus" if net_balance >= 0 else "Deficit"
)

# -------------------------------------------------
# CATEGORY CHART (EXPENSES)
# -------------------------------------------------
st.subheader("📊 Expense Breakdown")

expense_df = df[df["type"] == "Expense"]

if not expense_df.empty:
    pie = px.pie(
        expense_df,
        values="amount",
        names="category",
        hole=0.55
    )
    st.plotly_chart(pie, use_container_width=True)
else:
    st.info("No expenses recorded.")

# -------------------------------------------------
# RECORDS TABLE
# -------------------------------------------------
st.subheader("📄 All Records")

selected_rows = st.dataframe(
    df.sort_values("date", ascending=False),
    use_container_width=True,
    hide_index=True,
    selection_mode="single-row"
)

# -------------------------------------------------
# DELETE ENTRY (SAFE UX)
# -------------------------------------------------
if selected_rows and st.button("🗑 Delete Selected Entry"):
    try:
        delete_entry(selected_rows["id"].values[0])
        st.success("Entry deleted successfully")
    except Exception:
        st.error("Delete failed")

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit & Supabase")
