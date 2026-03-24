import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.utils.notifier import send_message
from src.core.database import PortfolioDB
from src.core.portfolio import PortfolioManager
from src.utils.notifier import send_daily_report

def test():
    print("--- Testing Telegram Connection ---")
    status, msg = send_message("[TEST] System Test: Notifications are now functional.")
    print(f"Simple Message: {status} ({msg})")

    if status:
        print("\n--- Testing Daily Report Building ---")
        db = PortfolioDB('data/portfolio.db')
        pm = PortfolioManager(db)
        status, msg = send_daily_report(db, pm)
        print(f"Daily Report: {status} ({msg})")

if __name__ == "__main__":
    test()
