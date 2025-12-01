import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase import create_client
import os

# --- LOAD SUPABASE CREDENTIALS FROM ENV ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")  # set in Streamlit Secrets
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- DATABASE TABLE NAME ---
TABLE_NAME = "expenses"

# --- FUNCTION TO ADD ENTRY ---
def add_entry(date, category, amount, entry_type):
    supabase.table(TABLE_NAME).insert({
        "date": str(date),
        "category": category,
        "amount": float(amount),
        "type": entry_type
    }).execute()

# --- FUNCTION TO LOAD DATA ---
def load_data(month, year):
    response = supabase.table(TABLE_NAME).select("*").execute()
    data = response.data
    df = pd.DataFrame(data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]
    else:
        df = pd.DataFrame(columns=["id","date","category","amount","type"])
    return df

# --- STREAMLIT PAGE ---
st.set_page_config(page_title="Expense Tracker (₹)", layout="wide")
st.title("💰 Expense Tracker")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Add Entry (Income / Expense)")

# --- Initialize session state for resetting inputs ---
if "amount" not in st.session_state:
    st.session_state.amount = 0.0
if "entry_type" not in st.session_state:
    st.session_state.entry_type = "Income"
if "category" not in st.session_state:
    st.session_state.category = "Salary"

date = st.sidebar.date_input("Date", datetime.now())
entry_type = st.sidebar.selectbox("Type", ["Income", "Expense"], key="entry_type")

if entry_type == "Income":
    category = st.sidebar.selectbox(
        "Category",
        ["Salary", "Bonus", "Interest", "Other"],
        key="category"
    )
else:
    category = st.sidebar.selectbox(
        "Category",
        ["Food", "Groceries", "Transport", "Shopping", "Rent", "Bills", "Utilities", "Health Care", "Electronics", "Other"],
        key="category"
    )

amount = st.sidebar.number_input("Amount (₹)", min_value=1.0, format="%.2f", key="amount")

if st.sidebar.button("Add"):
    add_entry(date, category, amount, entry_type)
    st.sidebar.success("Added successfully!")
    st.session_state.amount = 0.0  # reset amount input
    st.session_state.entry_type = "Income"  # optional: reset type
    st.session_state.category = "Salary"    # optional: reset category

# --- FILTER DATA BY MONTH/YEAR ---
today = datetime.now()
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("Month", list(range(1, 13)), index=today.month-1)
with col2:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=today.year)

df = load_data(month, year)

# --- ACCOUNTING SUMMARY ---
st.markdown("### 📘 Accounting Summary")
income = df[df["type"]=="Income"]["amount"].sum() if not df.empty else 0
expenses = df[df["type"]=="Expense"]["amount"].sum() if not df.empty else 0
balance = income - expenses

colA, colB, colC = st.columns([1,1,1])

with colA:
    st.markdown(f"""
    <div style='background:#0a9396;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Income</h3>
        <h2 style='color:#d8f3dc;margin:0;'>₹{income:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with colB:
    st.markdown(f"""
    <div style='background:#9b2226;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Expenses</h3>
        <h2 style='color:#fcd5ce;margin:0;'>₹{expenses:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

bal_color = "#2d6a4f" if balance >=0 else "#e63946"
with colC:
    st.markdown(f"""
    <div style='background:#001d3d;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Balance</h3>
        <h2 style='color:{bal_color};margin:0;'>₹{balance:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

# --- EMPTY CHECK ---
if df.empty:
    st.info("No records for this month.")
    st.stop()

# --- CATEGORY BREAKDOWN ---
st.markdown("### 📊 Category Breakdown")
cat_df = df.groupby(["category","type"])["amount"].sum().reset_index()
fig = px.pie(cat_df, names="category", values="amount", hole=0.5, title="Expense/Income Split (₹)")
st.plotly_chart(fig, use_container_width=True)

# --- TABLE VIEW ---
st.markdown("### 📄 Detailed Records")
st.dataframe(df, use_container_width=True)

# --- DELETE ENTRY ---
st.markdown("### ❌ Delete Record")
delete_id = st.number_input("Enter ID to delete", min_value=0, value=0)
if st.button("Delete"):
    supabase.table(TABLE_NAME).delete().eq("id", delete_id).execute()
    st.success("Deleted!")
