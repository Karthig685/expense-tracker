import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIG (MOBILE FIRST)
# --------------------------------------------------
st.set_page_config(
    page_title="Expense Tracker",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# MOBILE CSS
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding: 1rem 0.8rem;
}

.mobile-card {
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 14px;
    text-align: center;
}

.record-card {
    border-radius: 16px;
    padding: 14px;
    margin-bottom: 10px;
    background: #1e293b;
    color: white;
}

.add-btn {
    background: #3a86ff;
    color: white;
    padding: 12px;
    border-radius: 30px;
    text-align: center;
    font-weight: 600;
    margin: 10px auto;
    width: fit-content;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SUPABASE SETUP
# --------------------------------------------------
url = "https://ykgucpcjxwddnwznkqfa.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrZ3VjcGNqeHdkZG53em5rcWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MjgsImV4cCI6MjA4MDE0NDUyOH0.A-Gwlhbrb9QEa9u9C2Ghobm2zPw-zaLLUFdKU29rrP8"
supabase: Client = create_client(url, key)

# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------
def add_entry(date, category, amount, entry_type):
    supabase.table("expenses").insert({
        "date": str(date),
        "category": category,
        "amount": amount,
        "type": entry_type
    }).execute()

def load_data(month, year):
    res = supabase.table("expenses").select("*").execute()
    df = pd.DataFrame(res.data)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("<h2 style='text-align:center'>💸 Expense Tracker</h2>", unsafe_allow_html=True)

# --------------------------------------------------
# ADD ENTRY (MOBILE FRIENDLY)
# --------------------------------------------------
with st.expander("➕ Add Entry"):
    date = st.date_input("Date", datetime.now())
    entry_type = st.selectbox("Type", ["Income", "Expense", "Savings"])

    if entry_type == "Income":
        category = st.selectbox("Category", ["Salary", "Bonus", "Interest", "Other"])
    elif entry_type == "Savings":
        category = st.selectbox("Category", ["Fixed Deposit", "Mutual Funds", "Other"])
    else:
        category = st.selectbox(
            "Category",
            ["Food", "Groceries", "Transport", "Snacks", "Fashion",
             "Rent", "Bills", "Utilities", "Health Care", "Electronics", "Other"]
        )

    amount = st.number_input("Amount (₹)", min_value=1.0, format="%.2f")

    if st.button("Add Entry"):
        add_entry(date, category, amount, entry_type)
        st.success("Entry added successfully")

# --------------------------------------------------
# MONTH NAVIGATION (APP STYLE)
# --------------------------------------------------
today = datetime.now()
month = st.session_state.get("month", today.month)
year = st.session_state.get("year", today.year)

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅"):
        month = 12 if month == 1 else month - 1
with col2:
    st.markdown(
        f"<h4 style='text-align:center'>{datetime(year, month, 1).strftime('%B %Y')}</h4>",
        unsafe_allow_html=True
    )
with col3:
    if st.button("➡"):
        month = 1 if month == 12 else month + 1

st.session_state["month"] = month
st.session_state["year"] = year

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
df = load_data(month, year)

income = df[df["type"] == "Income"]["amount"].sum() if not df.empty else 0
expenses = df[df["type"] == "Expense"]["amount"].sum() if not df.empty else 0
savings = df[df["type"] == "Savings"]["amount"].sum() if not df.empty else 0
balance = income - expenses - savings
bal_color = "#2d6a4f" if balance >= 0 else "#e63946"

# --------------------------------------------------
# ACCOUNTING SUMMARY (STACKED CARDS)
# --------------------------------------------------
st.markdown("## 📘 Summary")

st.markdown(f"""
<div class='mobile-card' style='background:#0a9396;color:white;'>
<h4>Income</h4>
<h2>₹{income:,.2f}</h2>
</div>

<div class='mobile-card' style='background:#9b2226;color:white;'>
<h4>Expenses</h4>
<h2>₹{expenses:,.2f}</h2>
</div>

<div class='mobile-card' style='background:#001d3d;color:white;'>
<h4>Balance</h4>
<h2 style='color:{bal_color}'>₹{balance:,.2f}</h2>
</div>

<div class='mobile-card' style='background:#6a994e;color:white;'>
<h4>Savings</h4>
<h2>₹{savings:,.2f}</h2>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DONUT CHART (LIKE YOUR 2ND IMAGE)
# --------------------------------------------------
st.markdown("## 📊 Expense Breakdown")

expense_df = df[df["type"] == "Expense"]

if not expense_df.empty:
    fig = px.pie(
        expense_df,
        names="category",
        values="amount",
        hole=0.65
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No expenses for this month")

# --------------------------------------------------
# RECORD LIST (MOBILE CARDS)
# --------------------------------------------------
st.markdown("## 📄 Records")

if df.empty:
    st.info("No records available")
else:
    for _, row in df.sort_values("date", ascending=False).iterrows():
        st.markdown(f"""
        <div class='record-card'>
            <b>{row['category']}</b><br>
            {row['date'].strftime('%d %b %Y')} • {row['type']}<br>
            <h3>₹{row['amount']:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
