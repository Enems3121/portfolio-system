import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager

st.set_page_config(page_title="LIQUID Pillar", page_icon="💧", layout="wide")

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB('data/portfolio.db')
    st.session_state.pm = PortfolioManager(st.session_state.db)

db = st.session_state.db
pm = st.session_state.pm

# Header
st.title("💧 LIQUID Pillar - Trading & Cash")

# Get LIQUID holdings
liquid_holdings = db.get_holdings_by_pillar('LIQUID')
portfolio = pm.calculate_portfolio_value()

liquid_value = portfolio['liquid_value']
liquid_pct = portfolio['liquid_pct']
target_pct = 0.50  # 50% target

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total LIQUID",
        f"RM {liquid_value:,.2f}",
        delta=f"{liquid_pct:.1%} of portfolio"
    )

with col2:
    target_value = portfolio['total_value'] * target_pct
    drift_rm = liquid_value - target_value
    st.metric(
        "vs Target (50%)",
        f"RM {target_value:,.2f}",
        delta=f"{drift_rm:+,.2f}"
    )

with col3:
    # Money market portion (90% of LIQUID)
    money_market = [h for h in liquid_holdings if h['asset_type'] == 'Cash']
    mm_value = sum(h['current_value'] for h in money_market)
    st.metric(
        "Money Market (90%)",
        f"RM {mm_value:,.2f}",
        delta=f"{(mm_value/liquid_value*100) if liquid_value > 0 else 0:.1f}%"
    )

with col4:
    # Trading vault (10% of LIQUID)
    trading = [h for h in liquid_holdings if h['asset_type'] == 'Forex']
    trading_value = sum(h['current_value'] for h in trading)
    st.metric(
        "Trading Vault (10%)",
        f"RM {trading_value:,.2f}",
        delta=f"{(trading_value/liquid_value*100) if liquid_value > 0 else 0:.1f}%"
    )

st.markdown("---")

# Split view: Money Market vs Trading vs Options
tab1, tab2, tab3 = st.tabs(["💰 Money Market (Passive)", "🤖 Trading Vault (Active)", "💎 Options Trading"])

with tab1:
    # ... existing code ...
    st.subheader("Money Market Holdings")
    
    if money_market:
        # Display money market accounts
        for holding in money_market:
            with st.expander(f"{holding['symbol']} - RM {holding['current_value']:,.2f}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Balance", f"RM {holding['current_value']:,.2f}")
                
                with col2:
                    # Assuming interest rate stored in notes or separate field
                    st.metric("Interest Rate", "3.8% p.a.")
                
                with col3:
                    monthly_interest = holding['current_value'] * 0.038 / 12
                    st.metric("Monthly Interest", f"RM {monthly_interest:,.2f}")
                
                # Progress bar showing % of LIQUID pillar
                pct_of_liquid = holding['current_value'] / liquid_value if liquid_value > 0 else 0
                st.progress(pct_of_liquid)
                st.caption(f"{pct_of_liquid:.1%} of LIQUID pillar")
        
        # Summary
        st.info(f"""
        💡 **Strategy**: Money market provides stable 3-4% returns as your "ammunition reserve".
        This portion should remain at ~90% of LIQUID pillar for safety.
        """)
    else:
        st.warning("No money market holdings. Add KDI Save or TnG GO+ in 'Add Data' page.")
        
        if st.button("➕ Add Money Market Account"):
            st.switch_page("pages/6_Add_Data.py")

with tab2:
    st.subheader("Trading Vault Status")
    
    # Calculate max allowed for trading (10% of LIQUID)
    max_trading_vault = liquid_value * 0.10
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Current Trading Vault",
            f"RM {trading_value:,.2f}",
            delta=f"{(trading_value/max_trading_vault*100) if max_trading_vault > 0 else 0:.1f}% used"
        )
    
    with col2:
        st.metric(
            "Maximum Allowed (10%)",
            f"RM {max_trading_vault:,.2f}",
            delta=f"RM {max_trading_vault - trading_value:,.2f} buffer"
        )
    
    # Safety gauge
    usage_pct = (trading_value / max_trading_vault * 100) if max_trading_vault > 0 else 0
    
    if usage_pct < 80:
        gauge_color = "green"
        status = "✅ Safe"
    elif usage_pct < 95:
        gauge_color = "orange"
        status = "⚠️ Caution"
    else:
        gauge_color = "red"
        status = "🚨 Limit Reached"
    
    # Gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=usage_pct,
        title={'text': "Trading Vault Usage"},
        delta={'reference': 100},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': gauge_color},
            'steps': [
                {'range': [0, 80], 'color': "lightgray"},
                {'range': [80, 95], 'color': "lightyellow"},
                {'range': [95, 100], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 100
            }
        }
    ))
    
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"**Status**: {status}")
    
    st.markdown("---")
    
    # Trading positions (placeholder for MT5 integration later)
    st.subheader("Active Trading Positions")
    
    st.info("""
    🤖 **MT5 Integration Coming Soon**
    
    This section will show:
    - Open positions (USDJPY, AUDUSD, etc.)
    - Real-time P&L
    - Margin usage monitoring
    - Trading signals & confluences
    
    For now, you can manually track trading vault balance.
    """)
    
    # Manual tracking option
    with st.expander("📝 Manually Update Trading Vault Balance"):
        new_balance = st.number_input(
            "Current MT5 Balance (RM)",
            min_value=0.0,
            value=float(trading_value),
            step=10.0
        )
        
        if st.button("Update Balance"):
            # Update or create MT5 holding
            db.upsert_holding({
                'pillar': 'LIQUID',
                'asset_type': 'Forex',
                'symbol': 'MT5_ACCOUNT',
                'name': 'MT5 Trading Account',
                'quantity': 1,
                'avg_cost': new_balance,
                'current_price': new_balance,
                'current_value': new_balance,
                'unrealized_pnl': 0, # Simplified
                'broker': 'MT5'
            })
            
            st.success(f"✓ Updated MT5 balance to RM {new_balance:,.2f}")
            st.rerun()

with tab3:
    st.subheader("💎 Options Portfolio")
    
    options_holdings = [h for h in liquid_holdings if h['asset_type'] == 'Option']
    
    if options_holdings:
        from datetime import date
        
        # Dashboard for Options
        o_col1, o_col2 = st.columns([2, 1])
        
        with o_col1:
            st.markdown("#### Active Positions")
            
            # Prepare data for display
            opt_data = []
            for h in options_holdings:
                expiry = date.fromisoformat(h['expiry_date']) if h['expiry_date'] else None
                dte = (expiry - date.today()).days if expiry else -1
                
                # Risk status based on DTE
                if dte < 0: status = "🔴 Expired"
                elif dte < 21: status = "🟠 Danger (Gamma)"
                elif dte < 45: status = "🟡 Caution"
                else: status = "🟢 Safe (Theta)"
                
                opt_data.append({
                    "Symbol": h['symbol'],
                    "Type": h['option_type'],
                    "Strike": f"RM {h['strike_price']:.2f}" if h['strike_price'] else "N/A",
                    "DTE": dte,
                    "Status": status,
                    "Value": f"RM {h['current_value']:,.2f}",
                    "P&L": f"RM {h['unrealized_pnl']:+,.2f}"
                })
            
            opt_df = pd.DataFrame(opt_data)
            st.dataframe(opt_df, use_container_width=True, hide_index=True)

        with o_col2:
            st.markdown("#### Time Decay (Theta)")
            # DTE Breakdown chart
            dte_counts = opt_df['Status'].value_counts()
            fig_dte = go.Figure(data=[go.Pie(
                labels=dte_counts.index,
                values=dte_counts.values,
                hole=0.4,
                marker=dict(colors=['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71'])
            )])
            fig_dte.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig_dte, use_container_width=True)
            
        st.markdown("---")
        
        # Strategy Metrics
        st.subheader("📊 Options Risk Profile")
        m1, m2, m3 = st.columns(3)
        
        total_pnl = sum(h['unrealized_pnl'] or 0 for h in options_holdings)
        total_exposure = sum(h['current_value'] for h in options_holdings)
        
        with m1:
            st.metric("Total Options Value", f"RM {total_exposure:,.2f}")
        with m2:
            st.metric("Total Options P&L", f"RM {total_pnl:+,.2f}")
        with m3:
            calls = len([h for h in options_holdings if h['option_type'] == 'CALL'])
            puts = len([h for h in options_holdings if h['option_type'] == 'PUT'])
            st.metric("Call/Put Ratio", f"{calls}:{puts}")

        st.info("""
        💡 **Options Management**: 
        - Roll positions before 21 DTE to avoid explosive Gamma risk.
        - Watch the Theta (DTE) breakdown to prioritize your attention.
        """)
    else:
        st.info("No options positions found in the LIQUID pillar.")
        if st.button("➕ Add your first Option Position"):
            st.switch_page("pages/6_Add_Data.py")

st.markdown("---")

# LIQUID allocation breakdown (pie chart)
st.subheader("💧 LIQUID Breakdown")

if liquid_holdings:
    fig = go.Figure(data=[go.Pie(
        labels=[h['symbol'] for h in liquid_holdings],
        values=[h['current_value'] for h in liquid_holdings],
        hole=0.4,
        marker=dict(colors=['#2ecc71', '#3498db', '#9b59b6'])
    )])
    
    fig.update_layout(
        title="Asset Allocation within LIQUID",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Add your first LIQUID holdings to see breakdown.")

# Footer tips
st.markdown("---")
st.info("""
💡 **LIQUID Pillar Tips**:
- Keep 90% in money market for stability (KDI Save @ 3.8%)
- Use 10% for active trading (MT5)
- Never risk more than 2% per trade
- Max 10% margin usage rule applies to the trading vault portion only
""")
