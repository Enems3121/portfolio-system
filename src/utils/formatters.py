def format_currency(amount, currency='RM'):
      """Format number as currency"""
      return f"{currency} {amount:,.2f}"

def format_percentage(value, decimals=1):
      """Format as percentage"""
      return f"{value * 100:.{decimals}f}%"

def format_change(value):
      """Format change with + or - sign"""
      sign = '+' if value >= 0 else ''
      return f"{sign}{value:,.2f}"

def color_pnl(value):
      """Return color based on P&L"""
      return 'green' if value >= 0 else 'red'
  
