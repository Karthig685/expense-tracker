import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import calendar
from streamlit_option_menu import option_menu
import time

# --- SUPABASE SETUP ---
url = "https://ykgucpcjxwddnwznkqfa.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlrZ3VjcGNqeHdkZG53em5rcWZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ1Njg1MjgsImV4cCI6MjAwMDE0NDUyOH0.A-Gwlhbrb9QEa9u9C2Ghobm2zPw-zaLLUFdKU29rrP8"
supabase: Client = create_client(url, key)

# --- CATEGORY CONFIGURATION ---
CATEGORIES = [
    "Groceries", "Food", "Utilities", "Shopping", "Travel",
    "Healthcare", "Subscriptions", "Rent", "Transport", 
    "Entertainment", "Education", "Other"
]

INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Other"]

# --- DATA FUNCTIONS ---
def add_entry(date, category, amount, entry_type="Expense"):
    try:
        data = {
            "date": str(date),
            "category": category,
            "amount": float(amount),
            "type": entry_type
        }
        result = supabase.table("expenses").insert(data).execute()
        return result
    except Exception as e:
        st.error(f"Error adding entry: {str(e)}")
        return None

def load_data(month=None, year=None):
    try:
        query = supabase.table("expenses").select("*").execute()
        df = pd.DataFrame(query.data)
        
        if df.empty:
            return df
        
        df["date"] = pd.to_datetime(df["date"])
        
        if month and year:
            df = df[(df["date"].dt.month == month) & (df["date"].dt.year == year)]
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def delete_entry(entry_id):
    supabase.table("expenses").delete().eq("id", entry_id).execute()

# --- STREAMLIT CONFIG ---
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    
    .month-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
    }
    
    /* Card styling */
    .expense-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #4F46E5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        cursor: pointer;
    }
    
    .expense-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Checkbox styling */
    .stCheckbox > div > div {
        align-items: center;
    }
    
    /* Progress bar styling */
    .category-bar {
        height: 8px;
        background: #e2e8f0;
        border-radius: 4px;
        margin: 8px 0;
        overflow: hidden;
    }
    
    .category-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
        transition: width 0.5s ease;
    }
    
    /* Summary cards */
    .summary-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px;
    }
    
    .summary-title {
        font-size: 0.9rem;
        color: #718096;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .summary-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #2d3748;
    }
    
    .summary-value.income {
        color: #10B981;
    }
    
    .summary-value.expense {
        color: #EF4444;
    }
    
    .summary-value.balance.positive {
        color: #10B981;
    }
    
    .summary-value.balance.negative {
        color: #EF4444;
    }
    
    /* Total display */
    .total-display {
        font-size: 2.5rem;
        font-weight: 800;
        color: #2d3748;
        text-align: center;
        margin: 20px 0;
        padding: 20px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Add button */
    .add-button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 32px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
    
    .add-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
    }
    
    /* Mobile optimization */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .month-header {
            font-size: 1.5rem;
        }
        .summary-value {
            font-size: 1.5rem;
        }
        .total-display {
            font-size: 2rem;
            padding: 15px;
        }
    }
    
    /* Category colors */
    .category-groceries { border-left-color: #10B981; }
    .category-food { border-left-color: #3B82F6; }
    .category-utilities { border-left-color: #F59E0B; }
    .category-shopping { border-left-color: #8B5CF6; }
    .category-travel { border-left-color: #EF4444; }
    .category-healthcare { border-left-color: #EC4899; }
    .category-subscriptions { border-left-color: #14B8A6; }
    .category-rent { border-left-color: #F97316; }
    .category-transport { border-left-color: #6366F1; }
    .category-entertainment { border-left-color: #8B5CF6; }
    .category-education { border-left-color: #0EA5E9; }
    .category-other { border-left-color: #94A3B8; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'show_add_form' not in st.session_state:
    st.session_state.show_add_form = False
if 'current_view' not in st.session_state:
    st.session_state.current_view = "dashboard"

# --- APP HEADER ---
st.markdown('<h1 class="main-header">Expense Tracker</h1>', unsafe_allow_html=True)

# --- MONTH/YEAR SELECTOR ---
today = datetime.now()
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    month = st.selectbox(
        "",
        list(range(1, 13)),
        format_func=lambda x: calendar.month_name[x],
        index=today.month-1,
        label_visibility="collapsed"
    )

with col2:
    year = st.selectbox(
        "",
        list(range(2020, today.year + 3)),
        index=today.year - 2020,
        label_visibility="collapsed"
    )

with col3:
    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("📅 Today", use_container_width=True):
            month = today.month
            year = today.year
            st.rerun()
    with col_b:
        if st.button("📊 Overview", use_container_width=True):
            st.session_state.current_view = "overview"
            st.rerun()

# Display month header
month_name = calendar.month_name[month]
st.markdown(f'<h2 class="month-header">{month_name} {year}</h2>', unsafe_allow_html=True)

# --- LOAD DATA ---
df = load_data(month, year)

# --- ADD EXPENSE BUTTON ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("+ Add Expense", key="add_expense_main", use_container_width=True, type="primary"):
        st.session_state.show_add_form = True

# --- ADD EXPENSE FORM ---
if st.session_state.show_add_form:
    with st.expander("➕ Add New Expense", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date_input = st.date_input("Date", datetime.now())
            category = st.selectbox("Category", CATEGORIES)
        
        with col2:
            amount = st.number_input("Amount (₹)", min_value=1.0, value=1000.0, step=100.0, format="%.2f")
        
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            if st.button("💾 Save", use_container_width=True):
                add_entry(date_input, category, amount, "Expense")
                st.success("Expense added successfully! ✅")
                st.session_state.show_add_form = False
                time.sleep(1)
                st.rerun()
        
        with col_b:
            if st.button("✖️ Cancel", use_container_width=True):
                st.session_state.show_add_form = False
                st.rerun()

# --- DASHBOARD CONTENT ---
if not df.empty:
    # Filter expenses only
    expense_df = df[df["type"] == "Expense"]
    income_df = df[df["type"] == "Income"]
    
    if not expense_df.empty:
        # Calculate category totals and percentages
        category_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=False)
        total_expenses = category_totals.sum()
        
        # Create expense cards
        for category, amount in category_totals.items():
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            
            # Create category-specific CSS class
            category_class = category.lower().replace(" ", "-")
            
            with st.container():
                # Create columns for checkbox and content
                col1, col2 = st.columns([0.1, 0.9])
                
                with col1:
                    # Checkbox
                    st.checkbox("", key=f"check_{category}", label_visibility="collapsed")
                
                with col2:
                    # Expense card
                    st.markdown(f"""
                    <div class="expense-card category-{category_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: 600; font-size: 1.1rem; color: #2d3748;">
                                    {category} ({percentage:.1f}%)
                                </div>
                                <div class="category-bar">
                                    <div class="category-fill" style="width: {percentage}%"></div>
                                </div>
                            </div>
                            <div style="font-weight: 700; font-size: 1.2rem; color: #4F46E5;">
                                ₹{amount:,.2f}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Display total
        st.markdown(f"""
        <div style="text-align: center; margin-top: 30px;">
            <div style="font-size: 0.9rem; color: #718096; text-transform: uppercase; letter-spacing: 0.1em;">
                Total
            </div>
            <div class="total-display">
                ₹{total_expenses:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- SUMMARY CARDS ---
    st.markdown("---")
    
    income_total = income_df["amount"].sum() if not income_df.empty else 0
    expense_total = expense_df["amount"].sum() if not expense_df.empty else 0
    balance = income_total - expense_total
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Income</div>
            <div class="summary-value income">₹{income_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Expenses</div>
            <div class="summary-value expense">₹{expense_total:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        balance_class = "positive" if balance >= 0 else "negative"
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-title">Balance</div>
            <div class="summary-value balance {balance_class}">₹{balance:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # --- PIE CHART VISUALIZATION ---
    if not expense_df.empty:
        st.markdown("---")
        st.markdown("### 📊 Expense Breakdown")
        
        fig = px.pie(
            expense_df, 
            values='amount', 
            names='category',
            color_discrete_sequence=px.colors.sequential.Plasma,
            hole=0.4
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>₹%{value:,.2f}<br>%{percent}'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # --- TRANSACTION HISTORY ---
    st.markdown("---")
    st.markdown("### 📋 Recent Transactions")
    
    # Get recent transactions
    recent_df = df.sort_values("date", ascending=False).head(10)
    
    for _, row in recent_df.iterrows():
        is_income = row["type"] == "Income"
        color = "#10B981" if is_income else "#EF4444"
        symbol = "⬆️" if is_income else "⬇️"
        
        with st.container():
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            
            with col1:
                st.markdown(f"**{row['category']}**")
                st.caption(f"{row['date'].strftime('%b %d')}")
            
            with col2:
                st.markdown(f"<span style='color: {color};'>{row['type']}</span>", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"<div style='text-align: right; color: {color}; font-weight: 600;'>{symbol} ₹{row['amount']:,.2f}</div>", unsafe_allow_html=True)
            
            st.divider()
    
    # --- QUICK ADD INCOME ---
    st.markdown("---")
    with st.expander("💸 Add Quick Income"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            income_category = st.selectbox("Category", INCOME_CATEGORIES, key="quick_income_cat")
        
        with col2:
            income_amount = st.number_input("Amount", min_value=1.0, value=5000.0, step=1000.0, key="quick_income_amt")
        
        with col3:
            if st.button("Add Income", key="add_income_btn", use_container_width=True):
                add_entry(date.today(), income_category, income_amount, "Income")
                st.success("Income added! ✅")
                st.rerun()
    
    # --- DELETE FUNCTIONALITY ---
    st.markdown("---")
    with st.expander("🗑️ Delete Transaction"):
        delete_id = st.number_input("Enter Transaction ID to delete", min_value=1, value=1, step=1)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                delete_entry(int(delete_id))
                st.success("Transaction deleted! ✅")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("🔍 Show IDs", use_container_width=True):
                st.dataframe(df[['id', 'date', 'category', 'amount', 'type']], use_container_width=True)

else:
    # Empty state
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px; background: linear-gradient(135deg, #667eea0d 0%, #764ba20d 100%); border-radius: 20px; margin: 40px 0;">
        <div style="font-size: 5rem; margin-bottom: 20px;">📊</div>
        <h3 style="color: #4F46E5; margin-bottom: 10px;">No expenses tracked yet</h3>
        <p style="color: #718096; max-width: 500px; margin: 0 auto 30px;">
            Start tracking your expenses to see insights and manage your budget better.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick add suggestions
    st.markdown("### 💡 Quick Start")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🍔 Add Food Expense", use_container_width=True):
            add_entry(date.today(), "Food", 500, "Expense")
            st.success("Sample food expense added! ✅")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("🛒 Add Groceries", use_container_width=True):
            add_entry(date.today(), "Groceries", 1500, "Expense")
            st.success("Sample groceries added! ✅")
            time.sleep(1)
            st.rerun()
    
    with col3:
        if st.button("💰 Add Salary", use_container_width=True):
            add_entry(date.today(), "Salary", 50000, "Income")
            st.success("Sample salary added! ✅")
            time.sleep(1)
            st.rerun()

# --- FOOTER ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #94A3B8; font-size: 0.9rem; padding: 20px;'>"
           "Expense Tracker • Made with ❤️ • Track Smart, Save Smarter"
           "</div>", unsafe_allow_html=True)
