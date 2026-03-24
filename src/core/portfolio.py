from datetime import date

class PortfolioManager:
      def __init__(self, db):
                self.db = db

      def calculate_portfolio_value(self):
                holdings = self.db.get_all_holdings()

        liquid_value = sum(h['current_value'] for h in holdings if h['pillar'] == 'LIQUID')
        land_value = sum(h['current_value'] for h in holdings if h['pillar'] == 'LAND')
        business_value = sum(h['current_value'] for h in holdings if h['pillar'] == 'BUSINESS')

        total_value = liquid_value + land_value + business_value

        # Get daily change from latest snapshot
        latest = self.db.get_latest_snapshot()
        daily_change_rm = 0
        daily_change_pct = 0
        if latest:
                      daily_change_rm = total_value - latest['total_value']
                      daily_change_pct = (total_value / latest['total_value']) - 1 if latest['total_value'] > 0 else 0

        return {
                      'total_value': total_value,
                      'liquid_value': liquid_value,
                      'land_value': land_value,
                      'business_value': business_value,
                      'liquid_pct': liquid_value / total_value if total_value > 0 else 0,
                      'land_pct': land_value / total_value if total_value > 0 else 0,
                      'business_pct': business_value / total_value if total_value > 0 else 0,
                      'daily_change_rm': daily_change_rm,
                      'daily_change_pct': daily_change_pct
        }

    def save_daily_snapshot(self):
              portfolio = self.calculate_portfolio_value()
              latest = self.db.get_latest_snapshot()

        today = date.today().isoformat()

        daily_change_rm = 0
        daily_change_pct = 0

        if latest:
                      daily_change_rm = portfolio['total_value'] - latest['total_value']
                      daily_change_pct = (portfolio['total_value'] / latest['total_value']) - 1 if latest['total_value'] > 0 else 0

        snapshot_data = {
                      'date': today,
                      'total_value': portfolio['total_value'],
                      'land_value': portfolio['land_value'],
                      'business_value': portfolio['business_value'],
                      'liquid_value': portfolio['liquid_value'],
                      'land_pct': portfolio['land_pct'],
                      'business_pct': portfolio['business_pct'],
                      'liquid_pct': portfolio['liquid_pct'],
                      'daily_change_rm': daily_change_rm,
                      'daily_change_pct': daily_change_pct
        }

        self.db.save_snapshot(snapshot_data)
        return snapshot_data

    def check_allocation_drift(self):
              portfolio = self.calculate_portfolio_value()

        targets = {
                      'LIQUID': 0.50,
                      'BUSINESS': 0.30,
                      'LAND': 0.20
        }

        drifts = {
                      'LIQUID': portfolio['liquid_pct'] - targets['LIQUID'],
                      'BUSINESS': portfolio['business_pct'] - targets['BUSINESS'],
                      'LAND': portfolio['land_pct'] - targets['LAND']
        }

        needs_rebalance = any(abs(d) > 0.05 for d in drifts.values())

        return {
                      'drifts': drifts,
                      'needs_rebalance': needs_rebalance
        }

    def update_holding_price(self, symbol, new_price):
              holdings = self.db.get_all_holdings()
              holding = next((h for h in holdings if h['symbol'] == symbol), None)

        if holding:
                      current_value = holding['quantity'] * new_price
                      unrealized_pnl = holding['quantity'] * (new_price - holding['avg_cost'])

            update_data = holding.copy()
            update_data['current_price'] = new_price
            update_data['current_value'] = current_value
            update_data['unrealized_pnl'] = unrealized_pnl

            self.db.upsert_holding(update_data)
            return True
        return False

    def delete_holding(self, symbol):
              """Removes a holding from the portfolio."""
              self.db.delete_holding(symbol)
              return True
      
