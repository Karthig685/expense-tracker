import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime
import calendar
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
    # compute last day of month dynamically to avoid hardcoding 31
    last_day = calendar.monthrange(year, month)[1]
    res = (
        supabase.table("expenses")
        .select("*")
        .gte("date", f"{year}-{month:02d}-01")
        .lte("date", f"{year}-{month:02d}-{last_day:02d}")
        .execute()
    )
    df = pd.DataFrame(res.data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

def add_entry(data):
    supabase.table("expenses").insert(data).execute()
    # clear cache for load_data only so other caches remain intact
    load_data.clear()

def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()
    # clear cache for load_data only so other caches remain intact
    load_data.clear()

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


# ================= SAFE INITIALIZATION (ADD HERE) =================
income = 0.0
expenses = 0.0
savings = 0.0
net_balance = 0.0

if not df.empty:
    income = df[df["type"] == "Income"]["amount"].sum()
    expenses = df[df["type"] == "Expense"]["amount"].sum()
    savings = (
        df[df["type"] == "Savings"]["amount"].sum()
        if "Savings" in df["type"].values
        else 0.0
    )
    net_balance = income - expenses - savings
# ================================================================

# -------------------------------------------------
# CATEGORY MAP & ADD ENTRY (MOBILE-FRIENDLY UX)
# Entry type radio stays outside the form; the whole
# add-entry UI is placed inside an expander for small screens.
# -------------------------------------------------
category_map = {
    "Income": ["Salary", "Bonus", "Interest", "Other"],
    "Expense": [
        "Food", "Groceries", "Transport", "Rent",
        "Bills", "Utilities", "Health",
        "Shopping", "Entertainment", "Other"
    ],
    "Savings": ["Emergency Fund", "Investments", "FD / RD"]
}

with st.expander("➕ Add Entry", expanded=False):
    # Entry type must be outside the form so category updates correctly
    entry_type = st.radio(
        "Type",
        ["Income", "Expense", "Savings"],
        horizontal=True,
        key="entry_type"
    )

    # Category updates dynamically based on selected type
    category = st.selectbox(
        "Category",
        category_map.get(entry_type, []),
        key="entry_category"
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
            # Clear the load_data cache and rerun to show new data
            load_data.clear()
            st.experimental_rerun()

# -------------------------------------------------
# SUMMARY (ALWAYS VISIBLE FOR MOBILE)
# -------------------------------------------------
st.subheader("📘 Monthly Summary")
# Use values computed earlier (defaults to 0.0 when no records)
a, b, c, d = st.columns(4)
a.metric("Income", f"₹{income:,.0f}")
b.metric("Expenses", f"₹{expenses:,.0f}")
c.metric("Savings", f"₹{savings:,.0f}")
d.metric("Net Balance", f"₹{net_balance:,.0f}")

if df.empty:
    st.info("No records for this month.")

# -------------------------------------------------
# CHART
# -------------------------------------------------
st.subheader("📊 Expense Breakdown")
exp_df = df[df.type == "Expense"]
if not exp_df.empty:
    fig = px.pie(exp_df, values="amount", names="category", hole=0.55)
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------
# TABLE + SAFE DELETE WORKFLOW
# -------------------------------------------------
st.subheader("📄 Records")
df_table = df.sort_values("date", ascending=False)
st.dataframe(df_table, hide_index=True, use_container_width=True)

if not df_table.empty:
    # Build human-readable labels for safe deletion by ID
    options = []
    for _, row in df_table.iterrows():
        date_str = row["date"].date() if pd.notnull(row["date"]) else ""
        label = f"{int(row['id'])} | {date_str} | {row['type']} | {row['category']} | ₹{row['amount']:,.0f}"
        options.append(label)

    selected_label = st.selectbox("Select record to delete", options)
    if st.button("🗑 Delete Selected"):
        try:
            selected_id = int(selected_label.split(" | ")[0])
            delete_entry(selected_id)
            st.success("Deleted")
            # ensure cache cleared and UI refreshed
            load_data.clear()
            st.experimental_rerun()
        except Exception:
            st.error("Failed to delete selected record.")

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


if st.button("📥 Generate Visual PDF Report"):
    pdf_path = generate_visual_pdf(
        df, month, year,
        income, expenses, savings, net_balance
    )

    with open(pdf_path, "rb") as f:
        st.download_button(
            "⬇ Download Dashboard PDF",
            f,
            file_name=f"Dashboard_Report_{month}_{year}.pdf",
            mime="application/pdf"
        )


st.markdown("---")
st.caption("Built with Streamlit & Supabase")


