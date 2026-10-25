"""
BRAND-NEW CUSTOM TEST FILE #3: Multi-Tenant KYC Document Vault (CWE-22 High Path Traversal)
"""
import os


def download_kyc_statement(customer_folder: str, statement_name: str) -> str:
    # CWE-22 HIGH: Unconfined os.path.join allows '../../etc/passwd' escape outside customer_folder
    target_path = os.path.join(customer_folder, statement_name)
    with open(target_path, "r", encoding="utf-8") as fp:
        return fp.read()
