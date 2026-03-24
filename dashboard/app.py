import streamlit as st
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager
from src.utils.notifier import send_daily_report

# Page config
st.set_page_config(
      page_title="My Portfolio System",
      page_icon="money_bag",
      layout="wide",
      initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main theme colors */
        :root {
                --primary-color: #1f77b4;
                        --success-color: #2ecc71;
                                --warning-color: #f39c12;
                                        --danger-color: #e74c3c;
                                            }

                                                    /* Metric cards */
                                                        .metric-card {
                                                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                                                        padding: 20px;
                                                                                border-radius: 10px;
                                                                                        color: white;
                                                                                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                                                                                    }
                                                                                                        
                                                                                                            /* Pillar cards */
                                                                                                                .pillar-card {
                                                                                                                        border-left: 4px solid;
                                                                                                                                padding: 15px;
                                                                                                                                        margin: 10px 0;
                                                                                                                                                border-radius: 5px;
                                                                                                                                                        background: #f8f9fa;
                                                                                                                                                            }
                                                                                                                                                                
                                                                                                                                                                    .land-card { border-left-color: #8b4513; }
                                                                                                                                                                        .business-card { border-left-color: #1f77b4; }
                                                                                                                                                                            .liquid-card { border-left-color: #2ecc71; }
                                                                                                                                                                                
                                                                                                                                                                                    /* Progress bars */
                                                                                                                                                                                        .stProgress > div > div > div > div {
                                                                                                                                                                                                background: linear-gradient(to right, #667eea, #764ba2);
                                                                                                                                                                                                    }
                                                                                                                                                                                                        
                                                                                                                                                                                                            /* Tables */
                                                                                                                                                                                                                .dataframe {
                                                                                                                                                                                                                        font-size: 14px;
                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                
                                                                                                                                                                                                                                    /* Sidebar */
                                                                                                                                                                                                                                        .css-1d391kg {
                                                                                                                                                                                                                                                background-color: #f0f2f6;
                                                                                                                                                                                                                                                    }
                                                                                                                                                                                                                                                    </style>
                                                                                                                                                                                                                                                    """, unsafe_allow_html=True)

# Initialize session state
if 'db' not in st.session_state:
      # Ensure data directory exists
      Path("data").mkdir(exist_ok=True)
      st.session_state.db = PortfolioDB('data/portfolio.db')
      st.session_state.pm = PortfolioManager(st.session_state.db)

# Sidebar
with st.sidebar:
      st.title("MONEY Portfolio System")
      st.markdown("---")

    # Quick stats in sidebar
      portfolio = st.session_state.pm.calculate_portfolio_value()

    st.metric(
              "Total Value",
              f"RM {portfolio['total_value']:,.2f}",
              delta=None
    )

    st.markdown("---")

    # Navigation info
    st.info("""
        CHART **Overview** - Portfolio summary

                DROPLET **LIQUID** - Trading & cash

                        HOUSE **LAND** - REITs & gold

                                OFFICE **BUSINESS** - Stocks

                                        MEMO **Transactions** - History

                                                PLUS **Add Data** - New entries
                                                    """)

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")

    if st.button("CAMERA Save Snapshot", use_container_width=True):
              snapshot = st.session_state.pm.save_daily_snapshot()
              st.success(f"Snapshot saved! RM {snapshot['total_value']:,.2f}")

    if st.button("REFRESH Check Rebalance", use_container_width=True):
              drift = st.session_state.pm.check_allocation_drift()
              if drift['needs_rebalance']:
                            st.warning("WARN Rebalancing needed!")
    else:
            st.success("CHECK Portfolio balanced")

    st.markdown("---")
    st.subheader("MAIL Notifications")
    if st.button("SEND Send Daily Report", use_container_width=True):
              with st.spinner("Processing..."):
                            status, msg = send_daily_report(st.session_state.db, st.session_state.pm)
                            if status:
                                              st.success("Report sent!")
    else:
                st.error(f"Error: {msg}")

    st.markdown("---")
    latest_snapshot = st.session_state.db.get_latest_snapshot()
    st.caption(f"Last updated: {latest_snapshot['date'] if latest_snapshot else 'Never'}")

# Main content
st.title("CHART Portfolio Overview")

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
      st.markdown(f"""
          <div class="metric-card">
                  <h3 style="margin:0; font-size:16px;">Total Value</h3>
                          <h2 style="margin:10px 0;">RM {portfolio['total_value']:,.2f}</h2>
                              </div>
                                  """, unsafe_allow_html=True)

with col2:
      # Calculate daily change
      latest = st.session_state.db.get_latest_snapshot()
      if latest:
                change_pct = latest['daily_change_pct'] * 100
                change_rm = latest['daily_change_rm']
                change_color = "green" if change_pct >= 0 else "red"
                change_arrow = "UP" if change_pct >= 0 else "DOWN"
else:
        change_pct = 0
          change_rm = 0
        change_color = "gray"
        change_arrow = "RIGHT"

    # Simple color mapping for gradient
    bg_color = "#2ecc71" if change_pct >= 0 else "#e74c3c"
    if change_pct == 0: bg_color = "#95a5a6"

    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {bg_color} 0%, {bg_color} 100%);">
                <h3 style="margin:0; font-size:16px;">Today's Change</h3>
                        <h2 style="margin:10px 0;">{change_arrow} {abs(change_pct):.2f}%</h2>
                                <p style="margin:0;">RM {change_rm:+,.2f}</p>
                                    </div>
                                        """, unsafe_allow_html=True)

with col3:
      # Count holdings
      holdings = st.session_state.db.get_all_holdings()
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3 style="margin:0; font-size:16px;">Holdings</h3>
                        <h2 style="margin:10px 0;">{len(holdings)}</h2>
                                <p style="margin:0;">Assets</p>
                                    </div>
                                        """, unsafe_allow_html=True)

with col4:
      # Total unrealized P&L
      total_pnl = sum(h['unrealized_pnl'] or 0 for h in holdings)
    pnl_color = "#2ecc71" if total_pnl >= 0 else "#e74c3c"

    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {pnl_color} 0%, {pnl_color} 100%);">
                <h3 style="margin:0; font-size:16px;">Unrealized P&L</h3>
                        <h2 style="margin:10px 0;">RM {total_pnl:+,.2f}</h2>
                            </div>
                                """, unsafe_allow_html=True)

st.markdown("---")

# Pillar allocation visualization
st.subheader("TARGET Pillar Allocation (Target: 50-30-20)")

# Get targets
targets = {
      'LIQUID': 0.50,
      'BUSINESS': 0.30,
      'LAND': 0.20
}

# Create three columns for pillar cards
col1, col2, col3 = st.columns(3)

pillars_data = [
      ('LIQUID', 'DROPLET', 'liquid-card', col1, portfolio['liquid_value'], portfolio['liquid_pct']),
      ('BUSINESS', 'OFFICE', 'business-card', col2, portfolio['business_value'], portfolio['business_pct']),
      ('LAND', 'HOUSE', 'land-card', col3, portfolio['land_value'], portfolio['land_pct'])
]

for pillar_name, emoji, css_class, column, value, current_pct in pillars_data:
      with column:
                target_pct = targets[pillar_name]
                drift = current_pct - target_pct

        # Status indicator
                if abs(drift) <= 0.05:
                              status = "CHECK On Target"
                              status_color = "#2ecc71"
else:
            status = f"WARN {drift:+.1%} drift"
              status_color = "#f39c12"

        st.markdown(f"""
                <div class="pillar-card {css_class}">
                            <h3>{emoji} {pillar_name}</h3>
                                        <h2>RM {value:,.2f}</h2>
                                                    <p style="margin:5px 0;"><strong>{current_pct:.1%}</strong> of portfolio</p>
                                                                <p style="margin:5px 0; color: {status_color};">{status}</p>
                                                                            <p style="margin:5px 0; font-size:12px;">Target: {target_pct:.0%}</p>
                                                                                    </div>
                                                                                            """, unsafe_allow_html=True)

        # Progress bar
        st.progress(current_pct)

st.markdown("---")

# Holdings table
st.subheader("CLIPBOARD Current Holdings")

if holdings:
      # Convert to DataFrame
      df = pd.DataFrame(holdings)

    # Select and rename columns
    display_df = df[['pillar', 'symbol', 'name', 'quantity', 'avg_cost', 'current_price', 'current_value', 'unrealized_pnl']]
    display_df.columns = ['Pillar', 'Symbol', 'Name', 'Qty', 'Avg Cost', 'Current Price', 'Value (RM)', 'P&L (RM)']

    # Format numbers
    display_df['Avg Cost'] = display_df['Avg Cost'].apply(lambda x: f"RM {x:,.2f}")
    display_df['Current Price'] = display_df['Current Price'].apply(lambda x: f"RM {x:,.2f}")
    display_df['Value (RM)'] = display_df['Value (RM)'].apply(lambda x: f"RM {x:,.2f}")
    display_df['P&L (RM)'] = display_df['P&L (RM)'].apply(lambda x: f"RM {x:+,.2f}")

    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.info("No holdings yet. Add your first position in the 'Add Data' page.")

st.markdown("---")

# Recent transactions
st.subheader("SCROLL Recent Activity")

transactions = st.session_state.db.get_transactions(days=10)

if transactions:
      df_trans = pd.DataFrame(transactions)

    # Show only recent 5
    df_trans = df_trans.head(5)

    display_trans = df_trans[['date', 'type', 'pillar', 'symbol', 'total_amount', 'notes']]
    display_trans.columns = ['Date', 'Type', 'Pillar', 'Symbol', 'Amount (RM)', 'Notes']

    display_trans['Amount (RM)'] = display_trans['Amount (RM)'].apply(lambda x: f"RM {x:+,.2f}")

    st.dataframe(display_trans, use_container_width=True, hide_index=True)
else:
    st.info("No transactions yet. Add your first transaction in the 'Add Data' page.")

# Footer
st.markdown("---")
st.caption("BULB Tip: Use the sidebar to navigate between different views and add new data.")
