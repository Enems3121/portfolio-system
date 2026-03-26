import os
import sqlite3
from datetime import datetime

# Check if a PostgreSQL URL is provided (cloud deployment)
DATABASE_URL = os.getenv("DATABASE_URL", "")

def _test_pg_connection(url):
    """Test if a PostgreSQL connection is usable. Returns True/False."""
    try:
        import psycopg2
        conn = psycopg2.connect(url, connect_timeout=5)
        conn.close()
        return True
    except Exception:
        return False

class PortfolioDB:
    def __init__(self, db_path='data/portfolio.db'):
        self.db_path = db_path
        # Initialize use_pg to None, it will be set by _connect
        self.use_pg = None
        self._init_db()

    def _connect(self):
        """Get a fresh connection — PostgreSQL if working, else SQLite."""
        if DATABASE_URL:
            try:
                import psycopg2
                import psycopg2.extras
                conn = psycopg2.connect(DATABASE_URL, connect_timeout=10, sslmode='require')
                self.use_pg = True
                return conn
            except Exception:
                # PostgreSQL connection failed, fall back to SQLite
                pass

        # If DATABASE_URL is not set, or PG connection failed, use SQLite
        self.use_pg = False
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            if self.use_pg:
                # PostgreSQL syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS holdings (
                        id SERIAL PRIMARY KEY,
                        pillar TEXT,
                        asset_type TEXT,
                        symbol TEXT UNIQUE,
                        name TEXT,
                        quantity REAL,
                        avg_cost REAL,
                        current_price REAL,
                        current_value REAL,
                        unrealized_pnl REAL,
                        broker TEXT,
                        expiry_date DATE,
                        strike_price REAL,
                        option_type TEXT,
                        last_updated TIMESTAMP DEFAULT NOW()
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        date DATE,
                        type TEXT,
                        pillar TEXT,
                        symbol TEXT,
                        quantity REAL,
                        price REAL,
                        total_amount REAL,
                        fees REAL,
                        broker TEXT,
                        notes TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_summary (
                        id SERIAL PRIMARY KEY,
                        date DATE UNIQUE,
                        total_value REAL,
                        land_value REAL,
                        business_value REAL,
                        liquid_value REAL,
                        land_pct REAL,
                        business_pct REAL,
                        liquid_pct REAL,
                        daily_change_rm REAL,
                        daily_change_pct REAL
                    )
                ''')
            else:
                # SQLite syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS holdings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pillar TEXT,
                        asset_type TEXT,
                        symbol TEXT UNIQUE,
                        name TEXT,
                        quantity REAL,
                        avg_cost REAL,
                        current_price REAL,
                        current_value REAL,
                        unrealized_pnl REAL,
                        broker TEXT,
                        expiry_date DATE,
                        strike_price REAL,
                        option_type TEXT,
                        last_updated DATETIME
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE,
                        type TEXT,
                        pillar TEXT,
                        symbol TEXT,
                        quantity REAL,
                        price REAL,
                        total_amount REAL,
                        fees REAL,
                        broker TEXT,
                        notes TEXT
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_summary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATE UNIQUE,
                        total_value REAL,
                        land_value REAL,
                        business_value REAL,
                        liquid_value REAL,
                        land_pct REAL,
                        business_pct REAL,
                        liquid_pct REAL,
                        daily_change_rm REAL,
                        daily_change_pct REAL
                    )
                ''')
            conn.commit()
        finally:
            conn.close()

    def _rows_to_dict(self, cursor, rows):
        """Convert rows to list of dicts regardless of DB backend."""
        if not rows:
            return []
        if self.use_pg:
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        else:
            # SQLite Row objects
            return [dict(row) for row in rows]

    def get_all_holdings(self):
        conn = self._connect()
        try:
            if not self.use_pg:
                conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM holdings")
            return self._rows_to_dict(cursor, cursor.fetchall())
        finally:
            conn.close()

    def get_holdings_by_pillar(self, pillar):
        conn = self._connect()
        try:
            if not self.use_pg:
                conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if self.use_pg:
                cursor.execute("SELECT * FROM holdings WHERE pillar = %s", (pillar,))
            else:
                cursor.execute("SELECT * FROM holdings WHERE pillar = ?", (pillar,))
            return self._rows_to_dict(cursor, cursor.fetchall())
        finally:
            conn.close()

    def upsert_holding(self, data):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            if self.use_pg:
                cursor.execute('''
                    INSERT INTO holdings (pillar, asset_type, symbol, name, quantity, avg_cost, current_price,
                        current_value, unrealized_pnl, broker, expiry_date, strike_price, option_type, last_updated)
                    VALUES (%(pillar)s, %(asset_type)s, %(symbol)s, %(name)s, %(quantity)s, %(avg_cost)s,
                        %(current_price)s, %(current_value)s, %(unrealized_pnl)s, %(broker)s, %(expiry_date)s,
                        %(strike_price)s, %(option_type)s, NOW())
                    ON CONFLICT(symbol) DO UPDATE SET
                        quantity = EXCLUDED.quantity,
                        avg_cost = EXCLUDED.avg_cost,
                        current_price = EXCLUDED.current_price,
                        current_value = EXCLUDED.current_value,
                        unrealized_pnl = EXCLUDED.unrealized_pnl,
                        expiry_date = EXCLUDED.expiry_date,
                        strike_price = EXCLUDED.strike_price,
                        option_type = EXCLUDED.option_type,
                        last_updated = NOW()
                ''', data)
            else:
                cursor.execute('''
                    INSERT INTO holdings (pillar, asset_type, symbol, name, quantity, avg_cost, current_price,
                        current_value, unrealized_pnl, broker, expiry_date, strike_price, option_type, last_updated)
                    VALUES (:pillar, :asset_type, :symbol, :name, :quantity, :avg_cost, :current_price,
                        :current_value, :unrealized_pnl, :broker, :expiry_date, :strike_price, :option_type, datetime('now'))
                    ON CONFLICT(symbol) DO UPDATE SET
                        quantity = excluded.quantity,
                        avg_cost = excluded.avg_cost,
                        current_price = excluded.current_price,
                        current_value = excluded.current_value,
                        unrealized_pnl = excluded.unrealized_pnl,
                        expiry_date = excluded.expiry_date,
                        strike_price = excluded.strike_price,
                        option_type = excluded.option_type,
                        last_updated = datetime('now')
                ''', data)
            conn.commit()
        finally:
            conn.close()

    def add_transaction(self, data):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            if self.use_pg:
                cursor.execute('''
                    INSERT INTO transactions (date, type, pillar, symbol, quantity, price, total_amount, fees, broker, notes)
                    VALUES (%(date)s, %(type)s, %(pillar)s, %(symbol)s, %(quantity)s, %(price)s,
                        %(total_amount)s, %(fees)s, %(broker)s, %(notes)s)
                ''', data)
            else:
                cursor.execute('''
                    INSERT INTO transactions (date, type, pillar, symbol, quantity, price, total_amount, fees, broker, notes)
                    VALUES (:date, :type, :pillar, :symbol, :quantity, :price, :total_amount, :fees, :broker, :notes)
                ''', data)
            conn.commit()
        finally:
            conn.close()

    def delete_holding(self, symbol):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            if self.use_pg:
                cursor.execute("DELETE FROM holdings WHERE symbol = %s", (symbol,))
            else:
                cursor.execute("DELETE FROM holdings WHERE symbol = ?", (symbol,))
            conn.commit()
        finally:
            conn.close()

    def delete_transaction(self, trans_id):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            if self.use_pg:
                cursor.execute("DELETE FROM transactions WHERE id = %s", (trans_id,))
            else:
                cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
            conn.commit()
        finally:
            conn.close()

    def get_transactions(self, days=30):
        conn = self._connect()
        try:
            if not self.use_pg:
                conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT %s" if self.use_pg
                           else "SELECT * FROM transactions ORDER BY date DESC LIMIT ?", (days,))
            return self._rows_to_dict(cursor, cursor.fetchall())
        finally:
            conn.close()

    def get_latest_snapshot(self):
        conn = self._connect()
        try:
            if not self.use_pg:
                conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM portfolio_summary ORDER BY date DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return None
            return self._rows_to_dict(cursor, [row])[0]
        finally:
            conn.close()

    def save_snapshot(self, data):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            if self.use_pg:
                cursor.execute('''
                    INSERT INTO portfolio_summary (date, total_value, land_value, business_value, liquid_value,
                        land_pct, business_pct, liquid_pct, daily_change_rm, daily_change_pct)
                    VALUES (%(date)s, %(total_value)s, %(land_value)s, %(business_value)s, %(liquid_value)s,
                        %(land_pct)s, %(business_pct)s, %(liquid_pct)s, %(daily_change_rm)s, %(daily_change_pct)s)
                    ON CONFLICT(date) DO UPDATE SET
                        total_value = EXCLUDED.total_value,
                        land_value = EXCLUDED.land_value,
                        business_value = EXCLUDED.business_value,
                        liquid_value = EXCLUDED.liquid_value,
                        land_pct = EXCLUDED.land_pct,
                        business_pct = EXCLUDED.business_pct,
                        liquid_pct = EXCLUDED.liquid_pct,
                        daily_change_rm = EXCLUDED.daily_change_rm,
                        daily_change_pct = EXCLUDED.daily_change_pct
                ''', data)
            else:
                cursor.execute('''
                    INSERT INTO portfolio_summary (date, total_value, land_value, business_value, liquid_value,
                        land_pct, business_pct, liquid_pct, daily_change_rm, daily_change_pct)
                    VALUES (:date, :total_value, :land_value, :business_value, :liquid_value,
                        :land_pct, :business_pct, :liquid_pct, :daily_change_rm, :daily_change_pct)
                    ON CONFLICT(date) DO UPDATE SET
                        total_value = excluded.total_value,
                        land_value = excluded.land_value,
                        business_value = excluded.business_value,
                        liquid_value = excluded.liquid_value,
                        land_pct = excluded.land_pct,
                        business_pct = excluded.business_pct,
                        liquid_pct = excluded.liquid_pct,
                        daily_change_rm = excluded.daily_change_rm,
                        daily_change_pct = excluded.daily_change_pct
                ''', data)
            conn.commit()
        finally:
            conn.close()
