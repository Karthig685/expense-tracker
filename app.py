import streamlit as st
from supabase import create_client, Client
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.platypus import Image as RLImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import tempfile

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💸",
    layout="centered"
)

# -------------------------------------------------
# SUPABASE
# -------------------------------------------------
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -------------------------------------------------
# SESSION STATE (MONTH/YEAR)
# -------------------------------------------------
today = datetime.now()

st.session_state.setdefault("month", today.month)
st.session_state.setdefault("year", today.year)
st.session_state.setdefault("entry_type", "Income")

# -------------------------------------------------
# DB FUNCTIONS
# -------------------------------------------------
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

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("💸 Smart Expense Tracker")
st.caption("Stable • Correct • Production-Grade")

# -------------------------------------------------
# MONTH / YEAR
# -------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    st.session_state.month = st.selectbox(
        "Month",
        range(1, 13),
        index=st.session_state.month - 1
    )
with c2:
    years = list(range(2022, today.year + 2))
    st.session_state.year = st.selectbox(
        "Year",
        years,
        index=years.index(st.session_state.year)
    )

month = st.session_state.month
year = st.session_state.year

df = load_data(month, year)

# -------------------------------------------------
# ADD ENTRY (CORRECT UX)
# -------------------------------------------------
st.subheader("➕ Add Entry")

# 🔴 MUST BE OUTSIDE FORM
entry_type = st.radio(
    "Type",
    ["Income", "Expense", "Savings"],
    horizontal=True,
    key="entry_type_selector"
)

category_map = {
    "Income": ["Salary", "Bonus", "Interest", "Other"],
    "Expense": [
        "Food", "Groceries", "Transport", "Rent",
        "Bills", "Utilities", "Health",
        "Shopping", "Entertainment", "Other"
    ],
    "Savings": ["Emergency Fund", "Investments", "FD / RD"]
}

# Category updates instantly now ✅
category = st.selectbox(
    "Category",
    category_map[entry_type],
    key=f"category_{entry_type}"
)

with st.form("add_form", clear_on_submit=True):
    date = st.date_input("Date", today)
    amount = st.number_input("Amount (₹)", min_value=1.0, step=100.0)
    submit = st.form_submit_button("Add Entry")

    if submit:
        add_entry({
            "date": str(date),
            "type": entry_type,
            "category": category,
            "amount": amount
        })
        st.success("Entry added successfully ✅")

# -------------------------------------------------
# SUMMARY
# -------------------------------------------------
if df.empty:
    st.info("No records for this month.")
    st.stop()

income = df[df.type == "Income"].amount.sum()
expense = df[df.type == "Expense"].amount.sum()
savings = df[df.type == "Savings"].amount.sum()
net = income - expense - savings

st.subheader("📘 Monthly Summary")
a, b, c, d = st.columns(4)
a.metric("Income", f"₹{income:,.0f}")
b.metric("Expenses", f"₹{expense:,.0f}")
c.metric("Savings", f"₹{savings:,.0f}")
d.metric("Net Balance", f"₹{net:,.0f}")

# -------------------------------------------------
# CHART
# -------------------------------------------------
st.subheader("📊 Expense Breakdown")
exp_df = df[df.type == "Expense"]
if not exp_df.empty:
    fig = px.pie(exp_df, values="amount", names="category", hole=0.55)
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# TABLE
# -------------------------------------------------
st.subheader("📄 Records")
selected = st.dataframe(
    df.sort_values("date", ascending=False),
    hide_index=True,
    selection_mode="single-row",
    use_container_width=True
)

if selected and st.button("🗑 Delete Selected"):
    delete_entry(selected["id"].values[0])
    st.success("Deleted")

# -------------------------------------------------
# PDF REPORT
# -------------------------------------------------
st.subheader("📄 Download PDF Report")

def generate_pdf():
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(file.name, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Monthly Expense Report", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"Month / Year: {month} / {year}", styles["Normal"]))
    elements.append(Paragraph(f"Income: ₹{income:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Expenses: ₹{expense:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Savings: ₹{savings:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Net Balance: ₹{net:,.2f}", styles["Normal"]))

    doc.build(elements)
    return file.name

def generate_visual_pdf(df, month, year, income, expenses, savings, net_balance):
    temp_files = []

    # ---------------------------
    # 1️⃣ CASHFLOW LINE CHART
    # ---------------------------
    monthly = (
        df.groupby(["date", "type"])["amount"]
        .sum()
        .reset_index()
    )

    plt.figure(figsize=(6, 3))
    for t in ["Income", "Expense"]:
        subset = monthly[monthly["type"] == t]
        plt.plot(subset["date"], subset["amount"], label=t)

    plt.title("Cashflow Trend")
    plt.legend()
    plt.tight_layout()

    cashflow_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(cashflow_img.name)
    plt.close()
    temp_files.append(cashflow_img.name)

    # ---------------------------
    # 2️⃣ EXPENSE CATEGORY BAR
    # ---------------------------
    exp_cat = (
        df[df.type == "Expense"]
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(6, 3))
    exp_cat.plot(kind="bar")
    plt.title("Expense by Category")
    plt.tight_layout()

    category_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.savefig(category_img.name)
    plt.close()
    temp_files.append(category_img.name)

    # ---------------------------
    # 3️⃣ BUILD PDF
    # ---------------------------
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(pdf_file.name, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Monthly Financial Dashboard", styles["Title"]))
    elements.append(Spacer(1, 12))

    # KPI SECTION
    elements.append(Paragraph(
        f"""
        <b>Income:</b> ₹{income:,.0f} &nbsp;&nbsp;&nbsp;
        <b>Expenses:</b> ₹{expenses:,.0f} &nbsp;&nbsp;&nbsp;
        <b>Savings:</b> ₹{savings:,.0f} &nbsp;&nbsp;&nbsp;
        <b>Net Balance:</b> ₹{net_balance:,.0f}
        """,
        styles["Normal"]
    ))

    elements.append(Spacer(1, 20))

    # Charts
    elements.append(Paragraph("<b>Cashflow Trend</b>", styles["Heading2"]))
    elements.append(RLImage(cashflow_img.name, width=6 * inch, height=3 * inch))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>Expense Breakdown</b>", styles["Heading2"]))
    elements.append(RLImage(category_img.name, width=6 * inch, height=3 * inch))

    elements.append(Spacer(1, 20))

    # Written Analysis
    insight = (
        f"The month of {month}/{year} shows a "
        f"{'positive surplus' if net_balance >= 0 else 'negative deficit'} position. "
        "Expense concentration suggests areas for optimization. "
        "Maintaining or increasing savings will improve financial stability."
    )

    elements.append(Paragraph("<b>Financial Insights</b>", styles["Heading2"]))
    elements.append(Paragraph(insight, styles["Normal"]))

    doc.build(elements)

    return pdf_file.name


if st.button("📥 Generate PDF"):
    path = generate_pdf()
    with open(path, "rb") as f:
        st.download_button(
            "⬇ Download PDF",
            f,
            file_name=f"Expense_Report_{month}_{year}.pdf",
            mime="application/pdf"
        )

st.markdown("---")
st.caption("Built with Streamlit & Supabase")


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

