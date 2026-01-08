import streamlit as st
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

