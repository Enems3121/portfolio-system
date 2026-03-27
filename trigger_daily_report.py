"""Script to manually trigger the daily portfolio report.
Ideal for use with cron jobs or GitHub Actions."""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager
from src.utils.notifier import send_daily_report, send_alert

# Load env variables (for local/action usage)
load_dotenv()

def run_daily_checks():
    print("Running scheduled portfolio checks...")
    db = PortfolioDB('data/portfolio.db')
    pm = PortfolioManager(db)
    
    # 1. Send Daily Report
    print("Sending daily report...")
    status, msg = send_daily_report(db, pm)
    print(f"Report status: {msg}")

    # 2. Check Allocations (Drift)
    # Using existing logic from scheduler.py
    print("Checking allocation drift...")
    drift = pm.check_allocation_drift()
    if drift['needs_rebalance']:
        details = f"Your portfolio is out of balance:\n"
        for p, d in drift['drifts'].items():
            if abs(d) > 0.05:
                details += f"• *{p}*: {d:+.1%} drift from target\n"
        send_alert("Allocation Drift", details)
        print("-> Sent Drift Alert")

if __name__ == "__main__":
    run_daily_checks()
    print("Done!")
