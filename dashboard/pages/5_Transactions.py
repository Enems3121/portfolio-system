import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager

st.set_page_config(page_title="Transactions", page_icon="📝", layout="wide")

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB('data/portfolio.db')
    st.session_state.pm = PortfolioManager(st.session_state.db)

db = st.session_state.db
pm = st.session_state.pm

st.title("📝 Transaction History")

# Get all transactions for analysis
# Using a large number to get "all" and then filter in pandas for flexibility
all_transactions = db.get_transactions(days=1000)

if not all_transactions:
    st.info("No transactions found. Add some data in the 'Add Data' page!")
    st.stop()

df = pd.DataFrame(all_transactions)
df['date'] = pd.to_datetime(df['date'])

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Date range filter
min_date = df['date'].min().date()
max_date = df['date'].max().date()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Pillar filter
pillars = ["All"] + sorted(df['pillar'].unique().tolist())
selected_pillar = st.sidebar.selectbox("Pillar", pillars)

# Type filter
types = ["All"] + sorted(df['type'].unique().tolist())
selected_type = st.sidebar.selectbox("Transaction Type", types)

# Apply filters
filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[(filtered_df['date'].dt.date >= start_date) & 
                             (filtered_df['date'].dt.date <= end_date)]

if selected_pillar != "All":
    filtered_df = filtered_df[filtered_df['pillar'] == selected_pillar]

if selected_type != "All":
    filtered_df = filtered_df[filtered_df['type'] == selected_type]

# --- Summary Metrics ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    buys = filtered_df[filtered_df['type'] == 'BUY']['total_amount'].sum()
    st.metric("Total Buys", f"RM {buys:,.2f}")

with col2:
    sells = filtered_df[filtered_df['type'] == 'SELL']['total_amount'].sum()
    st.metric("Total Sells", f"RM {sells:,.2f}")

with col3:
    fees = filtered_df['fees'].sum()
    st.metric("Total Fees", f"RM {fees:,.2f}")

with col4:
    passive = filtered_df[filtered_df['type'].isin(['DIVIDEND', 'INTEREST'])]['total_amount'].sum()
    st.metric("Dividends/Interest", f"RM {passive:,.2f}")

st.markdown("---")

# --- Transactions Table ---
st.subheader("📜 Filtered Transactions")

# Format for display
display_df = filtered_df.copy()
display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
display_df = display_df[['date', 'type', 'pillar', 'symbol', 'quantity', 'price', 'total_amount', 'fees', 'broker', 'notes']]
display_df.columns = ['Date', 'Type', 'Pillar', 'Symbol', 'Qty', 'Price (RM)', 'Total (RM)', 'Fees (RM)', 'Broker', 'Notes']

# Fill NaN with 0 or empty string for display
display_df['Qty'] = display_df['Qty'].fillna(0)
display_df['Price (RM)'] = display_df['Price (RM)'].fillna(0)

st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- CSV Export ---
st.markdown("---")
csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Export to CSV",
    data=csv,
    file_name=f"portfolio_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
    mime='text/csv',
    use_container_width=True
)
