"""
Real vulnerable microservice module #3: Document Vault Storage Reader.
Contains genuine CWE-22 Path Traversal in `read_tenant_invoice()`.
"""
import os


def read_tenant_invoice(vault_dir: str, requested_filename: str) -> str:
    # VULNERABLE SINK (CWE-22): Naive os.path.join allows '../' escape outside tenant vault directory
    target_path = os.path.join(vault_dir, requested_filename)
    with open(target_path, "r", encoding="utf-8") as handle:
        return handle.read()
