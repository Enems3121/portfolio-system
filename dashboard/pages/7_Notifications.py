import streamlit as st
import os
from dotenv import load_dotenv, set_key
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.notifier import send_message, send_daily_report
from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager

st.set_page_config(page_title="Notifications", page_icon="🔔", layout="wide")

# Initialize DB/PM
if 'db' not in st.session_state:
    st.session_state.db = PortfolioDB('data/portfolio.db')
    st.session_state.pm = PortfolioManager(st.session_state.db)

# Load current env
env_path = Path('.env')
load_dotenv(dotenv_path=env_path)

st.title("🔔 Notification Settings")

st.markdown("""
Connect your portfolio to Telegram to receive:
- **Daily Summaries** 📊
- **DTE Warnings** 🎲 (for Options)
- **Allocation Drift Alerts** ⚖️
""")

with st.expander("🛠️ Telegram Bot Setup Guide", expanded=False):
    st.markdown("""
    1. Message **@BotFather** on Telegram.
    2. Create a `/newbot` and get the **API Token**.
    3. Send a message to your new bot.
    4. Get your **Chat ID** (search for '@userinfobot' or check bot updates API).
    """)

# --- Settings Form ---
with st.form("telegram_config"):
    st.subheader("Credential Config")
    
    current_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    current_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    bot_token = st.text_input("Telegram Bot Token", value=current_token, type="password")
    chat_id = st.text_input("Telegram Chat ID", value=current_chat_id)
    
    save_btn = st.form_submit_button("💾 Save Credentials", use_container_width=True)
    
    if save_btn:
        # Create .env if it doesn't exist
        if not env_path.exists():
            env_path.touch()
            
        # Update .env
        set_key(str(env_path), "TELEGRAM_BOT_TOKEN", bot_token)
        set_key(str(env_path), "TELEGRAM_CHAT_ID", chat_id)
        
        st.success("✅ Credentials saved! Please restart the dashboard to apply changes.")
        st.info("Note: The scheduler script will also need a restart if it's currently running.")

# --- Test Tools ---
st.markdown("---")
st.subheader("🧪 Test Tools")
col1, col2 = st.columns(2)

with col1:
    if st.button("🔔 Send Test Message", use_container_width=True):
        with st.spinner("Sending..."):
            status, msg = send_message("✅ *Test Successful!* Your portfolio is now connected to Telegram.")
            if status:
                st.success("Message sent! Check your Telegram.")
            else:
                st.error(f"Failed: {msg}")

with col2:
    if st.button("📊 Send Full Daily Report", use_container_width=True):
        with st.spinner("Building report..."):
            status, msg = send_daily_report(st.session_state.db, st.session_state.pm)
            if status:
                st.success("Full report sent!")
            else:
                st.error(f"Failed: {msg}")
