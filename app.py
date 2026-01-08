import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime

# --------------------------------------------------
# STREAMLIT CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Expense Tracker (₹)", layout="wide")
st.title("💰 Expense Tracker")

# --------------------------------------------------
# SUPABASE SETUP (USE SECRETS — NOT HARDCODED)
# --------------------------------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------
def add_entry(date, category, amount, entry_type):
    try:
        supabase.table("expenses").insert({
            "date": str(date),
            "category": category,
            "amount": amount,
            "type": entry_type
        }).execute()
        st.success("Entry added successfully")
    except Exception as e:
        st.error("Failed to add entry")

def load_data(month, year):
    try:
        res = supabase.table("expenses").select("*").execute()
        df = pd.DataFrame(res.data)
        if df.empty:
            return df

        df["date"] = pd.to_datetime(df["date"])
        df = df[
            (df["date"].dt.month == month) &
            (df["date"].dt.year == year)
        ]
        return df
    except Exception:
        return pd.DataFrame()

def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()

# --------------------------------------------------
# NAVIGATION (NO EXTRA LIBRARIES)
# --------------------------------------------------
page = st.radio(
    "Navigation",
    ["Dashboard", "Add Entry", "Records"],
    horizontal=True
)

# --------------------------------------------------
# DATE FILTER (USED ACROSS PAGES)
# --------------------------------------------------
today = datetime.now()
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1)
with col2:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=today.year)

df = load_data(month, year)

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if page == "Dashboard":
    st.subheader("📘 Accounting Summary")

    if df.empty:
        st.info("No records found for this month.")
    else:
        income = df[df["type"] == "Income"]["amount"].sum()
        expenses = df[df["type"] == "Expense"]["amount"].sum()
        balance = income - expenses

        c1, c2, c3 = st.columns(3)

        c1.metric("Income (₹)", f"{income:,.2f}")
        c2.metric("Expenses (₹)", f"{expenses:,.2f}")
        c3.metric("Balance (₹)", f"{balance:,.2f}")

        st.markdown("### 📊 Expense Breakdown")

        expense_df = df[df["type"] == "Expense"]
        if not expense_df.empty:
            fig = px.pie(
                expense_df,
                names="category",
                values="amount",
                hole=0.5
            )
            st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# ADD ENTRY (MOBILE FRIENDLY)
# --------------------------------------------------
elif page == "Add Entry":
    st.subheader("➕ Add Income or Expense")

    with st.form("add_entry_form", clear_on_submit=True):
        date = st.date_input("Date", datetime.now())
        entry_type = st.selectbox("Type", ["Income", "Expense"])

        if entry_type == "Income":
            category = st.selectbox(
                "Category",
                ["Salary", "Bonus", "Interest", "Other"]
            )
        else:
            category = st.selectbox(
                "Category",
                [
                    "Food", "Groceries", "Transport", "Snacks",
                    "Fashion", "Rent", "Bills", "Utilities",
                    "Healthcare", "Electronics", "Other"
                ]
            )

        amount = st.number_input("Amount (₹)", min_value=1.0, format="%.2f")

        submitted = st.form_submit_button("Add Entry")
        if submitted:
            add_entry(date, category, amount, entry_type)

# --------------------------------------------------
# RECORDS + SAFE DELETE
# --------------------------------------------------
elif page == "Records":
    st.subheader("📄 Records")

    if df.empty:
        st.info("No data available.")
    else:
        df_display = df.copy()
        df_display["date"] = df_display["date"].dt.strftime("%d-%m-%Y")
        df_display = df_display[["id", "date", "type", "category", "amount"]]

        st.dataframe(df_display, use_container_width=True)

        st.markdown("### ❌ Delete a Record")

        delete_id = st.number_input("Record ID", min_value=1, step=1)
        confirm = st.checkbox("I understand this action cannot be undone")

        if st.button("Delete Record"):
            if confirm:
                delete_entry(delete_id)
                st.success("Record deleted successfully")
            else:
                st.warning("Please confirm before deleting")
