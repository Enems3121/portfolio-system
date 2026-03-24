import requests
import os
from dotenv import load_dotenv
from datetime import date
import pandas as pd

# Load env variables at module level
load_dotenv()

# Use environment variables as primary source, fallback to hardcoded if needed
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7953684126:AAEIz_vtKL_qn5pIsZ-6ZJIuO15QW84DwNM")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8607976362")

def send_message(text: str):
      """Low-level function to send a Telegram message."""
      if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
                return False, "Telegram credentials not hardcoded"

      url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
      try:
                response = requests.post(url, data={
                              "chat_id": TELEGRAM_CHAT_ID,
                              "text": text,
                              "parse_mode": "HTML"
                }, timeout=10)

        if response.status_code == 200:
                      return True, "Success"
else:
            return False, f"Telegram API Error: {response.text}"
except Exception as e:
        return False, f"Connection Error: {str(e)}"

def send_daily_report(db, pm):
      """Builds and sends a professional portfolio summary."""
    portfolio = pm.calculate_portfolio_value()
    holdings = db.get_all_holdings()

    # 1. Header & Total
    report = [
              "<b>Portfolio Daily Summary</b>",
              f"Date: {date.today().strftime('%d %b %Y')}",
              "---------------------------",
              f"Total Value: RM {portfolio['total_value']:,.2f}",
              f"Today's Change: RM {portfolio['daily_change_rm']:+,.2f} ({portfolio['daily_change_pct']:+,.2f}%)",
              ""
    ]

    # 2. Pillar Allocation
    report.append("Pillar Allocation:")
    report.append(f"LIQUID: {portfolio['liquid_pct']:.1%} (Target 50%)")
    report.append(f"LAND: {portfolio['land_pct']:.1%} (Target 20%)")
    report.append(f"BUSINESS: {portfolio['business_pct']:.1%} (Target 30%)")
    report.append("")

    # 3. Top Gainers/Losers (Unrealized)
    if holdings:
              df = pd.DataFrame(holdings)
              if not df.empty:
                            df['unrealized_pnl'] = df['unrealized_pnl'].fillna(0)
                            top_pnl = df.sort_values(by='unrealized_pnl', ascending=False).head(3)
                            report.append("Top 3 Holdings (P&L):")
                            for _, h in top_pnl.iterrows():
                                              report.append(f"* {h['symbol']}: RM {h['unrealized_pnl']:+,.2f}")

                    status, msg = send_message("\n".join(report))
    return status, msg

def send_alert(alert_type, details):
      """Sends specific event alerts."""
    emoji = ""
    if "DTE" in alert_type: emoji = "ALERT"
          if "Drift" in alert_type: emoji = "ALERT"

    message = f"{emoji} {alert_type} Alert\n\n{details}"
    return send_message(message)
