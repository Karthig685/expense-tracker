import streamlit as st
from supabase import create_client, Client
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import tempfile
import os

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# ---------------- SUPABASE ----------------
url = "https://ykgucpcjxwddnwznkqfa.supabase.co"
key = "YOUR_SUPABASE_ANON_KEY"
supabase: Client = create_client(url, key)

# ---------------- HELPERS ----------------
def add_entry(date, category, amount, entry_type):
    supabase.table("expenses").insert({
        "date": str(date),
        "category": category,
        "amount": amount,
        "type": entry_type
    }).execute()

def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()

def load_data(month, year):
    res = supabase.table("expenses").select("*").execute()
    df = pd.DataFrame(res.data)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df[
        (df["date"].dt.month == month) &
        (df["date"].dt.year == year)
    ]

# ---------------- SIDEBAR ----------------
st.sidebar.header("➕ Add Entry")

today = datetime.now()

entry_type = st.sidebar.selectbox(
    "Type",
    ["Income", "Expense", "Savings"],
    key="entry_type"
)

CATEGORY_MAP = {
    "Income": ["Salary", "Bonus", "Interest", "Other"],
    "Expense": [
        "Food", "Groceries", "Transport", "Snacks", "Rent",
        "Bills", "Utilities", "Healthcare", "Electronics",
        "Fashion", "Entertainment", "Other"
    ],
    "Savings": ["Emergency Fund", "Investments", "FD", "PPF", "Other"]
}

category = st.sidebar.selectbox(
    "Category",
    CATEGORY_MAP[entry_type],
    key="category"
)

date = st.sidebar.date_input("Date", today)
amount = st.sidebar.number_input("Amount (₹)", min_value=1.0, format="%.2f")

if st.sidebar.button("Add Entry"):
    add_entry(date, category, amount, entry_type)
    st.sidebar.success("Entry added")

# ---------------- FILTERS ----------------
st.title("💰 Expense Tracker")

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
        list(range(2020, today.year + 2)),
        index=list(range(2020, today.year + 2)).index(today.year)
    )

df = load_data(month, year)

# ---------------- SAFE INITIALIZATION ----------------
income = 0.0
expenses = 0.0
savings = 0.0
net_balance = 0.0

if not df.empty:
    income = df[df["type"] == "Income"]["amount"].sum()
    expenses = df[df["type"] == "Expense"]["amount"].sum()
    savings = df[df["type"] == "Savings"]["amount"].sum()
    net_balance = income - expenses - savings

# ---------------- DASHBOARD CARDS ----------------
st.markdown("## 📊 Monthly Summary")

c1, c2, c3, c4 = st.columns(4)

def card(title, value, color):
    st.markdown(
        f"""
        <div style="
            background:{color};
            padding:20px;
            border-radius:15px;
            text-align:center;
            color:white;
        ">
            <h4>{title}</h4>
            <h2>₹{value:,.2f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

with c1: card("Income", income, "#1b9aaa")
with c2: card("Expenses", expenses, "#ef476f")
with c3: card("Savings", savings, "#06d6a0")
with c4: card("Net Balance", net_balance, "#118ab2")

if df.empty:
    st.info("No data for selected month.")
    st.stop()

# ---------------- TABLE ----------------
st.markdown("## 📄 Records")
st.dataframe(df, use_container_width=True)

# ---------------- DELETE ----------------
st.markdown("## ❌ Delete Entry")
del_id = st.number_input("Entry ID", min_value=0, step=1)
if st.button("Delete"):
    delete_entry(del_id)
    st.success("Deleted successfully")

# ---------------- PDF REPORT ----------------
def generate_pdf(df, month, year, income, expenses, savings, net_balance):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>Expense Report – {month}/{year}</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Income: ₹{income:,.2f}", styles["Normal"]))
    story.append(Paragraph(f"Expenses: ₹{expenses:,.2f}", styles["Normal"]))
    story.append(Paragraph(f"Savings: ₹{savings:,.2f}", styles["Normal"]))
    story.append(Paragraph(f"Net Balance: ₹{net_balance:,.2f}", styles["Normal"]))
    story.append(Spacer(1, 20))

    # CATEGORY CHART
    cat = df.groupby("category")["amount"].sum()
    plt.figure(figsize=(6, 4))
    cat.plot(kind="bar")
    plt.title("Category Breakdown")
    plt.tight_layout()

    img_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    plt.savefig(img_path)
    plt.close()

    story.append(Image(img_path, width=5 * inch, height=3 * inch))
    story.append(Spacer(1, 20))

    story.append(Paragraph(
        "Analysis: Expenses and savings are tracked clearly. "
        "Maintain savings above 20% of income for healthy cashflow.",
        styles["Normal"]
    ))

    doc.build(story)
    return tmp.name

st.markdown("## 📥 Monthly PDF Report")

if st.button("Generate PDF Report"):
    pdf_path = generate_pdf(
        df, month, year,
        income, expenses, savings, net_balance
    )
    with open(pdf_path, "rb") as f:
        st.download_button(
            "Download PDF",
            f,
            file_name=f"Expense_Report_{month}_{year}.pdf",
            mime="application/pdf"
        )
