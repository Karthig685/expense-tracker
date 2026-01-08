import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# --- SUPABASE SETUP ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "https://ykgucpcjxwddnwznkqfa.supabase.co")
    key = st.secrets.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrZ3VjcGNqeHdkZG53em5rcWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MjgsImV4cCI6MjAwMDE0NDUyOH0.A-Gwlhbrb9QEa9u9C2Ghobm2zPw-zaLLUFdKU29rrP8")
    return create_client(url, key)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"Failed to connect to database: {str(e)}")
    supabase = None

# --- INSERT NEW ENTRY ---
def add_entry(date, category, amount, entry_type):
    try:
        if supabase:
            supabase.table("expenses").insert({
                "date": str(date),
                "category": category,
                "amount": amount,
                "type": entry_type
            }).execute()
            return True
        return False
    except Exception as e:
        st.error(f"Error adding entry: {str(e)}")
        return False

# --- FETCH DATA ---
def load_data(month, year):
    if not supabase:
        return pd.DataFrame()
    
    try:
        # Fetch all data first (we'll filter locally)
        query = supabase.table("expenses").select("*").execute()
        df = pd.DataFrame(query.data)
        
        if df.empty:
            return df
        
        # Ensure date column exists
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            # Filter by month/year
            df = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# --- DELETE ENTRY ---
def delete_entry(entry_id):
    try:
        if supabase and entry_id > 0:
            supabase.table("expenses").delete().eq("id", entry_id).execute()
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting entry: {str(e)}")
        return False

# --- STREAMLIT CONFIG ---
st.set_page_config(page_title="Expense Tracker (₹)", layout="wide")
st.title("💰 Expense Tracker")

# Initialize session state for data refresh
if 'refresh_key' not in st.session_state:
    st.session_state.refresh_key = 0

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
    if add_entry(date, category, amount, entry_type):
        st.sidebar.success("Added successfully!")
        st.session_state.refresh_key += 1
        time.sleep(0.5)
        st.rerun()

# --- MONTH FILTER ---
today = datetime.now()
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("Month", list(range(1, 13)), index=today.month-1)
with col2:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=today.year)

# --- LOAD DATA ---
df = load_data(month, year)

# --- MOBILE-OPTIMIZED ACCOUNTING SUMMARY ---
st.markdown("### 📘 Accounting Summary")

# Handle empty data gracefully
if df.empty:
    income = expenses = savings = balance = 0
else:
    income = df[df["type"] == "Income"]["amount"].sum() if "type" in df.columns else 0
    expenses = df[df["type"] == "Expense"]["amount"].sum() if "type" in df.columns else 0
    savings = df[df["type"] == "Savings"]["amount"].sum() if "type" in df.columns else 0
    balance = income - expenses - savings

# Responsive grid for mobile (2x2 layout)
colA, colB = st.columns(2)

with colA:
    st.markdown(f"""
    <div style='background:#0a9396;padding:12px;border-radius:10px;text-align:center;margin-bottom:8px;min-height:100px;'>
        <h4 style='color:white;margin:0;font-size:14px;font-weight:600;'>Income</h4>
        <h3 style='color:#d8f3dc;margin:8px 0;font-size:20px;font-weight:700;'>₹{income:,.0f}</h3>
        <p style='color:#d8f3dc;margin:0;font-size:12px;opacity:0.9;'>₹{income:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

with colB:
    st.markdown(f"""
    <div style='background:#9b2226;padding:12px;border-radius:10px;text-align:center;margin-bottom:8px;min-height:100px;'>
        <h4 style='color:white;margin:0;font-size:14px;font-weight:600;'>Expenses</h4>
        <h3 style='color:#fcd5ce;margin:8px 0;font-size:20px;font-weight:700;'>₹{expenses:,.0f}</h3>
        <p style='color:#fcd5ce;margin:0;font-size:12px;opacity:0.9;'>₹{expenses:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

colC, colD = st.columns(2)

bal_color = "#2d6a4f" if balance >= 0 else "#e63946"
with colC:
    st.markdown(f"""
    <div style='background:#001d3d;padding:12px;border-radius:10px;text-align:center;margin-bottom:8px;min-height:100px;'>
        <h4 style='color:white;margin:0;font-size:14px;font-weight:600;'>Balance</h4>
        <h3 style='color:{bal_color};margin:8px 0;font-size:20px;font-weight:700;'>₹{balance:,.0f}</h3>
        <p style='color:{bal_color};margin:0;font-size:12px;opacity:0.9;'>{'+' if balance >= 0 else ''}₹{abs(balance):,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

with colD:
    st.markdown(f"""
    <div style='background:#6a994e;padding:12px;border-radius:10px;text-align:center;margin-bottom:8px;min-height:100px;'>
        <h4 style='color:white;margin:0;font-size:14px;font-weight:600;'>Savings</h4>
        <h3 style='color:#f0efeb;margin:8px 0;font-size:20px;font-weight:700;'>₹{savings:,.0f}</h3>
        <p style='color:#f0efeb;margin:0;font-size:12px;opacity:0.9;'>₹{savings:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

# Add a compact metric row for quick glance
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
mcol1, mcol2, mcol3 = st.columns(3)
with mcol1:
    st.metric("Income", f"₹{income:,.0f}", delta=f"₹{income:,.0f}")
with mcol2:
    st.metric("Expenses", f"₹{expenses:,.0f}", delta=f"-₹{expenses:,.0f}")
with mcol3:
    delta_pct = f"{(balance/income*100):.1f}%" if income > 0 else "0%"
    st.metric("Net", f"₹{balance:,.0f}", delta=delta_pct)

if df.empty:
    st.info("No records for this month.")
else:
    # --- CATEGORY BREAKDOWN ---
    st.markdown("### 📊 Category Breakdown")
    cat_df = df.groupby(["category", "type"])["amount"].sum().reset_index()
    
    if not cat_df.empty:
        fig = px.pie(cat_df, names="category", values="amount", hole=0.4, 
                     title="Category Distribution")
        fig.update_layout(font=dict(size=12))
        st.plotly_chart(fig, use_container_width=True)
    
    # --- TABLE VIEW ---
    st.markdown("### 📄 Detailed Records")
    
    # Format the dataframe for better display
    display_df = df.copy()
    if "date" in display_df.columns:
        display_df["date"] = display_df["date"].dt.strftime('%Y-%m-%d')
    if "amount" in display_df.columns:
        display_df["amount"] = display_df["amount"].apply(lambda x: f"₹{x:,.2f}")
    
    # Reorder columns for better mobile view
    preferred_order = ["date", "type", "category", "amount", "id"]
    available_cols = [col for col in preferred_order if col in display_df.columns]
    display_df = display_df[available_cols]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- DELETE ENTRY ---
st.markdown("### ❌ Delete Record")
del_col1, del_col2 = st.columns([1, 2])
with del_col1:
    delete_id = st.number_input("Enter ID to delete", min_value=0, value=0, 
                                key=f"delete_{st.session_state.refresh_key}")
with del_col2:
    if st.button("🗑️ Delete Entry", type="secondary", use_container_width=True):
        if delete_id > 0:
            if delete_entry(delete_id):
                st.success(f"Entry #{delete_id} deleted!")
                st.session_state.refresh_key += 1
                time.sleep(0.5)
                st.rerun()
        else:
            st.warning("Please enter a valid ID")

# Add a refresh button
if st.button("🔄 Refresh Data"):
    st.session_state.refresh_key += 1
    st.rerun()

# Error message if no database connection
if not supabase:
    st.error("⚠️ Database connection failed. Please check your Supabase credentials.")
