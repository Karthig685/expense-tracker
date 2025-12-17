import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import tempfile

# --- SUPABASE SETUP ---
url = "https://ykgucpcjxwddnwznkqfa.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrZ3VjcGNqeHdkZG53em5rcWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MjgsImV4cCI6MjA4MDE0NDUyOH0.A-Gwlhbrb9QEa9u9C2Ghobm2zPw-zaLLUFdKU29rrP8"
supabase: Client = create_client(url, key)

# --- INSERT ---
def add_entry(date, category, amount, entry_type):
    supabase.table("expenses").insert({
        "date": str(date),
        "category": category,
        "amount": amount,
        "type": entry_type
    }).execute()

# --- LOAD ---
def load_data(month, year):
    query = supabase.table("expenses").select("*").execute()
    df = pd.DataFrame(query.data)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]

# --- DELETE ---
def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()

# --- STREAMLIT ---
st.set_page_config(page_title="Expense Tracker (₹)", layout="wide")
st.title("💰 Expense Tracker")

# --- SIDEBAR ---
st.sidebar.header("Add Entry")
date = st.sidebar.date_input("Date", datetime.now())
entry_type = st.sidebar.selectbox("Type", ["Income", "Expense"])
category = st.sidebar.text_input("Category")
amount = st.sidebar.number_input("Amount (₹)", min_value=1.0, format="%.2f")

if st.sidebar.button("Add"):
    add_entry(date, category, amount, entry_type)
    st.sidebar.success("Added successfully!")

# --- FILTER ---
today = datetime.now()
month = st.selectbox("Month", range(1, 13), index=today.month-1)
year = st.number_input("Year", value=today.year)

df = load_data(month, year)

# --- ACCOUNTING SUMMARY (MOBILE FRIENDLY) ---
income = df[df["type"]=="Income"]["amount"].sum() if not df.empty else 0
expenses = df[df["type"]=="Expense"]["amount"].sum() if not df.empty else 0
balance = income - expenses

st.markdown("""
<style>
@media (max-width: 768px) {
    .summary-box h2 { font-size: 98%; }
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
for col, title, value in zip(
    [col1, col2, col3],
    ["Income", "Expenses", "Balance"],
    [income, expenses, balance]
):
    col.markdown(f"""
    <div class="summary-box" style="padding:15px;border-radius:12px;background:#001d3d;color:white;text-align:center">
        <h3>{title}</h3>
        <h2>₹{value:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

if df.empty:
    st.info("No records found.")
    st.stop()

# --- PIE CHART ---
cat_df = df.groupby(["category"])["amount"].sum().reset_index()
fig = px.pie(cat_df, names="category", values="amount", hole=0.5)
st.plotly_chart(fig, use_container_width=True)

# --- CATEGORY SEGREGATION (BOTTOM) ---
st.markdown("## 📂 Expense Category Segregation")

seg_df = df[df["type"]=="Expense"].groupby("category")["amount"].sum().reset_index()
st.dataframe(seg_df, use_container_width=True)

bar_fig = px.bar(seg_df, x="category", y="amount", title="Expenses by Category")
st.plotly_chart(bar_fig, use_container_width=True)

# --- RECORD TABLE ---
st.markdown("## 📄 Monthly Records")
st.dataframe(df, use_container_width=True)

# --- DELETE ---
st.markdown("## ❌ Delete Record")
delete_id = st.number_input("Enter ID", min_value=0)
if st.button("Delete"):
    delete_entry(delete_id)
    st.success("Deleted")

# --- PDF EXPORT ---
st.markdown("## 📥 Download Monthly Report")

def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp.name, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Monthly Expense Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Income: ₹{income}", styles["Normal"]))
    elements.append(Paragraph(f"Expenses: ₹{expenses}", styles["Normal"]))
    elements.append(Paragraph(f"Balance: ₹{balance}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    table_data = [df.columns.tolist()] + df.values.tolist()
    elements.append(Table(table_data))

    doc.build(elements)
    return tmp.name

if st.button("Download PDF"):
    pdf_path = generate_pdf()
    with open(pdf_path, "rb") as f:
        st.download_button(
            "📄 Download Monthly PDF",
            f,
            file_name=f"Expense_Report_{month}_{year}.pdf",
            mime="application/pdf"
        )
