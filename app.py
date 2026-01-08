import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💸",
    layout="centered"
)

# ---------------- SUPABASE ----------------
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ---------------- DATA LAYER ----------------
@st.cache_data(ttl=60)
def load_data(month, year):
    res = (
        supabase.table("expenses")
        .select("*")
        .gte("date", f"{year}-{month:02d}-01")
        .lte("date", f"{year}-{month:02d}-31")
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

def add_entry(data):
    supabase.table("expenses").insert(data).execute()
    st.cache_data.clear()

def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()
    st.cache_data.clear()

# ---------------- HEADER ----------------
st.title("💸 Smart Expense Tracker")
st.caption("Mobile-optimized • Accountant-approved")

# ---------------- FILTER ----------------
today = datetime.now()
col1, col2 = st.columns(2)

with col1:
    month = st.selectbox("Month", range(1, 13), index=today.month - 1)
with col2:
    year = st.selectbox("Year", range(2022, today.year + 2), index=2)

df = load_data(month, year)

# ---------------- ADD ENTRY ----------------
with st.expander("➕ Add Income / Expense", expanded=False):
    with st.form("add_form", clear_on_submit=True):
        date = st.date_input("Date", today)
        entry_type = st.radio("Type", ["Income", "Expense", "Savings"], horizontal=True)

        category_map = {
            "Income": ["Salary", "Bonus", "Interest", "Other"],
            "Expense": ["Food", "Groceries", "Transport", "Rent", "Bills", "Health", "Shopping", "Other"],
            "Savings": ["Emergency Fund", "Investments", "FD/RD"]
        }

        category = st.selectbox("Category", category_map[entry_type])
        amount = st.number_input("Amount (₹)", min_value=1.0, step=100.0)

        submitted = st.form_submit_button("Add Entry")
        if submitted:
            add_entry({
                "date": str(date),
                "type": entry_type,
                "category": category,
                "amount": amount
            })
            st.success("Entry added successfully")

# ---------------- ACCOUNTING SUMMARY ----------------
if not df.empty:
    income = df[df.type == "Income"].amount.sum()
    expenses = df[df.type == "Expense"].amount.sum()
    savings = df[df.type == "Savings"].amount.sum()
    net_balance = income - expenses - savings

    colA, colB, colC, colD = st.columns(4)

    colA.metric("Income", f"₹{income:,.0f}")
    colB.metric("Expenses", f"₹{expenses:,.0f}", delta=f"-₹{expenses:,.0f}")
    colC.metric("Savings", f"₹{savings:,.0f}")
    colD.metric(
        "Net Balance",
        f"₹{net_balance:,.0f}",
        delta="Surplus" if net_balance >= 0 else "Deficit"
    )

# ---------------- VISUALS ----------------
if df.empty:
    st.info("No data available for selected period.")
    st.stop()

st.subheader("📊 Spending Distribution")

expense_df = df[df.type == "Expense"]
if not expense_df.empty:
    pie = px.pie(
        expense_df,
        values="amount",
        names="category",
        hole=0.55
    )
    st.plotly_chart(pie, use_container_width=True)

# ---------------- TABLE ----------------
st.subheader("📄 Records")
selected = st.dataframe(
    df.sort_values("date", ascending=False),
    use_container_width=True,
    hide_index=True,
    selection_mode="single-row"
)

# ---------------- DELETE ----------------
if selected and st.button("🗑 Delete Selected Entry"):
    delete_entry(selected["id"].values[0])
    st.success("Entry deleted")
