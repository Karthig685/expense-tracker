import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import tempfile

# -------------------------------------------------
# PAGE CONFIG (Mobile Friendly)
# -------------------------------------------------
st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💸",
    layout="centered"
)

# -------------------------------------------------
# SUPABASE (FROM STREAMLIT SECRETS)
# -------------------------------------------------
supabase: Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# -------------------------------------------------
# SESSION STATE (FIX MONTH/YEAR RESET)
# -------------------------------------------------
today = datetime.now()

if "month" not in st.session_state:
    st.session_state.month = today.month

if "year" not in st.session_state:
    st.session_state.year = today.year

# -------------------------------------------------
# DATABASE FUNCTIONS
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_data(month, year):
    response = (
        supabase.table("expenses")
        .select("*")
        .gte("date", f"{year}-{month:02d}-01")
        .lte("date", f"{year}-{month:02d}-31")
        .execute()
    )
    df = pd.DataFrame(response.data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

def add_entry(entry):
    supabase.table("expenses").insert(entry).execute()
    st.cache_data.clear()

def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()
    st.cache_data.clear()

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.title("💸 Smart Expense Tracker")
st.caption("Secure • Mobile-Friendly • Finance-Grade")

# -------------------------------------------------
# MONTH / YEAR FILTER
# -------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.session_state.month = st.selectbox(
        "Month",
        range(1, 13),
        index=st.session_state.month - 1
    )

with col2:
    years = list(range(2022, today.year + 2))
    st.session_state.year = st.selectbox(
        "Year",
        years,
        index=years.index(st.session_state.year)
    )

month = st.session_state.month
year = st.session_state.year

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
with st.spinner("Loading data..."):
    df = load_data(month, year)

# -------------------------------------------------
# ADD ENTRY (FIXED CATEGORY BUG)
# -------------------------------------------------
with st.expander("➕ Add Income / Expense / Savings"):
    with st.form("add_form", clear_on_submit=True):

        date = st.date_input("Date", today)

        entry_type = st.radio(
            "Type",
            ["Income", "Expense", "Savings"],
            horizontal=True,
            key="entry_type"
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

        # 🔑 IMPORTANT FIX: dynamic key
        category = st.selectbox(
            "Category",
            category_map[entry_type],
            key=f"category_{entry_type}"
        )

        amount = st.number_input(
            "Amount (₹)",
            min_value=1.0,
            step=100.0,
            format="%.2f"
        )

        submit = st.form_submit_button("Add Entry")

        if submit:
            try:
                add_entry({
                    "date": str(date),
                    "type": entry_type,
                    "category": category,
                    "amount": amount
                })
                st.success("Entry added successfully ✅")
            except Exception:
                st.error("Failed to add entry ❌")

# -------------------------------------------------
# SUMMARY
# -------------------------------------------------
if df.empty:
    st.info("No records found for this month.")
    st.stop()

income = df[df.type == "Income"].amount.sum()
expenses = df[df.type == "Expense"].amount.sum()
savings = df[df.type == "Savings"].amount.sum()
net_balance = income - expenses - savings

st.subheader("📘 Monthly Financial Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Income", f"₹{income:,.0f}")
c2.metric("Expenses", f"₹{expenses:,.0f}")
c3.metric("Savings", f"₹{savings:,.0f}")
c4.metric(
    "Net Balance",
    f"₹{net_balance:,.0f}",
    delta="Surplus" if net_balance >= 0 else "Deficit"
)

# -------------------------------------------------
# CHART
# -------------------------------------------------
st.subheader("📊 Expense Breakdown")

expense_df = df[df.type == "Expense"]
if not expense_df.empty:
    fig = px.pie(
        expense_df,
        values="amount",
        names="category",
        hole=0.55
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No expenses recorded.")

# -------------------------------------------------
# RECORDS TABLE
# -------------------------------------------------
st.subheader("📄 Records")

selected = st.dataframe(
    df.sort_values("date", ascending=False),
    hide_index=True,
    selection_mode="single-row",
    use_container_width=True
)

if selected and st.button("🗑 Delete Selected Entry"):
    delete_entry(selected["id"].values[0])
    st.success("Entry deleted successfully")

# -------------------------------------------------
# PDF REPORT GENERATION
# -------------------------------------------------
st.subheader("📄 Download Detailed PDF Report")

def generate_pdf():
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(file.name, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Monthly Expense Report", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Month / Year: {month} / {year}", styles["Normal"]))
    elements.append(Paragraph(f"Total Income: ₹{income:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Total Expenses: ₹{expenses:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Total Savings: ₹{savings:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Net Balance: ₹{net_balance:,.2f}", styles["Normal"]))

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Category-wise Expense Analysis", styles["Heading2"]))

    cat_data = (
        expense_df.groupby("category")["amount"]
        .sum()
        .reset_index()
        .values.tolist()
    )
    cat_data.insert(0, ["Category", "Amount (₹)"])
    elements.append(Table(cat_data))

    elements.append(Spacer(1, 0.3 * inch))
    analysis = (
        f"The month shows a {'surplus' if net_balance >= 0 else 'deficit'} position. "
        "Expense concentration should be reviewed and consistent savings is recommended."
    )
    elements.append(Paragraph("Financial Analysis", styles["Heading2"]))
    elements.append(Paragraph(analysis, styles["Normal"]))

    doc.build(elements)
    return file.name

if st.button("📥 Generate PDF Report"):
    pdf_path = generate_pdf()
    with open(pdf_path, "rb") as f:
        st.download_button(
            "⬇ Download PDF Report",
            f,
            file_name=f"Expense_Report_{month}_{year}.pdf",
            mime="application/pdf"
        )

# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown("---")
st.caption("Built with Streamlit • Supabase • ReportLab")
