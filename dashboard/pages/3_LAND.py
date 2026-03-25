import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager

st.set_page_config(page_title="LAND Pillar", page_icon="🏠", layout="wide")

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB('data/portfolio.db')
    st.session_state.pm = PortfolioManager(st.session_state.db)

db = st.session_state.db
pm = st.session_state.pm

st.title("🏠 LAND Pillar - REITs & Gold")

# Get LAND holdings
land_holdings = db.get_holdings_by_pillar('LAND')
portfolio = pm.calculate_portfolio_value()

land_value = portfolio['land_value']
land_pct = portfolio['land_pct']
target_pct = 0.20  # 20% target

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total LAND",
        f"RM {land_value:,.2f}",
        delta=f"{land_pct:.1%} of portfolio"
    )

with col2:
    target_value = portfolio['total_value'] * target_pct
    drift_rm = land_value - target_value
    st.metric(
        "vs Target (20%)",
        f"RM {target_value:,.2f}",
        delta=f"{drift_rm:+,.2f}"
    )

with col3:
    # REITs portion
    reits = [h for h in land_holdings if h['asset_type'] == 'REIT']
    reits_value = sum(h['current_value'] for h in reits)
    st.metric(
        "REITs Value",
        f"RM {reits_value:,.2f}",
        delta=f"{(reits_value/land_value*100) if land_value > 0 else 0:.1f}% of pillar"
    )

with col4:
    # Gold/Other portion
    others = [h for h in land_holdings if h['asset_type'] != 'REIT']
    others_value = sum(h['current_value'] for h in others)
    st.metric(
        "Gold & Other",
        f"RM {others_value:,.2f}",
        delta=f"{(others_value/land_value*100) if land_value > 0 else 0:.1f}% of pillar"
    )

st.markdown("---")

tab1, tab2 = st.tabs(["🏗️ REIT Holdings", "🪙 Gold & Physical"])

with tab1:
    st.subheader("REIT Portfolio")
    if reits:
        # Convert to DataFrame for display
        rdf = pd.DataFrame(reits)
        rdf = rdf[['symbol', 'name', 'quantity', 'avg_cost', 'current_price', 'current_value', 'unrealized_pnl']]
        rdf.columns = ['Symbol', 'Name', 'Qty', 'Avg Cost', 'Price', 'Value (RM)', 'P&L (RM)']
        
        # Formatting
        rdf['Avg Cost'] = rdf['Avg Cost'].apply(lambda x: f"RM {x:,.3f}")
        rdf['Price'] = rdf['Price'].apply(lambda x: f"RM {x:,.3f}")
        rdf['Value (RM)'] = rdf['Value (RM)'].apply(lambda x: f"RM {x:,.2f}")
        rdf['P&L (RM)'] = rdf['P&L (RM)'].apply(lambda x: f"RM {x:+,.2f}")
        
        st.dataframe(rdf, use_container_width=True, hide_index=True)
        
        # Strategy Note
        st.info("""
        💡 **REIT Strategy**: Focus on high-quality Malaysian REITs (e.g., IGBREIT, SUNREIT, PAVREIT) 
        providing 5-7% dividend yield. This pillar provides physical asset backing and inflation protection.
        """)
    else:
        st.warning("No REIT holdings yet. Add some in the 'Add Data' page.")

with tab2:
    st.subheader("Physical Assets & Gold")
    if others:
        odf = pd.DataFrame(others)
        odf = odf[['symbol', 'name', 'quantity', 'current_value']]
        odf.columns = ['Asset', 'Name', 'Qty/Units', 'Value (RM)']
        st.dataframe(odf, use_container_width=True, hide_index=True)
    else:
        st.info("""
        🪙 **Gold Tracking**: You can add Gold (e.g., HelloGold, Public Gold, or Bank Gold Accounts) 
        as a 'Gold' asset type in the Add Data page. 
        
        Physical assets provide the ultimate insurance for your portfolio.
        """)
        
        if st.button("➕ Add Gold Holding"):
            st.switch_page("pages/6_➕_Add_Data.py")

st.markdown("---")

# LAND breakdown chart
if land_holdings:
    fig = go.Figure(data=[go.Pie(
        labels=[h['symbol'] for h in land_holdings],
        values=[h['current_value'] for h in land_holdings],
        hole=0.4,
        marker=dict(colors=['#8b4513', '#d4af37', '#cd7f32', '#a0522d'])
    )])
    
    fig.update_layout(
        title="Asset Allocation within LAND",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
