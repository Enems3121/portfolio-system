import streamlit as st
from datetime import date
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager
from src.utils.notifier import send_daily_report

st.set_page_config(page_title="Add Data", page_icon="➕", layout="wide")

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB('data/portfolio.db')
    st.session_state.pm = PortfolioManager(st.session_state.db)

db = st.session_state.db
pm = st.session_state.pm

st.title("➕ Add New Data")

# Tabs for different entry types
tab1, tab2, tab3 = st.tabs(["🆕 New Holding", "💰 Transaction", "💵 Price Update"])

with tab1:
    st.subheader("Add New Holding")
    
    pillar = st.selectbox(
        "Pillar",
        ["LIQUID", "LAND", "BUSINESS"]
    )
    
    # Map pillars to their relevant asset types
    asset_type_options = {
        "LIQUID": ["Cash", "Forex", "Option", "ETF"],
        "LAND": ["REIT", "Gold"],
        "BUSINESS": ["Stock", "ETF"]
    }
    
    asset_type = st.selectbox(
        "Asset Type",
        options=asset_type_options.get(pillar, ["Stock", "ETF", "Cash"])
    )
    
    with st.form("new_holding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("Symbol (e.g., TSLA 240621C180)", "").upper()
            
            name = st.text_input("Full Name / Description", "")
        
        with col2:
            quantity = st.number_input("Quantity / Contracts", min_value=0.0, step=1.0)
            
            avg_cost = st.number_input("Average Cost (RM per unit/contract)", min_value=0.0, step=0.01)
            
            current_price = st.number_input("Current Price (RM per unit/contract)", min_value=0.0, step=0.01, value=avg_cost)
            
            broker = st.text_input("Broker", "")

        # Option-specific fields
        if asset_type == "Option":
            st.markdown("---")
            st.subheader("🎲 Option Details")
            o_col1, o_col2, o_col3 = st.columns(3)
            with o_col1:
                option_type = st.selectbox("Type", ["CALL", "PUT"])
            with o_col2:
                strike_price = st.number_input("Strike Price", min_value=0.0)
            with o_col3:
                expiry_date = st.date_input("Expiry Date")
        else:
            option_type, strike_price, expiry_date = None, None, None
        
        submitted = st.form_submit_button("➕ Add Holding", use_container_width=True)
        
        if submitted:
            if not symbol:
                st.error("Symbol is required!")
            else:
                current_value = quantity * current_price
                unrealized_pnl = quantity * (current_price - avg_cost)
                
                db.upsert_holding({
                    'pillar': pillar,
                    'asset_type': asset_type,
                    'symbol': symbol,
                    'name': name,
                    'quantity': quantity,
                    'avg_cost': avg_cost,
                    'current_price': current_price,
                    'current_value': current_value,
                    'unrealized_pnl': unrealized_pnl,
                    'broker': broker,
                    'expiry_date': expiry_date.isoformat() if expiry_date else None,
                    'strike_price': strike_price,
                    'option_type': option_type
                })
                
                # Also add as BUY transaction
                db.add_transaction({
                    'date': date.today(),
                    'type': 'BUY',
                    'pillar': pillar,
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': avg_cost,
                    'total_amount': quantity * avg_cost,
                    'fees': 0,
                    'broker': broker,
                    'notes': f'Initial purchase of {name}'
                })
                
                send_daily_report(db, pm)
                
                st.success(f"✓ Added {quantity} units of {symbol} worth RM {current_value:,.2f}")
                st.balloons()

with tab2:
    st.subheader("Add Transaction")
    
    with st.form("new_transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            trans_date = st.date_input("Date", date.today())
            
            trans_type = st.selectbox(
                "Type",
                ["BUY", "SELL", "DIVIDEND", "INTEREST", "FEE", "TRANSFER"]
            )
            
            trans_pillar = st.selectbox(
                "Pillar",
                ["LIQUID", "LAND", "BUSINESS"]
            )
            
            trans_symbol = st.text_input("Symbol (optional)", "").upper()
        
        with col2:
            trans_quantity = st.number_input("Quantity (if applicable)", min_value=0.0, step=1.0)
            
            trans_price = st.number_input("Price per unit (RM)", min_value=0.0, step=0.01)
            
            trans_amount = st.number_input("Total Amount (RM)", min_value=0.0, step=1.0)
            
            trans_fees = st.number_input("Fees (RM)", min_value=0.0, step=0.01, value=0.0)
        
        trans_broker = st.text_input("Broker", "")
        trans_notes = st.text_area("Notes", "")
        
        submitted_trans = st.form_submit_button("💾 Save Transaction", use_container_width=True)
        
        if submitted_trans:
            db.add_transaction({
                'date': trans_date,
                'type': trans_type,
                'pillar': trans_pillar,
                'symbol': trans_symbol if trans_symbol else None,
                'quantity': trans_quantity if trans_quantity > 0 else None,
                'price': trans_price if trans_price > 0 else None,
                'total_amount': trans_amount,
                'fees': trans_fees,
                'broker': trans_broker,
                'notes': trans_notes
            })
            
            send_daily_report(db, pm)
            
            st.success(f"✓ Transaction recorded: {trans_type} RM {trans_amount:,.2f}")

with tab3:
    st.subheader("Update Prices")
    
    holdings = db.get_all_holdings()
    
    if holdings:
        st.info("Update current prices for your holdings. This will recalculate P&L.")
        
        for holding in holdings:
            with st.expander(f"{holding['symbol']} - Current: RM {holding['current_price']:.2f}"):
                new_price = st.number_input(
                    f"New price for {holding['symbol']}",
                    min_value=0.0,
                    value=float(holding['current_price']),
                    step=0.01,
                    key=f"price_{holding['id']}"
                )
                
                if st.button(f"Update {holding['symbol']}", key=f"btn_{holding['id']}"):
                    pm.update_holding_price(holding['symbol'], new_price)
                    send_daily_report(db, pm)
                    st.success(f"✓ Updated {holding['symbol']} to RM {new_price:.2f}")
                    st.rerun()
    else:
        st.warning("No holdings to update. Add holdings first.")

st.markdown("---")

# Quick start guide
with st.expander("📖 Quick Start Guide"):
    st.markdown("""
    ### Getting Started with RM 1,500
    
    **Step 1: Add Money Market (LIQUID - 50%)**
    1. Go to "New Holding" tab
    2. Pillar: LIQUID
    3. Asset Type: Cash
    4. Symbol: KDI_SAVE
    5. Quantity: 1
    6. Cost: 750.00 (50% of RM 1,500)
    
    **Step 2: Add Initial Trading Vault (LIQUID - optional)**
    1. Symbol: MT5_ACCOUNT
    2. Asset Type: Forex
    3. Amount: RM 50-100 (for testing)
    
    **Step 3: Add REIT (LAND - 20%)**
    1. Pillar: LAND
    2. Asset Type: REIT
    3. Symbol: SENTRAL (example)
    4. Buy 200 units @ RM 1.50 = RM 300
    
    **Step 4: Add Stock (BUSINESS - 30%)**
    1. Pillar: BUSINESS
    2. Asset Type: Stock
    3. Symbol: TENAGA
    4. Buy 100 shares @ RM 4.50 = RM 450
    
    💡 Adjust quantities based on actual prices!
    """)
