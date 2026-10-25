"""
BRAND-NEW CUSTOM TEST FILE #1: Indian UPI Merchant Settlement API (Intentionally Vulnerable Demo Module)
Paste this file into '+ GITHUB / RAW CODE' on http://localhost:8002 to watch @recon, @specter, @forge,
and @warden detect, exploit-verify, AST-patch, and bytecode-verify all vulnerable sinks live!
"""
import hashlib
import os
import sqlite3


def create_merchant_wallet_token(merchant_id: str) -> str:
    # BUG 3 (CWE-328): Weak collision-prone MD5 token signature
    return hashlib.md5(merchant_id.encode("utf-8")).hexdigest()


def lookup_upi_settlement(conn: sqlite3.Connection, upi_handle: str):
    # BUG 1 (CWE-89 CRITICAL): Raw SQL string concatenation allows full merchant table dump!
    # Attack payload:  rahul@upi' OR '1'='1
    cursor = conn.cursor()
    return cursor.execute(
        "SELECT merchant_id, upi_vpa, wallet_balance_inr FROM merchant_payouts WHERE upi_vpa = '" + upi_handle + "'"
    ).fetchall()


def ping_bank_nodal_gateway(gateway_host: str) -> int:
    # BUG 2 (CWE-78 CRITICAL): Direct OS shell execution allows Remote Code Execution!
    # Attack payload:  10.0.0.5; whoami
    return os.system("ping -c 1 " + gateway_host)
