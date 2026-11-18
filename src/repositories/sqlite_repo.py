import sqlite3
from threading import RLock


class WalletRepository:
    def __init__(self, database: str = "wallet.db"):
        self.conn = sqlite3.connect(database, check_same_thread=False, isolation_level=None, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.lock = RLock()
        with self.lock:
            self.conn.execute("PRAGMA busy_timeout=30000")
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL,
                    balance INTEGER NOT NULL CHECK(balance >= 0)
                );
                CREATE TABLE IF NOT EXISTS transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    key TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    transfer_id INTEGER,
                    type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

    def close(self):
        self.conn.close()
