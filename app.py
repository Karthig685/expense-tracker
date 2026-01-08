import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import calendar
import numpy as np

# --- SUPABASE SETUP ---
url = "https://ykgucpcjxwddnwznkqfa.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrZ3VjcGNqeHdkZG53em5rcWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MjgsImV4cCI6MjAwMDE0NDUyOH0.A-Gwlhbrb9QEa9u9C2Ghobm2zPw-zaLLUFdKU29rrP8"
supabase: Client = create_client(url, key)

# --- CATEGORY CONFIGURATION ---
INCOME_CATEGORIES = ["Salary", "Bonus", "Freelance", "Investment", "Gift", "Other"]
EXPENSE_CATEGORIES = [
    "Food", "Groceries", "Transport", "Snacks", "Fashion", 
    "Rent", "Bills", "Utilities", "Health Care", "Electronics", 
    "Entertainment", "Education", "Travel", "Other"
]
SAVINGS_CATEGORIES = ["Emergency Fund", "Investment", "Retirement", "Vacation", "Big Purchase", "Other"]

# --- DATA FUNCTIONS ---
def add_entry(date, category, amount, entry_type, description=""):
    data = {
        "date": str(date),
        "category": category,
        "amount": float(amount),
        "type": entry_type,
        "description": description
    }
    result = supabase.table("expenses").insert(data).execute()
    return result

def load_data(month=None, year=None):
    query = supabase.table("expenses").select("*").order("date", desc=True).execute()
    df = pd.DataFrame(query.data)
    
    if df.empty:
        return df
    
    df["date"] = pd.to_datetime(df["date"])
    
    if month and year:
        df = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]
    
    return df

def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()

def get_savings_rate(income, expenses):
    if income > 0:
        return ((income - expenses) / income) * 100
    return 0

# --- STREAMLIT CONFIG ---
st.set_page_config(
    page_title="💰 Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# --- CUSTOM CSS FOR MOBILE OPTIMIZATION ---
st.markdown("""
<style>
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.5rem !important;
            padding: 10px !important;
        }
        .stButton button {
            width: 100% !important;
            margin: 5px 0 !important;
        }
        .card {
            padding: 10px !important;
            margin: 5px 0 !important;
        }
        .stSelectbox, .stNumberInput, .stDateInput {
            width: 100% !important;
        }
    }
    
    /* Card styling */
    .card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .card-income {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .card-expense {
        background: linear-gradient(135deg, #f46b45 0%, #eea849 100%);
    }
    
    .card-savings {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    .card-balance {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        color: #333;
    }
    
    /* Progress bar styling */
    .progress-container {
        width: 100%;
        background-color: #f0f0f0;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .progress-bar {
        height: 20px;
        border-radius: 10px;
        text-align: center;
        line-height: 20px;
        color: white;
        font-weight: bold;
        transition: width 0.5s ease-in-out;
    }
    
    /* Category chips */
    .category-chip {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        margin: 3px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Mobile-friendly tabs */
    .mobile-tabs {
        display: flex;
        justify-content: space-around;
        margin: 10px 0;
        border-bottom: 2px solid #e0e0e0;
    }
    
    .mobile-tab {
        padding: 10px 0;
        text-align: center;
        flex-grow: 1;
        cursor: pointer;
        border-bottom: 3px solid transparent;
        font-weight: 500;
    }
    
    .mobile-tab.active {
        border-bottom: 3px solid #667eea;
        color: #667eea;
        font-weight: bold;
    }
    
    /* Quick action buttons */
    .quick-action {
        display: flex;
        justify-content: space-around;
        margin: 15px 0;
    }
    
    .quick-btn {
        padding: 10px;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- APP TITLE ---
st.markdown('<h1 class="main-header">💰 Personal Finance Tracker</h1>', unsafe_allow_html=True)

# --- MOBILE TABS FOR NAVIGATION ---
tabs = ["📊 Dashboard", "➕ Add Transaction", "📋 History", "🎯 Savings Goals"]
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "📊 Dashboard"

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.current_tab = "📊 Dashboard"
with col2:
    if st.button("➕ Add", use_container_width=True):
        st.session_state.current_tab = "➕ Add Transaction"
with col3:
    if st.button("📋 History", use_container_width=True):
        st.session_state.current_tab = "📋 History"
with col4:
    if st.button("🎯 Savings", use_container_width=True):
        st.session_state.current_tab = "🎯 Savings Goals"

# --- QUICK ACTIONS (Mobile-friendly) ---
st.markdown('<div class="quick-action">', unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💰", help="Quick Income", use_container_width=True):
        st.session_state.quick_income = True
        st.session_state.current_tab = "➕ Add Transaction"
with col2:
    if st.button("💸", help="Quick Expense", use_container_width=True):
        st.session_state.quick_expense = True
        st.session_state.current_tab = "➕ Add Transaction"
with col3:
    if st.button("🏦", help="Quick Savings", use_container_width=True):
        st.session_state.quick_savings = True
        st.session_state.current_tab = "➕ Add Transaction"
with col4:
    if st.button("📈", help="View Stats", use_container_width=True):
        st.session_state.current_tab = "📊 Dashboard"
st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD TAB ---
if st.session_state.current_tab == "📊 Dashboard":
    # --- MONTH/YEAR SELECTOR ---
    today = datetime.now()
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        month = st.selectbox(
            "Month",
            list(range(1, 13)),
            format_func=lambda x: calendar.month_name[x],
            index=today.month-1
        )
    with col2:
        year = st.selectbox(
            "Year",
            list(range(2020, today.year + 2)),
            index=today.year - 2020
        )
    with col3:
        if st.button("📅 Current Month", use_container_width=True):
            month = today.month
            year = today.year
    
    # --- LOAD DATA ---
    df = load_data(month, year)
    
    if df.empty:
        st.info(f"📭 No records for {calendar.month_name[month]} {year}. Add your first transaction!")
        
        # Quick add suggestions
        st.markdown("### 💡 Quick Start")
        quick_cols = st.columns(3)
        with quick_cols[0]:
            if st.button("Add Salary 💰", use_container_width=True):
                add_entry(today, "Salary", 50000, "Income", "Monthly salary")
                st.success("Sample salary added!")
        with quick_cols[1]:
            if st.button("Add Expense 💸", use_container_width=True):
                add_entry(today, "Food", 1500, "Expense", "Monthly groceries")
                st.success("Sample expense added!")
        with quick_cols[2]:
            if st.button("Add Savings 🏦", use_container_width=True):
                add_entry(today, "Emergency Fund", 10000, "Savings", "Monthly savings")
                st.success("Sample savings added!")
        
        st.stop()
    
    # --- CALCULATE METRICS ---
    income = df[df["type"] == "Income"]["amount"].sum()
    expenses = df[df["type"] == "Expense"]["amount"].sum()
    savings = df[df["type"] == "Savings"]["amount"].sum()
    balance = income - expenses - savings
    savings_rate = get_savings_rate(income, expenses)
    
    # --- KPI CARDS ---
    st.markdown("### 📈 Financial Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="card card-income">
            <h4>Income</h4>
            <h2>₹{income:,.0f}</h2>
            <small>Total received</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="card card-expense">
            <h4>Expenses</h4>
            <h2>₹{expenses:,.0f}</h2>
            <small>Total spent</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="card card-savings">
            <h4>Savings</h4>
            <h2>₹{savings:,.0f}</h2>
            <small>{savings_rate:.1f}% of income</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        bal_color = "#2d6a4f" if balance >= 0 else "#e63946"
        st.markdown(f"""
        <div class="card card-balance">
            <h4>Balance</h4>
            <h2 style="color: {bal_color}">₹{balance:,.0f}</h2>
            <small>Remaining balance</small>
        </div>
        """, unsafe_allow_html=True)
    
    # --- SAVINGS PROGRESS ---
    st.markdown("### 🎯 Savings Progress")
    target_savings = income * 0.2  # 20% of income as target
    savings_percentage = (savings / target_savings * 100) if target_savings > 0 else 0
    
    col1, col2 = st.columns([3, 1])
    with col1:
        progress_html = f"""
        <div class="progress-container">
            <div class="progress-bar" style="width: {min(savings_percentage, 100)}%; background: {'#4CAF50' if savings_percentage >= 100 else '#2196F3'}">
                {savings_percentage:.1f}%
            </div>
        </div>
        """
        st.markdown(progress_html, unsafe_allow_html=True)
        st.caption(f"Target: ₹{target_savings:,.0f} (20% of income)")
    
    with col2:
        if savings_percentage >= 100:
            st.success("🎉 Target achieved!")
        elif savings_percentage >= 80:
            st.info("👍 Almost there!")
        else:
            st.warning("📈 Keep saving!")
    
    # --- CATEGORY BREAKDOWN ---
    st.markdown("### 📊 Category Breakdown")
    
    # Expense breakdown
    expense_df = df[df["type"] == "Expense"]
    if not expense_df.empty:
        fig1 = px.pie(expense_df, names="category", values="amount", 
                     title="Expense Categories", hole=0.4)
        st.plotly_chart(fig1, use_container_width=True)
    
    # Savings breakdown
    savings_df = df[df["type"] == "Savings"]
    if not savings_df.empty:
        fig2 = px.pie(savings_df, names="category", values="amount",
                     title="Savings Allocation", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    
    # --- MONTHLY TREND ---
    st.markdown("### 📈 Monthly Trend")
    monthly_data = df.groupby([df['date'].dt.day, 'type'])['amount'].sum().unstack(fill_value=0)
    fig3 = px.line(monthly_data, title="Daily Cash Flow", markers=True)
    fig3.update_layout(xaxis_title="Day of Month", yaxis_title="Amount (₹)")
    st.plotly_chart(fig3, use_container_width=True)

# --- ADD TRANSACTION TAB ---
elif st.session_state.current_tab == "➕ Add Transaction":
    st.markdown("### ➕ Add New Transaction")
    
    # Quick preset handling
    if 'quick_income' in st.session_state and st.session_state.quick_income:
        preset_type = "Income"
        preset_category = "Salary"
        st.session_state.quick_income = False
    elif 'quick_expense' in st.session_state and st.session_state.quick_expense:
        preset_type = "Expense"
        preset_category = "Food"
        st.session_state.quick_expense = False
    elif 'quick_savings' in st.session_state and st.session_state.quick_savings:
        preset_type = "Savings"
        preset_category = "Emergency Fund"
        st.session_state.quick_savings = False
    else:
        preset_type = "Expense"
        preset_category = "Food"
    
    # Form in columns for better mobile layout
    col1, col2 = st.columns(2)
    
    with col1:
        entry_type = st.selectbox(
            "Type",
            ["Income", "Expense", "Savings"],
            index=["Income", "Expense", "Savings"].index(preset_type)
        )
        
        if entry_type == "Income":
            category = st.selectbox("Category", INCOME_CATEGORIES, 
                                  index=INCOME_CATEGORIES.index(preset_category) if preset_category in INCOME_CATEGORIES else 0)
        elif entry_type == "Expense":
            category = st.selectbox("Category", EXPENSE_CATEGORIES,
                                  index=EXPENSE_CATEGORIES.index(preset_category) if preset_category in EXPENSE_CATEGORIES else 0)
        else:
            category = st.selectbox("Category", SAVINGS_CATEGORIES,
                                  index=SAVINGS_CATEGORIES.index(preset_category) if preset_category in SAVINGS_CATEGORIES else 0)
    
    with col2:
        amount = st.number_input("Amount (₹)", min_value=1.0, value=1000.0, step=100.0, format="%.2f")
        date_input = st.date_input("Date", datetime.now())
    
    description = st.text_area("Description (optional)", placeholder="e.g., Monthly salary, Groceries shopping...")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("💾 Save", type="primary", use_container_width=True):
            add_entry(date_input, category, amount, entry_type, description)
            st.success("✅ Transaction saved successfully!")
            st.balloons()
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.rerun()
    
    # Quick amount suggestions
    st.markdown("#### 💡 Quick Amounts")
    quick_amounts = [500, 1000, 2000, 5000, 10000]
    cols = st.columns(len(quick_amounts))
    for idx, amt in enumerate(quick_amounts):
        with cols[idx]:
            if st.button(f"₹{amt}", use_container_width=True):
                st.session_state.quick_amount = amt
                st.rerun()

# --- HISTORY TAB ---
elif st.session_state.current_tab == "📋 History":
    st.markdown("### 📋 Transaction History")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_type = st.selectbox("Filter by Type", ["All", "Income", "Expense", "Savings"])
    with col2:
        filter_category = st.selectbox("Filter by Category", ["All"] + INCOME_CATEGORIES + EXPENSE_CATEGORIES + SAVINGS_CATEGORIES)
    with col3:
        sort_order = st.selectbox("Sort by", ["Newest First", "Oldest First", "Amount (High to Low)", "Amount (Low to High)"])
    
    # Load all data
    df = load_data()
    
    if not df.empty:
        # Apply filters
        if filter_type != "All":
            df = df[df["type"] == filter_type]
        if filter_category != "All":
            df = df[df["category"] == filter_category]
        
        # Apply sorting
        if sort_order == "Newest First":
            df = df.sort_values("date", ascending=False)
        elif sort_order == "Oldest First":
            df = df.sort_values("date", ascending=True)
        elif sort_order == "Amount (High to Low)":
            df = df.sort_values("amount", ascending=False)
        elif sort_order == "Amount (Low to High)":
            df = df.sort_values("amount", ascending=True)
        
        # Display transactions with color coding
        for _, row in df.iterrows():
            color = "#4CAF50" if row["type"] == "Income" else ("#FF9800" if row["type"] == "Savings" else "#F44336")
            emoji = "💰" if row["type"] == "Income" else ("🏦" if row["type"] == "Savings" else "💸")
            
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**{row['category']}**")
                    st.caption(f"{row['date'].strftime('%b %d, %Y')}")
                    if row["description"]:
                        st.caption(f"📝 {row['description']}")
                with col2:
                    st.markdown(f"**{row['type']}**")
                with col3:
                    st.markdown(f"<h3 style='color: {color}; text-align: right;'>{emoji} ₹{row['amount']:,.0f}</h3>", 
                              unsafe_allow_html=True)
                
                # Delete button
                if st.button(f"Delete", key=f"delete_{row['id']}", use_container_width=True):
                    delete_entry(row["id"])
                    st.success("Transaction deleted!")
                    st.rerun()
                
                st.divider()
    else:
        st.info("No transactions yet. Add your first transaction!")

# --- SAVINGS GOALS TAB ---
elif st.session_state.current_tab == "🎯 Savings Goals":
    st.markdown("### 🎯 Savings Goals & Progress")
    
    # Savings goals input
    col1, col2 = st.columns(2)
    with col1:
        goal_name = st.text_input("Goal Name", placeholder="e.g., New Laptop, Vacation")
        goal_amount = st.number_input("Target Amount (₹)", min_value=1000, value=50000, step=1000)
    with col2:
        deadline = st.date_input("Target Date", min_value=date.today())
        priority = st.select_slider("Priority", ["Low", "Medium", "High"])
    
    if st.button("➕ Add Goal", type="primary", use_container_width=True):
        st.success(f"Goal '{goal_name}' added!")
    
    st.divider()
    
    # Sample savings goals (you can connect this to your database)
    st.markdown("### 🏆 Active Goals")
    
    goals = [
        {"name": "Emergency Fund", "target": 100000, "saved": 75000, "deadline": "2024-12-31", "priority": "High"},
        {"name": "Vacation", "target": 50000, "saved": 20000, "deadline": "2024-06-30", "priority": "Medium"},
        {"name": "New Laptop", "target": 80000, "saved": 45000, "deadline": "2024-08-15", "priority": "Medium"},
        {"name": "Investment", "target": 200000, "saved": 120000, "deadline": "2024-12-31", "priority": "High"},
    ]
    
    for goal in goals:
        progress = (goal["saved"] / goal["target"]) * 100
        priority_color = {"High": "#F44336", "Medium": "#FF9800", "Low": "#4CAF50"}[goal["priority"]]
        
        with st.expander(f"🎯 {goal['name']} - ₹{goal['saved']:,.0f}/₹{goal['target']:,.0f}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.progress(progress / 100)
                st.caption(f"Progress: {progress:.1f}% • Due: {goal['deadline']}")
            with col2:
                st.markdown(f"<span style='color: {priority_color}; font-weight: bold;'>{goal['priority']}</span>", 
                          unsafe_allow_html=True)
            
            # Quick add to this goal
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Add ₹1000", key=f"add_1k_{goal['name']}", use_container_width=True):
                    st.success(f"Added ₹1000 to {goal['name']}!")
            with col2:
                if st.button(f"Add ₹5000", key=f"add_5k_{goal['name']}", use_container_width=True):
                    st.success(f"Added ₹5000 to {goal['name']}!")
            with col3:
                if st.button("Mark Complete", key=f"complete_{goal['name']}", use_container_width=True):
                    st.balloons()
                    st.success(f"🎉 Congratulations on completing {goal['name']}!")
    
    # Savings tips
    st.markdown("### 💡 Savings Tips")
    tips = [
        "💡 **Automate your savings** - Set up automatic transfers to savings account",
        "💡 **50/30/20 rule** - 50% needs, 30% wants, 20% savings",
        "💡 **Track small expenses** - They add up quickly!",
        "💡 **Review monthly** - Check where you can cut unnecessary expenses",
        "💡 **Save bonuses & raises** - Don't inflate your lifestyle immediately"
    ]
    
    for tip in tips:
        st.info(tip)

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
           "💰 Personal Finance Tracker • Track Smart, Save Smarter • Made with ❤️"
           "</div>", unsafe_allow_html=True)
