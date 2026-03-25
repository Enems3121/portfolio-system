import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager

st.set_page_config(page_title="BUSINESS Pillar", page_icon="🏢", layout="wide")

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB('data/portfolio.db')
    st.session_state.pm = PortfolioManager(st.session_state.db)

db = st.session_state.db
pm = st.session_state.pm

st.title("🏢 BUSINESS Pillar - Stocks")

# Get BUSINESS holdings
business_holdings = db.get_holdings_by_pillar('BUSINESS')
portfolio = pm.calculate_portfolio_value()

business_value = portfolio['business_value']
business_pct = portfolio['business_pct']
target_pct = 0.30  # 30% target

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total BUSINESS",
        f"RM {business_value:,.2f}",
        delta=f"{business_pct:.1%} of portfolio"
    )

with col2:
    target_value = portfolio['total_value'] * target_pct
    drift_rm = business_value - target_value
    st.metric(
        "vs Target (30%)",
        f"RM {target_value:,.2f}",
        delta=f"{drift_rm:+,.2f}"
    )

with col3:
    num_stocks = len(business_holdings)
    st.metric("Number of Stocks", num_stocks)

with col4:
    total_pnl = sum(h['unrealized_pnl'] or 0 for h in business_holdings)
    st.metric("Total P&L", f"RM {total_pnl:+,.2f}", delta_color="normal")

st.markdown("---")

tab1, tab2 = st.tabs(["📈 Stock Holdings", "🔭 Watchlist"])

with tab1:
    st.subheader("Current Stock Portfolio")
    if business_holdings:
        # Convert to DataFrame
        bdf = pd.DataFrame(business_holdings)
        bdf = bdf[['symbol', 'name', 'quantity', 'avg_cost', 'current_price', 'current_value', 'unrealized_pnl']]
        bdf.columns = ['Symbol', 'Name', 'Qty', 'Avg Cost', 'Price', 'Value (RM)', 'P&L (RM)']
        
        # Formatting
        bdf['Avg Cost'] = bdf['Avg Cost'].apply(lambda x: f"RM {x:,.2f}")
        bdf['Price'] = bdf['Price'].apply(lambda x: f"RM {x:,.2f}")
        bdf['Value (RM)'] = bdf['Value (RM)'].apply(lambda x: f"RM {x:,.2f}")
        bdf['P&L (RM)'] = bdf['P&L (RM)'].apply(lambda x: f"RM {x:+,.2f}")
        
        st.dataframe(bdf, use_container_width=True, hide_index=True)
        
        st.info("""
        💡 **BUSINESS Strategy**: This pillar represents your stake in productive businesses. 
        Focus on value/growth names with strong moats. Avoid over-diversifying (max 8-12 names).
        """)
    else:
        st.warning("No stock holdings yet. Add your first stock in the 'Add Data' page!")

with tab2:
    st.subheader("Watchlist")
    st.info("""
    🔭 **Research Area**: Keep track of businesses you'd buy if the price was right.
    
    *Future Update*: Integration with market data APIs to track relative strength and RSI.
    """)
    
    # Placeholder watchlist
    watchlist_data = [
        {"Symbol": "MAYBANK", "Name": "Malayan Banking", "Reason": "Excellent dividends"},
        {"Symbol": "PBBANK", "Name": "Public Bank", "Reason": "Consistent growth"},
        {"Symbol": "INARI", "Name": "Inari Amertron", "Reason": "Tech/5G play"}
    ]
    st.table(watchlist_data)

st.markdown("---")

# BUSINESS breakdown chart
if business_holdings:
    fig = go.Figure(data=[go.Pie(
        labels=[h['symbol'] for h in business_holdings],
        values=[h['current_value'] for h in business_holdings],
        hole=0.4,
        marker=dict(colors=['#1f77b4', '#3498db', '#5dade2', '#85c1e9'])
    )])
    
    fig.update_layout(
        title="Stock Allocation within BUSINESS",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
