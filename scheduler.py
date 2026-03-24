from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, date
import sys
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager
from src.utils.notifier import send_daily_report, send_alert

# Load env variables
load_dotenv()

def check_for_alerts():
      """Checks for DTE and Drift alerts."""
      print(f"[{datetime.now()}] Running alert checks...")

    db = PortfolioDB('data/portfolio.db')
    pm = PortfolioManager(db)

    # 1. Check Drift
    drift = pm.check_allocation_drift()
    if drift['needs_rebalance']:
              details = f"Your portfolio is out of balance:\n"
              for p, d in drift['drifts'].items():
                            if abs(d) > 0.05:
                                              details += f"- {p}: {d:+.1%} drift from target\n"
                                      send_alert('Allocation Drift', details)
                        print('-> Sent Drift Alert')

    # 2. Check DTE (Options)
    holdings = db.get_all_holdings()
    if holdings:
              for h in holdings:
                            if h['asset_type'] == 'Option' and h['expiry_date']:
                                              try:
                                                                    expiry = date.fromisoformat(h['expiry_date'])
                                                                    dte = (expiry - date.today()).days
                                                                    if 0 < dte <= 21:
                                                                                              details = f"{h['symbol']} has only {dte} days left until expiry ({h['expiry_date']}).\nConsider rolling or closing to avoid Gamma risk."
                                                                                              send_alert('Low DTE (Option)', details)
                                                                                              print(f'-> Sent DTE Alert for {h['symbol']}')
                                                                                      except:
                                                                    pass

def daily_scheduled_report():
      """Sends the standard daily summary."""
    print(f"[{datetime.now()}] Sending scheduled daily report...")
    db = PortfolioDB('data/portfolio.db')
    pm = PortfolioManager(db)
    status, msg = send_daily_report(db, pm)
    print(f"-> Status: {msg}")

if __name__ == '__main__':
      scheduler = BlockingScheduler()

    # Send daily report at 6:00 PM (18:00)
    scheduler.add_job(daily_scheduled_report, 'cron', hour=18, minute=0)

    # Check for alerts every morning at 9:00 AM
    scheduler.add_job(check_for_alerts, 'cron', hour=9, minute=0)

    print('Portfolio Scheduler is running...')
    print('--- Scheduled Jobs ---')
    print('1. Daily Report: 18:00 (6:00 PM)')
    print('2. Danger Alerts: 09:00 (9:00 AM)')
    print('-----------------------')
    print('Press Ctrl+C to exit')

    try:
              scheduler.start()
except (KeyboardInterrupt, SystemExit):
        print('\nScheduler stopped.')
