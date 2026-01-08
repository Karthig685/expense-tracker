import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- SUPABASE SETUP ---
url = "https://ykgucpcjxwddnwznkqfa.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrZ3VjcGNqeHdkZG53em5rcWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MjgsImV4cCI6MjA4MDE0NDUyOH0.A-Gwlhbrb9QEa9u9C2Ghobm2zPw-zaLLUFdKU29rrP8"
supabase: Client = create_client(url, key)

# --- INSERT NEW ENTRY ---
def add_entry(date, category, amount, entry_type):
    supabase.table("expenses").insert({
        "date": str(date),
        "category": category,
        "amount": amount,
        "type": entry_type
    }).execute()

# --- FETCH DATA ---
def load_data(month, year):
    # Filter by month/year
    query = supabase.table("expenses").select("*").execute()
    df = pd.DataFrame(query.data)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]
    return df

# --- DELETE ENTRY ---
def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="Expense Tracker (₹)", layout="wide")
st.title("💰 Expense Tracker")

# --- SIDEBAR INPUT ---
st.sidebar.header("Add Entry (Income / Expense / Savings)")
date = st.sidebar.date_input("Date", datetime.now())
entry_type = st.sidebar.selectbox("Type", ["Income", "Expense", "Savings"])

if entry_type == "Income":
    category = st.sidebar.selectbox("Category", ["Salary", "Bonus", "Interest", "Other"])
elif entry_type == "Savings":
    category = st.sidebar.selectbox("Category", ["Fixed Deposit", "Mutual Funds", "Other"]) 
else:
    category = st.sidebar.selectbox("Category", ["Food", "Groceries", "Transport","Snacks", "Fashion", "Rent", "Bills", "Utilities", "Health Care", "Electronics", "Other"])

amount = st.sidebar.number_input("Amount (₹)", min_value=1.0, format="%.2f")

if st.sidebar.button("Add"):
    add_entry(date, category, amount, entry_type)
    st.sidebar.success("Added successfully!")

# --- MONTH FILTER ---
today = datetime.now()
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("Month", list(range(1, 13)), index=today.month-1)
with col2:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=today.year)

# --- LOAD DATA ---
df = load_data(month, year)

# --- ACCOUNTING SUMMARY ---
st.markdown("### 📘 Accounting Summary")

income = df[df["type"] == "Income"]["amount"].sum() if not df.empty else 0
expenses = df[df["type"] == "Expense"]["amount"].sum() if not df.empty else 0
savings = df[df["type"] == "Savings"]["amount"].sum() if not df.empty else 0
balance = income - expenses - savings

# Add responsive CSS
st.markdown("""
<style>
@media (max-width: 768px) {
    .summary-box {
        padding: 12px !important;
    }
    .summary-box h3 {
        font-size: 14px !important;
    }
    .summary-box h2 {
        font-size: 18px !important;
    }
}
</style>
""", unsafe_allow_html=True)

colA, colB, colC, colD = st.columns([1,1,1,1])

with colA:
    st.markdown(f"""
    <div class='summary-box' style='background:#0a9396;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Income</h3>
        <h2 style='color:#d8f3dc;margin:0;'>₹{income:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with colB:
    st.markdown(f"""
    <div class='summary-box' style='background:#9b2226;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Expenses</h3>
        <h2 style='color:#fcd5ce;margin:0;'>₹{expenses:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

bal_color = "#2d6a4f" if balance >= 0 else "#e63946"
with colC:
    st.markdown(f"""
    <div class='summary-box' style='background:#001d3d;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Balance</h3>
        <h2 style='color:{bal_color};margin:0;'>₹{balance:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with colD:
    st.markdown(f"""
    <div class='summary-box' style='background:#6a994e;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Savings</h3>
        <h2 style='color:#f0efeb;margin:0;'>₹{savings:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

if df.empty:
    st.info("No records for this month.")
    st.stop()

# --- CATEGORY BREAKDOWN ---
st.markdown("### 📊 Category Breakdown")
cat_df = df.groupby(["category", "type"])["amount"].sum().reset_index()

fig = px.pie(cat_df, names="category", values="amount", hole=0.5, title="Expense/Income Split (₹)")
st.plotly_chart(fig, use_container_width=True)

# --- TABLE VIEW ---
st.markdown("### 📄 Detailed Records")
st.dataframe(df, use_container_width=True)

# --- DELETE ENTRY ---
st.markdown("### ❌ Delete Record")
delete_id = st.number_input("Enter ID to delete", min_value=0, value=0)
if st.button("Delete"):
    delete_entry(delete_id)
    st.success("Deleted!")
