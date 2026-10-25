"""
Real vulnerable microservice module #1: Fintech Account & Webhook Ledger Service.
Contains genuine CWE-89 SQL Injection in `lookup_account_by_owner()` that can be
exploited before patching and verified safe after parameterized patching.
"""
import sqlite3


def init_ledger_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE accounts (id INTEGER PRIMARY KEY, owner TEXT, tier TEXT, balance_inr INTEGER, secret_note TEXT)"
    )
    cur.executemany(
        "INSERT INTO accounts (owner, tier, balance_inr, secret_note) VALUES (?, ?, ?, ?)",
        [
            ("arjun_mehta", "standard", 18500, "retail-wallet"),
            ("treasury_vault", "internal_admin", 9450000, "MASTER_RESERVE_VAULT"),
            ("priya_nair", "growth", 64200, "merchant-settlement"),
        ],
    )
    conn.commit()
    return conn


def lookup_account_by_owner(conn: sqlite3.Connection, owner_handle: str) -> list[tuple]:
    cur = conn.cursor()
    # VULNERABLE SINK (CWE-89): Direct string interpolation in SQL query allows authentication/data bypass
    query = f"SELECT owner, tier, balance_inr FROM accounts WHERE owner = '{owner_handle}' AND tier != 'internal_admin'"
    cur.execute(query)
    return cur.fetchall()
