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
            amount REAL
        )
        """
    )
    conn.commit()
    return conn

# --- INSERT NEW EXPENSE ---
def add_expense(conn, date, category, amount):
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (date, category, amount) VALUES (?, ?, ?)",
        (date, category, amount),
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
    df = pd.DataFrame(rows, columns=["id", "date", "category", "amount"])
    return df

# --- UI START ---
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("📊 Expense Tracker (Streamlit + SQLite)")
conn = init_db()

# SIDEBAR INPUT
st.sidebar.header("Add Expense")
date = st.sidebar.date_input("Date", datetime.now())
category = st.sidebar.selectbox(
    "Category", ["Groceries", "Food", "Utilities", "Shopping", "Travel", "Healthcare", "Subscriptions"]
)
amount = st.sidebar.number_input("Amount (₹)", min_value=0.01, format="%.2f")

if st.sidebar.button("Add Expense"):
    add_expense(conn, str(date), category, amount)
    st.sidebar.success("Expense added!")

# SELECT MONTH & YEAR
today = datetime.now()
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("Month", list(range(1, 13)), index=today.month - 1)
with col2:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=today.year)

# LOAD DATA
df = load_data(conn, month, year)

if df.empty:
    st.info("No expenses found for this month.")
else:
    total = df["amount"].sum()

    st.subheader(f"Total Expenses for {month}/{year}: ${total:.2f}")

    # CATEGORY BREAKDOWN
    category_summary = df.groupby("category")["amount"].sum().reset_index()
    category_summary["percentage"] = (category_summary["amount"] / total * 100).round(1)

    # PIE CHART
    fig = px.pie(
        category_summary,
        values="amount",
        names="category",
        hole=0.5,
        title="Expense Breakdown by Category",
    )
    st.plotly_chart(fig, use_container_width=True)

    # SHOW TABLE
    st.subheader("📄 Expense Details")
    st.dataframe(df)

    # DELETE OPTION
    delete_id = st.number_input("Enter Expense ID to Delete", min_value=0, value=0)
    if st.button("Delete Expense"):
        c = conn.cursor()
        c.execute("DELETE FROM expenses WHERE id=?", (delete_id,))
        conn.commit()
        st.success("Deleted successfully!")

