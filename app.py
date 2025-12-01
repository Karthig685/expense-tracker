import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("expenses.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            type TEXT
        )
        """
    )
    conn.commit()
    return conn

# --- INSERT NEW ENTRY ---
def add_entry(conn, date, category, amount, entry_type):
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (date, category, amount, type) VALUES (?, ?, ?, ?)",
        (date, category, amount, entry_type),
    )
    conn.commit()

# --- FETCH DATA ---
def load_data(conn, month, year):
    c = conn.cursor()
    c.execute(
        "SELECT * FROM expenses WHERE strftime('%m', date)=? AND strftime('%Y', date)=?",
        (f"{month:02d}", str(year)),
    )
    rows = c.fetchall()
    df = pd.DataFrame(rows, columns=["id", "date", "category", "amount", "type"])
    return df

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="💰 Expense Tracker (₹)", layout="wide")
st.title("💰 Expense Tracker — Rupees Version (Mobile Optimized)")

conn = init_db()

# --- SIDEBAR INPUT ---
st.sidebar.header("Add Entry (Income / Expense)")
date = st.sidebar.date_input("Date", datetime.now())
entry_type = st.sidebar.selectbox("Type", ["Income", "Expense"])

if entry_type == "Income":
    category = st.sidebar.selectbox("Category", ["Salary", "Bonus", "Interest", "Other"])
else:
    category = st.sidebar.selectbox("Category", ["Food", "Groceries", "Travel", "Shopping", "Rent", "Bills", "Other"])

amount = st.sidebar.number_input("Amount (₹)", min_value=1.0, format="%.2f")

if st.sidebar.button("Add"):
    add_entry(conn, str(date), category, amount, entry_type)
    st.sidebar.success("Added successfully!")

# --- MONTH FILTER ---
today = datetime.now()
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("Month", list(range(1, 12+1)), index=today.month-1)
with col2:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=today.year)

# --- LOAD DATA ---
df = load_data(conn, month, year)

# --- ACCOUNTING SUMMARY ---
st.markdown("### 📘 Accounting Summary")

income = df[df["type"] == "Income"]["amount"].sum() if not df.empty else 0
expenses = df[df["type"] == "Expense"]["amount"].sum() if not df.empty else 0
balance = income - expenses

# Mobile-optimized stacked layout
colA, colB, colC = st.columns([1,1,1])

# Income card
with colA:
    st.markdown(f"""
    <div style='background:#0a9396;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Income</h3>
        <h2 style='color:#d8f3dc;margin:0;'>₹{income:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

# Expense card
with colB:
    st.markdown(f"""
    <div style='background:#9b2226;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Expenses</h3>
        <h2 style='color:#fcd5ce;margin:0;'>₹{expenses:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

# Balance card
bal_color = "#2d6a4f" if balance >= 0 else "#e63946"
with colC:
    st.markdown(f"""
    <div style='background:#001d3d;padding:20px;border-radius:15px;text-align:center;'>
        <h3 style='color:white;margin:0;'>Balance</h3>
        <h2 style='color:{bal_color};margin:0;'>₹{balance:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

# --- IF EMPTY ---
if df.empty:
    st.info("No records for this month.")
    st.stop()

# --- CATEGORY BREAKDOWN ---
st.markdown("### 📊 Category Breakdown")
cat_df = df.groupby(["category", "type"])["amount"].sum().reset_index()

# Pie chart
fig = px.pie(cat_df, names="category", values="amount", hole=0.5, title="Expense/Income Split (₹)")
st.plotly_chart(fig, use_container_width=True)

# --- TABLE VIEW ---
st.markdown("### 📄 Detailed Records")
st.dataframe(df, use_container_width=True)

# --- DELETE ENTRY ---
st.markdown("### ❌ Delete Record")
delete_id = st.number_input("Enter ID to delete", min_value=0, value=0)
if st.button("Delete"):
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (delete_id,))
    conn.commit()
    st.success("Deleted!")
