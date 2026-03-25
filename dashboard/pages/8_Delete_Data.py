import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager

st.set_page_config(page_title="Delete Data", page_icon="🗑️", layout="wide")

# Initialize
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB('data/portfolio.db')
    st.session_state.pm = PortfolioManager(st.session_state.db)

db = st.session_state.db
pm = st.session_state.pm

st.title("🗑️ Delete Data")

tab1, tab2 = st.tabs(["Holdings", "Transactions"])

with tab1:
    st.subheader("🗑️ Delete a Holding")
    holdings = db.get_all_holdings()
    if holdings:
        df_holdings = pd.DataFrame(holdings)
        symbols = df_holdings['symbol'].tolist()
        
        selected_symbol = st.selectbox("Select a holding to delete:", symbols)
        
        if st.button(f"Delete {selected_symbol}", type="primary"):
            db.delete_holding(selected_symbol)
            st.success(f"Successfully deleted {selected_symbol}!")
            st.rerun()
            
        st.write("Current Holdings:")
        st.dataframe(df_holdings[['pillar', 'asset_type', 'symbol', 'name', 'quantity', 'avg_cost']], use_container_width=True)
    else:
        st.info("No holdings found.")

with tab2:
    st.subheader("🗑️ Delete a Transaction")
    transactions = db.get_transactions(days=1000)
    if transactions:
        df_trans = pd.DataFrame(transactions)
        
        # Add a combined description for the dropdown
        df_trans['display_text'] = df_trans['date'] + " | " + df_trans['type'] + " | " + df_trans['symbol'].fillna("N/A") + " | RM " + df_trans['total_amount'].astype(str)
        
        trans_options = df_trans[['id', 'display_text']].to_dict('records')
        
        selected_trans = st.selectbox(
            "Select a transaction to delete:",
            options=[t['id'] for t in trans_options],
            format_func=lambda x: next(t['display_text'] for t in trans_options if t['id'] == x)
        )
        
        if st.button("Delete Selected Transaction", type="primary"):
            db.delete_transaction(selected_trans)
            st.success("Successfully deleted the transaction!")
            st.rerun()

        st.write("Recent Transactions:")
        st.dataframe(df_trans[['id', 'date', 'type', 'symbol', 'total_amount', 'notes']], use_container_width=True)
    else:
        st.info("No transactions found.")
